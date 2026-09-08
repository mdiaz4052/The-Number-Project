"""Validate bounded mutation controls, inventory and execution evidence."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from Discovery import g_measurement_joint_inference_mutations as m


class JointMutationTests(unittest.TestCase):
    def evidence(self, fail=True):
        imports = {'Discovery.g_measurement_joint_inference': m.MODULE_PATH}
        return {'runner_status': 'completed', 'tests_run': 1,
                'failing_tests': m.CASES[0]['tests'] if fail else [], 'error_tests': [],
                'skipped_tests': [], 'successful': not fail,
                'validated_imports_before': imports, 'validated_imports_after': imports,
                'test_output': 'AssertionError: exact parameter sign mismatch' if fail else ''}

    def test_assertion_failure_and_survival(self):
        self.assertEqual(m.assess_execution(self.evidence(), m.CASES[0]['tests']), 'KILLED')
        self.assertEqual(m.assess_execution(self.evidence(False), m.CASES[0]['tests']), 'SURVIVED')

    def test_invalid_infrastructure_never_counts_as_kill(self):
        for field, value in [('runner_status', 'invalid'), ('tests_run', 0),
                             ('error_tests', ['test']), ('skipped_tests', ['test']),
                             ('test_output', 'commit result-driving source before emitting an artifact'),
                             ('test_output', 'SyntaxError'), ('test_output', 'ImportError'),
                             ('successful', True), ('validated_imports_after', {}),
                             ('failing_tests', ['unrelated.test'])]:
            record = self.evidence(); record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(m.j.InferenceError):
                m.assess_execution(record, m.CASES[0]['tests'])

    def test_controls_are_distinct_and_equivalent_change_is_executable(self):
        import ast
        source = (m.j.ROOT / m.MODULE_PATH).read_text()
        m.validate_definitions(source)
        production_tuples = {m.mutation_tuple(c) for c in m.CASES[2:]}
        self.assertNotIn(m.mutation_tuple(m.CASES[0]), production_tuples)
        self.assertEqual(len(m.CASES), 11)
        self.assertTrue(all(t.startswith(m.TEST_PREFIX) for c in m.CASES for t in c['tests']))
        c = m.CASES[1]
        self.assertNotEqual(ast.dump(ast.parse(source)), ast.dump(ast.parse(source.replace(c['old'], c['new']))))
        duplicated = (dict(m.CASES[2], id=m.CASES[0]['id'], category='calibration'),) + m.CASES[1:]
        with patch.object(m, 'CASES', duplicated), self.assertRaises(m.j.InferenceError):
            m.validate_definitions(source)

    def test_committed_evidence_and_tampering(self):
        artifact = m.j.read_json((m.j.ROOT / m.DEFAULT_OUTPUT).read_bytes())
        m.verify_artifact(artifact)
        source = (m.j.ROOT / m.MODULE_PATH).read_text()
        for change in ('omit', 'reorder', 'survive', 'calibration', 'patch_hash'):
            bad = deepcopy(artifact['records'])
            if change == 'omit': bad.pop()
            elif change == 'reorder': bad.reverse()
            elif change == 'survive': bad[-1]['outcome'] = 'SURVIVED'
            elif change == 'calibration': bad[2]['evidence']['failing_tests'] = bad[2]['tests']
            else: bad[-1]['applied_source_sha256'] = '0'*64
            with self.subTest(change=change), self.assertRaises(m.j.InferenceError):
                m.validate_records(bad, source)
        bad = deepcopy(artifact); bad['definitions_sha256'] = '0'*64
        with self.assertRaises(m.j.InferenceError): m.verify_artifact(bad)


if __name__ == '__main__':
    unittest.main()
