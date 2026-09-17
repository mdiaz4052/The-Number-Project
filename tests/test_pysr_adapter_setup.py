"""Truthful early-stop evidence tests; no adapter/native coverage is claimed."""
from copy import deepcopy
import unittest

from Discovery import candidate_exchange as cx
from Discovery import pysr_adapter_setup_verifier as verifier


class SetupEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.raw = verifier.setup_bytes()
        self.anchor = verifier.read('anchor.json')
        self.binding = {'fixture': 'explicit synthetic binding; never accepted by committed check'}
        self.report = verifier.expected_report(self.raw, self.anchor, self.binding)

    def change(self, name, key, value):
        data = cx.loads(self.raw[name])
        data[key] = value
        self.raw[name] = cx.encoded(data)

    def test_truthful_setup_no_go_is_verifiable_but_not_accepted_adapter(self):
        self.assertEqual(verifier.validate_report(self.report, self.raw, self.anchor, self.binding),
                         'PYSR_ADAPTER_1_NO_GO')
        self.assertEqual(self.report['evidence_integrity'], 'PASS')
        self.assertIs(self.report['operational_acceptance'], False)
        self.assertEqual(len(self.report['planned_runs']), 4)
        self.assertTrue(all(r['state'] == 'NOT_EXECUTED' for r in self.report['planned_runs']))

    def test_all_unsubstantiated_dispositions_are_rejected(self):
        for label in ['PASS', 'PARTIAL', 'FAIL', 'UNRESOLVED', 'UNKNOWN']:
            with self.subTest(label=label):
                r = deepcopy(self.report)
                r['disposition'] = 'PYSR_ADAPTER_1_' + label
                with self.assertRaisesRegex(cx.ContractError, 'DISPOSITION'):
                    verifier.validate_report(r, self.raw, self.anchor, self.binding)

    def test_adverse_label_alone_cannot_validate_successful_or_unexplained_process(self):
        self.change('julia-resolve-01.json', 'returncode', 0)
        with self.assertRaisesRegex(cx.ContractError, 'FAILURE_ROUTE'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_raw_log_corruption_is_rejected(self):
        self.raw['julia-resolve-01.stderr'] += b'altered'
        with self.assertRaisesRegex(cx.ContractError, 'RAW_BINDING'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_resigned_but_unrelated_failure_cannot_claim_sigbus(self):
        self.raw['julia-resolve-01.stderr'] = b'network unavailable'
        self.change('julia-resolve-01.json', 'stderr_sha256', cx.sha(self.raw['julia-resolve-01.stderr']))
        with self.assertRaisesRegex(cx.ContractError, 'FAILURE_ROUTE'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_inventory_cannot_drop_failure_or_add_target_output(self):
        for key in ['julia-resolve-01.stderr', 'extraction-failure.json']:
            raw = dict(self.raw)
            del raw[key]
            with self.assertRaisesRegex(cx.ContractError, 'INVENTORY'):
                verifier.validate_setup(raw, self.anchor['created_at'])
        raw = {**self.raw, 'target-output.json': b'{}'}
        with self.assertRaisesRegex(cx.ContractError, 'INVENTORY'):
            verifier.validate_setup(raw, self.anchor['created_at'])

    def test_qualification_or_live_claims_cannot_be_fabricated(self):
        for key, value in [('qualified_environment', True), ('master_seed_created', True),
                           ('target_fits_executed', 1), ('cards_issued', 1),
                           ('eight_adapter_mutations', 'PASS'), ('julia_manifest_exists', True)]:
            with self.subTest(key=key):
                raw = dict(self.raw)
                stop = cx.loads(raw['stop.json'])
                stop[key] = value
                raw['stop.json'] = cx.encoded(stop)
                with self.assertRaisesRegex(cx.ContractError, 'UNPERFORMED'):
                    verifier.validate_setup(raw, self.anchor['created_at'])

    def test_retry_exhaustion_and_partial_log_retention_are_preserved(self):
        self.change('stop.json', 'retry_used', 0)
        with self.assertRaisesRegex(cx.ContractError, 'RETRY'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_pinned_version_substitution_rejected(self):
        data = cx.loads(self.raw['requested-juliapkg.json'])
        data['packages']['SymbolicRegression']['version'] = '=2.0.0'
        self.raw['requested-juliapkg.json'] = cx.encoded(data)
        with self.assertRaisesRegex(cx.ContractError, 'IDENTITY'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_pre_anchor_setup_is_rejected(self):
        self.change('julia-resolve-01.json', 'started_at', '2026-09-16T00:00:00Z')
        with self.assertRaisesRegex(cx.ContractError, 'CHRONOLOGY'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_source_binding_and_result_substitution_rejected(self):
        with self.assertRaisesRegex(cx.ContractError, 'DISPOSITION'):
            verifier.validate_report(self.report, self.raw, self.anchor, {'forged': True})
        self.raw['resolve_stack.py'] += b'\n# changed after attempt\n'
        with self.assertRaisesRegex(cx.ContractError, 'SOURCE_PIN'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])

    def test_no_scientific_promotion_or_operational_acceptance(self):
        for key, value in [('operational_acceptance', True), ('search_coverage', 'EXHAUSTIVE'),
                           ('scientific_evidence', {'empirical_support': 'PASS'})]:
            r = deepcopy(self.report)
            r[key] = value
            with self.assertRaisesRegex(cx.ContractError, 'DISPOSITION'):
                verifier.validate_report(r, self.raw, self.anchor, self.binding)

    def test_duplicate_json_keys_are_rejected(self):
        self.raw['stop.json'] = b'{"schema":"first","schema":"second"}'
        with self.assertRaisesRegex(cx.ContractError, 'DUPLICATE_KEY'):
            verifier.validate_setup(self.raw, self.anchor['created_at'])


class CommittedSetupEvidenceTests(unittest.TestCase):
    def test_offline_committed_evidence_guard(self):
        self.assertEqual(verifier.check(), 'PYSR_ADAPTER_1_NO_GO')


if __name__ == '__main__':
    unittest.main()
