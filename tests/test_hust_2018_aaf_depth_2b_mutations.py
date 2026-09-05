from __future__ import annotations

from pathlib import Path
import unittest

from Discovery.hust_2018_aaf_depth_2b_mutations import (
    DEFAULT_OUTPUT,
    run_mutations,
    serialize_artifact,
)
from Discovery.hust_2018_aaf_depth_2b_path_mutants import (
    DISPLAYED_TOTAL_SPEC,
    HUSTDepth2BPathMutationError,
    apply_exact_source_replacement,
)


EXPECTED_MUTATIONS = {
    "missing_component",
    "duplicate_component",
    "extra_component",
    "renamed_component",
    "reordered_components",
    "wrong_component_unit",
    "wrong_component_source",
    "cross_column_component",
    "combined_authorization_flag",
    "official_source_hash_bypass",
    "falsified_table_locator",
    "unknown_target_derived_note",
    "normalized_byte_identity_overclaim",
    "wrong_component_role",
    "cross_scope_component_ancestry",
    "physical_independence_overclaim",
    "sum_instead_of_rss",
    "missing_component_square",
    "missing_square_root",
    "incorrect_ppm_conversion",
    "default_decimal_precision_28",
    "displayed_total_as_input",
    "published_final_uncertainty_as_input",
    "combined_scope_authorization",
}


class HUST2018AAFDepth2BMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = run_mutations(Path("."))

    def test_every_scored_behavioral_mutation_is_killed(self) -> None:
        artifact = self.artifact
        self.assertEqual(artifact["decision"], "PASS")
        self.assertEqual(
            {case["mutation_id"] for case in artifact["cases"]},
            EXPECTED_MUTATIONS,
        )
        self.assertTrue(
            all(case["outcome"] == "KILLED" for case in artifact["cases"])
        )
        self.assertEqual(artifact["score"]["killed"], len(EXPECTED_MUTATIONS))
        self.assertEqual(artifact["score"]["total"], len(EXPECTED_MUTATIONS))
        self.assertEqual(artifact["score"]["survived"], 0)
        self.assertEqual(artifact["score"]["ratio_decimal"], "1")

    def test_nonbehavioral_sentinels_are_explicitly_excluded_from_scoring(self) -> None:
        artifact = self.artifact
        exclusions = "\n".join(artifact["excluded_non_behavioral_guards"])
        self.assertIn("tree-state", exclusions)
        self.assertIn("source-state --check", exclusions)
        self.assertIn("historical byte-preservation", exclusions)
        self.assertTrue(
            all(
                "behavioral" in artifact["scoring_rule"]
                for _case in artifact["cases"]
            )
        )

    def test_committed_mutation_artifact_is_fresh(self) -> None:
        self.assertEqual(
            DEFAULT_OUTPUT.read_text(encoding="utf-8"),
            serialize_artifact(self.artifact),
        )

    def test_terminal_cases_are_valid_isolated_source_path_mutants(self) -> None:
        by_id = {case["mutation_id"]: case for case in self.artifact["cases"]}
        expected_tests = {
            "displayed_total_as_input": (
                "tests.test_hust_2018_aaf_depth_2b_measurement_models."
                "HUST2018AAFDepth2BMeasurementModelTests."
                "test_displayed_total_is_not_an_uncertainty_input"
            ),
            "published_final_uncertainty_as_input": (
                "tests.test_hust_2018_aaf_depth_2b_measurement_models."
                "HUST2018AAFDepth2BMeasurementModelTests."
                "test_published_final_uncertainty_is_not_an_uncertainty_input"
            ),
        }
        for mutation_id, test_id in expected_tests.items():
            with self.subTest(mutation=mutation_id):
                case = by_id[mutation_id]
                self.assertEqual(case["mutation_kind"], "source_path")
                self.assertEqual(case["designated_test_id"], test_id)
                self.assertTrue(case["mutant_applied"])
                self.assertTrue(case["mutant_importable"])
                self.assertEqual(case["sentinels_fired"], [])
                self.assertTrue(case["cleanup_confirmed"])
                self.assertTrue(case["canonical_builder_unchanged"])
                self.assertTrue(case["canonical_worktree_unchanged"])
                self.assertEqual(case["outcome"], "KILLED")

    def test_unapplied_or_ambiguous_source_mutants_are_invalid_not_killed(self) -> None:
        with self.assertRaises(HUSTDepth2BPathMutationError):
            apply_exact_source_replacement("no matching source", DISPLAYED_TOTAL_SPEC)
        with self.assertRaises(HUSTDepth2BPathMutationError):
            apply_exact_source_replacement(
                DISPLAYED_TOTAL_SPEC.old_source * 2,
                DISPLAYED_TOTAL_SPEC,
            )


if __name__ == "__main__":
    unittest.main()
