"""Validate Newman Table 11 bounded mutation controls and evidence."""

from copy import deepcopy
import ast
import unittest
from unittest.mock import patch

from Discovery import newman_2014_table11_rounding_consistency_mutations as m


class NewmanMutationTests(unittest.TestCase):
    def evidence(self, fail=True):
        imports = {
            "Discovery.newman_2014_table11_rounding_consistency": m.MODULE_PATH
        }
        return {
            "runner_status": "completed",
            "tests_run": 1,
            "failing_tests": m.CASES[0]["tests"] if fail else [],
            "error_tests": [],
            "skipped_tests": [],
            "successful": not fail,
            "validated_imports_before": imports,
            "validated_imports_after": imports,
            "test_output": "AssertionError: frozen schedule order mismatch" if fail else "",
        }

    def test_assertion_failure_and_survival(self):
        self.assertEqual(
            m.assess_execution(self.evidence(), m.CASES[0]["tests"]), "KILLED")
        self.assertEqual(
            m.assess_execution(self.evidence(False), m.CASES[0]["tests"]), "SURVIVED")

    def test_invalid_infrastructure_never_counts_as_kill(self):
        for field, value in (
            ("runner_status", "invalid"),
            ("tests_run", 0),
            ("error_tests", ["test"]),
            ("skipped_tests", ["test"]),
            ("test_output", "commit result-driving source before emitting an artifact"),
            ("test_output", "SyntaxError"),
            ("test_output", "ImportError"),
            ("successful", True),
            ("validated_imports_after", {}),
            ("failing_tests", ["unrelated.test"]),
        ):
            record = self.evidence()
            record[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(m.j.RoundingError):
                m.assess_execution(record, m.CASES[0]["tests"])

    def test_controls_are_distinct_and_equivalent_change_is_executable(self):
        source = (m.j.ROOT / m.MODULE_PATH).read_text()
        m.validate_definitions(source)
        production_tuples = {m.mutation_tuple(c) for c in m.production_cases()}
        self.assertNotIn(m.mutation_tuple(m.calibration_cases()[0]), production_tuples)
        self.assertEqual(len(m.calibration_cases()), 2)
        self.assertEqual(len(m.production_cases()), 8)
        self.assertTrue(
            all(test.startswith(m.TEST_PREFIX) for case in m.CASES for test in case["tests"]))
        equivalent = m.calibration_cases()[1]
        changed = source.replace(equivalent["old"], equivalent["new"])
        self.assertNotEqual(ast.dump(ast.parse(source)), ast.dump(ast.parse(changed)))
        self.assertEqual(
            len({m.j.digest(source.replace(c["old"], c["new"]).encode()) for c in m.CASES}),
            len(m.CASES),
        )

    def test_envelope_derives_counts_and_validity(self):
        records = []
        for definition in (m.baseline_definition(),) + m.CASES:
            records.append({
                "id": definition["id"],
                "category": definition["category"],
                "tests": definition["tests"],
                "expected": definition["expected"],
                "outcome": definition["expected"],
                "applied_source_sha256": "0" * 64,
                "evidence": {},
            })
        artifact = m.envelope({"source_commit_sha": "x", "files": []}, records)
        self.assertEqual(artifact["production_count"], len(m.production_cases()))
        self.assertEqual(artifact["family_status"], "valid")
        bad = deepcopy(records)
        for record in bad:
            if record["category"] == "production":
                record["outcome"] = "SURVIVED"
                break
        self.assertEqual(
            m.envelope({"source_commit_sha": "x", "files": []}, bad)["family_status"],
            "invalid",
        )

    def test_duplicate_calibration_definition_is_rejected(self):
        source = (m.j.ROOT / m.MODULE_PATH).read_text()
        duplicate = (
            dict(m.CASES[2], id=m.CASES[0]["id"], category="calibration"),
        ) + m.CASES[1:]
        with patch.object(m, "CASES", duplicate), self.assertRaises(m.j.RoundingError):
            m.validate_definitions(source)


if __name__ == "__main__":
    unittest.main()
