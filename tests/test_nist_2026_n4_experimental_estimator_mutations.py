from __future__ import annotations

import builtins
from contextlib import ExitStack
from copy import deepcopy
from fractions import Fraction as F
import io
from itertools import permutations, product
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from Discovery import nist_2026_n4_experimental_estimator as n
from Discovery import nist_2026_n4_experimental_estimator_mutations as m


def determinant_by_permutations(matrix):
    """Independent Leibniz oracle; does not call the production elimination code."""
    total = F(0)
    for p in permutations(range(len(matrix))):
        inversions = sum(p[i] > p[j] for i in range(len(p)) for j in range(i + 1, len(p)))
        term = F((-1) ** inversions)
        for i, j in enumerate(p):
            term *= matrix[i][j]
        total += term
    return total


def independent_oracle(projection):
    values = tuple(F(row["G_decimal_in_1e_minus_11_units"]) for row in projection["measurements"])
    sigmas = tuple(F(row["relative_standard_uncertainty_ppm"]) for row in projection["measurements"])
    absolute = tuple(x * s / 10**6 for x, s in zip(values, sigmas))
    covariance = [[F(projection["correlation_matrix"][i][j]) * absolute[i] * absolute[j]
                   for j in range(4)] for i in range(4)]
    denominator = determinant_by_permutations(covariance)
    z = []
    for column in range(4):
        replaced = [[F(1) if j == column else covariance[i][j] for j in range(4)] for i in range(4)]
        z.append(determinant_by_permutations(replaced) / denominator)
    weights = tuple(v / sum(z) for v in z)
    return values, sigmas, absolute, covariance, weights, F(1) / sum(z)


