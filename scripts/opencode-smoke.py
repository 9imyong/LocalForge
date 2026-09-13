#!/usr/bin/env python3
"""Exercise real OpenCode, preserve evidence, fail unless the agent fixes the fixture."""
import datetime
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (
    "Perform ALL steps using tools, in order:\n"
    "1. Run bash python3 -m unittest -v NOW to observe the failure before editing.\n"
    "2. Run bash ls.\n"
    "3. Read README.md, calculator.py and test_calculator.py.\n"
    "4. Run bash grep -n add calculator.py.\n"
    "5. Analyze the observed failure and edit only calculator.py. Do not change tests.\n"
    "6. Run bash python3 -m unittest -v again.\n"
    "7. Run bash git diff, briefly report cause/result, then STOP.\n"
    "Never stage or commit. No narration between tools. Do not skip step 1."
)


def run(args, cwd=ROOT, timeout=180, **kwargs):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True,
                          timeout=timeout, **kwargs)


def file_hashes(workspace):
    return {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in workspace.rglob('*') if p.is_file()
            and '.git' not in p.relative_to(workspace).parts
            and '__pycache__' not in p.relative_to(workspace).parts}


def assess_agent(events, before, after, before_code, after_code):
    """Do not confuse JSON-shaped model text with executed tools."""
    tools = [e['part'] for e in events if e.get('type') == 'tool_use'
             and e.get('part', {}).get('type') == 'tool']
    completed = [p for p in tools if p.get('state', {}).get('status') == 'completed']
    names = {p.get('tool') for p in completed}
    bash = [p['state'] for p in completed if p.get('tool') == 'bash']
    commands = [s.get('input', {}).get('command', '') for s in bash]
    # Shell equivalents count only when an actual completed bash call ran them.
    # Model text mentioning ls/grep does not qualify.
    argv = []
    for command in commands:
        try:
            argv.append(shlex.split(command))
        except ValueError:
            pass
    test_outputs = [s.get('output', '') for s in bash
                    if 'python3 -m unittest' in s.get('input', {}).get('command', '')]
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    checks = {
        'explored': 'glob' in names or any(a and a[0] == 'ls' for a in argv),
        'read': 'read' in names,
        'searched': 'grep' in names or any(a and a[0] in ('grep', 'rg') for a in argv),
        'edited': 'edit' in names,
        'shell': bool(bash),
        'agent_observed_failure': any('FAILED' in o for o in test_outputs),
        'agent_observed_pass': bool(test_outputs) and '\nOK' in test_outputs[-1],
        'agent_inspected_diff': any('git diff' in c for c in commands),
        'fixture_failed_before': before_code != 0,
        'fixture_passes_after': after_code == 0,
        'only_intended_change': changed == ['calculator.py'],
    }
    return {'checks': checks, 'passed': all(checks.values()),
            'completed_tools': sorted(names), 'changed_files': changed}


