import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'opencode_smoke', Path(__file__).resolve().parents[1] / 'scripts/opencode-smoke.py')
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class AgentEvidenceTest(unittest.TestCase):
    def test_text_claims_are_not_tool_execution(self):
        events = [{'type': 'text', 'part': {
            'text': 'Tests passed. {"name":"edit","arguments":{}}'}}]
        result = smoke.assess_agent(events, {'calculator.py': 'old'},
                                    {'calculator.py': 'new'}, 1, 0)
        self.assertFalse(result['passed'])
        self.assertEqual(result['completed_tools'], [])

    def test_full_evidence_requires_no_unintended_changes(self):
        def tool(name, command='', output=''):
            return {'type': 'tool_use', 'part': {'type': 'tool', 'tool': name,
                    'state': {'status': 'completed', 'input': {'command': command}, 'output': output}}}
        events = [tool(name) for name in ('read', 'edit')]
        events += [tool('bash', 'ls', 'calculator.py'),
                   tool('bash', 'grep -n add calculator.py', '1:def add(a, b):'),
                   tool('bash', 'python3 -m unittest -v', 'FAILED (failures=1)'),
                   tool('bash', 'python3 -m unittest -v', 'Ran 1 test\nOK'),
                   tool('bash', 'git diff', '-return a - b\n+return a + b')]
        before = {'calculator.py': 'old', 'test_calculator.py': 'original'}
        after = {**before, 'calculator.py': 'new'}
        self.assertTrue(smoke.assess_agent(events, before, after, 1, 0)['passed'])
        after['test_calculator.py'] = 'tampered'
        self.assertFalse(smoke.assess_agent(events, before, after, 1, 0)['passed'])


if __name__ == '__main__':
    unittest.main()
