from __future__ import annotations

from pathlib import Path
import unittest

from Discovery.hust_2018_aaf_depth_2b_mutations import (
    DEFAULT_OUTPUT,
    run_mutations,
    serialize_artifact,
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
    def test_every_scored_behavioral_mutation_is_killed(self) -> None:
        artifact = run_mutations(Path("."))
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
        artifact = run_mutations(Path("."))
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
            serialize_artifact(run_mutations(Path("."))),
        )


if __name__ == "__main__":
    unittest.main()
