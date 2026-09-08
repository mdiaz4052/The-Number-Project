"""Behavior and artifact tests for Newman 2014 multi-resolution constraints."""

from copy import deepcopy
from fractions import Fraction
import inspect
import unittest

from Discovery import multiresolution_rounding as mr
from Discovery import newman_2014_multiresolution_rounding_consistency as m
from Discovery.rounding_consistency import (
    Budget, Calculation, Candidate, Interval, RoundingError,
    enclose_relative_variance, evaluate_point,
)


class NewmanMultiResolutionBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = m.load_protocol()
        cls.parent_source = m.load_component_source(cls.protocol)
        cls.calculations = m.calculate_components(
            cls.parent_source["input_projection"],
            cls.protocol["component_model"]["component_half_width_ppm"],
            cls.protocol["candidate_schedule"],
        )
        cls.attestation = m.load_terminal_attestation(
            cls.protocol, cls.parent_source
        )

    def test_schedule_order_and_inventory(self):
        parameters = m.candidate_parameters(self.protocol["candidate_schedule"])
        self.assertEqual(
            parameters,
            (
                Fraction(0), Fraction(-1, 8), Fraction(1, 8),
                Fraction(-2, 8), Fraction(2, 8), Fraction(-3, 8),
                Fraction(3, 8), Fraction(-4, 8), Fraction(4, 8),
                Fraction(-5, 8), Fraction(5, 8), Fraction(-6, 8),
                Fraction(6, 8), Fraction(-7, 8), Fraction(7, 8),
            ),
        )
        self.assertEqual(set(self.calculations), set(m.j.SCOPES))
        for calculation in self.calculations.values():
            self.assertEqual(len(calculation.candidates), 3375)

    def test_candidate_api_excludes_terminal_inputs(self):
        self.assertEqual(
            tuple(inspect.signature(m.calculate_components).parameters),
            ("input_projection", "component_half_width_ppm", "schedule"),
        )
        self.assertNotIn(
            "terminal",
            " ".join(inspect.signature(m.calculate_components).parameters),
        )
        altered = deepcopy(self.attestation)
        for scope in m.j.SCOPES:
            altered["terminal_representations"][scope][1]["half_width_ppm"] = "999.5"
        recalculated = m.calculate_components(
            self.parent_source["input_projection"],
            self.protocol["component_model"]["component_half_width_ppm"],
            self.protocol["candidate_schedule"],
        )
        for scope in m.j.SCOPES:
            self.assertEqual(
                self.calculations[scope].candidates[0].evaluation,
                recalculated[scope].candidates[0].evaluation,
            )

    def test_component_half_width_parameter_controls_domain(self):
        exact = self.calculations["fibre_1"].budget.components[0][0]
        self.assertEqual((exact.low, exact.high), (Fraction(153, 20), Fraction(31, 4)))
        widened = m.calculate_components(
            self.parent_source["input_projection"],
            "0.5",
            self.protocol["candidate_schedule"],
        )["fibre_1"].budget.components[0][0]
        self.assertEqual((widened.low, widened.high), (Fraction(36, 5), Fraction(41, 5)))
        self.assertNotEqual(exact, widened)

    def test_terminal_schema_and_parent_crosscheck(self):
        m.validate_terminal_attestation(self.attestation, self.parent_source)
        self.assertEqual(self.attestation["scope_order"], list(m.j.SCOPES))
        for scope in m.j.SCOPES:
            self.assertEqual(
                [item["id"] for item in self.attestation["terminal_representations"][scope]],
                ["table11_one_decimal", "conclusion_integer"],
            )

    def test_exact_joint_intervals_and_resolution_widths(self):
        expected = {
            "fibre_1": (Fraction(289, 20), Fraction(29, 2), Fraction(1, 2), True),
            "fibre_2": (Fraction(443, 20), Fraction(89, 4), Fraction(1), False),
            "fibre_3": (Fraction(391, 20), Fraction(393, 20), Fraction(1), False),
        }
        for scope, (low, high, ratio, narrowed) in expected.items():
            constraints = m.constraint_intervals(self.attestation, scope)
            joint = mr.intersect_closed(constraints)
            self.assertEqual((joint.low, joint.high), (low, high))
            record = m.resolution_record(self.attestation, scope, constraints, joint)
            self.assertEqual(
                record["joint_to_table11_width_ratio"], m.j.rational_record(ratio)
            )
            self.assertEqual(
                record["narrowed_by_multiresolution_constraint"], narrowed
            )

    def test_real_expected_verdicts_are_compatible_midpoints(self):
        decisions = m.terminal_decisions(self.calculations, self.attestation)
        for scope in m.j.SCOPES:
            decision = decisions[scope]
            self.assertEqual(decision["outcome"], "compatible")
            self.assertEqual(
                decision["status"],
                "representable_under_the_declared_multiresolution_reporting_model",
            )
            self.assertEqual(decision["reason"], "scheduled_strict_interior_witness")
            self.assertEqual(decision["witness"]["candidate_index"], 0)
            self.assertEqual(decision["witness"]["witness_kind"], "unshifted_midpoint")
            self.assertTrue(decision["witness"]["membership_verified"])

    def test_disjoint_terminal_constraints_are_incompatible(self):
        calculation = self.calculations["fibre_1"]
        constraints = (
            mr.printed_constraint(Fraction(145, 10), Fraction(5, 100)),
            mr.printed_constraint(Fraction(13), Fraction(1, 2)),
        )
        outcome, index, reason, joint = mr.classify_multiresolution(
            calculation, constraints
        )
        self.assertEqual((outcome, index, reason, joint), (
            "incompatible", None, "terminal_constraints_disjoint", None
        ))

    def test_degenerate_joint_interval_is_unresolved(self):
        calculation = self.calculations["fibre_1"]
        point = Interval.point(Fraction(29, 2))
        broad = Interval(Fraction(14), Fraction(15))
        outcome, index, reason, joint = mr.classify_multiresolution(
            calculation, (point, broad)
        )
        self.assertEqual(outcome, "unresolved")
        self.assertIsNone(index)
        self.assertEqual(reason, "degenerate_joint_terminal")
        self.assertEqual(joint, point)

    def test_component_box_disjoint_from_joint_terminal(self):
        calculation = self.calculations["fibre_1"]
        constraints = (
            mr.printed_constraint(Fraction(30), Fraction(5, 100)),
            mr.printed_constraint(Fraction(30), Fraction(1, 2)),
        )
        outcome, index, reason, joint = mr.classify_multiresolution(
            calculation, constraints
        )
        self.assertEqual(outcome, "incompatible")
        self.assertIsNone(index)
        self.assertEqual(reason, "component_box_disjoint_from_joint_terminal")
        self.assertIsNotNone(joint)

    def test_strict_boundary_is_not_a_compatible_witness(self):
        budget = Budget(
            (Fraction(1),),
            ((Interval(Fraction(1), Fraction(3)),),),
            ("independent",),
        )
        values = ((Fraction(2),),)
        candidate = Candidate(Fraction(0), values, evaluate_point(budget, values))
        calculation = Calculation(
            budget, enclose_relative_variance(budget), (candidate,)
        )
        self.assertEqual(candidate.evaluation.relative_variance_ppm_squared, 4)
        self.assertFalse(
            mr.strict_witness(
                calculation, candidate, Interval(Fraction(2), Fraction(3))
            )
        )

    def test_central_value_cannot_affect_truth(self):
        changed = deepcopy(self.parent_source["input_projection"])
        changed["central_values"]["fibre_1"]["value"] = "1e-50"
        changed["central_values"]["fibre_2"]["value"] = "1e20"
        changed["central_values"]["fibre_3"]["value"] = "9.9e7"
        recalculated = m.calculate_components(
            changed,
            self.protocol["component_model"]["component_half_width_ppm"],
            self.protocol["candidate_schedule"],
        )
        original = m.terminal_decisions(self.calculations, self.attestation)
        perturbed = m.terminal_decisions(recalculated, self.attestation)
        for scope in m.j.SCOPES:
            self.assertEqual(
                self.calculations[scope].candidates[0].evaluation.relative_variance_ppm_squared,
                recalculated[scope].candidates[0].evaluation.relative_variance_ppm_squared,
            )
            self.assertEqual(original[scope]["outcome"], perturbed[scope]["outcome"])

    def test_model_relative_labels_and_known_prior_status(self):
        self.assertIn("declared_multiresolution_reporting_model", m.STATUS_LABELS["incompatible"])
        self.assertFalse(self.protocol["known_prior_information"]["outcome_blind"])
        self.assertFalse(m.EXTERNAL_ANCHOR["outcome_blind"])


class NewmanMultiResolutionArtifactTests(unittest.TestCase):
    def test_frozen_terminal_projection(self):
        protocol = m.load_protocol()
        parent = m.load_component_source(protocol)
        attestation = m.load_terminal_attestation(protocol, parent)
        self.assertEqual(attestation, protocol["terminal_attestation"]["projection"])

    def test_e001_inventory_isolation(self):
        protocol = m.load_protocol()
        reachable = set(m.SOURCE_PATHS) | set(protocol["preserved_baseline_paths"])
        self.assertFalse(set(m.j.E001_FORBIDDEN) & reachable)

    def test_committed_artifact_matches_rebuild(self):
        artifact = m.read_json((m.ROOT / m.DEFAULT_OUTPUT).read_bytes())
        rebuilt = m.build_artifact()
        self.assertEqual(artifact, rebuilt)
        self.assertEqual(
            [artifact["terminal_decisions"][scope]["outcome"] for scope in m.j.SCOPES],
            ["compatible", "compatible", "compatible"],
        )
        self.assertTrue(
            artifact["terminal_decisions"]["fibre_1"]["resolution"][
                "narrowed_by_multiresolution_constraint"
            ]
        )


if __name__ == "__main__":
    unittest.main()
