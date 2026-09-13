#!/usr/bin/env python3
"""Direct HTTP tool contract checks; no OpenCode, proxy, or text-to-tool fallback."""
import argparse
import datetime
import json
from pathlib import Path
import urllib.request

TOOL = {'type': 'function', 'function': {
    'name': 'add', 'description': 'Add two integers',
    'parameters': {'type': 'object', 'properties': {
        'a': {'type': 'integer'}, 'b': {'type': 'integer'}}, 'required': ['a', 'b']}}}
MESSAGES = [{'role': 'user', 'content': 'What is 2 plus 3? Use add.'}]


def check_call(message):
    calls = message.get('tool_calls', [])
    assert len(calls) == 1, 'Expected one structured tool call, not content text'
    call = calls[0]
    assert call.get('id') and call.get('type') == 'function', 'Missing call ID/type'
    assert call['function']['name'] == 'add', 'Unexpected function'
    assert json.loads(call['function']['arguments']) == {'a': 2, 'b': 3}, 'Wrong arguments'
    return call


def collect_stream(lines):
    calls, reason, done = {}, None, False
    for line in lines:
        if not line.startswith('data: '):
            continue
        if line[6:].strip() == '[DONE]':
            done = True
            break
        event = json.loads(line[6:])
        assert 'error' not in event, event
        for choice in event.get('choices', []):
            reason = choice.get('finish_reason') or reason
            for delta in choice.get('delta', {}).get('tool_calls', []):
                call = calls.setdefault(delta['index'], {
                    'id': '', 'type': '', 'function': {'name': '', 'arguments': ''}})
                for key in ['id', 'type']:
                    if delta.get(key):
                        call[key] = delta[key]
                for key in ['name', 'arguments']:
                    call['function'][key] += delta.get('function', {}).get(key, '')
    assert done and reason == 'tool_calls', 'Incomplete stream or missing tool_calls finish'
    message = {'role': 'assistant', 'content': '', 'tool_calls': list(calls.values())}
    check_call(message)
    return message


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:18000/v1')
    parser.add_argument('--model', default='localforge-baseline')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / '.local/results/tool-calling' / stamp
    output.mkdir(parents=True)
    results = {}
    base = {'model': args.model, 'messages': MESSAGES, 'tools': [TOOL],
            'temperature': 0, 'max_tokens': 128}

    def request(name, body):
        (output / (name + '-request.json')).write_text(json.dumps(body, indent=2))
        req = urllib.request.Request(args.base_url.rstrip('/') + '/chat/completions',
                                     data=json.dumps(body).encode(),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read().decode()
        (output / (name + '-response.txt')).write_text(raw)
        return raw.splitlines() if body.get('stream') else json.loads(raw)

    for name, choice in [('auto', 'auto'), ('required', 'required'),
                         ('named', {'type': 'function', 'function': {'name': 'add'}}),
                         ('stream', 'auto'), ('none', 'none')]:
        try:
            response = request(name, {**base, 'tool_choice': choice, 'stream': name == 'stream'})
            if name == 'stream':
                message = collect_stream(response)
            else:
                message = response['choices'][0]['message']
                if name == 'none':
                    assert not message.get('tool_calls'), 'none must not execute a tool'
                    results[name] = {'passed': True}
                    continue
                assert response['choices'][0]['finish_reason'] == 'tool_calls', 'Wrong finish reason'
                check_call(message)
            # Execute only the hard-coded arithmetic fixture, never model-generated code.
            call = check_call(message)
            arguments = json.loads(call['function']['arguments'])
            result = arguments['a'] + arguments['b']
            followup = request(name + '-followup', {**base, 'tool_choice': 'auto', 'messages': [
                *MESSAGES, message, {'role': 'tool', 'tool_call_id': call['id'], 'content': str(result)}]})
            final = followup['choices'][0]
            assert final['finish_reason'] == 'stop', 'Tool loop did not finish'
            assert not final['message'].get('tool_calls'), 'Unexpected repeated tool call'
            assert '5' in final['message'].get('content', ''), 'Tool result not reflected'
            results[name] = {'passed': True, 'call_id_present': True, 'followup': final['message']['content']}
        except Exception as exc:
            results[name] = {'passed': False, 'error': str(exc)}
    summary = {'passed': all(r['passed'] for r in results.values()), 'cases': results}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'results': str(output), **summary}, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
