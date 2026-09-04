from pathlib import Path
import json
import sys
import types
import unittest

from Discovery.mutation_harness import (
    ANTI_GOODHART_RULE,
    CALIBRATION_MUTANTS,
    CALIBRATION_RULE,
    DEFAULT_OUTPUT,
    INVALID,
    KILLED,
    NONCLAIMS,
    PRODUCTION_MUTANTS,
    SOURCE_PATHS,
    SURVIVED,
    Mutant,
    apply_mutation,
    canonical_head,
    canonical_status_bytes,
    classify_runner_record,
    mutation_records_sha256,
    _sanitize_diagnostic,
    repository_root,
    run_mutant,
    source_path_snapshot,
    validate_result_integrity,
    verify_result_source_snapshot,
)
from Discovery.mutation_test_runner import validate_import_paths


class MutationHarnessUnitTests(unittest.TestCase):
    def test_classification_distinguishes_killed_survived_invalid(self) -> None:
        killed = classify_runner_record(
            {
                "runner_status": "completed",
                "failing_tests": ["test.behavior"],
                "error_tests": [],
                "successful": False,
            }
        )
        survived = classify_runner_record(
            {
                "runner_status": "completed",
                "failing_tests": [],
                "error_tests": [],
                "successful": True,
            }
        )
        invalid = classify_runner_record(
            {"runner_status": "invalid", "infrastructure_error": "bad import"}
        )
        self.assertEqual(killed[0], KILLED)
        self.assertEqual(killed[1], ("test.behavior",))
        self.assertEqual(survived[0], SURVIVED)
        self.assertEqual(invalid[0], INVALID)

    def test_physical_bridge_schema_is_source_attested(self) -> None:
        self.assertIn("Discovery/physical_bridge.py", SOURCE_PATHS)
        self.assertIn("Discovery/physical_bridge_schema.py", SOURCE_PATHS)
        self.assertIn(
            "tests/test_physical_bridge_source_identifier_hardening.py",
            SOURCE_PATHS,
        )

    def test_direct_budget_behavioral_mutants_are_registered(self) -> None:
        identifiers = {mutant.identifier for mutant in PRODUCTION_MUTANTS}
        self.assertTrue(
            {
                "production_allow_uncertainty_component_in_estimator_ancestry",
                "production_omit_empirical_uncertainty_component_source_metadata",
                "production_treat_missing_target_uncertainty_as_satisfied",
                "production_silently_normalize_source_identifier",
            }
            <= identifiers
        )

    def test_import_path_validation_rejects_external_project_copy(self) -> None:
        fake = types.ModuleType("Discovery.fake")
        fake.__file__ = "/unexpected/Discovery/fake.py"
        with self.assertRaisesRegex(RuntimeError, "outside mutation root"):
            validate_import_paths(
                Path("/expected"),
                {"Discovery.fake": fake},
                required_module_names=("Discovery.fake",),
            )

    def test_ephemeral_paths_are_removed_from_diagnostics(self) -> None:
        root = Path("/tmp/tnp-mutation-random/worktree")
        diagnostic = _sanitize_diagnostic(
            f"failure in {root}/tests/test_x.py\nRan 1 test in 0.123s",
            root,
        )
        self.assertEqual(
            diagnostic,
            "failure in <DISPOSABLE_WORKTREE>/tests/test_x.py\n"
            "Ran 1 test(s) in <ELAPSED>",
        )

    def test_result_integrity_rejects_hash_and_seed_mismatch(self) -> None:
        from Discovery.falsification_preregistration import (
            load_preregistration,
            preregistration_sha256_bytes,
        )

        preregistration, content = load_preregistration()
        record = {
            "result_schema_version": 3,
            "experiment_identifier": preregistration["experiment_identifier"],
            "integrity": {
                "preregistration_sha256": preregistration_sha256_bytes(content),
                "seeds": dict(preregistration["randomness"]["seeds"]),
            },
        }
        record["integrity"]["preregistration_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            validate_result_integrity(record)
        record["integrity"]["preregistration_sha256"] = preregistration_sha256_bytes(content)
        record["integrity"]["seeds"]["local_null"] += 1
        with self.assertRaisesRegex(ValueError, "seed mismatch"):
            validate_result_integrity(record)

    def test_apply_mutation_refuses_canonical_checkout(self) -> None:
        root = repository_root()
        mutant = Mutant(
            "unit_refuse_canonical",
            "production",
            "Must not touch canonical source.",
            "README.md",
            "The Number Project",
            "Changed Number Project",
            ("tests.test_dimensions.DimensionTests.test_g_dimension_is_exact",),
            ("Discovery.dimensions",),
        )
        with self.assertRaisesRegex(RuntimeError, "not an established disposable"):
            apply_mutation(root, root, mutant)

    def test_committed_record_tampering_is_rejected(self) -> None:
        original = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))

        def changed() -> dict[str, object]:
            return json.loads(json.dumps(original))

        cases = []
        record = changed()
        record["production_results"][0]["classification"] = SURVIVED
        cases.append(record)
        record = changed()
        record["calibration_results"][0]["classification"] = SURVIVED
        cases.append(record)
        record = changed()
        record["production_results"][0]["killing_tests"] = []
        cases.append(record)
        record = changed()
        record["calibration_results"][0]["import_path_integrity"]["validated"] = False
        cases.append(record)
        record = changed()
        record["production_results"][1]["invalid_reason"] = "tampered"
        cases.append(record)

        for tampered in cases:
            with self.subTest(field=tampered):
                with self.assertRaisesRegex(ValueError, "mutation-record hash mismatch"):
                    validate_result_integrity(tampered)

    def test_pinned_methodological_claims_reject_rehashed_edits(self) -> None:
        original = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        changes = {
            "calibration_rule": f"{CALIBRATION_RULE} Changed.",
            "anti_goodhart_rule": f"{ANTI_GOODHART_RULE} Changed.",
            "nonclaims": [*NONCLAIMS[:-1], "Changed methodological nonclaim."],
        }
        for field, replacement in changes.items():
            with self.subTest(field=field):
                result = json.loads(json.dumps(original))
                result[field] = replacement
                result["integrity"]["records_sha256"] = mutation_records_sha256(
                    result["calibration_results"],
                    result["production_results"],
                    source_commit_sha=result["integrity"]["source_commit_sha"],
                    source_snapshot=result["integrity"]["source_snapshot"],
                )
                with self.assertRaisesRegex(
                    ValueError,
                    f"pinned field mismatch: {field}",
                ):
                    validate_result_integrity(result)

    def test_clean_committed_methodological_claims_are_canonical(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(result["calibration_rule"], CALIBRATION_RULE)
        self.assertEqual(result["anti_goodhart_rule"], ANTI_GOODHART_RULE)
        self.assertEqual(result["nonclaims"], list(NONCLAIMS))
        validate_result_integrity(result)

    def test_calibration_status_is_rederived_from_records(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        result["calibration_results"][0]["classification"] = SURVIVED
        result["calibration_results"][0]["killing_tests"] = []
        result["integrity"]["records_sha256"] = mutation_records_sha256(
            result["calibration_results"],
            result["production_results"],
            source_commit_sha=result["integrity"]["source_commit_sha"],
            source_snapshot=result["integrity"]["source_snapshot"],
        )
        with self.assertRaisesRegex(ValueError, "production-record count"):
            validate_result_integrity(result)

    def test_serialized_expected_calibration_is_checked_against_catalog(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        result["calibration_results"][0]["expected_classification"] = SURVIVED
        result["integrity"]["records_sha256"] = mutation_records_sha256(
            result["calibration_results"],
            result["production_results"],
            source_commit_sha=result["integrity"]["source_commit_sha"],
            source_snapshot=result["integrity"]["source_snapshot"],
        )
        with self.assertRaisesRegex(ValueError, "record/catalog mismatch"):
            validate_result_integrity(result)

    def test_canonical_safety_invariants_are_rederived_from_records(self) -> None:
        original = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))

        cases = (
            ("canonical_head_unchanged", {"canonical_head_unchanged": False}),
            ("canonical_status_unchanged", {"canonical_status_unchanged": False}),
            ("cleanup_confirmed", {"cleanup_confirmed": False}),
            (
                "canonical_status_before_sha256",
                {
                    "canonical_status_before_sha256": "0" * 64,
                    "canonical_status_after_sha256": "0" * 64,
                },
            ),
        )
        for rejected_field, changes in cases:
            with self.subTest(field=rejected_field):
                result = json.loads(json.dumps(original))
                result["production_results"][0].update(changes)
                result["integrity"]["records_sha256"] = mutation_records_sha256(
                    result["calibration_results"],
                    result["production_results"],
                    source_commit_sha=result["integrity"]["source_commit_sha"],
                    source_snapshot=result["integrity"]["source_snapshot"],
                )
                with self.assertRaisesRegex(ValueError, rejected_field):
                    validate_result_integrity(result)

    def test_source_commit_is_bound_into_records_hash(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        result["integrity"]["source_commit_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "mutation-record hash mismatch"):
            validate_result_integrity(result)

    def test_rehashed_source_bump_cannot_reuse_old_record_anchors(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        root = repository_root()
        replacement_sha = canonical_head(root)
        result["integrity"]["source_commit_sha"] = replacement_sha
        result["integrity"]["source_snapshot"] = source_path_snapshot(
            root, replacement_sha
        )
        result["integrity"]["records_sha256"] = mutation_records_sha256(
            result["calibration_results"],
            result["production_results"],
            source_commit_sha=replacement_sha,
            source_snapshot=result["integrity"]["source_snapshot"],
        )
        with self.assertRaisesRegex(ValueError, "canonical_anchor_sha"):
            validate_result_integrity(result)

    def test_source_blob_snapshot_is_bound_and_verified(self) -> None:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        first_path = next(iter(result["integrity"]["source_snapshot"]["path_blob_oids"]))
        result["integrity"]["source_snapshot"]["path_blob_oids"][first_path] = "0" * 40
        result["integrity"]["records_sha256"] = mutation_records_sha256(
            result["calibration_results"],
            result["production_results"],
            source_commit_sha=result["integrity"]["source_commit_sha"],
            source_snapshot=result["integrity"]["source_snapshot"],
        )
        validate_result_integrity(result)
        with self.assertRaisesRegex(ValueError, "blob snapshot mismatch"):
            verify_result_source_snapshot(repository_root(), result)


class MutationHarnessIntegrationTests(unittest.TestCase):
    def test_calibration_mutants_use_real_isolated_path_and_classify_correctly(self) -> None:
        root = repository_root()
        head = canonical_head(root)
        records = [
            run_mutant(root, head, mutant, python_executable=sys.executable)
            for mutant in CALIBRATION_MUTANTS
        ]
        self.assertEqual(
            [record["classification"] for record in records],
            [KILLED, SURVIVED],
        )
        self.assertTrue(records[0]["killing_tests"])
        self.assertTrue(
            all(record["import_path_integrity"]["validated"] for record in records)
        )
        self.assertTrue(all(record["cleanup_confirmed"] for record in records))
        self.assertTrue(
            all(record["canonical_status_unchanged"] for record in records)
        )
        self.assertTrue(
            all(
                record["isolated_test_process_command"][0] == "<PYTHON_EXECUTABLE>"
                for record in records
            )
        )
        self.assertTrue(
            all(
                all(
                    "/tmp/tnp-mutation-" not in argument
                    for argument in record["isolated_test_process_command"]
                )
                for record in records
            )
        )

    def test_invalid_mutant_cleans_up_and_preserves_canonical_state(self) -> None:
        root = repository_root()
        head = canonical_head(root)
        status = canonical_status_bytes(root)
        mutant = Mutant(
            "integration_missing_replacement",
            "production",
            "Exercise invalid patch classification.",
            "Discovery/dimensions.py",
            "THIS TEXT DOES NOT EXIST",
            "replacement",
            ("tests.test_dimensions.DimensionTests.test_g_dimension_is_exact",),
            ("Discovery.dimensions",),
        )
        record = run_mutant(root, head, mutant, python_executable=sys.executable)
        self.assertEqual(record["classification"], INVALID)
        self.assertTrue(record["cleanup_confirmed"])
        self.assertTrue(record["canonical_head_unchanged"])
        self.assertTrue(record["canonical_status_unchanged"])
        self.assertEqual(canonical_head(root), head)
        self.assertEqual(canonical_status_bytes(root), status)


if __name__ == "__main__":
    unittest.main()
