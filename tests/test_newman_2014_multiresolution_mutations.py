"""Meta-tests for Newman multi-resolution mutation evidence."""

from copy import deepcopy
import ast
import unittest
from unittest.mock import patch

from Discovery import newman_2014_multiresolution_mutations as mm


class NewmanMultiResolutionMutationTests(unittest.TestCase):
    def evidence(self, fail=True):
        imports = {
            "Discovery.multiresolution_rounding": mm.PRIMITIVE_PATH,
            "Discovery.newman_2014_multiresolution_rounding_consistency": mm.MODULE_PATH,
        }
        return {
            "runner_status": "completed",
            "tests_run": 1,
            "failing_tests": mm.CASES[0]["tests"] if fail else [],
            "error_tests": [],
            "skipped_tests": [],
            "successful": not fail,
            "validated_imports_before": imports,
            "validated_imports_after": imports,
            "test_output": "AssertionError: multi-resolution invariant changed" if fail else "",
        }

    def test_assertion_failure_and_survival(self):
        self.assertEqual(
            mm.assess_execution(self.evidence(), mm.CASES[0]["tests"]), "KILLED"
        )
        self.assertEqual(
            mm.assess_execution(self.evidence(False), mm.CASES[0]["tests"]), "SURVIVED"
        )

    def test_invalid_infrastructure_never_counts_as_kill(self):
        for field, value in (
            ("runner_status", "invalid"),
            ("tests_run", 0),
            ("error_tests", ["test"]),
            ("skipped_tests", ["test"]),
            ("test_output", "commit multi-resolution result-driving source"),
            ("test_output", "SyntaxError"),
            ("test_output", "ImportError"),
            ("successful", True),
            ("validated_imports_after", {}),
            ("failing_tests", ["unrelated.test"]),
        ):
            record = self.evidence()
            record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(mm.m.j.RoundingError):
                mm.assess_execution(record, mm.CASES[0]["tests"])

    def test_controls_are_distinct_and_equivalent_change_is_executable(self):
        sources = mm.source_map(mm.m.ROOT)
        mm.validate_definitions(sources)
        production_tuples = {mm.mutation_tuple(c) for c in mm.production_cases()}
        self.assertNotIn(mm.mutation_tuple(mm.calibration_cases()[0]), production_tuples)
        self.assertEqual(len(mm.calibration_cases()), 2)
        self.assertEqual(len(mm.production_cases()), 7)
        self.assertTrue(
            all(test.startswith(mm.TEST_PREFIX) for case in mm.CASES for test in case["tests"])
        )
        equivalent = mm.calibration_cases()[1]
        source = sources[equivalent["path"]]
        changed = source.replace(equivalent["old"], equivalent["new"])
        self.assertNotEqual(ast.dump(ast.parse(source)), ast.dump(ast.parse(changed)))
        changed_hashes = {
            mm.m.digest(
                sources[case["path"]].replace(case["old"], case["new"]).encode()
            )
            for case in mm.CASES
        }
        self.assertEqual(len(changed_hashes), len(mm.CASES))

    def test_envelope_derives_counts_and_validity(self):
        records = []
        for definition in (mm.baseline_definition(),) + mm.CASES:
            records.append({
                "id": definition["id"],
                "category": definition["category"],
                "path": definition.get("path"),
                "tests": definition["tests"],
                "expected": definition["expected"],
                "outcome": definition["expected"],
                "applied_source_sha256": "0" * 64,
                "evidence": {},
            })
        artifact = mm.envelope({"source_commit_sha": "x", "files": []}, records)
        self.assertEqual(artifact["production_count"], len(mm.production_cases()))
        self.assertEqual(artifact["family_status"], "valid")
        bad = deepcopy(records)
        for record in bad:
            if record["category"] == "production":
                record["outcome"] = "SURVIVED"
                break
        self.assertEqual(
            mm.envelope({"source_commit_sha": "x", "files": []}, bad)["family_status"],
            "invalid",
        )

    def test_duplicate_calibration_definition_is_rejected(self):
        sources = mm.source_map(mm.m.ROOT)
        duplicate = (
            dict(mm.CASES[2], id=mm.CASES[0]["id"], category="calibration"),
        ) + mm.CASES[1:]
        with patch.object(mm, "CASES", duplicate), self.assertRaises(mm.m.j.RoundingError):
            mm.validate_definitions(sources)


if __name__ == "__main__":
    unittest.main()
