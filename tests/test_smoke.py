import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('smoke', Path(__file__).parents[1] / 'scripts/smoke.py')
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class StreamTests(unittest.TestCase):
    def test_usage_not_chunk_count(self):
        lines = [b'data: {"choices":[{"delta":{"role":"assistant"}}]}\n',
                 'data: {"choices":[{"delta":{"content":"안녕"}}]}\n'.encode(),
                 b'data: {"choices":[{"delta":{"content":"!"},"finish_reason":"stop"}]}\n',
                 b'data: {"choices":[],"usage":{"completion_tokens":7}}\n', b'data: [DONE]\n']
        clock = iter([11., 12., 13.])
        r = smoke.read_stream(lines, 10., lambda: next(clock))
        self.assertEqual(r['completion_tokens'], 7)
        self.assertEqual(r['ttft_seconds'], 1)
        self.assertEqual(r['post_first_content_tokens_per_second_estimate'], 6)

    def test_truncated_stream_rejected(self):
        with self.assertRaises(RuntimeError):
            smoke.read_stream([b'data: {"choices":[{"delta":{"content":"hello"}}]}'], 0)

    def test_missing_usage_rejected(self):
        with self.assertRaises(RuntimeError):
            smoke.read_stream([b'data: {"choices":[{"delta":{"content":"hello"},"finish_reason":"stop"}]}',
                               b'data: [DONE]'], 0)

    def test_error_event_rejected(self):
        with self.assertRaises(RuntimeError):
            smoke.read_stream([b'data: {"error":{"message":"failed"}}'], 0)
