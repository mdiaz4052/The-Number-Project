import copy
import math
from pathlib import Path
import tempfile
import unittest
import subprocess
from unittest.mock import patch

from Discovery import estimated_noise1_calibration as cal
from Discovery import estimated_noise1_schema as schema
from Discovery import estimated_noise1_science as science
from Discovery import estimated_noise1_reference as reference
from Discovery import estimated_noise1_fixtures as fixtures
from Discovery import estimated_noise1_mutations as mutations
from Discovery.estimated_noise1_selection import discovery_payload
from Discovery.estimated_noise1_workers import staged_calibration, valid as calibration_receipt
from Discovery.symbolic_suite_runner import staged_discovery, valid_receipt
from Discovery.estimated_noise1 import PKG, new_bytes


class EstimatedNoise1Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.p = fixtures.policy()

    def test_numeric_moment_and_alternate_quantiles(self):
        for alpha, budgets in ((.05, [16, 64, 256]), (.1, [3, 17, 127]), (.01, [1, 32, 256])):
            v = fixtures.pair_payload(alpha=alpha, budgets=budgets)
            e = cal.estimate(v)
            self.assertTrue(reference.calibration(v['pairs'], v['settings'], e['estimates'])['pass'])

    def test_zero_tiny_and_equal_differences(self):
        v = fixtures.pair_payload()
        for r in v['pairs']: r['response_1'] = r['response_2'] = 1.
        for e in cal.estimate(v)['estimates'].values():
            self.assertEqual(e['point'], 0.)
            self.assertEqual(e['ideal_upper'], 0.)
            self.assertEqual(e['padded_upper'], v['settings']['pad']/(2*e['q']))

    def test_invalid_pair_values_and_inventories(self):
        base = fixtures.pair_payload()
        for value in (0, -1, True, None, float('nan'), float('inf'), '1'):
            v = copy.deepcopy(base); v['pairs'][0]['response_1'] = value
            with self.assertRaises(ValueError): cal.estimate(v)
        for edit in ('missing', 'extra', 'duplicate', 'unordered', 'bool_budget', 'empty'):
            v = copy.deepcopy(base)
            if edit == 'missing': v['pairs'].pop()
            if edit == 'extra': v['pairs'][0]['features'] = {}
            if edit == 'duplicate': v['pairs'][1]['pair_id'] = 'p001'
            if edit == 'unordered': v['pairs'].reverse()
            if edit == 'bool_budget': v['settings']['budgets'] = [True]
            if edit == 'empty': v['pairs'] = []
            with self.assertRaises(ValueError): cal.estimate(v)

    def test_duplicate_json_and_nonfinite_rejection(self):
        for raw in ('{"a":1,"a":2}', '{"n":NaN}', '{"n":Infinity}'):
            with self.assertRaises(ValueError): cal.loads(raw)
        with self.assertRaises(ValueError): schema.same({'x': False}, {'x': 0}, 'types')

    def test_calibration_only_schema(self):
        for field in ('features', 'truth', 'true_epsilon', 'candidate_residuals', 'heldout', 'seed', 'preregistration'):
            v = fixtures.pair_payload(); v[field] = 1
            with self.assertRaises(ValueError): cal.estimate(v)

    def test_staged_calibration_completed_reads_and_fresh_cache(self):
        v = fixtures.pair_payload()
        output = staged_calibration(v)
        self.assertTrue(calibration_receipt(output))
        schema.worker(output, schema.CAL_RESULT)
        schema.same(output['discovery'], cal.estimate(v), 'pair worker parity')
        self.assertFalse(calibration_receipt(staged_calibration(v, stale_cache=True, enforce=False)))
        for probe in ('module:Discovery.estimated_noise1_science', 'module:Discovery.symbolic_suite_worlds',
                      '<stage>/heldout.json', '<stage>/preregistration.v1.json'):
            output = staged_calibration(v, probe=probe, enforce=False)
            self.assertFalse(calibration_receipt(output))
            self.assertTrue(output['receipt']['denied_unexpected_attempts'])

    def test_discovery_threshold_invariance_inventory_and_numeric_reference(self):
        public, heldout, truth = fixtures.observations(self.p)
        a = staged_discovery(discovery_payload(public, science.policy(self.p, 1e-8)))
        b = staged_discovery(discovery_payload(public, science.policy(self.p, .1)))
        self.assertTrue(valid_receipt(a) and valid_receipt(b))
        schema.worker(a, schema.DISCOVERY)
        self.assertEqual(a['discovery']['ranking'], b['discovery']['ranking'])
        self.assertNotEqual(a['discovery']['decision'], b['discovery']['decision'])
        inventory = science.expected_signatures(self.p)
        self.assertEqual(len(inventory), 5)
        self.assertEqual({c['class_id']: c['expanded'] for c in a['discovery']['ranking']}, inventory)
        metrics = {c['class_id']: {'heldout_rmse': science.rmse(c, heldout)} for c in a['discovery']['ranking']}
        self.assertTrue(reference.candidate_arithmetic(public, a['discovery']['ranking'], heldout=heldout,
                                                      truth=truth, metrics=metrics)['pass'])

    def test_inventory_is_derived_from_dimensions(self):
        p = copy.deepcopy(self.p); p['grammar']['target']['dimension']['L'] = 2
        self.assertTrue(all(s['x'] == '2' for s in science.expected_signatures(p).values()))

    def test_discovery_heldout_denial_and_poison_sources(self):
        public, heldout, _ = fixtures.observations(self.p)
        with self.assertRaises(ValueError): discovery_payload({**public, 'heldout': heldout}, science.policy(self.p, .01))
        payload = discovery_payload(public, science.policy(self.p, .01))
        for probe in ('module:Discovery.estimated_noise1_science', 'module:Discovery.estimated_noise1_calibration',
                      '<stage>/oracle_reveal.json', '<stage>/heldout.json'):
            out = staged_discovery(payload, probe=probe, enforce=False)
            self.assertFalse(valid_receipt(out))
            self.assertTrue(out['receipt']['denied_unexpected_attempts'])
        self.assertFalse(valid_receipt(staged_discovery(payload, stale_cache=True, enforce=False)))

    def test_family_rank1_equality_and_signed_margins(self):
        result = science.assess([{'validation_rmse': .02}, {'validation_rmse': .01}], .01)
        self.assertFalse(result['family_rejected'])
        self.assertEqual(result['family_margin'], 0.)
        self.assertEqual(result['rank1_decision'], 'no_stable_law')

    def test_no_curved_structural_credit_or_stale_policy(self):
        self.assertFalse(science.credit(False, True, True, [.001]*3, .01, 0, True))
        self.assertFalse(science.credit(True, False, True, [.001]*3, .01, 0, True))
        self.assertFalse(science.credit(True, True, True, [.001]*3, .01, .03, True, .02))
        self.assertTrue(science.credit(True, True, True, [.001]*3, .01, .03, True, .04))

    def test_all_dispositions_and_failure_precedence(self):
        cases = [(0, [], [], True, 'NO_GO'), (1, [], [], True, 'PARTIAL'), (96, [], [], True, 'COMPLETE'),
                 (96, [], ['missing'], True, 'UNRESOLVED'), (96, [], [], False, 'UNRESOLVED'),
                 (0, ['violation'], ['missing'], False, 'FAIL')]
        for n, failures, missing, accounted, expected in cases:
            self.assertEqual(science.disposition(96, n, violations=failures, missing_evidence=missing,
                accounted=accounted)['disposition'], 'ESTIMATED_NOISE_1_'+expected)
        with self.assertRaises(ValueError): science.disposition(96, True, violations=[], missing_evidence=[], accounted=True)

    def test_stopped_evidence_dispositions_are_derived(self):
        from Discovery.estimated_noise1_failure import derive, classification
        for error_type, expected in [('TimeoutExpired', 'NO_GO'), ('ValueError', 'FAIL'), ('KeyError', 'UNRESOLVED')]:
            f = {'stage': 'discovery', 'error_type': error_type, 'error': 'deliberate engineering fixture',
                 'classification': classification(error_type), 'scientific_pipeline_stopped': True,
                 'scientific_retry_authorized': False}
            report = derive(self.p, [f], {}, set())
            self.assertEqual(report['disposition'], 'ESTIMATED_NOISE_1_'+expected)
            self.assertEqual(len(report['missing_or_failed_ids']), 96)
            self.assertTrue(all(s['state'] == 'NOT_EXECUTED' for s in report['dataset_status'].values()))
            f['classification'] = 'COMPLETE'
            with self.assertRaises(ValueError): derive(self.p, [f], {}, set())

    def test_real_git_chronology_rejects_reversed_ancestry(self):
        from Discovery import estimated_noise1 as custody
        from Discovery import estimated_noise1_verifier as verifier
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def command(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
            command('init', '-q'); command('config', 'user.name', 'Engineering Fixture')
            command('config', 'user.email', 'engineering-fixture@example.invalid')
            (root/'a').write_text('snapshot'); command('add', 'a'); command('commit', '-qm', 'snapshot')
            a = command('rev-parse', 'HEAD')
            (root/'b').write_text('freeze'); command('add', 'b'); command('commit', '-qm', 'freeze')
            b = command('rev-parse', 'HEAD')
            with patch.object(custody, 'ROOT', root), patch.object(verifier, 'ROOT', root):
                verifier.direct(a, b); verifier.ancestor(a, b)
                with self.assertRaises(ValueError): verifier.direct(b, a)
                with self.assertRaises(ValueError): verifier.ancestor(b, a)

    def test_fixed_design_matching_streams_and_anonymization(self):
        # Explicit engineering seed, never the private master seed.
        public, calibration, heldout, oracle = science.generate(self.p, 'e'*64)
        schema.scientific_inputs(public, calibration, heldout, oracle)
        self.assertEqual(len(public), 96)
        self.assertEqual(sum(len(v) for v in calibration.values()), 24576)
        self.assertEqual(len({v['child_seed'] for v in oracle['blocks'].values()}), 16)
        for bank in oracle['blocks'].values():
            self.assertNotEqual([r['u1'] for r in bank['calibration']], [r['u2'] for r in bank['calibration']])
            self.assertNotEqual([r['u'] for r in bank['splits']['train']], [r['u'] for r in bank['splits']['heldout']])
        for b in range(16):
            ids = [rid for rid, t in oracle['datasets'].items() if t['block'] == b]
            self.assertEqual(len(ids), 6)
            self.assertTrue(all([r['features'] for r in public[rid]['train']] ==
                                [r['features'] for r in public[ids[0]]['train']] for rid in ids))

    def test_primary_six_rules_and_end_to_end_fixture_report(self):
        public, heldout, truth = fixtures.observations(self.p, beta=.01)
        v = fixtures.pair_payload(); e = cal.estimate(v)['estimates']
        output = staged_discovery(discovery_payload(public, science.policy(self.p, e['64']['upper95_threshold'])))
        operational = science.operational(self.p, output['discovery'], e)
        schema.validate(operational, schema.OPERATIONAL)
        self.assertEqual(len(operational['rules']), 6)
        evaluated = science.evaluate(self.p, {'worker': output, 'operational': operational}, truth, heldout, e)
        self.assertEqual(len(evaluated['methods']), 7)
        self.assertFalse(any(v['structural_credit'] for v in evaluated['methods'].values()))
        rid = 'd001'
        statuses = {i: {'state': 'INTERPRETABLE' if i == rid else 'NOT_EXECUTED', 'stage': 'fixture',
                       'reason': None if i == rid else 'explicit engineering partial fixture'} for i in science.identities()}
        summary = science.aggregate(self.p, {rid: evaluated}, statuses, [], [])
        self.assertEqual(summary['disposition'], 'ESTIMATED_NOISE_1_PARTIAL')
        self.assertEqual(len(summary['missing_or_failed_ids']), 95)
        malformed = copy.deepcopy(evaluated); malformed['methods'].pop('point/16')
        self.assertNotEqual(science.aggregate(self.p, {rid: malformed}, statuses, [], [])['disposition'], 'ESTIMATED_NOISE_1_COMPLETE')
        broken = copy.deepcopy(output); broken['discovery']['ranking'].pop()
        with self.assertRaises(ValueError): science.operational(self.p, broken['discovery'], e)

    def test_closed_artifact_binding_hash_and_type_tamper(self):
        b = {'actual_base_sha': 'a'*40, 'freeze_sha': 'b'*40, 'preregistration_sha256': 'c'*64, 'science_sha256': 'd'*64}
        value = schema.envelope('fixture', {'observation': 1.}, b)
        self.assertEqual(schema.unwrap(cal.encoded(value), 'fixture', b), {'observation': 1.})
        for field in ('task', 'revision', 'schema'):
            altered = copy.deepcopy(value); altered[field] = False
            with self.assertRaises(ValueError): schema.unwrap(cal.encoded(altered), 'fixture', b)
        altered = copy.deepcopy(value); altered['bindings']['science_sha256'] = 'e'*64
        with self.assertRaises(ValueError): schema.unwrap(altered, 'fixture', b)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'exclusive'; new_bytes(path, b'original')
            with self.assertRaises(FileExistsError): new_bytes(path, b'replacement')
            self.assertEqual(path.read_bytes(), b'original')

    def test_ten_designated_semantic_mutations(self):
        result = mutations.run()
        self.assertEqual(len(result['mutants']), 10)
        self.assertEqual(result['baseline'], result['equivalent_control'])


class EstimatedNoise1CommittedEvidence(unittest.TestCase):
    @unittest.skipUnless((PKG/'result.json').exists(), 'prospective epoch not executed at engineering preflight')
    def test_read_only_committed_evidence(self):
        from Discovery.estimated_noise1_verifier import check
        value = check()
        self.assertIn(value['disposition'], {'ESTIMATED_NOISE_1_'+s for s in ('COMPLETE', 'PARTIAL', 'NO_GO', 'FAIL', 'UNRESOLVED')})


if __name__ == '__main__': unittest.main()
