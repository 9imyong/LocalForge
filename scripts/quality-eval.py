#!/usr/bin/env python3
"""Fixed local baseline quality observations; never execute generated code."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unicodedata
import uuid

from smoke import request

ROOT = Path(__file__).resolve().parents[1]
DETECTOR = 'unicode-prose-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def prose_only(text):
    """Exclude fenced and inline code; unclosed fences consume the remainder."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line.rstrip('\r\n'))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        lines.append(line)
    return re.sub(r'(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)', '', ''.join(lines), flags=re.S)


def analyze(text):
    prose = unicodedata.normalize('NFC', prose_only(text))
    counts = {'hangul_letters': 0, 'latin_letters': 0, 'other_letters': 0}
    others = {}
    for ch in prose:
        if not unicodedata.category(ch).startswith('L'):
            continue
        name = unicodedata.name(ch, '')
        if name.startswith('HANGUL'):
            counts['hangul_letters'] += 1
        elif 'LATIN' in name:
            counts['latin_letters'] += 1
        else:
            counts['other_letters'] += 1
            others[ch] = others.get(ch, 0) + 1
    total = sum(counts.values())
    return {**counts, 'counted_letters': total,
            'other_letter_ratio': counts['other_letters'] / total if total else None,
            'other_characters': others,
            'status': ('not_assessable' if not total else
                       'needs_manual_review' if counts['other_letters'] or not counts['hangul_letters']
                       else 'no_candidate_detected')}


def load_suite(path):
    suite = json.loads(Path(path).read_text())
    if not isinstance(suite.get('version'), str) or not suite.get('cases'):
        raise ValueError('Suite version and nonempty cases required')
    seen = set()
    for case in suite['cases']:
        if (not isinstance(case.get('id'), str) or not case['id'] or case['id'] in seen
                or case.get('category') not in ('korean', 'coding')
                or not isinstance(case.get('prompt'), str) or not case['prompt'].strip()
                or not isinstance(case.get('rubric'), list) or not case['rubric']
                or not all(isinstance(x, str) and x.strip() for x in case['rubric'])):
            raise ValueError('Invalid or duplicate suite case')
        seen.add(case['id'])
    return suite


def docker_json(*args):
    return json.loads(subprocess.check_output(['docker', *args], text=True, timeout=30))[0]


def template_matches(file_text, effective):
    # Pinned server omits one final LF in /props. Do not strip meaningful whitespace.
    return effective in (file_text, file_text.removesuffix('\n'))


def baseline_identity(base, model):
    """Validate declared configuration against the running local container."""
    keys = ('LLAMA_REV', 'IMAGE', 'MODEL_REPO', 'MODEL_REV', 'MODEL_FILE',
            'MODEL_SHA256', 'CONTEXT', 'GPU_LAYERS', 'GPU_ID')
    declared = {key: os.environ[key] for key in keys}
    container = docker_json('inspect', 'localforge-baseline')
    if not container['State']['Running']:
        raise ValueError('Baseline container is not running')
    image = docker_json('image', 'inspect', declared['IMAGE'])
    if image['Id'] != container['Image']:
        raise ValueError('Running image differs from configured IMAGE')
    ports = container['NetworkSettings']['Ports'].get('8080/tcp') or []
    if not any(p['HostIp'] == '127.0.0.1' and p['HostPort'] == os.getenv('PORT', '18000') for p in ports):
        raise ValueError('Baseline port binding differs from configuration')
    cmd = container['Config']['Cmd']

    def option(name):
        if name not in cmd:
            return None
        index = cmd.index(name) + 1
        return cmd[index] if index < len(cmd) else None

    expected = {'--model': '/models/' + declared['MODEL_FILE'], '--alias': model,
                '--ctx-size': declared['CONTEXT'], '--n-gpu-layers': declared['GPU_LAYERS'],
                '--parallel': '1'}
    if any(option(k) != v for k, v in expected.items()):
        raise ValueError('Running model/context/GPU layers differ from configuration')
    devices = container['HostConfig'].get('DeviceRequests') or []
    if not any(d.get('DeviceIDs') == [declared['GPU_ID']] for d in devices):
        raise ValueError('GPU device differs from configuration')
    mounts = {m['Destination']: m for m in container['Mounts']}
    model_path = Path(mounts['/models']['Source']) / declared['MODEL_FILE']
    if file_hash(model_path) != declared['MODEL_SHA256']:
        raise ValueError('Actual model SHA256 differs from configuration')
    with request(base, '/props') as response:
        props = json.load(response)
    with request(base, '/v1/models') as response:
        models = json.load(response)
    if model not in [m['id'] for m in models['data']]:
        raise ValueError('Configured model not advertised')
    build = props['build_info']
    commit = build.rsplit('-', 1)[-1]
    if len(commit) < 7 or not declared['LLAMA_REV'].startswith(commit):
        raise ValueError('Runtime build does not match declared commit')
    template = props['chat_template']
    if not isinstance(template, str) or not template:
        raise ValueError('Server did not expose its effective template')
    template_file = os.getenv('CHAT_TEMPLATE_FILE', '')
    source = 'builtin'
    template_file_sha256 = None
    if template_file:
        source = 'file'
        configured = Path(template_file)
        if not configured.is_absolute():
            configured = ROOT / configured
        mounted = mounts.get('/config/chat-template.jinja', {}).get('Source')
        if (option('--chat-template-file') != '/config/chat-template.jinja' or not mounted
                or Path(mounted).resolve() != configured.resolve()
                or not template_matches(configured.read_text(), template)):
            raise ValueError('Effective template differs from configured file')
        template_file_sha256 = file_hash(configured)
    elif option('--chat-template-file') is not None:
        raise ValueError('Expected builtin template, found file override')
    if props['default_generation_settings']['n_ctx'] != int(declared['CONTEXT']):
        raise ValueError('Server effective context differs from configuration')
    return {'declared': declared, 'image_id': container['Image'], 'server_build': build,
            'model_alias': model, 'template_source': source,
            'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
            'template_file_sha256': template_file_sha256,
            'server_generation_defaults': props['default_generation_settings']}


