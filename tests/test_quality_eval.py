import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('quality_eval', ROOT / 'scripts/quality-eval.py')
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


class LetterTests(unittest.TestCase):
    def test_template_only_allows_one_trailing_newline_difference(self):
        self.assertTrue(quality.template_matches('template\n', 'template'))
        self.assertTrue(quality.template_matches('template\n', 'template\n'))
        self.assertFalse(quality.template_matches('template\n\n', 'template'))
        self.assertFalse(quality.template_matches(' template', 'template'))

    def test_normal_korean_technical_terms_and_symbols(self):
        result = quality.analyze('한글 HTTP café 123、。! 😀 # *')
        self.assertEqual(result['hangul_letters'], 2)
        self.assertEqual(result['latin_letters'], 8)
        self.assertEqual(result['other_letters'], 0)
        self.assertEqual(result['status'], 'no_candidate_detected')

    def test_foreign_letters_and_hangul_jamo(self):
        result = quality.analyze('한국어 中文 あカ Ω Ж 한')
        self.assertEqual(result['other_letters'], 6)
        self.assertEqual(result['hangul_letters'], 4)
        self.assertEqual(result['status'], 'needs_manual_review')

    def test_fences_and_inline_code_are_excluded(self):
        result = quality.analyze('한국어 `中文` ``x`あ``\n~~~python\n中文\n~~~\n```py\nカ\n```')
        self.assertEqual(result['other_letters'], 0)
        self.assertEqual(result['hangul_letters'], 3)

    def test_mismatched_fence_does_not_end_code(self):
        self.assertEqual(quality.analyze('````\n```\n中文\n````\n한국어')['other_letters'], 0)

    def test_code_only_or_symbols_are_not_automatic_pass(self):
        for text in ('```python\nprint(1)\n```', ' 123!?', '~~~\n中文'):
            result = quality.analyze(text)
            self.assertEqual(result['status'], 'not_assessable')
            self.assertIsNone(result['other_letter_ratio'])

    def test_english_only_requires_manual_review(self):
        self.assertEqual(quality.analyze('Only English')['status'], 'needs_manual_review')


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.suite = quality.load_suite(ROOT / 'evals/korean-coding-v1.json')
        self.conditions = {'identity': {'model': 'fixture'}, 'suite_sha256': quality.digest(self.suite),
                           'case_ids': [c['id'] for c in self.suite['cases']],
                           'generation': {'temperature': 0, 'seed': 42, 'max_tokens': 768}}

    @staticmethod
    def response(content='한국어 설명', finish='stop'):
        return io.StringIO(json.dumps({'choices': [{'message': {'content': content}, 'finish_reason': finish}]}))

    def successful(self):
        return quality.run_suite(self.suite, self.conditions, '', 'fixture',
                                 send=lambda *a, **kw: self.response())

    def test_all_cases_sent_and_manual_pending(self):
        sent = []

        def send(base, path, payload, timeout):
            sent.append(payload)
            return self.response()

        result = quality.run_suite(self.suite, self.conditions, '', 'fixture', send)
        self.assertEqual(len(sent), 8)
        self.assertEqual([p['messages'][0]['content'] for p in sent], [c['prompt'] for c in self.suite['cases']])
        self.assertTrue(all(p['seed'] == 42 and p['temperature'] == 0 for p in sent))
        self.assertEqual(result['status'], 'complete')
        self.assertTrue(all(c['manual']['status'] == 'pending' for c in result['cases']))

    def test_failed_empty_and_truncated_cases_do_not_stop_remaining(self):
        calls = []

        def send(*a, **kw):
            calls.append(1)
            if len(calls) == 1:
                raise OSError('private URL must not appear in artifact')
            if len(calls) == 2:
                return self.response('')
            return self.response(finish='length' if len(calls) == 3 else 'stop')

        result = quality.run_suite(self.suite, self.conditions, '', 'fixture', send)
        self.assertEqual(len(calls), 8)
        self.assertEqual(result['status'], 'incomplete')
        self.assertEqual([c['status'] for c in result['cases'][:4]], ['error', 'error', 'incomplete', 'ok'])
        self.assertNotIn('private URL', json.dumps(result))
        with self.assertRaises(ValueError):
            quality.compare(result, result)

    def test_compare_rejects_changed_conditions_and_missing_cases(self):
        a = self.successful()
        self.assertEqual(len(quality.compare(a, a)['cases']), 8)
        b = copy.deepcopy(a)
        b['conditions']['identity']['model'] = 'different'
        b['fingerprint'] = quality.digest(b['conditions'])
        with self.assertRaises(ValueError):
            quality.compare(a, b)
        b = copy.deepcopy(a)
        b['cases'].pop()
        with self.assertRaises(ValueError):
            quality.compare(a, b)

    def test_compare_reports_delta_without_grading(self):
        a = self.successful()
        b = copy.deepcopy(a)
        b['cases'][0]['response'] = '한국어 中文'
        b['cases'][0]['automatic'] = quality.analyze(b['cases'][0]['response'])
        result = quality.compare(a, b)
        self.assertEqual(result['cases'][0]['other_letters_delta'], 2)
        self.assertEqual(result['manual_verdict'], 'not_graded')

    def test_duplicate_case_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'suite.json'
            self.suite['cases'].append(self.suite['cases'][0])
            path.write_text(json.dumps(self.suite))
            with self.assertRaises(ValueError):
                quality.load_suite(path)

    def test_cli_writes_partial_result_and_does_not_overwrite(self):
        result = self.successful()
        result['status'] = 'incomplete'
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'result.json'
            with patch.object(sys, 'argv', ['quality-eval', '--output', str(output)]), \
                    patch.object(quality, 'baseline_identity', return_value={}), \
                    patch.object(quality, 'run_suite', return_value=result):
                self.assertEqual(quality.main(), 1)
                self.assertEqual(json.loads(output.read_text())['status'], 'incomplete')
                original = output.read_bytes()
                with self.assertRaises(SystemExit):
                    quality.main()
                self.assertEqual(output.read_bytes(), original)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.env = {'LLAMA_REV': 'abcdef0123456789', 'IMAGE': 'fixture', 'MODEL_REPO': 'repo',
                    'MODEL_REV': 'revision', 'MODEL_FILE': 'model.gguf', 'MODEL_SHA256': 'hash',
                    'CONTEXT': '4096', 'GPU_LAYERS': '99', 'GPU_ID': '0', 'CHAT_TEMPLATE_FILE': ''}
        self.container = {'State': {'Running': True}, 'Image': 'image-id',
                          'NetworkSettings': {'Ports': {'8080/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '18000'}]}},
                          'Config': {'Cmd': ['--model', '/models/model.gguf', '--alias', 'fixture',
                                             '--ctx-size', '4096', '--n-gpu-layers', '99', '--parallel', '1']},
                          'HostConfig': {'DeviceRequests': [{'DeviceIDs': ['0']}]},
                          'Mounts': [{'Destination': '/models', 'Source': '/fixture'}]}
        self.props = {'build_info': 'b1-abcdef0', 'chat_template': 'builtin template',
                      'default_generation_settings': {'n_ctx': 4096}}

    def identity(self, actual_hash='hash'):
        def send(base, path):
            return io.StringIO(json.dumps(self.props if path == '/props' else {'data': [{'id': 'fixture'}]}))

        with patch.dict(quality.os.environ, self.env, clear=True), \
                patch.object(quality, 'docker_json', side_effect=[self.container, {'Id': 'image-id'}]), \
                patch.object(quality, 'file_hash', return_value=actual_hash), \
                patch.object(quality, 'request', side_effect=send):
            return quality.baseline_identity('http://fixture', 'fixture')

    def test_builtin_template_and_actual_image_recorded(self):
        identity = self.identity()
        self.assertEqual(identity['template_source'], 'builtin')
        self.assertIsNone(identity['template_file_sha256'])
        self.assertEqual(len(identity['template_sha256']), 64)
        self.assertEqual(identity['image_id'], 'image-id')

    def test_changed_actual_model_refused(self):
        with self.assertRaisesRegex(ValueError, 'Actual model SHA256'):
            self.identity('wrong-hash')

    def test_changed_runtime_or_effective_context_refused(self):
        self.props['build_info'] = 'b1-fedcba0'
        with self.assertRaisesRegex(ValueError, 'Runtime build'):
            self.identity()
        self.props['build_info'] = 'b1-abcdef0'
        self.props['default_generation_settings']['n_ctx'] = 2048
        with self.assertRaisesRegex(ValueError, 'effective context'):
            self.identity()

    def test_running_config_mismatch_refused(self):
        self.container['Config']['Cmd'][5] = '2048'
        with self.assertRaisesRegex(ValueError, 'Running model/context'):
            self.identity()

    def test_option_without_value_is_a_configuration_error(self):
        self.container['Config']['Cmd'] = ['--model']
        with self.assertRaisesRegex(ValueError, 'Running model/context'):
            self.identity()


if __name__ == '__main__':
    unittest.main()
