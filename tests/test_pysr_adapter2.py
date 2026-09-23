"""Offline adverse-archive tests; no live qualification or mutation credit."""
import copy
import unittest
from Discovery import pysr_adapter2_verifier as v


class SetupArchiveTests(unittest.TestCase):
    def setUp(self):
        self.raw = v.setup_bytes()
        self.anchor = v.read('anchor.json')
        self.snapshot = {'schema': v.NS+'/source-snapshot', 'source_sha': 'a'*40,
                         'files': {}, 'accepted_source_sha': self.anchor['base_sha'],
                         'accepted_files': {}}

    def edit(self, path, mutate):
        record = v.loads(self.raw[path])
        mutate(record)
        self.raw[path] = v.encoded(record)

    def rebind(self):
        # Recompute transport receipts so semantic tests cannot pass merely
        # because a changed JSON file has an old hash in its stop inventory.
        for epoch in (1, 2):
            prefix = f'epoch-{epoch:02d}/'
            path = prefix+'stop.json'
            record = v.loads(self.raw[path])
            record['evidence_inventory'] = {
                p[len(prefix):]: {'bytes': len(b), 'sha256': v.sha(b)}
                for p, b in self.raw.items() if p.startswith(prefix) and p != path}
            self.raw[path] = v.encoded(record)
        self.edit('recovery_plan.json', lambda x: x.update(
            prior_stop_sha256=v.sha(self.raw['epoch-01/stop.json']),
            prior_diagnostic_sha256=v.sha(self.raw['epoch-01/namespace-capability.stderr'])))

    def rejected(self, code):
        with self.assertRaisesRegex(v.EvidenceError, '^'+code+':'):
            v.validate_setup(self.raw, self.anchor)

    def test_retained_failure_is_no_go_and_never_operational(self):
        facts = v.validate_setup(self.raw, self.anchor)
        self.assertEqual(facts['disposition'], 'PYSR_ADAPTER_2_NO_GO')
        self.assertEqual(facts['evidence_integrity'], 'PASS')
        self.assertIs(facts['operational_acceptance'], False)
        self.assertEqual(facts['setup_epochs'], 2)

    def test_each_alternate_disposition_requires_different_evidence(self):
        for disposition in ('PASS', 'PARTIAL', 'FAIL', 'UNRESOLVED'):
            with self.subTest(disposition=disposition):
                report = v.expected_report(self.raw, self.anchor, self.snapshot)
                report['disposition'] = 'PYSR_ADAPTER_2_'+disposition
                report['adapter_conformance'] = disposition
                with self.assertRaisesRegex(v.EvidenceError, '^DISPOSITION:'):
                    v.validate_report(report, self.raw, self.anchor, self.snapshot)

    def test_unsupported_report_promotions_are_rejected(self):
        original = v.expected_report(self.raw, self.anchor, self.snapshot)
        variants = []
        for key, value in [('operational_acceptance', True), ('outcome_blind', True),
                           ('evidence_integrity', 'FAIL'), ('review_status', 'ACCEPTED')]:
            report = copy.deepcopy(original); report[key] = value; variants.append(report)
        report = copy.deepcopy(original)
        report['planned_runs'][0].update(state='PASS', fit_invocations=1)
        variants.append(report)
        report = copy.deepcopy(original)
        report['scientific_evidence']['formal_proof'] = 'PASS'; variants.append(report)
        report = copy.deepcopy(original)
        report['evidence']['fixtures'] = 'PASS'; variants.append(report)
        for report in variants:
            with self.subTest(report=report):
                with self.assertRaisesRegex(v.EvidenceError, '^DISPOSITION:'):
                    v.validate_report(report, self.raw, self.anchor, self.snapshot)

    def test_runtime_qualification_has_no_completed_layer(self):
        q = v.expected_runtime(self.raw, self.anchor)
        self.assertEqual(q['state'], 'NO_GO')
        self.assertEqual(q['completed_layers'], [])
        self.assertEqual(len(q['failures']), 2)

    def test_missing_evidence_cannot_verify(self):
        del self.raw['epoch-01/initial-controller-tool-output.txt']
        self.rejected('INVENTORY')

    def test_extra_epoch_cannot_verify(self):
        self.raw['epoch-03/stop.json'] = b'{}'
        self.rejected('INVENTORY')

    def test_changed_diagnostic_rejected_by_raw_binding(self):
        self.raw['epoch-02/namespace-shared-network.stderr'] += b'x'
        self.rejected('RAW_BINDING')

    def test_consistently_rehashed_unrelated_failure_is_rejected(self):
        path = 'epoch-02/namespace-shared-network.stderr'
        self.raw[path] = b'bwrap: some unrelated failure\n'
        def update(x):
            x['stderr_sha256'] = v.sha(self.raw[path])
            x['capture']['stderr_bytes'] = len(self.raw[path])
        self.edit('epoch-02/namespace-shared-network.json', update)
        self.rebind()
        self.rejected('FAILURE_ROUTE')

    def test_incomplete_child_capture_is_rejected(self):
        self.edit('epoch-02/namespace-shared-network.json',
                  lambda x: x['capture'].update(status='INCOMPLETE'))
        self.rebind(); self.rejected('CAPTURE')

    def test_initial_capture_limitation_must_be_retained(self):
        self.raw['epoch-01/initial-retention.md'] = b'Full original OS streams captured.'
        self.rebind(); self.rejected('RETENTION')

    def test_retry_count_cannot_be_reset(self):
        self.edit('epoch-02/stop.json', lambda x: x['recovery'].update(used=0))
        self.rejected('RETRY')

    def test_boolean_retry_counter_is_not_an_integer(self):
        self.edit('epoch-02/stop.json', lambda x: x['recovery'].update(used=True))
        self.rejected('RETRY')

    def test_seed_creation_invalidates_predata_stop(self):
        self.edit('epoch-02/stop.json', lambda x: x['activity'].update(master_seed_created=True))
        self.rejected('UNPERFORMED')

    def test_boolean_zero_is_not_a_fit_counter(self):
        self.edit('epoch-02/stop.json', lambda x: x['activity'].update(target_fits_executed=False))
        self.rejected('UNPERFORMED')

    def test_completed_runtime_layer_invalidates_this_route(self):
        self.edit('epoch-02/stop.json', lambda x: x['runtime_layers'].update(standalone='PASS'))
        self.rejected('UNPERFORMED')

    def test_postexecution_recovery_plan_is_rejected(self):
        self.edit('recovery_plan.json', lambda x: x.update(recorded_at='2099-01-01T00:00:00Z'))
        self.rejected('CHRONOLOGY')

    def test_recovery_must_bind_first_failure(self):
        self.edit('recovery_plan.json', lambda x: x.update(prior_stop_sha256='0'*64))
        self.rejected('RETRY')

    def test_unrecorded_environment_change_is_rejected(self):
        self.edit('epoch-02/namespace-shared-network.json',
                  lambda x: x['environment'].update(UNRECORDED_VALUE='present'))
        self.rebind(); self.rejected('ISOLATION')

    def test_changed_recovery_command_is_rejected(self):
        self.edit('epoch-02/namespace-shared-network.json', lambda x: x['command'].remove('--share-net'))
        self.rebind(); self.rejected('ISOLATION')

    def test_source_substitution_is_rejected(self):
        self.edit('epoch-02/namespace-shared-network.json', lambda x: x.update(source_sha='a'*40))
        self.rebind(); self.rejected('SOURCE_PIN')

    def test_changed_host_mapping_is_rejected(self):
        self.edit('epoch-01/host.json', lambda x: x['isolation'].update(uid_map='0 0 65536'))
        self.rebind(); self.rejected('ISOLATION')

    def test_false_sandbox_claim_is_rejected(self):
        self.edit('epoch-01/host.json', lambda x: x['isolation'].update(credential_separation='PASS'))
        self.rebind(); self.rejected('ISOLATION')

    def test_process_signal_cannot_be_relabelled_as_known_refusal(self):
        self.edit('epoch-02/namespace-shared-network.json', lambda x: x.update(returncode=-7, signal=7))
        self.rebind(); self.rejected('FAILURE_ROUTE')

    def test_preanchor_execution_is_rejected(self):
        self.anchor['created_at'] = '2099-01-01T00:00:00Z'
        self.rejected('CHRONOLOGY')

    def test_duplicate_keys_and_nonfinite_numbers_are_rejected(self):
        for raw in (b'{"epoch":1,"epoch":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(v.EvidenceError):
                v.loads(raw)

    def test_unknown_top_level_fields_are_rejected(self):
        self.edit('epoch-02/stop.json', lambda x: x.update(extra='uncontracted'))
        self.rejected('SCHEMA')


class CommittedArchiveTests(unittest.TestCase):
    def test_committed_source_chronology_and_retained_bytes(self):
        self.assertEqual(v.check(), 'PYSR_ADAPTER_2_NO_GO')


if __name__ == '__main__':
    unittest.main()
