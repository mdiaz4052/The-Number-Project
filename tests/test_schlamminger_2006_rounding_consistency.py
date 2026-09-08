"""Independent arithmetic and source/terminal-boundary tests for Table VII."""

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from Discovery import schlamminger_2006_rounding_consistency as s
from Discovery.rounding_consistency import (
    Interval, RoundingError, calculate, classify, evaluate_point, rounding_bin,
)
from Discovery.source_history import SourceStateViolationError
from tests.support.synthetic_history import SyntheticHistory


EXPECTED = {
    'statistical': [('weighings', '11.6'), ('tm_sorption', '7.4'), ('linearity', '6.1'),
                    ('calibration', '4.0'), ('mass_integration', '5.0')],
    'systematic': [('tm_sorption', '7.4'), ('calibration', '0.5'), ('mass_integration', '3.3')],
}
PARAMETERS = (F(0),) + tuple(F(sign*k, 8) for k in range(1, 8) for sign in (-1, 1))


class SchlammingerBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.protocol, self.source = s.load_source()
        self.projection = deepcopy(self.source['input_projection'])

    def calculations(self, projection=None):
        return s.calculate_scopes(self.projection if projection is None else projection,
                                  self.protocol['rounding_policy'], self.protocol['candidate_schedule'])

    def test_exact_table_transcription_and_source_roles(self):
        self.assertEqual(self.projection['scope_order'], ['statistical', 'systematic'])
        for scope, rows in EXPECTED.items():
            self.assertEqual([(r['id'], r['value_ppm']) for r in self.projection['components'][scope]], rows)
        self.assertEqual(self.source['terminal_comparisons'], {
            k: {'scope': k, 'role': 'terminal_only', 'value_ppm': v, 'half_width_ppm': '0.05'}
            for k, v in [('statistical', '16.3'), ('systematic', '8.1')]})
        self.assertEqual(self.projection['central_value']['value'], '6.674252e-11')
        pub, ms = self.source['sources']['publication'], self.source['sources']['manuscript']
        self.assertEqual(pub['publisher'], 'American Physical Society')
        self.assertEqual(pub['doi'], '10.1103/PhysRevD.74.082001')
        self.assertEqual(ms['identifier'], 'gr-qc/0609027v1')
        self.assertEqual(ms['role'], 'numerical_transcription_authority')
        self.assertEqual(ms['sha256'], '789db21fc81c12bff11e8a13e2db69529a88c1927e4c22657ad35d54e442a954')

    def test_exact_bins_schedule_and_independent_oracle(self):
        calculations = self.calculations()
        self.assertEqual(tuple(calculations), ('statistical', 'systematic'))
        for scope, calc in calculations.items():
            centers = [F(v) for _, v in EXPECTED[scope]]
            self.assertEqual(len(calc.budget.components), len(centers))
            for center, row in zip(centers, calc.budget.components):
                self.assertEqual(row, (Interval(center-F(1, 20), center+F(1, 20)),))
            self.assertEqual(tuple(c.parameter for c in calc.candidates), PARAMETERS)
            self.assertEqual(calc.enclosure,
                Interval(sum((c-F(1, 20))**2 for c in centers),
                         sum((c+F(1, 20))**2 for c in centers)))
            for t, candidate in zip(PARAMETERS, calc.candidates):
                values = tuple((center+t/20,) for center in centers)
                self.assertEqual(candidate.values, values)
                self.assertEqual(candidate.evaluation.relative_variance_ppm_squared,
                                 sum((center+t/20)**2 for center in centers))
                self.assertEqual(candidate.evaluation.weights, (F(1),))
                self.assertEqual(candidate.evaluation.propagation_coefficients, (F(1),))

    def test_one_run_corners_and_correlation_tags(self):
        for calc in self.calculations().values():
            for choices in product((0, 1), repeat=len(calc.budget.components)):
                values = tuple((row[0].low if bit == 0 else row[0].high,)
                               for row, bit in zip(calc.budget.components, choices))
                expected = sum(row[0]**2 for row in values)
                for correlation in ('shared', 'independent'):
                    budget = replace(calc.budget, correlations=(correlation,)*len(values))
                    result = evaluate_point(budget, values)
                    self.assertEqual(result.relative_variance_ppm_squared, expected)
                    self.assertTrue(calc.enclosure.contains(expected))

    def test_positive_central_value_invariance(self):
        original = self.calculations()
        comparisons = self.source['terminal_comparisons']
        expected = s.terminal_decisions(original, comparisons)
        for central in ('1e-100', '0.1', '1', '7.123456789', '1e100'):
            projection = deepcopy(self.projection)
            projection['central_value']['value'] = central
            changed = self.calculations(projection)
            self.assertEqual(s.terminal_decisions(changed, comparisons), expected)
            for scope in original:
                self.assertEqual(changed[scope].enclosure, original[scope].enclosure)
                for a, b in zip(changed[scope].candidates, original[scope].candidates):
                    self.assertEqual(a.values, b.values)
                    self.assertEqual(a.evaluation.relative_variance_ppm_squared,
                                     b.evaluation.relative_variance_ppm_squared)
                    self.assertEqual(a.evaluation.propagation_coefficients, (F(1),))

    def test_scope_omission_merge_swap_and_foreign_inputs_rejected(self):
        bad = []
        p = deepcopy(self.projection); del p['components']['systematic']; bad.append(p)
        p = deepcopy(self.projection); p['scope_order'].reverse(); bad.append(p)
        p = deepcopy(self.projection); p['components']['statistical'], p['components']['systematic'] = p['components']['systematic'], p['components']['statistical']; bad.append(p)
        p = deepcopy(self.projection); p['components']['statistical'] += p['components']['systematic']; bad.append(p)
        p = deepcopy(self.projection); p['components']['systematic'].append({'id':'weighings','value_ppm':'0.0'}); bad.append(p)
        for field in ('HUST_target', 'external_G_reference', 'terminal_comparisons'):
            p = deepcopy(self.projection); p[field] = '11.61'; bad.append(p)
        for p in bad:
            with self.subTest(p=p), self.assertRaises(RoundingError):
                self.calculations(p)

    def test_targets_cannot_enter_calculator_or_change_candidates(self):
        expected = self.calculations()
        # Pure numerical entrypoint must work even when source/terminal access is forbidden.
        with patch.object(s, 'load_protocol', side_effect=AssertionError('target/source access')), \
             patch.object(s, 'load_source', side_effect=AssertionError('target/source access')):
            self.assertEqual(self.calculations(), expected)
        before = repr(expected)
        for statistical, systematic in [('99.0', '99.0'), ('16.0', '8.0'), ('1.0', '1.0')]:
            comparisons = deepcopy(self.source['terminal_comparisons'])
            comparisons['statistical']['value_ppm'] = statistical
            comparisons['systematic']['value_ppm'] = systematic
            s.terminal_decisions(expected, comparisons)
            self.assertEqual(repr(expected), before)
            self.assertEqual(self.calculations(), expected)

    def test_both_calculations_finish_before_any_classification(self):
        events = []
        real_calculate, real_classify = s.calculate, s.classify
        def calc(*args):
            result = real_calculate(*args); events.append(('calculate', len(result.candidates))); return result
        def decide(*args):
            self.assertEqual(events[:2], [('calculate', 15), ('calculate', 15)])
            events.append(('classify', None)); return real_classify(*args)
        with patch.object(s, 'calculate', side_effect=calc), patch.object(s, 'classify', side_effect=decide), \
             patch.object(s, 'source_snapshot', return_value={'test_only': True}):
            artifact = s.build_artifact()
        self.assertEqual(len(events), 4)
        self.assertEqual(set(artifact['terminal_decisions']), set(s.SCOPES))

    def test_both_scopes_execute_for_every_first_verdict(self):
        calculations = self.calculations()
        for first in ('compatible', 'incompatible', 'unresolved'):
            with patch.object(s, 'classify', side_effect=[(first, None), ('unresolved', None)]) as classifier:
                result = s.terminal_decisions(calculations, self.source['terminal_comparisons'])
            self.assertEqual(classifier.call_count, 2)
            self.assertEqual(tuple(result), ('statistical', 'systematic'))

    def test_terminal_bins_and_malformed_evidence(self):
        comparisons = self.source['terminal_comparisons']
        self.assertEqual(s.comparison_intervals(comparisons), {
            'statistical': Interval(F('16.25'), F('16.35')),
            'systematic': Interval(F('8.05'), F('8.15'))})
        bad = [None, {}, {'statistical': comparisons['statistical']}]
        for field, value in [('value_ppm', None), ('value_ppm', 8.1), ('value_ppm', 'NaN'),
                             ('half_width_ppm', '-0.05'), ('scope', 'statistical'), ('role', 'input')]:
            c = deepcopy(comparisons); c['systematic'][field] = value; bad.append(c)
        c = deepcopy(comparisons); del c['systematic']['value_ppm']; bad.append(c)
        for c in bad:
            with self.subTest(c=c), self.assertRaises(RoundingError):
                s.terminal_decisions(self.calculations(), c)

    def test_verdicts_match_independent_certificate_rules(self):
        calculations = self.calculations()
        scenarios = [self.source['terminal_comparisons']]
        # Include all three terminal behaviors, including sparse-schedule noncoverage.
        for value in ('99.0', '1.0'):
            c = deepcopy(scenarios[0])
            for scope in s.SCOPES: c[scope]['value_ppm'] = value
            scenarios.append(c)
        for comparisons in scenarios:
            actual = s.terminal_decisions(calculations, comparisons)
            for scope, calc in calculations.items():
                center = F(comparisons[scope]['value_ppm']); half = F(comparisons[scope]['half_width_ppm'])
                low, high = (center-half)**2, (center+half)**2
                witnesses = [i for i, candidate in enumerate(calc.candidates)
                             if low < sum(row[0]**2 for row in candidate.values) < high]
                excluded = calc.enclosure.high < low or high < calc.enclosure.low
                expected = 'incompatible' if excluded else 'compatible' if witnesses else 'unresolved'
                self.assertEqual(actual[scope]['outcome'], expected)
                if expected == 'compatible':
                    self.assertEqual(actual[scope]['witness']['candidate_index'], witnesses[0])
                    self.assertTrue(actual[scope]['witness']['membership_verified'])
                elif expected == 'incompatible':
                    self.assertTrue(actual[scope]['exclusion']['strict_disjointness'])

    def test_source_component_substitution_deletion_and_role_mutations_fail(self):
        for scope, rows in EXPECTED.items():
            for index in range(len(rows)):
                for deletion in (False, True):
                    bad = deepcopy(self.source)
                    cells = bad['input_projection']['components'][scope]
                    if deletion: del cells[index]
                    else: cells[index]['value_ppm'] = '9.9'
                    with self.assertRaises(RoundingError):
                        s.verify_source_bytes(s.serialize_artifact(bad).encode(), self.protocol)
        bad = deepcopy(self.source); bad['sources']['publication']['publisher'] = 'arXiv'
        with self.assertRaises(RoundingError):
            s.verify_source_bytes(s.serialize_artifact(bad).encode(), self.protocol)

    def test_freeze_gate_cannot_be_skipped(self):
        with TemporaryDirectory() as temp:
            history = SyntheticHistory(Path(temp)/'repo')
            base = history.commit({'seed': b'base\n'})
            data = (s.ROOT / s.PREREGISTRATION_PATH).read_bytes()
            freeze = history.commit({s.PREREGISTRATION_PATH.as_posix(): data, 'extra': b'mixed\n'})
            with patch.object(s, 'BASELINE', base), patch.object(s, 'PREREGISTRATION_COMMIT', freeze), \
                 patch.object(s, 'load_protocol', return_value=self.protocol):
                with self.assertRaisesRegex(SourceStateViolationError, 'preregistration alone'):
                    s.verify_preregistration(history.root)

    def test_three_generic_controls_remain_available(self):
        from Discovery.rounding_consistency import Budget
        budget = Budget((F(1),), ((rounding_bin(F(2), F('0.005')),),), ('independent',))
        calc = calculate(budget, PARAMETERS)
        for center, half, expected in [('2', '0.005', 'compatible'), ('3', '0.005', 'incompatible'),
                                       ('2.0048', '0.0001', 'unresolved')]:
            self.assertEqual(classify(calc, rounding_bin(F(center), F(half)))[0], expected)


