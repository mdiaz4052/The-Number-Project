from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from Discovery.hust_2018_aaf_depth_2b_mutations import (
    DEFAULT_OUTPUT,
    FROZEN_MILESTONE_7_POST_AUDIT_V2_SHA256,
    HUSTDepth2BMutationError,
    run_mutations,
    serialize_artifact,
    verify_frozen_post_audit_v2_artifacts,
)
from Discovery.hust_2018_aaf_depth_2b_path_mutants import (
    AUTHORIZATION_MODULE,
    AUTHORIZATION_PATH,
    CLARIFICATION_TRAVERSAL_SPEC,
    DISPLAYED_TOTAL_SPEC,
    HUSTDepth2BPathMutationError,
    MEASUREMENT_MODEL_MODULE,
    MEASUREMENT_MODEL_PATH,
    PUBLISHED_UNCERTAINTY_SPEC,
    _import_probe,
    apply_exact_source_replacement,
    run_source_path_mutant,
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
    "clarification_byte_identity_traversal_removed",
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
        self.assertEqual(
            artifact["mutation_counts_by_kind"],
            {"in_memory": 22, "source_path": 3},
        )
        self.assertEqual(
            sum(
                case["mutation_kind"] == "source_path"
                for case in artifact["cases"]
            ),
            3,
        )

    def test_v3_revision_names_frozen_v2_predecessor(self) -> None:
        artifact = self.artifact
        self.assertEqual(artifact["artifact_schema_version"], 3)
        revision = artifact["revision"]
        self.assertEqual(
            revision["predecessor_path"],
            "Experiments/GMeasurements/"
            "hust_2018_aaf_depth_2b_mutation_results_v2.json",
        )
        self.assertEqual(
            revision["predecessor_sha256"],
            FROZEN_MILESTONE_7_POST_AUDIT_V2_SHA256[
                "Experiments/GMeasurements/"
                "hust_2018_aaf_depth_2b_mutation_results_v2.json"
            ],
        )
        self.assertFalse(revision["numerical_values_changed"])
        self.assertFalse(revision["scientific_authorization_changed"])
        self.assertFalse(revision["scope_boundaries_changed"])

    def test_nonbehavioral_sentinels_are_explicitly_excluded_from_scoring(self) -> None:
        artifact = self.artifact
        exclusions = "\n".join(artifact["excluded_non_behavioral_guards"])
        self.assertIn("tree-state", exclusions)
        self.assertIn("source-state --check", exclusions)
        self.assertIn("byte-preservation", exclusions)
        self.assertIn("import-integrity", exclusions)
        self.assertIn("cleanup", exclusions)
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
        expected_metadata = {
            "displayed_total_as_input": (
                MEASUREMENT_MODEL_PATH.as_posix(),
                MEASUREMENT_MODEL_MODULE,
                "tests.test_hust_2018_aaf_depth_2b_measurement_models."
                "HUST2018AAFDepth2BMeasurementModelTests."
                "test_displayed_total_is_not_an_uncertainty_input",
            ),
            "published_final_uncertainty_as_input": (
                MEASUREMENT_MODEL_PATH.as_posix(),
                MEASUREMENT_MODEL_MODULE,
                "tests.test_hust_2018_aaf_depth_2b_measurement_models."
                "HUST2018AAFDepth2BMeasurementModelTests."
                "test_published_final_uncertainty_is_not_an_uncertainty_input",
            ),
            "clarification_byte_identity_traversal_removed": (
                AUTHORIZATION_PATH.as_posix(),
                AUTHORIZATION_MODULE,
                "tests.test_hust_2018_aaf_depth_2b_authorization."
                "HUST2018AAFDepth2BAuthorizationTests."
                "test_clarification_nested_byte_identity_traversal_rejects_overclaim",
            ),
        }
        for mutation_id, (source_path, module_name, test_id) in (
            expected_metadata.items()
        ):
            with self.subTest(mutation=mutation_id):
                case = by_id[mutation_id]
                self.assertEqual(case["mutation_kind"], "source_path")
                self.assertEqual(case["source_path"], source_path)
                self.assertEqual(case["module_name"], module_name)
                self.assertEqual(case["designated_test_id"], test_id)
                self.assertTrue(case["mutant_applied"])
                self.assertTrue(case["mutant_importable"])
                self.assertEqual(case["sentinels_fired"], [])
                self.assertTrue(case["cleanup_confirmed"])
                self.assertTrue(case["canonical_source_unchanged"])
                self.assertNotIn("canonical_builder_unchanged", case)
                self.assertTrue(case["canonical_worktree_unchanged"])
                self.assertEqual(case["outcome"], "KILLED")

    def test_unapplied_or_ambiguous_source_mutants_are_invalid_not_killed(self) -> None:
        for spec in (DISPLAYED_TOTAL_SPEC, CLARIFICATION_TRAVERSAL_SPEC):
            with self.subTest(mutation=spec.mutation_id, replacement="absent"):
                with self.assertRaises(HUSTDepth2BPathMutationError):
                    apply_exact_source_replacement("no matching source", spec)
            with self.subTest(mutation=spec.mutation_id, replacement="ambiguous"):
                with self.assertRaises(HUSTDepth2BPathMutationError):
                    apply_exact_source_replacement(spec.old_source * 2, spec)

    def test_invalid_source_mutant_cannot_enter_scored_artifact(self) -> None:
        with patch(
            "Discovery.hust_2018_aaf_depth_2b_mutations.run_source_path_mutants",
            side_effect=HUSTDepth2BPathMutationError("invalid source mutant"),
        ):
            with self.assertRaisesRegex(
                HUSTDepth2BMutationError,
                "invalid source mutant",
            ):
                run_mutations(Path("."))

    def test_cosmetic_source_mutant_receives_no_kill_credit(self) -> None:
        cosmetic = replace(
            DISPLAYED_TOTAL_SPEC,
            mutation_id="cosmetic_source_change",
            old_source="from __future__ import annotations\n",
            new_source="from __future__ import annotations\n\n",
        )
        with self.assertRaisesRegex(
            HUSTDepth2BPathMutationError,
            "valid source-path mutant survived",
        ):
            run_source_path_mutant(Path("."), cosmetic)

    def test_wrong_import_path_is_rejected(self) -> None:
        canonical_path = (Path(".") / MEASUREMENT_MODEL_PATH).resolve()
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=canonical_path.as_posix() + "\n",
            stderr="",
        )
        with patch(
            "Discovery.hust_2018_aaf_depth_2b_path_mutants.subprocess.run",
            return_value=completed,
        ):
            with self.assertRaisesRegex(
                HUSTDepth2BPathMutationError,
                "canonical module",
            ):
                _import_probe(Path("/tmp/disposable-hust-copy"), DISPLAYED_TOTAL_SPEC)

    def test_syntax_and_discovery_failures_receive_no_kill_credit(self) -> None:
        syntax_failure = replace(
            DISPLAYED_TOTAL_SPEC,
            mutation_id="syntax_failure",
            old_source="from __future__ import annotations\n",
            new_source="from __future__ import ???\n",
        )
        discovery_failure = replace(
            PUBLISHED_UNCERTAINTY_SPEC,
            mutation_id="discovery_failure",
            designated_test_id="tests.missing_test_module.missing_test",
        )
        for spec in (syntax_failure, discovery_failure):
            with self.subTest(mutation=spec.mutation_id):
                with self.assertRaises(HUSTDepth2BPathMutationError):
                    run_source_path_mutant(Path("."), spec)

    def test_all_four_post_audit_v2_hashes_are_live_and_exact(self) -> None:
        expected_rows = [
            {"path": path, "sha256": digest}
            for path, digest in sorted(
                FROZEN_MILESTONE_7_POST_AUDIT_V2_SHA256.items()
            )
        ]
        self.assertEqual(
            self.artifact["frozen_milestone_7_post_audit_v2_preservation"],
            expected_rows,
        )
        for path, expected_sha256 in (
            FROZEN_MILESTONE_7_POST_AUDIT_V2_SHA256.items()
        ):
            with self.subTest(path=path):
                actual_sha256 = hashlib.sha256(Path(path).read_bytes()).hexdigest()
                self.assertEqual(actual_sha256, expected_sha256)

    def test_v2_hash_mismatch_fails_before_behavioral_scoring(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative_path in FROZEN_MILESTONE_7_POST_AUDIT_V2_SHA256:
                destination = root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(relative_path, destination)
            first_path = next(iter(FROZEN_MILESTONE_7_POST_AUDIT_V2_SHA256))
            (root / first_path).write_bytes(b"tampered\n")
            with self.assertRaisesRegex(
                HUSTDepth2BMutationError,
                "non-behavioral v2 integrity hash mismatch",
            ):
                verify_frozen_post_audit_v2_artifacts(root)


if __name__ == "__main__":
    unittest.main()
