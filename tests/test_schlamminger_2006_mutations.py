"""The bounded mutation evidence cannot promote invalid executions to kills."""

from copy import deepcopy
import unittest

from Discovery import schlamminger_2006_mutations as m
from Discovery.rounding_consistency import RoundingError


class SchlammingerMutationTests(unittest.TestCase):
    def evidence(self, fail=True):
        definition = m.CASES[0]
        imports = {'Discovery.schlamminger_2006_rounding_consistency': m.MODULE_PATH}
        return {'runner_status': 'completed', 'tests_run': 1,
                'failing_tests': definition['tests'] if fail else [], 'error_tests': [],
                'skipped_tests': [], 'successful': not fail,
                'validated_imports_before': imports, 'validated_imports_after': imports,
                'test_output': 'AssertionError: independent arithmetic mismatch' if fail else ''}

    def test_assertion_failure_and_equivalent_survival_are_distinct(self):
        self.assertEqual(m.assess_execution(self.evidence(), m.CASES[0]['tests']), 'KILLED')
        self.assertEqual(m.assess_execution(self.evidence(False), m.CASES[0]['tests']), 'SURVIVED')

    def test_infrastructure_errors_skips_and_freshness_are_invalid(self):
        for field, value in [('runner_status', 'invalid'), ('tests_run', 0),
                             ('error_tests', ['test']), ('skipped_tests', ['test']),
                             ('test_output', 'commit result-driving source before emitting an artifact'),
                             ('successful', True), ('validated_imports_after', {}),
                             ('failing_tests', ['unrelated.test'])]:
            record = self.evidence(); record[field] = value
            with self.subTest(field=field), self.assertRaises(RoundingError):
                m.assess_execution(record, m.CASES[0]['tests'])

    def test_mutation_inventory_is_bounded_and_wrapper_only(self):
        self.assertEqual(len(m.CASES), 10)
        self.assertEqual(len({case['id'] for case in m.CASES}), 10)
        self.assertEqual({case['path'] for case in m.CASES}, {m.MODULE_PATH})
        self.assertEqual([case['expected'] for case in m.CASES[:2]], ['KILLED', 'SURVIVED'])
        source = (m.s.ROOT / m.MODULE_PATH).read_text()
        for case in m.CASES:
            self.assertEqual(source.count(case['old']), 1)
            self.assertTrue(all('SchlammingerBehaviorTests.' in test for test in case['tests']))

    def test_committed_mutation_evidence_and_inventory(self):
        artifact = m.s.read_json((m.s.ROOT / m.DEFAULT_OUTPUT).read_bytes())
        m.verify_artifact(artifact)
        for change in ('omit', 'reorder', 'survival', 'calibration'):
            bad = deepcopy(artifact['records'])
            if change == 'omit': bad.pop()
            elif change == 'reorder': bad.reverse()
            elif change == 'survival': bad[-1]['outcome'] = 'SURVIVED'
            else: bad[1]['evidence']['failing_tests'] = bad[1]['tests']
            with self.subTest(change=change), self.assertRaises(RoundingError):
                m.validate_records(bad)


if __name__ == '__main__':
    unittest.main()
