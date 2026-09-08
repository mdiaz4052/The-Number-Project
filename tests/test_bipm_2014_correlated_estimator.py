from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import unittest

from Discovery.correlated_weighted_mean import (
    CorrelatedMeanError,
    Interval,
    closed_intersection,
    decimal_cell,
    linear_enclosure,
    minimum_variance_unbiased_weights,
)
from Discovery import bipm_2014_correlated_estimator as b


class BIPMCorrelatedEstimatorBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.weights = minimum_variance_unbiased_weights(
            Fraction(61), Fraction(54), Fraction(-2080)
        )

    def test_exact_minimum_variance_weights_and_sum(self):
        self.assertEqual(self.weights.first, Fraction(4996, 10797))
        self.assertEqual(self.weights.second, Fraction(5801, 10797))
        self.assertEqual(self.weights.first + self.weights.second, 1)
        self.assertEqual(self.weights.denominator, 10797)
        self.assertEqual(self.weights.determinant, 6524036)
        self.assertEqual(self.weights.variance, Fraction(6524036, 10797))

    def test_covariance_changes_weights_and_variance(self):
        independent = minimum_variance_unbiased_weights(
            Fraction(61), Fraction(54), Fraction(0)
        )
        self.assertNotEqual(independent.first, self.weights.first)
        self.assertNotEqual(independent.variance, self.weights.variance)
        opposite = minimum_variance_unbiased_weights(
            Fraction(61), Fraction(54), Fraction(2080)
        )
        self.assertNotEqual(opposite.first, self.weights.first)

    def test_positive_definite_and_denominator_guards(self):
        with self.assertRaises(CorrelatedMeanError):
            minimum_variance_unbiased_weights(Fraction(0), Fraction(54), Fraction(0))
        with self.assertRaises(CorrelatedMeanError):
            minimum_variance_unbiased_weights(Fraction(1), Fraction(1), Fraction(1))
        with self.assertRaises(CorrelatedMeanError):
            minimum_variance_unbiased_weights(Fraction(1), Fraction(1), Fraction(-1))

    def test_swap_symmetry(self):
        swapped = minimum_variance_unbiased_weights(
            Fraction(54), Fraction(61), Fraction(-2080)
        )
        self.assertEqual(swapped.first, self.weights.second)
        self.assertEqual(swapped.second, self.weights.first)
        servo = decimal_cell("6.67515", 5)
        cavendish = decimal_cell("6.67586", 5)
        original = linear_enclosure((servo, cavendish), (self.weights.first, self.weights.second))
        reverse = linear_enclosure((cavendish, servo), (swapped.first, swapped.second))
        self.assertEqual(original, reverse)

    def test_decimal_cells_and_sign_aware_linear_enclosure(self):
        servo = decimal_cell("6.67515", 5)
        self.assertEqual(servo.low, Fraction(1335029, 200000))
        self.assertEqual(servo.high, Fraction(1335031, 200000))
        interval = linear_enclosure(
            (Interval(Fraction(1), Fraction(2)), Interval(Fraction(10), Fraction(20))),
            (Fraction(2), Fraction(-1)),
        )
        self.assertEqual(interval, Interval(Fraction(-18), Fraction(-6)))

    def test_real_source_midpoint_and_enclosure_are_distinct(self):
        protocol = {"source_projection": {"estimator_inputs": {}}}
        attestation = {
            "transcription": {
                "estimator_inputs": {
                    "servo": {
                        "value_decimal_in_1e_minus_11_units": "6.67515",
                        "printed_decimal_places": 5,
                        "relative_standard_uncertainty_ppm": "61",
                    },
                    "cavendish": {
                        "value_decimal_in_1e_minus_11_units": "6.67586",
                        "printed_decimal_places": 5,
                        "relative_standard_uncertainty_ppm": "54",
                    },
                    "covariance_ppm_squared": {"value": "-2080"},
                }
            }
        }
        state = b.estimator_state(protocol, attestation)
        target = decimal_cell("6.67554", 5)
        self.assertLess(state["midpoint_aggregate"], target.low)
        self.assertIsNotNone(closed_intersection(state["aggregate_enclosure"], target))
        self.assertEqual(
            state["aggregate_enclosure"].low,
            Fraction(2883026371, 431880000),
        )
        self.assertEqual(
            state["aggregate_enclosure"].high,
            Fraction(14415153449, 2159400000),
        )

    def test_target_and_printed_summary_invariance(self):
        protocol = {
            "source_projection": {
                "comparison_only": {
                    "printed_servo_weight": "0.46",
                    "printed_cavendish_weight": "0.54",
                    "printed_combined_relative_uncertainty_ppm": "25",
                    "published_combined_G_decimal_in_1e_minus_11_units": "6.67554",
                    "published_combined_printed_decimal_places": 5,
                }
            }
        }
        attestation = {
            "transcription": {
                "estimator_inputs": {
                    "servo": {
                        "value_decimal_in_1e_minus_11_units": "6.67515",
                        "printed_decimal_places": 5,
                        "relative_standard_uncertainty_ppm": "61",
                    },
                    "cavendish": {
                        "value_decimal_in_1e_minus_11_units": "6.67586",
                        "printed_decimal_places": 5,
                        "relative_standard_uncertainty_ppm": "54",
                    },
                    "covariance_ppm_squared": {"value": "-2080"},
                }
            }
        }
        state = b.estimator_state(protocol, attestation)
        changed_protocol = deepcopy(protocol)
        changed = changed_protocol["source_projection"]["comparison_only"]
        changed["published_combined_G_decimal_in_1e_minus_11_units"] = "9.99999"
        changed["printed_servo_weight"] = "0.99"
        changed["printed_cavendish_weight"] = "0.01"
        changed["printed_combined_relative_uncertainty_ppm"] = "999"
        changed_state = b.estimator_state(changed_protocol, attestation)
        self.assertEqual(state["weights"], changed_state["weights"])
        self.assertEqual(state["aggregate_enclosure"], changed_state["aggregate_enclosure"])
        self.assertEqual(b.classify(state, changed)["outcome"], "incompatible")

    def test_synthetic_compatible_and_incompatible_classification(self):
        state = {"aggregate_enclosure": Interval(Fraction(10), Fraction(12))}
        compatible = {
            "published_combined_G_decimal_in_1e_minus_11_units": "11",
            "published_combined_printed_decimal_places": 0,
        }
        incompatible = {
            "published_combined_G_decimal_in_1e_minus_11_units": "20",
            "published_combined_printed_decimal_places": 0,
        }
        self.assertEqual(b.classify(state, compatible)["outcome"], "compatible")
        result = b.classify(state, incompatible)
        self.assertEqual(result["outcome"], "incompatible")
        self.assertEqual(
            result["status"],
            "not_representable_under_the_declared_bipm_2014_correlated_weighted_mean_model",
        )

    def test_comparison_only_fields_not_accepted_by_estimator_api(self):
        self.assertEqual(b.estimator_state.__code__.co_argcount, 2)
        self.assertEqual(b.estimator_state.__code__.co_varnames[:2], ("protocol", "attestation"))


class BIPMCorrelatedEstimatorArtifactTests(unittest.TestCase):
    def test_e001_inventory_is_disjoint(self):
        b.verify_e001_isolation()
        self.assertFalse(set(b.E001_FORBIDDEN) & set(b.SOURCE_PATHS))


if __name__ == "__main__":
    unittest.main()