def run_suite(suite, conditions, base, model, send=request):
    results = []
    for case in suite['cases']:
        row = {'id': case['id'], 'category': case['category'], 'prompt': case['prompt'],
               'manual': {'status': 'pending', 'rubric': case['rubric']},
               'status': 'error', 'response': None, 'automatic': None}
        try:
            payload = {'model': model, 'messages': [{'role': 'user', 'content': case['prompt']}],
                       **conditions['generation'], 'stream': False}
            with send(base, '/v1/chat/completions', payload, timeout=120) as response:
                data = json.load(response)
            choice = data['choices'][0]
            content = choice['message']['content']
            if not isinstance(content, str) or not content.strip():
                raise ValueError('Empty or non-text response')
            row.update(response=content, finish_reason=choice.get('finish_reason'),
                       usage=data.get('usage'), automatic=analyze(content))
            row['status'] = 'ok' if choice.get('finish_reason') == 'stop' else 'incomplete'
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            # Persist type only: transport messages can include private URLs or server data.
            row['error'] = type(exc).__name__
        results.append(row)
    return {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
            'conditions': conditions, 'fingerprint': digest(conditions),
            'status': 'complete' if all(r['status'] == 'ok' for r in results) else 'incomplete',
            'cases': results}


def compare(a, b):
    for result in (a, b):
        conditions = result['conditions']
        if (result.get('schema_version') != 1 or result.get('status') != 'complete'
                or result.get('fingerprint') != digest(conditions)
                or not result.get('cases')
                or any(r.get('status') != 'ok' for r in result['cases'])
                or [r['id'] for r in result['cases']] != conditions['case_ids']):
            raise ValueError('Incomplete or inconsistent result cannot be compared')
    if a['fingerprint'] != b['fingerprint']:
        raise ValueError('Conditions differ; comparison refused')
    return {'fingerprint': a['fingerprint'], 'manual_verdict': 'not_graded',
            'cases': [{'id': x['id'], 'response_changed': x['response'] != y['response'],
                       'other_letters_before': x['automatic']['other_letters'],
                       'other_letters_after': y['automatic']['other_letters'],
                       'other_letters_delta': y['automatic']['other_letters'] - x['automatic']['other_letters']}
                      for x, y in zip(a['cases'], b['cases'])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', type=Path, default=ROOT / 'evals/korean-coding-v1.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--compare', nargs=2, type=Path, metavar=('BEFORE', 'AFTER'))
    parser.add_argument('--max-tokens', type=int, default=768)
    args = parser.parse_args()
    try:
        if args.compare:
            print(json.dumps(compare(*(json.loads(p.read_text()) for p in args.compare)), ensure_ascii=False, indent=2))
            return 0
        if args.max_tokens < 1:
            parser.error('--max-tokens must be positive')
        output = args.output or ROOT / '.local/results/quality' / (
            datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8] + '.json')
        if output.exists():
            raise ValueError('Output already exists; refusing to overwrite')
        suite = load_suite(args.suite)
        base = 'http://127.0.0.1:' + os.environ.get('PORT', '18000')
        model = os.environ.get('MODEL_ALIAS', 'localforge-baseline')
        identity = baseline_identity(base, model)
        conditions = {'identity': identity, 'suite_version': suite['version'], 'suite_sha256': digest(suite),
                      'case_ids': [c['id'] for c in suite['cases']], 'detector': DETECTOR,
                      'unicode_version': unicodedata.unidata_version,
                      'generation': {'temperature': 0, 'seed': 42, 'max_tokens': args.max_tokens},
                      'concurrency': 1}
        result = run_suite(suite, conditions, base, model)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f"status={result['status']} cases={len(result['cases'])} result={output}")
        return 0 if result['status'] == 'complete' else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'Evaluation failed ({type(exc).__name__}): {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
