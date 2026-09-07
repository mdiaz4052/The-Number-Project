"""Independent matrix arithmetic and boundary controls for rounding certificates."""

from dataclasses import replace
from decimal import FloatOperation, ROUND_UP, localcontext
from fractions import Fraction as F
from itertools import product
import unittest

from Discovery.rounding_consistency import (
    Budget, Candidate, Interval, RoundingError, calculate, classify,
    decimal_fraction, enclose_relative_variance, evaluate_point, rounding_bin,
    sqrt_display_bounds, verify_witness,
)


PARAMETERS = (F(0),) + tuple(F(sign*k, 8) for k in range(1, 8) for sign in (-1, 1))


def matrix_oracle(central, components, correlations):
    """Construct absolute C and p^T C p, independently of component propagation."""
    n = len(central)
    absolute = [[central[i]*row[i]/1000000 for i in range(n)] for row in components]
    covariance = [[sum(row[i]*row[j] for row, corr in zip(absolute, correlations)
                       if i == j or corr == "shared") for j in range(n)] for i in range(n)]
    inverse = [1/covariance[i][i] for i in range(n)]
    weights = [v/sum(inverse) for v in inverse]
    mean = sum(weights[i]*central[i] for i in range(n))
    variance = sum(weights[i]*weights[j]*covariance[i][j] for i in range(n) for j in range(n))
    return tuple(weights), mean, variance/mean**2*10**12