class N4MutationBehaviorTests(unittest.TestCase):
    def setUp(self):
        # The parent harness verifies Git chronology and all source pins before execution.
        # The sandbox only reads this immutable fixture; it never bypasses a history gate.
        data = (n.ROOT / n.PREREGISTRATION_PATH).read_bytes()
        self.assertEqual(n.digest(data), n.PREREGISTRATION_SHA256)
        self.projection = json.loads(data)["input_projection"]
        self.oracle = independent_oracle(self.projection)

    def state(self, projection=None):
        try:
            return n.estimator_state(self.projection if projection is None else projection)
        except n.NISTN4EstimatorError as error:
            # Only this exact numerical rejection of the valid fixture is a behavioral failure.
            # Other exceptions (including source/history/import failures) remain test errors.
            if str(error) == "estimator weights do not sum to one":
                self.fail("valid input rejected by the unbiased-normalization contract")
            raise

    def test_cell_calibration(self):
        self.assertEqual(n.decimal_cell("12.34", 2), (F(2467, 200), F(2469, 200)))

    def test_equivalent_decimal_calibration(self):
        self.assertEqual(n.decimal_fraction("12.34"), F(617, 50))
        self.assertEqual(n.decimal_fraction("-0.125"), F(-1, 8))

    def test_correlated_weights(self):
        state = self.state()
        self.assertEqual(state["weights"], self.oracle[4])
        self.assertEqual(state["variance"], self.oracle[5])
        # Stationarity, independently: V w is constant in all four coordinates.
        stationarity = [sum(v * w for v, w in zip(row, state["weights"])) for row in self.oracle[3]]
        self.assertEqual(stationarity, [self.oracle[5]] * 4)

    def test_precise_uncertainties(self):
        state = self.state()
        self.assertEqual(state["relative_uncertainties_ppm"], self.oracle[1])
        self.assertEqual(state["weights"], self.oracle[4])

    def test_absolute_scaling(self):
        state = self.state()
        self.assertEqual(state["absolute_uncertainties"], self.oracle[2])
        self.assertEqual(state["covariance"], tuple(map(tuple, self.oracle[3])))
        self.assertEqual(state["weights"], self.oracle[4])

    def test_four_input_aggregate(self):
        state = self.state()
        self.assertEqual(state["estimate"], sum(w * x for w, x in zip(self.oracle[4], self.oracle[0])))
        self.assertEqual(state["order"], tuple(self.projection["order"]))
        for index in range(4):
            changed = deepcopy(self.projection)
            changed["measurements"][index]["G_decimal_in_1e_minus_11_units"] = "6.680001"
            expected = independent_oracle(changed)
            self.assertEqual(self.state(changed)["estimate"], sum(w * x for w, x in zip(expected[4], expected[0])))

    def test_terminal_free_execution(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("the pure estimator attempted a filesystem or subprocess read")
        with ExitStack() as stack:
            for owner, name in ((Path, "read_bytes"), (Path, "read_text"), (builtins, "open"),
                                (io, "open"), (os, "open"), (subprocess, "run")):
                stack.enter_context(patch.object(owner, name, forbidden))
            state = self.state()
        self.assertEqual(state["weights"], self.oracle[4])
        for key in ("equation_64", "dark_uncertainty", "CODATA", "BIPM"):
            changed = deepcopy(self.projection)
            changed[key] = "9.999999"
            with self.assertRaises(n.NISTN4EstimatorError):
                n.estimator_state(changed)

    def test_resolution_box(self):
        state = self.state()
        half = F(1, 2_000_000)
        cells = tuple((x - half, x + half) for x in self.oracle[0])
        self.assertEqual(state["input_cells"], cells)
        images = [sum(w * x for w, x in zip(self.oracle[4], corner)) for corner in product(*cells)]
        self.assertEqual(state["aggregate_enclosure"], (min(images), max(images)))

    def test_signed_extrema(self):
        cells = ((F(0), F(2)), (F(10), F(14)), (F(-2), F(5)), (F(3), F(7)))
        weights = (F(3, 2), F(-1, 2), F(1, 3), F(-1, 3))
        images = [sum(w * x for w, x in zip(weights, corner)) for corner in product(*cells)]
        self.assertEqual(n.linear_enclosure(cells, weights), (min(images), max(images)))

    def test_unbiased_normalization(self):
        state = self.state()
        self.assertEqual(sum(state["weights"]), F(1))
        self.assertEqual(state["weights"], self.oracle[4])


class N4MutationMetaTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((n.ROOT / n.PREREGISTRATION_PATH).read_bytes())
        self.source = (n.ROOT / m.MODULE).read_text()

    def good_execution(self):
        return {
            "runner_status": "completed", "tests_run": 1, "failing_tests": [],
            "error_tests": [], "skipped_tests": [], "successful": True,
            "validated_imports_before": dict(m.IMPORTS), "validated_imports_after": dict(m.IMPORTS),
        }

    def test_requirement_mapping_and_distinct_controls(self):
        m.validate_definitions(self.source, self.protocol)
        self.assertEqual([c["requirement_index"] for c in m.CASES[2:]], list(range(8)))
        duplicated = (*m.CASES[:-1], m.CASES[0])
        with patch.object(m, "CASES", duplicated), self.assertRaises(m.MutationEvidenceError):
            m.validate_definitions(self.source, self.protocol)
        with self.assertRaises(m.MutationEvidenceError):
            m.validate_definitions(self.source + "\n" + m.CASES[0]["old"], self.protocol)

    def test_only_named_assertions_score(self):
        tests = [m.PREFIX + "test_correlated_weights"]
        evidence = self.good_execution()
        self.assertEqual(m.assess_execution(evidence, tests), "SURVIVED")
        evidence["failing_tests"] = tests
        evidence["successful"] = False
        self.assertEqual(m.assess_execution(evidence, tests), "KILLED")
        failures = [
            ("runner_status", "invalid"), ("tests_run", 0), ("tests_run", True),
            ("error_tests", tests), ("skipped_tests", tests), ("successful", True),
            ("failing_tests", ["unrelated.test"]), ("failing_tests", tests * 2),
            ("validated_imports_before", {}), ("validated_imports_after", {}),
            ("test_output", "SyntaxError"), ("test_output", "ImportError"),
            ("test_output", "source_state_violated"), ("test_output", "history_unavailable"),
        ]
        for key, value in failures:
            changed = deepcopy(evidence)
            changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(m.MutationEvidenceError):
                m.assess_execution(changed, tests)
        with self.assertRaises(m.MutationEvidenceError):
            m.assess_execution({}, tests)

    def test_real_syntax_and_import_failures_get_no_credit(self):
        for replacement in ("return Fraction(", "raise ImportError('unavailable dependency')"):
            definition = m.case("invalid_control", "return Fraction(number)", replacement,
                                "test_equivalent_decimal_calibration")
            with self.subTest(replacement=replacement), self.assertRaises(m.MutationEvidenceError):
                m.run_case(n.ROOT, definition)

    def test_new_estimator_read_closure_is_bounded(self):
        root = n.ROOT.resolve()
        seen = set()
        git_reads = set()

        def record(path):
            if not isinstance(path, (str, bytes, os.PathLike)):
                return
            resolved = Path(os.fsdecode(path)).resolve()
            if resolved.is_relative_to(root):
                relative = resolved.relative_to(root).as_posix()
                if not relative.startswith(".git/"):
                    seen.add(relative)

        def tracked(method):
            def wrapper(path, *args, **kwargs):
                record(path)
                return method(path, *args, **kwargs)
            return wrapper

        real_run = subprocess.run

        def tracked_run(args, *more, **kwargs):
            for arg in args:
                if isinstance(arg, str) and ":" in arg:
                    ref, path = arg.split(":", 1)
                    if len(ref) == 40 and all(c in "0123456789abcdef" for c in ref):
                        git_reads.add(path)
            return real_run(args, *more, **kwargs)

        with ExitStack() as stack:
            for owner, name in ((Path, "read_bytes"), (Path, "read_text"), (builtins, "open"),
                                (io, "open"), (os, "open")):
                stack.enter_context(patch.object(owner, name, tracked(getattr(owner, name))))
            stack.enter_context(patch.object(subprocess, "run", tracked_run))
            n.build_artifact()
        self.assertEqual(seen, set(n.SOURCE_PATHS))
        self.assertTrue(git_reads)
        self.assertLessEqual(git_reads, set(n.SOURCE_PATHS))


class N4MutationArtifactTests(unittest.TestCase):
    def test_committed_evidence_is_current_and_derived(self):
        artifact = m.check_artifact()
        self.assertEqual(artifact["production_count"], 8)
        self.assertEqual(artifact["production_killed"], 8)
        self.assertTrue(artifact["calibration_valid"])
        self.assertEqual(artifact["family_status"], "valid")
        protocol = n.verify_preregistration()
        records = deepcopy(artifact["records"])
        records[1]["outcome"] = "SURVIVED"
        changed = m.envelope(artifact["source_snapshot"], records, protocol)
        self.assertFalse(changed["calibration_valid"])
        self.assertEqual(changed["family_status"], "invalid")
        with self.assertRaises(m.MutationEvidenceError):
            m.validate_records(records, (n.ROOT / m.MODULE).read_text())

    def test_top_level_tampering_is_rejected_read_only(self):
        original = (n.ROOT / m.OUTPUT).read_text()
        for key, value in (("production_count", 9), ("production_killed", 0),
                           ("calibration_valid", False), ("scope", "a different claim")):
            edited = json.loads(original)
            edited[key] = value
            real_read = Path.read_text

            def substituted(path, *args, **kwargs):
                if path.resolve() == (n.ROOT / m.OUTPUT).resolve():
                    return n.serialize_artifact(edited)
                return real_read(path, *args, **kwargs)

            with self.subTest(key=key), patch.object(Path, "read_text", substituted), self.assertRaises(m.MutationEvidenceError):
                m.check_artifact()
        self.assertEqual((n.ROOT / m.OUTPUT).read_text(), original)


if __name__ == "__main__":
    unittest.main()
