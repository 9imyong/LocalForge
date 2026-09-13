#!/usr/bin/env python3
"""OpenAI-compatible baseline probe. Standard library only; no prompt logging."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import urllib.error
import urllib.request


def request(base, path, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode()
    return urllib.request.urlopen(urllib.request.Request(
        base + path, data=data, headers={'Content-Type': 'application/json'}), timeout=timeout)


def read_stream(lines, started, clock=time.perf_counter):
    first = last = None
    tokens = None
    server_timings = None
    done = False
    finished = False
    parts = []
    for line in lines:
        line = line.decode('utf-8').strip()
        if not line.startswith('data:'):
            continue
        raw = line[5:].strip()
        if raw == '[DONE]':
            done = True
            break
        event = json.loads(raw)
        if event.get('error'):
            raise RuntimeError('Streaming API returned an error')
        for choice in event.get('choices', []):
            content = choice.get('delta', {}).get('content')
            if content:
                now = clock()
                first = now if first is None else first
                last = now
                parts.append(content)
            finished |= choice.get('finish_reason') is not None
        if event.get('timings'):
            server_timings = event['timings']
        usage = event.get('usage') or {}
        if 'completion_tokens' in usage:
            tokens = usage['completion_tokens']
    if not done or not finished or not parts:
        raise RuntimeError('Incomplete stream: content, finish_reason and DONE required')
    if not isinstance(tokens, int) or tokens <= 0:
        raise RuntimeError('Missing completion token usage; cannot calculate token throughput')
    # Content chunks may contain multiple tokens: never equate chunks with tokens.
    elapsed = clock() - started
    return {'server_timings_optional': server_timings,
            'ttft_seconds': first - started,
            'request_seconds': elapsed, 'completion_tokens': tokens,
            'end_to_end_tokens_per_second': tokens / elapsed,
            'post_first_content_tokens_per_second_estimate':
                (tokens - 1) / (last - first) if tokens > 1 and last > first else None}


def gpu_sample(stop, samples):
    while not stop.is_set():
        try:
            p = subprocess.run(['nvidia-smi', '-i', os.getenv('GPU_ID', '0'),
                                '--query-gpu=memory.used,utilization.gpu',
                                '--format=csv,noheader,nounits'],
                               capture_output=True, text=True, timeout=5, check=True)
            mem, util = p.stdout.strip().split(',')
            samples.append({'memory_used_mib': int(mem), 'utilization_percent': int(util)})
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
        stop.wait(0.2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:' + os.getenv('PORT', '18000'))
    parser.add_argument('--model', default=os.getenv('MODEL_ALIAS', 'localforge-baseline'))
    parser.add_argument('--output', default='.local/results/smoke.json')
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--ready-timeout', type=float, default=300)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error('--runs must be positive')
    deadline = time.monotonic() + args.ready_timeout
    while True:
        try:
            with request(args.base_url, '/health', timeout=3) as response:
                if response.status == 200:
                    break
        except (OSError, urllib.error.URLError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError('Readiness deadline exceeded')
        time.sleep(1)
    ready_at = time.time()
    with request(args.base_url, '/v1/models') as response:
        models = json.load(response)['data']
    if args.model not in [m['id'] for m in models]:
        raise RuntimeError('Configured model not advertised')
    prompt = '파이썬 리스트와 튜플의 차이를 한국어로 설명하고 간단한 예제를 작성해 주세요.'
    payload = {'model': args.model, 'messages': [{'role': 'user', 'content': prompt}],
               'temperature': 0, 'max_tokens': 128, 'stream': False}
    with request(args.base_url, '/v1/chat/completions', payload) as response:
        data = json.load(response)
    if not data['choices'][0]['message']['content'].strip():
        raise RuntimeError('Empty chat completion')
    # Non-streaming request doubles as warmup. Measurements below are warm requests.
    payload.update(stream=True, stream_options={'include_usage': True})
    samples, runs = [], []
    stop = threading.Event()
    thread = threading.Thread(target=gpu_sample, args=(stop, samples), daemon=True)
    thread.start()
    try:
        for _ in range(args.runs):
            started = time.perf_counter()
            with request(args.base_url, '/v1/chat/completions', payload) as response:
                runs.append(read_stream(response, started))
    finally:
        stop.set()
        thread.join(timeout=6)
    start_file = Path('.local/results/start-time')
    result = {'configuration': {key: os.getenv(key) for key in
              ['LLAMA_REV', 'IMAGE', 'MODEL_REPO', 'MODEL_REV', 'MODEL_SHA256', 'CONTEXT', 'GPU_LAYERS']},
              'model_alias': args.model, 'runs': runs, 'warmup_requests': 1,
              'prompt_case': 'python-list-tuple-ko-v1', 'max_tokens': 128,
              'temperature': 0, 'concurrency': 1,
              'start_to_ready_seconds': ready_at - float(start_file.read_text()) if start_file.exists() else None,
              'gpu_samples': samples,
              'peak_device_memory_mib': max((x['memory_used_mib'] for x in samples), default=None),
              'peak_device_utilization_percent': max((x['utilization_percent'] for x in samples), default=None),
              'notes': ['GPU metrics are whole-device, including other processes.',
                        'Startup timing includes Docker startup and probe scheduling; not isolated model load.',
                        'Post-first-content rate is approximate because chunks are not token boundaries.',
                        'Repeated identical prompts may benefit from runtime prompt caching.']}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'gpu_samples'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