class RoundingConsistencyTests(unittest.TestCase):
    def single(self, center="2", half="0.005"):
        return Budget((F(1),), ((rounding_bin(F(center), F(half)),),), ("shared",))

    def unequal(self):
        rows = (("2", "3"), ("4", "2"), ("1", "5"))
        return Budget((F(2), F(7)), tuple(tuple(rounding_bin(F(x), F("0.1")) for x in row)
                                        for row in rows), ("shared", "independent", "shared"))

    def test_three_outcomes_have_distinct_certificates(self):
        calculation = calculate(self.single(), PARAMETERS)
        for target, half, expected in (("2", "0.005", "compatible"),
                                       ("3", "0.005", "incompatible"),
                                       ("2.0048", "0.0001", "unresolved")):
            with self.subTest(expected=expected):
                outcome, index = classify(calculation, rounding_bin(F(target), F(half)))
                self.assertEqual(outcome, expected)
                self.assertEqual(index is not None, expected == "compatible")

    def test_unresolved_does_not_mean_impossible(self):
        budget = self.single()
        target = rounding_bin(F("2.0048"), F("0.0001"))
        self.assertEqual(classify(calculate(budget, PARAMETERS), target), ("unresolved", None))
        unscheduled = evaluate_point(budget, ((F("2.0048"),),))
        self.assertTrue(target.square().contains(unscheduled.relative_variance_ppm_squared, interior=True))

    def test_unequal_central_values_and_shifted_weights_match_matrix_oracle(self):
        budget = self.unequal()
        calculation = calculate(budget, PARAMETERS)
        for candidate in calculation.candidates:
            weights, mean, variance = matrix_oracle(budget.central_values, candidate.values, budget.correlations)
            self.assertEqual(candidate.evaluation.weights, weights)
            self.assertEqual(candidate.evaluation.combined_central_value, mean)
            self.assertEqual(candidate.evaluation.relative_variance_ppm_squared, variance)
            self.assertEqual(sum(weights), 1)
            self.assertEqual(sum(candidate.evaluation.propagation_coefficients), 1)
        self.assertNotEqual(calculation.candidates[0].evaluation.weights, calculation.candidates[1].evaluation.weights)

    def test_shared_and_independent_terms_have_different_covariance(self):
        budget = Budget((F(1), F(1)), ((Interval.point(F(2)), Interval.point(F(2))),), ("shared",))
        values = ((F(2), F(2)),)
        shared = evaluate_point(budget, values).relative_variance_ppm_squared
        independent = evaluate_point(replace(budget, correlations=("independent",)), values).relative_variance_ppm_squared
        self.assertEqual(shared, F(4))
        self.assertEqual(independent, F(2))

    def test_direct_point_weights_use_absolute_total_variance(self):
        budget = self.unequal()
        values = tuple(tuple((x.low+x.high)/2 for x in row) for row in budget.components)
        weights, mean, variance = matrix_oracle(budget.central_values, values, budget.correlations)
        actual = evaluate_point(budget, values)
        self.assertEqual(actual.weights, weights)
        self.assertEqual(actual.combined_central_value, mean)
        self.assertEqual(actual.relative_variance_ppm_squared, variance)

    def test_all_small_box_corners_are_enclosed_and_match_matrix_oracle(self):
        budget = self.unequal()
        enclosure = enclose_relative_variance(budget)
        cells = [cell for row in budget.components for cell in row]
        for choices in product((0, 1), repeat=len(cells)):
            flat = [cell.low if choice == 0 else cell.high for cell, choice in zip(cells, choices)]
            values = tuple(tuple(flat[i:i+2]) for i in range(0, len(flat), 2))
            result = evaluate_point(budget, values)
            self.assertEqual(result.relative_variance_ppm_squared,
                             matrix_oracle(budget.central_values, values, budget.correlations)[2])
            self.assertTrue(enclosure.contains(result.relative_variance_ppm_squared))

    def test_exact_single_component_enclosure_and_rational_interior_grid(self):
        budget = self.single("2", "1")
        enclosure = enclose_relative_variance(budget)
        self.assertEqual(enclosure, Interval(F(1), F(9)))
        for k in range(1, 21):
            x = F(1) + F(k, 10)
            result = evaluate_point(budget, ((x,),))
            self.assertTrue(enclosure.contains(result.relative_variance_ppm_squared))

    def test_degenerate_intervals_collapse_exactly(self):
        budget = self.unequal()
        exact = replace(budget, components=tuple(tuple(Interval.point((x.low+x.high)/2) for x in row)
                                                 for row in budget.components))
        result = calculate(exact, PARAMETERS)
        self.assertEqual(result.enclosure.low, result.enclosure.high)
        self.assertEqual(result.enclosure.low, result.candidates[0].evaluation.relative_variance_ppm_squared)

    def test_touching_enclosures_do_not_establish_exclusion(self):
        calculation = calculate(self.single("2", "1"), (F(0),))
        self.assertEqual(classify(calculation, Interval(F(3), F(4))), ("unresolved", None))

    def test_comparison_boundary_contact_is_not_a_witness(self):
        calculation = calculate(self.single("2", "1"), (F(0),))
        self.assertEqual(classify(calculation, Interval(F(2), F(4))), ("unresolved", None))

    def test_input_boundary_contact_is_not_a_witness(self):
        budget = self.single("2", "1")
        values = ((F(3),),)
        candidate = Candidate(F(0), values, evaluate_point(budget, values))
        self.assertFalse(verify_witness(budget, candidate, Interval.point(F(3))))

    def test_zero_width_comparison_permits_exact_equality(self):
        self.assertEqual(classify(calculate(self.single(), PARAMETERS), Interval.point(F(2))), ("compatible", 0))

    def test_tampered_witness_arithmetic_is_rejected(self):
        budget = self.single()
        candidate = calculate(budget, PARAMETERS).candidates[0]
        corrupt = replace(candidate, evaluation=replace(candidate.evaluation, relative_variance_ppm_squared=F(9)))
        with self.assertRaisesRegex(RoundingError, "arithmetic certificate"):
            verify_witness(budget, corrupt, Interval(F(1), F(4)))

    def test_comparison_changes_never_change_calculation(self):
        calculation = calculate(self.unequal(), PARAMETERS)
        before = repr(calculation)
        for target in (Interval(F(0), F(1)), Interval(F(1), F(100)), Interval(F(100), F(200))):
            classify(calculation, target)
            self.assertEqual(repr(calculation), before)

    def test_candidate_schedule_is_complete_ordered_and_interior(self):
        calculation = calculate(self.single(), PARAMETERS)
        self.assertEqual(tuple(c.parameter for c in calculation.candidates), PARAMETERS)
        self.assertEqual(len(calculation.candidates), 15)
        for candidate in calculation.candidates:
            self.assertEqual(candidate.values[0][0], F(2) + candidate.parameter*F("0.005"))

    def test_invalid_candidate_schedules_fail(self):
        for schedule in ((), (F(1),), (F(-1),), (F(0), F(0)), (0.0,)):
            with self.subTest(schedule=schedule), self.assertRaises(RoundingError):
                calculate(self.single(), schedule)

    def test_invalid_authoritative_scalars_fail(self):
        for value in (1.2, 1, True, "NaN", "Infinity", "1/2", " 1", "1_000", ""):
            with self.subTest(value=value), self.assertRaises(RoundingError):
                decimal_fraction(value)
        self.assertEqual(decimal_fraction("6.674484e-11"), F("6.674484e-11"))

    def test_nonpositive_or_malformed_budget_fails(self):
        for operation in (
            lambda: Interval(F(2), F(1)), lambda: Interval(F(-1), F(1)),
            lambda: Interval(0.0, 1.0), lambda: rounding_bin(F(2), F(-1)),
            lambda: Interval(F(0), F(1)).reciprocal(),
            lambda: Budget((F(0),), ((Interval.point(F(1)),),), ("shared",)),
            lambda: Budget((F(1),), ((Interval(F(0), F(1)),),), ("shared",)),
            lambda: Budget((F(1), F(2)), ((Interval.point(F(1)),),), ("shared",)),
            lambda: replace(self.single(), correlations=("invented",)),
            lambda: replace(self.single(), components=()),
        ):
            with self.assertRaises(RoundingError):
                operation()

    def test_point_outside_domain_or_wrong_shape_fails(self):
        for values in (((F(9),),), ((2.0,),), (), ((F(2), F(2)),)):
            with self.subTest(values=values), self.assertRaises(RoundingError):
                evaluate_point(self.single(), values)

    def test_integer_square_root_rounds_outward(self):
        for value in (F(0), F(1, 3), F(4), F(4000001, 1000000), F(10)**40):
            interval = Interval.point(value)
            displayed = sqrt_display_bounds(interval, 6)
            lower, upper = F(displayed["low"]), F(displayed["high"])
            self.assertLessEqual(lower**2, value)
            self.assertGreaterEqual(upper**2, value)
            self.assertLessEqual(upper-lower, F(1, 1000000))
        self.assertEqual(sqrt_display_bounds(Interval.point(F(4)), 0)["low"], "2")

    def test_decimal_context_cannot_affect_calculation(self):
        expected = calculate(self.unequal(), PARAMETERS)
        with localcontext() as context:
            context.prec = 3
            context.rounding = ROUND_UP
            context.traps[FloatOperation] = True
            self.assertEqual(calculate(self.unequal(), PARAMETERS), expected)
            self.assertEqual(decimal_fraction("0.005"), F(1, 200))


if __name__ == "__main__":
    unittest.main()
