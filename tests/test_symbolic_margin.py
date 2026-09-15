"""Independent fixtures for the forward margin boundary; no target epoch outcomes."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from Discovery import symbolic_margin as run
from Discovery import symbolic_margin_science as science
from Discovery.symbolic_suite_engine import discover, prepare
from Discovery.symbolic_suite_runner import staged_discovery, valid_receipt
from Discovery.symbolic_benchmark_engine import digest
from tests.test_symbolic_suite import fixture


def fixture_design():
    """Deliberately different source-independent numeric policy, not the target design."""
    raw = fixture()
    return {'grammar': {**{k: raw['policy'][k] for k in ('max_factors', 'max_abs_power', 'max_denominator')}, 'target': raw['target']},
        'features': raw['features'],
        'scoring': {'complexity_lambda': 0.017, 'adequacy_noise_multiplier': 3.5, 'numeric_floor': 0.0002,
                    'approximation_rmse_max': 0.087, 'coefficient_relative_error_max': 0.13,
                    'independent_metric_tolerance': 1e-10},
        'design': {'independent_blocks': 2, 'conditions': ['adequate', 'curved'], 'noise_levels': [0.02, 0.07],
                   'stratified_exponents': [-1, 2], 'analysis_unit': 'two independent fixture blocks, four matched conditions'},
        'generation': {'version': 'independent-fixture', 'adequate_beta': 0, 'curvature_beta': 0.23,
                       'coefficient_log_range': [-0.4, 0.8], 'scale_center_log_ranges': {'x': [-0.2, 0.3], 't': [0.1, 0.2], 'z': [0, 0]},
                       'base_offset_log_ranges': {'x': [-0.8, 0.8], 't': [-0.3, 0.4], 'z': [-1.1, 1.2]},
                       'heldout_offset_log_ranges': {'x': [-0.9, 0.9], 't': [-0.4, 0.5], 'z': [-1.3, 1.3]},
                       'sample_counts': {'train': 12, 'validation': 10, 'heldout': 8}, 'proof': 'fixture nonzero second derivative'},
        'evaluation': {'labels': {k: 'FIXTURE_' + k for k in ('COMPLETE', 'PARTIAL', 'FAIL', 'NO_GO', 'UNRESOLVED')}},
        'nonclaims': ['fixture only']}


def evaluate_fixture(p=None, curved=False):
    p = p or fixture_design()
    raw = fixture()
    raw['policy'] = science.policy_for(p, 0.02)
    if curved:
        for split in ('train', 'validation'):
            for row in raw[split]:
                row['target'] *= math.exp(p['generation']['curvature_beta'] * math.log(row['features']['z'])**2)
    truth = {'block': 0, 'condition': 'curved' if curved else 'adequate', 'noise_index': 0, 'epsilon': 0.02,
             'coefficient': 1.7, 'exponent': -1, 'curve_beta': p['generation']['curvature_beta'] if curved else 0,
             'in_family': not curved, 'base_signature': {'x': '1', 't': '-2', 'z': '-1'},
             'irrelevant_atoms': [], 'forbidden_features': [],
             'wrong_grammar_proof': p['generation']['proof'] if curved else None}
    wrapped = {'discovery': discover(raw)}
    return p, raw, wrapped, truth, copy.deepcopy(raw['validation'])


class MarginMathTests(unittest.TestCase):
    def test_exact_threshold_equality_and_flip(self):
        s = {'adequacy_noise_multiplier': 3., 'numeric_floor': 0.125}
        m = science.threshold_metrics(0.5, 0.125, s)
        self.assertEqual(m['critical_assumed_noise'], 0.125)
        self.assertFalse(m['inadequate'])
        self.assertTrue(science.threshold_metrics(0.5, 0.124, s)['inadequate'])
        self.assertFalse(science.threshold_metrics(0.5, 0.126, s)['inadequate'])
        p = fixture(); d = discover(p)
        p['policy']['acceptance_validation_rmse'] = d['minimum_validation_rmse']
        self.assertEqual(discover(p)['family_assessment'], 'contains_validation_adequate_member')
        p['policy']['acceptance_validation_rmse'] = 0
        self.assertEqual(discover(p)['family_assessment'], 'family_inadequate_on_validation')

    def test_zero_noise_nonpositive_boundary_and_invalid_inputs(self):
        s = {'adequacy_noise_multiplier': 7, 'numeric_floor': .2}
        for r in (.1, .2):
            d = science.threshold_metrics(r, 0, s)
            self.assertIsNone(d['critical_original_noise_ratio'])
            self.assertFalse(d['inadequate'])
            self.assertEqual(d['critical_domain'], 'no_nonnegative_inadequacy_region')
        self.assertTrue(science.threshold_metrics(.3, 0, s)['inadequate'])
        for r, e in [(-1, 1), (1, -1), (math.nan, 1), (1, math.inf)]:
            with self.assertRaises(ValueError): science.threshold_metrics(r, e, s)

    def test_policy_values_not_stale_literals(self):
        p = fixture_design()
        policy = science.policy_for(p, .02)
        self.assertAlmostEqual(policy['acceptance_validation_rmse'], .0702)
        self.assertEqual(policy['approximation_rmse_max'], .087)
        self.assertEqual(policy['complexity_lambda'], .017)
        r = science.threshold_metrics(.06, .02, p['scoring'])
        self.assertFalse(r['inadequate'])
        p['scoring']['adequacy_noise_multiplier'] = 1.5
        self.assertTrue(science.threshold_metrics(.06, .02, p['scoring'])['inadequate'])

    def test_retrospective_family_and_rank1_are_distinct(self):
        p = {'retrospective': {'source_sha': 'fixture', 'counterfactual_assumed_noise': [0, .03, .1]}}
        old = {'scoring': {'adequacy_noise_multiplier': 3, 'numeric_floor': .01}}
        oracle = {'realizations': {'r': {'epsilon': .02, 'cell': 'fixture'}}}
        selections = {'r': {'discovery': {'ranking': [{'validation_rmse': .1}, {'validation_rmse': .07}]}}}
        policies = {'r': {'policy': {'acceptance_validation_rmse': 3 * .02 + .01}}}
        r = science.retrospective(p, old, oracle, selections, policies)['rows']['r']
        self.assertAlmostEqual(r['family']['critical_assumed_noise'], .02)
        self.assertAlmostEqual(r['rank1']['critical_assumed_noise'], .03)
        self.assertNotEqual(r['family'], r['rank1'])
        tree = ast.parse(Path(science.__file__).read_text())
        f = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'retrospective')
        calls = {n.func.id for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertFalse(calls & {'generate', 'discover', 'fit', 'rmse', 'staged_discovery'})


class GeneratorAndEvaluationTests(unittest.TestCase):
    def test_independent_formula_matching_strata_streams_and_changed_noise(self):
        p = fixture_design(); seed = 'a1' * 32
        public, held, oracle = science.generate(p, seed)
        self.assertEqual(set(public), set(science.dataset_ids(p)))
        children = {t['child_seed'] for t in oracle['realizations'].values()}
        self.assertEqual(len(children), 2)
        self.assertEqual(children, {hashlib.sha256(f'{seed}:margin1:block:{b}'.encode()).hexdigest() for b in range(2)})
        for b in range(2):
            ref = f'b{b+1:02d}-adequate-n1'; t = oracle['realizations'][ref]
            self.assertEqual(t['exponent'], p['design']['stratified_exponents'][b])
            for split in ('train', 'validation', 'heldout'):
                reference = held[ref] if split == 'heldout' else public[ref][split]
                for condition in ('adequate', 'curved'):
                    for n, epsilon in enumerate(p['design']['noise_levels']):
                        rid = f'b{b+1:02d}-{condition}-n{n+1}'
                        rows = held[rid] if split == 'heldout' else public[rid][split]
                        beta = 0 if condition == 'adequate' else .23
                        for a, r in zip(reference, rows):
                            self.assertEqual(a['features'], r['features'])
                            x, v, z = (r['features'][k] for k in ('x', 't', 'z'))
                            clean = math.log(t['coefficient'] * x / v**2 * z**t['exponent'])
                            u = (math.log(a['target']) - clean) / .02
                            observed_u = (math.log(r['target']) - clean - beta * math.log(z)**2) / epsilon
                            self.assertAlmostEqual(observed_u, u, places=11)
                            self.assertLessEqual(abs(u), 1 + 1e-12)
        self.assertNotEqual(public['b01-adequate-n1']['validation'][0]['target'], public['b01-adequate-n2']['validation'][0]['target'])
        altered = copy.deepcopy(p); altered['generation']['curvature_beta'] = .4
        alternate = science.generate(altered, seed)[0]
        self.assertEqual(alternate['b01-adequate-n1'], public['b01-adequate-n1'])
        self.assertNotEqual(alternate['b01-curved-n1'], public['b01-curved-n1'])

    def test_forward_runner_and_heldout_cannot_rescue_or_change_selection(self):
        p, raw, _, truth, held = evaluate_fixture()
        payload, _ = prepare(raw)
        wrapped = staged_discovery(payload)
        self.assertTrue(valid_receipt(wrapped))
        before = copy.deepcopy(wrapped)
        good = science.evaluate(p, raw, wrapped, truth, held)
        self.assertTrue(good['structural_credit'])
        for row in held: row['target'] *= 4
        bad = science.evaluate(p, raw, wrapped, truth, held)
        self.assertFalse(bad['structural_credit'])
        self.assertEqual(wrapped, before)
        self.assertEqual(good['pre_reveal_selection_decision'], bad['pre_reveal_selection_decision'])
        self.assertGreater(bad['rank1_heldout_error'], good['rank1_heldout_error'])

    def test_wrong_predictive_stable_selection_gets_no_structural_credit(self):
        p = fixture_design(); p['scoring']['adequacy_noise_multiplier'] = 80
        p['scoring']['approximation_rmse_max'] = 2
        p, raw, wrapped, truth, held = evaluate_fixture(p, curved=True)
        result = science.evaluate(p, raw, wrapped, truth, held)
        self.assertTrue(result['integrity_pass'])
        self.assertTrue(result['missed_inadequacy'])
        self.assertTrue(result['heldout_approximation'])
        self.assertTrue(result['structurally_wrong_stable_selection'])
        self.assertFalse(result['structural_credit'])
        self.assertFalse(any(c['scientific_credit'] for c in result['candidates']))
        p['scoring']['approximation_rmse_max'] = 1e-6
        raw['policy'] = science.policy_for(p, .02)
        changed = science.evaluate(p, raw, {'discovery': discover(raw)}, truth, held)
        self.assertFalse(changed['heldout_approximation'])

    def test_empty_family_is_capability_failure_and_not_recognition(self):
        p, raw, wrapped, truth, held = evaluate_fixture()
        d = wrapped['discovery']
        d.update(ranking=[], family_assessment='no_candidate_capability', decision='no_stable_law', top_class=None)
        result = science.evaluate(p, raw, wrapped, truth, held)
        self.assertFalse(result['interpretable'])
        self.assertFalse(result['recognized_inadequacy'])
        self.assertFalse(result['structural_credit'])

    def test_complete_forward_fixture_controls(self):
        p = fixture_design()
        public, heldout, oracle = science.generate(p, 'd4'*32)
        inputs, eligibility = {}, {}
        for rid, raw in public.items(): inputs[rid], eligibility[rid] = prepare(raw)
        outputs = {rid: staged_discovery(v) for rid, v in inputs.items()}
        c = {name + '_sha256': digest(v) for name, v in [('public', public), ('inputs', inputs),
             ('eligibility', eligibility), ('oracle', oracle), ('heldout', heldout)]}
        self.assertTrue(all(run.controls(p, c, public, inputs, eligibility, outputs, oracle, heldout).values()))
        outputs[next(iter(outputs))]['discovery']['ranking'].pop()
        self.assertFalse(run.controls(p, c, public, inputs, eligibility, outputs, oracle, heldout)['exhaustive_family'])

    def test_coefficient_tolerance_fixture_changes_credit(self):
        p, raw, wrapped, truth, held = evaluate_fixture()
        truth['coefficient'] = 1.7 / 1.06
        self.assertTrue(science.evaluate(p, raw, wrapped, truth, held)['structural_credit'])
        p['scoring']['coefficient_relative_error_max'] = .05
        self.assertFalse(science.evaluate(p, raw, wrapped, truth, held)['structural_credit'])


class CustodyAndAggregationTests(unittest.TestCase):
    def test_binding_seed_and_exclusive_writes(self):
        output, oracle, held = {'r': 1}, {'seed': 'b2'*32}, [2]
        c = {'oracle_sha256': digest(oracle), 'heldout_sha256': digest(held)}
        seal = {'commitment_sha256': digest(c), 'selection_sha256': digest(output)}
        run.check_binding(c, seal, output, oracle, held)
        for obj in ('output', 'oracle', 'heldout', 'commitment'):
            with self.assertRaises(ValueError):
                run.check_binding({**c, 'changed': True} if obj == 'commitment' else c, seal,
                    {} if obj == 'output' else output, {} if obj == 'oracle' else oracle, [] if obj == 'heldout' else held)
        self.assertNotEqual(run.seed_digest('b2'*32), run.seed_digest('b3'*32))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'stage.json'; run.write_new(path, c)
            with self.assertRaises(FileExistsError): run.write_new(path, {})
            self.assertEqual(run.read(path), c)

    def test_explicit_forward_route_includes_historical_final_disposition(self):
        with tempfile.TemporaryDirectory(dir=run.ROOT) as directory:
            art = Path(directory)
            run.write_new(art / 'result.json', {'disposition': 'FIXTURE_COMPLETE'})
            run.write_new(art / 'summary.json', {'disposition': 'FIXTURE_COMPLETE'})
            with patch.object(run, 'ART', art):
                routed = run.make_routes('fixture-sha')
            old = routed['accepted_baseline_routes']
            self.assertEqual(old['Benchmark0']['raw_epoch']['disposition'], 'BENCHMARK_0_FAIL')
            self.assertEqual(old['Benchmark0']['reconciliation']['disposition_key'], 'final_disposition')
            self.assertEqual(old['BenchmarkSuite1']['operational_failures'][0]['disposition'], 'BENCHMARK_SUITE_1_NO_GO_CAPABILITY')
            self.assertEqual(routed['MisspecificationMargin1']['raw_epoch']['disposition_key'], 'disposition')
        tree = ast.parse(Path(run.__file__).read_text())
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr == 'make_index' for n in ast.walk(tree)))

    def test_adverse_performance_complete_partial_failure_and_nonmonotonic(self):
        p = fixture_design()
        public, held, oracle = science.generate(p, 'c3'*32)
        records = {rid: science.evaluate(p, raw, {'discovery': discover(raw)}, oracle['realizations'][rid], held[rid]) for rid, raw in public.items()}
        # Artificial adverse observations test aggregation independently of the generated scores.
        for v in records.values():
            v.update(integrity_pass=True, interpretable=True, recognized_inadequacy=False,
                     missed_inadequacy=v['condition'] == 'curved', unjustified_family_rejection=v['condition'] == 'adequate')
        records['b01-curved-n2']['recognized_inadequacy'] = True
        result = science.aggregate(p, records)
        self.assertEqual(result['disposition'], 'FIXTURE_COMPLETE')
        self.assertTrue(result['curved_block_sequences']['0']['nonmonotonic_false_to_true'])
        self.assertEqual(result['cells']['adequate-n1']['unjustified_family_rejection'], 2)
        self.assertEqual(result['matched_conditions_per_block'], 4)
        self.assertEqual(science.aggregate(p, dict(list(records.items())[:1]))['disposition'], 'FIXTURE_PARTIAL')
        self.assertEqual(science.aggregate(p, {})['disposition'], 'FIXTURE_NO_GO')
        self.assertEqual(science.aggregate(p, records, integrity=False)['disposition'], 'FIXTURE_FAIL')
        self.assertEqual(science.aggregate(p, records, evidence_available=False)['disposition'], 'FIXTURE_UNRESOLVED')

    def test_unique_introduction_and_change_revert_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args): return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
            git('init', '-q'); git('config', 'user.name', 'Fixture'); git('config', 'user.email', 'fixture@example.invalid')
            (root / 'a').write_text('initial'); git('add', '.'); git('commit', '-qm', 'base')
            (root / 'study').mkdir(); f = root / 'study' / 'f.json'; f.write_text('{}')
            git('add', '.'); git('commit', '-qm', 'introduce'); intro = git('rev-parse', 'HEAD')
            with patch.object(run, 'ROOT', root), patch.object(run, 'REL', 'study'):
                h = run.history(); self.assertEqual(run.introduction(h, 'study/f.json'), intro)
                run.immutable(intro, ['study/f.json'])
                f.write_text('{"changed":true}'); git('add', '.'); git('commit', '-qm', 'tamper')
                f.write_text('{}'); git('add', '.'); git('commit', '-qm', 'revert')
                with self.assertRaises(ValueError): run.immutable(intro, ['study/f.json'])


if __name__ == '__main__':
    unittest.main()
