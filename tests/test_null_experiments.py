from dataclasses import replace
import json
import math
from pathlib import Path
import tempfile
import unittest

from Discovery.dependency_analysis import (
    NO_REGISTERED_TARGET_DEPENDENCY,
    TARGET_DEPENDENT,
    analyze_default_candidates,
)
from Discovery.null_experiments import (
    CandidateClass,
    DEFAULT_OUTPUT,
    analytic_nearest_distance_cdf,
    build_candidate_classes,
    calibration_regime_record,
    derive_global_interval,
    iter_trial_rows,
    maximum_cdf_deviation,
    nearest_classes,
    sample_uniform_log_targets,
    stratify_classes,
    unique_log_positions,
    validate_result_integrity,
    _planted_controls,
)


class NullExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates = analyze_default_candidates()
        cls.classes = build_candidate_classes(cls.candidates)
        cls.primary, cls.circularity, cls.unresolved = stratify_classes(cls.classes)

    def test_provenance_filtering_and_circularity_separation(self) -> None:
        self.assertTrue(self.primary)
        self.assertTrue(self.circularity)
        self.assertTrue(
            all(
                item.dependency_status == NO_REGISTERED_TARGET_DEPENDENCY
                for item in self.primary
            )
        )
        self.assertTrue(
            all(item.dependency_status != NO_REGISTERED_TARGET_DEPENDENCY for item in self.circularity)
        )
        self.assertFalse(set(self.primary) & set(self.circularity))

    def test_equivalence_class_accounting_is_derived(self) -> None:
        self.assertEqual(len(self.candidates), 21)
        self.assertEqual(len(self.classes), 10)
        self.assertEqual(
            len(self.primary) + len(self.circularity) + len(self.unresolved),
            len(self.classes),
        )

    def test_duplicate_positions_do_not_expand_geometric_coverage(self) -> None:
        self.assertEqual(
            analytic_nearest_distance_cdf(0.25, 0.0, 2.0, (1.0, 1.0)),
            0.25,
        )

    def test_analytic_cdf_is_correct_on_hand_checkable_examples(self) -> None:
        self.assertEqual(analytic_nearest_distance_cdf(0.0, 0.0, 10.0, (2.0, 8.0)), 0.0)
        self.assertEqual(analytic_nearest_distance_cdf(1.0, 0.0, 10.0, (2.0, 8.0)), 0.4)
        self.assertEqual(analytic_nearest_distance_cdf(3.0, 0.0, 10.0, (2.0, 8.0)), 1.0)
        self.assertEqual(analytic_nearest_distance_cdf(2.0, 0.0, 4.0, (0.0,)), 0.5)

    def test_monte_carlo_sampler_is_reproducible(self) -> None:
        first = sample_uniform_log_targets(-3.0, 3.0, count=20, seed=123)
        second = sample_uniform_log_targets(-3.0, 3.0, count=20, seed=123)
        different = sample_uniform_log_targets(-3.0, 3.0, count=20, seed=124)
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)

    def test_small_monte_carlo_fixture_agrees_with_analytic_oracle(self) -> None:
        samples = sample_uniform_log_targets(0.0, 10.0, count=5000, seed=991)
        positions = (2.0, 8.0)
        distances = [min(abs(value - position) for position in positions) for value in samples]
        self.assertLess(
            maximum_cdf_deviation(distances, 0.0, 10.0, positions),
            0.03,
        )

    def test_global_bounds_include_candidates_and_local_window(self) -> None:
        positions = unique_log_positions(self.primary)
        local = (-14.0, -8.0)
        lower, upper = derive_global_interval(positions, local)
        self.assertLessEqual(lower, local[0])
        self.assertGreaterEqual(upper, local[1])
        self.assertLessEqual(lower, min(positions) - 3.0)
        self.assertGreaterEqual(upper, max(positions) + 3.0)

    def test_target_dependent_class_cannot_enter_primary_fixture(self) -> None:
        changed = replace(self.primary[0], dependency_status=TARGET_DEPENDENT)
        primary, circularity, _ = stratify_classes((changed, *self.primary[1:]))
        self.assertNotIn(changed, primary)
        self.assertIn(changed, circularity)

    def test_nearest_class_reports_transparent_ties(self) -> None:
        left = CandidateClass("a", NO_REGISTERED_TARGET_DEPENDENCY, (), ("a",), 0.0)
        right = CandidateClass("b", NO_REGISTERED_TARGET_DEPENDENCY, (), ("b",), 2.0)
        distance, winners = nearest_classes(1.0, (right, left))
        self.assertEqual(distance, 1.0)
        self.assertEqual(winners, ("a", "b"))

    def test_preregistered_planted_targets_recover_intended_classes(self) -> None:
        result = _planted_controls(self.primary, ("-0.01", "0.001", "0.01"))
        self.assertEqual(result["status"], "valid")
        self.assertEqual(len(result["controls"]), 3)
        self.assertTrue(all(control["recovered"] for control in result["controls"]))
        self.assertTrue(
            all(control["distance_matches"] for control in result["controls"])
        )

    def test_integrity_rejects_preregistration_hash_and_seed_mismatch(self) -> None:
        from Discovery.falsification_preregistration import load_preregistration

        preregistration, content = load_preregistration()
        base = {
            "result_schema_version": 2,
            "experiment_identifier": preregistration["experiment_identifier"],
            "integrity": {
                "preregistration_sha256": __import__("hashlib").sha256(content).hexdigest(),
                "seeds": preregistration["randomness"]["seeds"],
            },
        }
        changed_hash = json.loads(json.dumps(base))
        changed_hash["integrity"]["preregistration_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            validate_result_integrity(changed_hash)
        changed_seed = json.loads(json.dumps(base))
        changed_seed["integrity"]["seeds"]["local_null"] += 1
        with self.assertRaisesRegex(ValueError, "seed mismatch"):
            validate_result_integrity(changed_seed)

    def test_trial_chunk_decoder_detects_payload_corruption(self) -> None:
        run = {
            "target_count": 1,
            "trial_encoding": {
                "format": "tab_separated_utf8_chunks_v1",
                "payload_sha256": "0" * 64,
                "chunks": ["0\t0x0.0p+0\t0x1.0p+0\t0x0.0p+0\teq-a"],
            },
        }
        with self.assertRaisesRegex(ValueError, "payload hash mismatch"):
            tuple(iter_trial_rows(run))

    def test_calibration_regime_record_is_hand_checkable(self) -> None:
        left = CandidateClass("a", NO_REGISTERED_TARGET_DEPENDENCY, (), ("a",), 0.0)
        right = CandidateClass("b", NO_REGISTERED_TARGET_DEPENDENCY, (), ("b",), 2.0)
        record = calibration_regime_record(
            (left, right),
            -1.0,
            3.0,
            (-1.0, 0.5, 1.0, 3.0),
            (("a",), ("a",), ("a", "b"), ("b",)),
        )
        self.assertEqual(
            record["minimum_pairwise_position_separation_log10"]["decimal"],
            "2",
        )
        self.assertTrue(record["eligible_position_inside_interval"])
        self.assertEqual(record["overlap_regime"]["trial_count"], 2)
        self.assertEqual(record["overlap_regime"]["trial_fraction"]["decimal"], "0.5")
        self.assertEqual(record["observed_distinct_winning_class_count"], 2)

    def test_current_local_regime_is_explicitly_degenerate(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        regime = result["local_null"]["calibration_regime"]
        self.assertFalse(regime["eligible_position_inside_interval"])
        self.assertEqual(regime["overlap_regime"]["trial_count"], 0)
        self.assertEqual(regime["observed_distinct_winning_class_count"], 1)
        self.assertTrue(
            result["real_G_navigation"][
                "local_null_analytic_cdf_is_forced_by_centering"
            ]
        )


if __name__ == "__main__":
    unittest.main()