def streaming_probe(base, output):
    def request(path, body=None):
        req = urllib.request.Request(base + path, headers={'Content-Type': 'application/json'},
                                     data=None if body is None else json.dumps(body).encode())
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.load(response)

    session = request('/session', {'title': 'LocalForge streaming smoke'})['id']
    events, errors = [], []
    ready = threading.Event()

    def consume():
        try:
            with urllib.request.urlopen(base + '/event', timeout=100) as response:
                ready.set()
                for line in response:
                    if not line.startswith(b'data: '):
                        continue
                    event = json.loads(line[6:])
                    events.append(event)
                    if (event.get('type') == 'session.idle'
                            and event.get('properties', {}).get('sessionID') == session):
                        break
        except Exception as exc:
            errors.append(str(exc))
            ready.set()

    thread = threading.Thread(target=consume, daemon=True)
    thread.start()
    if not ready.wait(10) or errors:
        raise RuntimeError(f'OpenCode event subscription failed: {errors}')
    response = request('/session/' + session + '/message', {
        'agent': 'chat',
        'parts': [{'type': 'text', 'text': 'Explain what a Python function does in three short sentences.'}],
    })
    thread.join(3)
    (output / 'stream-events.json').write_text(json.dumps(events, indent=2))
    (output / 'stream-response.json').write_text(json.dumps(response, indent=2))
    deltas = [e['properties'].get('delta', '') for e in events
              if e.get('type') == 'message.part.delta'
              and e.get('properties', {}).get('sessionID') == session
              and e['properties'].get('field') == 'text']
    content = ''.join(p.get('text', '') for p in response.get('parts', []) if p.get('type') == 'text')
    return {'passed': len(deltas) > 1 and ''.join(deltas) == content and bool(content)
            and not response.get('info', {}).get('error') and not errors,
            'text_delta_count': len(deltas), 'text': content, 'errors': errors}


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / '.local/results/opencode' / stamp
    output.mkdir(parents=True)
    workspace = Path(tempfile.mkdtemp(prefix='localforge-agent-'))
    shutil.copytree(ROOT / 'tests/fixtures/agent-repo', workspace, dirs_exist_ok=True)
    for args in [['git', 'init', '-q'], ['git', 'add', '.'],
                 ['git', '-c', 'user.name=LocalForge', '-c', 'user.email=fixture@localhost',
                  'commit', '-qm', 'fixture']]:
        result = run(args, cwd=workspace)
        if result.returncode:
            raise RuntimeError(result.stderr)
    before = file_hashes(workspace)
    initial = run(['python3', '-m', 'unittest', '-v'], cwd=workspace)
    (output / 'tests-before.txt').write_text(initial.stdout + initial.stderr)
    summary = {'workspace': str(workspace), 'started_at': stamp, 'passed': False}
    name = 'localforge-opencode-smoke-' + str(os.getpid())
    env = {**os.environ, 'LOCALFORGE_OPENCODE_CONTAINER': name}
    launcher = ['bash', str(ROOT / 'scripts/opencode.sh'), str(workspace)]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    gpu = None
    gpu_file = (output / 'gpu.csv').open('w')
    server = None
    try:
        gpu = subprocess.Popen(['nvidia-smi', '--query-gpu=timestamp,name,memory.used,utilization.gpu',
                                '--format=csv', '-lms', '200'], stdout=gpu_file, stderr=subprocess.STDOUT)
        prompt = run(launcher + ['run', '--agent', 'chat', '--title', 'LocalForge prompt smoke',
                                '--format', 'json', 'Reply with exactly LOCALFORGE_OK.'], env=env)
        (output / 'prompt.jsonl').write_text(prompt.stdout)
        (output / 'prompt.stderr').write_text(prompt.stderr)
        prompt_events = [json.loads(line) for line in prompt.stdout.splitlines() if line.startswith('{')]
        summary['prompt_exact_match'] = any(
            e.get('type') == 'text' and e.get('part', {}).get('text', '').strip() == 'LOCALFORGE_OK'
            for e in prompt_events)
        # Connectivity checks a completed nonempty response; exact instruction following
        # is a separate model-quality observation (e.g. an extra trailing period).
        summary['prompt_passed'] = bool(prompt.returncode == 0
            and not any(e.get('type') == 'error' for e in prompt_events)
            and any(e.get('type') == 'text' and e.get('part', {}).get('text', '').strip()
                    for e in prompt_events)
            and any(e.get('type') == 'step_finish' and e.get('part', {}).get('reason') == 'stop'
                    for e in prompt_events))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        with (output / 'opencode-server.log').open('w') as log:
            server = subprocess.Popen(launcher + ['serve', '--hostname', '127.0.0.1', '--port', str(port)],
                                      stdout=log, stderr=subprocess.STDOUT, env=env)
            base = f'http://127.0.0.1:{port}'
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError('OpenCode server exited; inspect opencode-server.log')
                try:
                    with urllib.request.urlopen(base + '/global/health', timeout=1) as r:
                        summary['opencode_health'] = json.load(r)
                    break
                except OSError:
                    time.sleep(0.5)
            else:
                raise RuntimeError('OpenCode server readiness timeout')
            summary['stream'] = streaming_probe(base, output)
        run(['docker', 'stop', name], timeout=30)
        server.wait(timeout=10)
        agent = run(launcher + ['run', '--agent', 'localforge', '--title', 'LocalForge fixture e2e',
                               '--format', 'json', PROMPT], env=env)
        (output / 'agent.jsonl').write_text(agent.stdout)
        (output / 'agent.stderr').write_text(agent.stderr)
        events = [json.loads(line) for line in agent.stdout.splitlines() if line.startswith('{')]
        final = run(['python3', '-m', 'unittest', '-v'], cwd=workspace)
        (output / 'tests-after.txt').write_text(final.stdout + final.stderr)
        (output / 'fixture.diff').write_text(run(['git', 'diff'], cwd=workspace).stdout)
        (output / 'fixture-status.txt').write_text(run(['git', 'status', '--porcelain'], cwd=workspace).stdout)
        summary['agent'] = assess_agent(events, before, file_hashes(workspace), initial.returncode, final.returncode)
        summary['agent_exit_code'] = agent.returncode
        summary['passed'] = bool(summary['prompt_passed'] and summary['stream']['passed']
                                 and summary['agent']['passed'] and agent.returncode == 0)
    except Exception as exc:
        summary['error'] = str(exc)
    finally:
        run(['docker', 'rm', '-f', name], timeout=30)
        if server and server.poll() is None:
            server.wait(timeout=10)
        if gpu:
            gpu.terminate()
            gpu.wait(timeout=5)
        gpu_file.close()
        logs = run(['docker', 'logs', '--since', started,
                    os.environ.get('LOCALFORGE_INFERENCE_CONTAINER', 'localforge-baseline')])
        (output / 'inference-server.log').write_text(logs.stdout + logs.stderr)
        try:
            with (output / 'gpu.csv').open() as stream:
                samples = [{k.strip(): v.strip() for k, v in row.items()} for row in csv.DictReader(stream)]
            memory = [int(row['memory.used [MiB]'].split()[0]) for row in samples]
            utilization = [int(row['utilization.gpu [%]'].split()[0]) for row in samples]
            summary['evidence'] = {
                'gpu_samples': len(samples),
                'gpu_memory_mib_range': [min(memory), max(memory)],
                'gpu_utilization_percent_range': [min(utilization), max(utilization)],
                'server_processed_tasks': (logs.stdout + logs.stderr).count('processing task, is_child'),
            }
            summary['evidence']['passed'] = bool(max(utilization) > 0 and logs.returncode == 0
                                                  and summary['evidence']['server_processed_tasks'] > 0)
        except (KeyError, ValueError, AttributeError) as exc:
            summary['evidence'] = {'passed': False, 'error': str(exc)}
        summary['passed'] = summary['passed'] and summary['evidence']['passed']
        (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'results': str(output), **summary}, indent=2, ensure_ascii=False))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
