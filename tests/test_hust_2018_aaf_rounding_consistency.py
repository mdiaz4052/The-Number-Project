"""HUST source isolation, fixed policies, and a separate matrix oracle."""

from copy import deepcopy
from fractions import Fraction as F
import hashlib
import io
import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from Discovery import hust_2018_aaf_rounding_consistency as hust
from Discovery.rounding_consistency import (
    Interval, RoundingError, calculate, classify, decimal_fraction, rounding_bin,
    verify_witness,
)
from tests.test_rounding_consistency import matrix_oracle


class HUSTRoundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, cls.projection, cls.calculation = hust.build_calculation()

    def test_hust_points_match_independent_covariance_oracle(self):
        budget = self.calculation.budget
        for candidate in self.calculation.candidates:
            weights, mean, variance = matrix_oracle(budget.central_values, candidate.values, budget.correlations)
            self.assertEqual(candidate.evaluation.weights, weights)
            self.assertEqual(candidate.evaluation.combined_central_value, mean)
            self.assertEqual(candidate.evaluation.relative_variance_ppm_squared, variance)

    def test_midpoint_display_contains_the_frozen_measurement_reference(self):
        from Discovery.rounding_consistency import sqrt_display_bounds
        frozen = json.loads((hust.ROOT / hust.DIRECTORY / "hust_2018_aaf_combined_measurement_model_v1.json").read_text())
        reference = F(frozen["reconstruction"]["relative_standard_uncertainty_ppm"])
        midpoint = self.calculation.candidates[0].evaluation.relative_variance_ppm_squared
        shown = sqrt_display_bounds(Interval.point(midpoint), self.protocol["calculation"]["output_ppm_decimal_places"])
        self.assertLessEqual(F(shown["low"]), reference)
        self.assertLessEqual(reference, F(shown["high"]))

    def test_verdict_is_supported_without_requiring_hust_agreement(self):
        target = rounding_bin(F("11.61"), F("0.005"))
        outcome, index = classify(self.calculation, target)
        self.assertIn(outcome, ("compatible", "incompatible", "unresolved"))
        if outcome == "compatible":
            self.assertTrue(verify_witness(self.calculation.budget, self.calculation.candidates[index], target))
        elif outcome == "incompatible":
            self.assertTrue(self.calculation.enclosure.high < target.low**2
                            or target.high**2 < self.calculation.enclosure.low)
        else:
            self.assertIsNone(index)

    def test_sixty_three_bins_use_the_preregistered_half_width(self):
        self.assertEqual(sum(len(row) for row in self.calculation.budget.components), 63)
        width = F(self.protocol["rounding_policy"]["component_half_width_ppm"])
        self.assertEqual(2*width, F(self.protocol["rounding_policy"]["component_quantum_ppm"]))
        for projected, domains in zip(self.projection["components"], self.calculation.budget.components):
            for value, domain in zip(projected["values"], domains):
                self.assertEqual(domain.low, F(value)-width)
                self.assertEqual(domain.high, F(value)+width)

    def test_fifteen_candidate_parameters_are_taken_from_frozen_schedule(self):
        expected = (F(0),) + tuple(F(sign*k, 8) for k in range(1, 8) for sign in (-1, 1))
        self.assertEqual(hust.candidate_parameters(self.protocol), expected)
        self.assertEqual(tuple(c.parameter for c in self.calculation.candidates), expected)

    def test_correlation_and_inventory_are_source_bound(self):
        correlations = self.calculation.budget.correlations
        self.assertEqual(correlations.count("shared"), 20)
        self.assertEqual(correlations.count("independent"), 1)
        self.assertEqual(self.projection["components"][-1]["component_id"], "statistical_angular_acceleration")
        self.assertEqual(correlations[-1], "independent")
        for change in ("extra", "duplicate", "correlation", "order", "value"):
            projection = deepcopy(self.projection)
            if change == "extra": projection["published_G"] = "11.61"
            elif change == "duplicate": projection["components"][-1] = projection["components"][0]
            elif change == "correlation": projection["components"][-1]["correlation"] = "shared"
            elif change == "order": projection["components"].reverse()
            else: projection["central_values"][0] = "6.674484e-11"
            with self.subTest(change=change), self.assertRaises(RoundingError):
                hust.budget_from_projection(projection, self.protocol)

    def test_terminal_fields_can_be_removed_from_upstream_projection(self):
        protocol, records = hust.load_frozen_records()
        records[hust.GRAPH_NAME].pop("terminal_comparisons")
        for model in records[hust.MODELS_NAME]["models"]:
            model.pop("external_comparison")
            scope = model["uncertainty_reconstruction"]["scope"]
            model["quantities"] = [q for q in model["quantities"]
                                   if q["identifier"] not in (scope+":published_G", scope+":comparison_delta")]
        self.assertEqual(hust.project_inputs(records, protocol), self.projection)

    def test_target_cannot_change_bins_or_candidate_calculations(self):
        protocol = deepcopy(self.protocol)
        for value in ("11.6101", "11.6099"):
            protocol["comparison"]["value_ppm"] = value
            actual = calculate(hust.budget_from_projection(self.projection, protocol),
                               hust.candidate_parameters(protocol))
            self.assertEqual(actual, self.calculation)
        protocol.pop("comparison")
        self.assertEqual(calculate(hust.budget_from_projection(self.projection, protocol),
                                  hust.candidate_parameters(protocol)), self.calculation)

    def test_combined_and_feasibility_artifacts_are_not_calculator_inputs(self):
        original = Path.read_bytes
        forbidden = {"hust_2018_aaf_combined_feasibility_v1.json", "hust_2018_aaf_combined_measurement_model_v1.json"}
        def without_historical_outputs(path):
            if path.name in forbidden:
                raise FileNotFoundError(path.name)
            return original(path)
        with patch.object(Path, "read_bytes", without_historical_outputs):
            self.assertEqual(hust.build_calculation()[2], self.calculation)

    def test_mutating_source_bytes_fails_closed(self):
        original = Path.read_bytes
        for name in (hust.MODELS_NAME, hust.GRAPH_NAME):
            def corrupted(path):
                data = original(path)
                return data + b" " if path.name == name else data
            with self.subTest(name=name), patch.object(Path, "read_bytes", corrupted):
                with self.assertRaisesRegex(RoundingError, "frozen source bytes"):
                    hust.build_calculation()

    def test_preregistered_policy_cannot_be_amended_in_place(self):
        original = Path.read_bytes
        def altered(path):
            if path == hust.ROOT / hust.PREREGISTRATION_PATH:
                value = json.loads(original(path))
                value["rounding_policy"]["component_half_width_ppm"] = "0.05"
                return hust.serialize_artifact(value).encode()
            return original(path)
        with patch.object(Path, "read_bytes", altered):
            with self.assertRaisesRegex(RoundingError, "preregistration bytes"):
                hust.load_protocol()

    def test_print_precision_unit_role_and_missing_cells_fail(self):
        for defect in ("precision", "unit", "dimension", "role", "missing", "duplicate"):
            protocol, records = hust.load_frozen_records()
            rows = records[hust.GRAPH_NAME]["components"]
            model = records[hust.MODELS_NAME]["models"][0]
            target = next(q for q in model["quantities"] if q["identifier"] == "AAF-I:G_hat")
            if defect == "precision": rows[0]["AAF-I"] = "0.160"
            elif defect == "unit": target["unit"] = "ppm"
            elif defect == "dimension": target["dimension"][0] = "0"
            elif defect == "role": target["role"] = "external_comparison_reference"
            elif defect == "missing": rows.pop()
            else: model["quantities"].append(deepcopy(target))
            with self.subTest(defect=defect), self.assertRaises(RoundingError):
                hust.project_inputs(records, protocol)

    def test_all_three_preregistered_controls_pass(self):
        self.assertEqual([r["outcome"] for r in hust.run_controls(self.protocol)],
                         ["compatible", "incompatible", "unresolved"])

    def test_default_artifact_is_conditional_and_target_changes_only_comparison(self):
        before = hust.build_artifact()
        after = hust.build_artifact(comparison=Interval(F(100), F(101)))
        self.assertEqual(after["decision"]["outcome"], "incompatible")
        for record in (before, after):
            for field in ("comparison", "decision", "interpretation"):
                record.pop(field)
        self.assertEqual(before, after)
        self.assertEqual(before["kind"], "conditional_rounding_consistency_diagnostic")
        self.assertNotIn("measurement_model", before)
        self.assertGreater(len(before["claim_limits"]), 0)

    def test_historical_files_and_specification_remain_frozen(self):
        hust.verify_preserved_files()
        specification = self.protocol["specification"]
        self.assertEqual(hashlib.sha256((hust.ROOT/specification["path"]).read_bytes()).hexdigest(),
                         specification["sha256"])

    def test_real_preregistration_chronology_and_public_anchor(self):
        self.assertEqual(hust.verify_preregistration(), self.protocol)
        self.assertEqual(hust.EXTERNAL_ANCHOR["preregistration_commit_sha"], hust.PREREGISTRATION_COMMIT)
        self.assertEqual(hust.EXTERNAL_ANCHOR["url"], "https://github.com/mdiaz4052/The-Number-Project/pull/39")

    def test_duplicate_json_and_float_scalars_are_rejected(self):
        with self.assertRaises(RoundingError):
            hust._json(b'{"a":1,"a":2}')
        with self.assertRaises(RoundingError):
            decimal_fraction(0.005)

    def test_check_is_read_only_and_rejects_a_stale_artifact(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            data = hust.serialize_artifact(hust.build_artifact()).encode()
            path.write_bytes(data)
            with patch.object(hust, "DEFAULT_OUTPUT", path), patch("sys.stdout", new=io.StringIO()):
                hust.main(["--check"])
                self.assertEqual(path.read_bytes(), data)
                stale = data + b" "
                path.write_bytes(stale)
                with patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit) as raised:
                    hust.main(["--check"])
                self.assertEqual(raised.exception.code, 1)
                self.assertEqual(path.read_bytes(), stale)

    def test_source_snapshot_rejects_uncommitted_source_bytes(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data + b"# uncommitted\n" if path == hust.ROOT / hust.SOURCE_PATHS[0] else data
        with patch.object(Path, "read_bytes", changed), self.assertRaises(hust.SourceStateViolationError):
            hust.source_snapshot(hust.ROOT)


if __name__ == "__main__":
    unittest.main()
