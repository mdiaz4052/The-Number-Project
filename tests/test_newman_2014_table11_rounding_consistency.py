"""Behavior and artifact tests for Newman et al. 2014 Table 11 rounding consistency."""

from copy import deepcopy
from fractions import Fraction
import unittest

from Discovery import newman_2014_table11_rounding_consistency as j
from Discovery.rounding_consistency import Calculation, RoundingError


class NewmanBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, cls.attestation = j.load_source()
        cls.projection = cls.attestation["input_projection"]
        cls.policy = cls.protocol["rounding_policy"]
        cls.schedule = cls.protocol["candidate_schedule"]
        cls.calculations = j.calculate_scopes(cls.projection, cls.policy, cls.schedule)

    def test_schedule_order_freeze(self):
        parameters = j.candidate_parameters(self.schedule)
        self.assertEqual(
            parameters,
            (Fraction(0), Fraction(-1, 8), Fraction(1, 8), Fraction(-2, 8), Fraction(2, 8),
             Fraction(-3, 8), Fraction(3, 8), Fraction(-4, 8), Fraction(4, 8),
             Fraction(-5, 8), Fraction(5, 8), Fraction(-6, 8), Fraction(6, 8),
             Fraction(-7, 8), Fraction(7, 8)),
        )

    def test_tensor_schedule_and_independent_coordinates(self):
        parameters = j.candidate_parameters(self.schedule)
        self.assertEqual(len(parameters), 15)
        self.assertEqual(parameters[0], 0)
        for scope in j.SCOPES:
            calculation = self.calculations[scope]
            self.assertEqual(len(calculation.candidates), 3375)
            self.assertEqual(j.candidate_coordinates(calculation.candidates[0]), (0, 0, 0))
            coordinates = [j.candidate_coordinates(c) for c in calculation.candidates]
            self.assertEqual(len(set(coordinates)), 3375)
            self.assertIn((0, 0, Fraction(-1, 8)), coordinates)
            self.assertIn((Fraction(1, 8), Fraction(-2, 8), Fraction(3, 8)), coordinates)

    def test_all_three_published_scopes_are_required(self):
        self.assertEqual(set(self.calculations), set(j.SCOPES))
        projection = deepcopy(self.projection)
        projection["scope_order"] = projection["scope_order"][:2]
        projection["components"].pop("fibre_3")
        projection["central_values"].pop("fibre_3")
        with self.assertRaises(RoundingError):
            j.calculate_scopes(projection, self.policy, self.schedule)
        incomplete = dict(self.calculations)
        incomplete.pop("fibre_3")
        with self.assertRaises(RoundingError):
            j.terminal_decisions(
                incomplete, self.attestation["terminal_comparisons"], self.policy)

    def test_real_table11_midpoints_are_representable(self):
        decisions = j.terminal_decisions(
            self.calculations, self.attestation["terminal_comparisons"], self.policy)
        self.assertEqual(set(decisions), set(j.SCOPES))
        for scope in j.SCOPES:
            decision = decisions[scope]
            self.assertEqual(decision["outcome"], "compatible")
            self.assertEqual(
                decision["status"],
                "representable_under_the_declared_table11_rounding_model")
            self.assertEqual(decision["witness"]["candidate_index"], 0)
            self.assertEqual(
                decision["witness"]["tensor_parameters"],
                [j.rational_record(Fraction(0))] * 3)
            self.assertTrue(decision["witness"]["membership_verified"])

    def test_terminal_resolution_cannot_drive_candidate_generation(self):
        altered = dict(self.policy)
        altered["component_half_width_ppm"] = "0.05"
        altered["terminal_half_width_ppm"] = "0.50"
        calculations = j.calculate_scopes(self.projection, altered, self.schedule)
        domain = calculations["fibre_1"].budget.components[0][0]
        self.assertEqual(domain.low, Fraction(765, 100))
        self.assertEqual(domain.high, Fraction(775, 100))
        self.assertEqual(len(calculations["fibre_1"].candidates), 3375)

    def test_component_rounding_bin_is_exact(self):
        domain = self.calculations["fibre_1"].budget.components[0][0]
        self.assertEqual(domain.low, Fraction(765, 100))
        self.assertEqual(domain.high, Fraction(775, 100))
        midpoint = self.calculations["fibre_1"].candidates[0].values[0][0]
        self.assertEqual(midpoint, Fraction(77, 10))

    def test_synthetic_incompatible_and_unresolved_statuses(self):
        far = {
            scope: {
                "scope": scope, "role": "terminal_only",
                "value_ppm": "30.0", "half_width_ppm": "0.05",
            } for scope in j.SCOPES
        }
        incompatible = j.terminal_decisions(self.calculations, far, self.policy)
        for decision in incompatible.values():
            self.assertEqual(decision["outcome"], "incompatible")
            self.assertEqual(
                decision["status"],
                "not_representable_under_the_declared_table11_rounding_model")
            self.assertTrue(decision["exclusion"]["strict_disjointness"])

        empty = {
            scope: Calculation(calc.budget, calc.enclosure, tuple())
            for scope, calc in self.calculations.items()
        }
        unresolved = j.terminal_decisions(
            empty, self.attestation["terminal_comparisons"], self.policy)
        for decision in unresolved.values():
            self.assertEqual(decision["outcome"], "unresolved")
            self.assertEqual(
                decision["status"], "undetermined_under_the_frozen_tensor_schedule")
            self.assertIsNone(decision["witness"])

    def test_central_value_cannot_affect_variance_or_truth(self):
        changed = deepcopy(self.projection)
        changed["central_values"]["fibre_1"]["value"] = "6.67435e-5"
        changed["central_values"]["fibre_2"]["value"] = "6.67408e-15"
        changed["central_values"]["fibre_3"]["value"] = "9.99999e5"
        recalculated = j.calculate_scopes(changed, self.policy, self.schedule)
        original = j.terminal_decisions(
            self.calculations, self.attestation["terminal_comparisons"], self.policy)
        perturbed = j.terminal_decisions(
            recalculated, self.attestation["terminal_comparisons"], self.policy)
        for scope in j.SCOPES:
            self.assertEqual(
                self.calculations[scope].candidates[0].evaluation.relative_variance_ppm_squared,
                recalculated[scope].candidates[0].evaluation.relative_variance_ppm_squared)
            self.assertEqual(original[scope]["outcome"], perturbed[scope]["outcome"])
            self.assertEqual(original[scope]["status"], perturbed[scope]["status"])

    def test_model_relative_negative_label(self):
        self.assertEqual(
            j.STATUS_LABELS["incompatible"],
            "not_representable_under_the_declared_table11_rounding_model")
        self.assertIn("declared_table11_rounding_model", j.STATUS_LABELS["incompatible"])

    def test_projection_schema_and_one_decimal_cells(self):
        malformed = deepcopy(self.projection)
        malformed["components"]["fibre_1"][0]["value_ppm"] = "7.70"
        with self.assertRaises(RoundingError):
            j.validate_projection(malformed)
        extra = deepcopy(self.projection)
        extra["foreign"] = "not allowed"
        with self.assertRaises(RoundingError):
            j.validate_projection(extra)


class NewmanArtifactTests(unittest.TestCase):
    def test_frozen_source_projection(self):
        protocol, attestation = j.load_source()
        self.assertEqual(attestation, protocol["source_attestation"]["projection"])
        self.assertEqual(attestation["record_id"], "newman_2014_source_attestation_v1")
        self.assertEqual(
            set(attestation["terminal_comparisons"]), set(j.SCOPES))

    def test_e001_inventory_isolation(self):
        protocol = j.load_protocol()
        reachable = set(j.SOURCE_PATHS) | set(protocol["preserved_baseline_paths"])
        self.assertFalse(set(j.E001_FORBIDDEN) & reachable)

    def test_committed_artifact_matches_rebuild(self):
        artifact = j.read_json((j.ROOT / j.DEFAULT_OUTPUT).read_bytes())
        self.assertEqual(artifact, j.build_artifact())
        self.assertEqual(
            [artifact["terminal_decisions"][scope]["outcome"] for scope in j.SCOPES],
            ["compatible", "compatible", "compatible"])


if __name__ == "__main__":
    unittest.main()