class SchlammingerArtifactTests(unittest.TestCase):
    def test_frozen_specification_history_and_preserved_hust(self):
        s.verify_preregistration()
        s.verify_preserved_files()

    def test_result_freshness_and_separated_terminal_records(self):
        actual = s.build_artifact()
        stored = (s.ROOT / s.DEFAULT_OUTPUT).read_text()
        self.assertEqual(s.serialize_artifact(actual), stored)
        self.assertEqual(tuple(actual['calculations']), s.SCOPES)
        self.assertEqual(tuple(actual['terminal_decisions']), s.SCOPES)
        self.assertNotIn('terminal_comparisons', actual['input_projection'])
        for record in actual['calculations'].values():
            self.assertEqual(len(record['candidates']), 15)
            self.assertNotIn('outcome', record)
            self.assertNotIn('comparison', record)

    def test_missing_source_and_changed_specification_fail(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            protocol = s.load_protocol()
            for path in (s.PREREGISTRATION_PATH, Path(protocol['specification']['path'])):
                (root/path).parent.mkdir(parents=True, exist_ok=True)
                (root/path).write_bytes((s.ROOT/path).read_bytes())
            with self.assertRaises(OSError): s.load_source(root)
            (root/protocol['specification']['path']).write_text('changed')
            with self.assertRaises(RoundingError): s.load_protocol(root)


if __name__ == '__main__':
    unittest.main()
