from pathlib import Path
import sys
import types
import unittest

from Discovery.mutation_harness import (
    CALIBRATION_MUTANTS,
    INVALID,
    KILLED,
    SURVIVED,
    Mutant,
    apply_mutation,
    canonical_head,
    canonical_status_bytes,
    classify_runner_record,
    _sanitize_diagnostic,
    repository_root,
    run_mutant,
    validate_result_integrity,
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
            "result_schema_version": 1,
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
