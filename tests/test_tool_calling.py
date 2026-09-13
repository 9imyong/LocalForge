import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'tool_smoke', Path(__file__).resolve().parents[1] / 'scripts/tool-calling-smoke.py')
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class ToolContractTest(unittest.TestCase):
    def test_content_only_is_not_a_call(self):
        with self.assertRaises(AssertionError):
            smoke.check_call({'content': '{"name":"add","arguments":{"a":2,"b":3}}'})

    def test_fragmented_sse_arguments(self):
        def event(delta, reason=None):
            return 'data: ' + json.dumps({'choices': [{'delta': delta, 'finish_reason': reason}]})
        events = [event({'tool_calls': [{'index': 0, 'id': 'call_1', 'type': 'function',
                                        'function': {'name': 'add', 'arguments': '{"a":'}}]}),
                  event({'tool_calls': [{'index': 0, 'function': {'arguments': '2,"b":3}'}}]}),
                  event({}, 'tool_calls'), 'data: [DONE]']
        self.assertEqual(smoke.collect_stream(events)['tool_calls'][0]['id'], 'call_1')
        with self.assertRaises(AssertionError):
            smoke.collect_stream(events[:-1])

    def test_incorrect_function_is_rejected(self):
        with self.assertRaises(AssertionError):
            smoke.check_call({'tool_calls': [{'id': 'call_1', 'type': 'function',
                              'function': {'name': 'shell', 'arguments': '{"a":2,"b":3}'}}]})


if __name__ == '__main__':
    unittest.main()
