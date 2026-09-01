"""Parameterized adversarial corpus for the physical-bridge target gate.

Each case names the attempted construction, its mutation of the valid structural
example, the expected gate or status, and why the case belongs at the validation
boundary.  The corpus complements the focused unit tests in
``test_physical_bridge.py``; it does not replace them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Callable
import unittest

from Discovery.physical_bridge import (
    EXTERNAL_COMPARISON_REFERENCE,
    INCOMPLETE,
    NOT_APPLICABLE,
    NO_REGISTERED_TARGET_PATH,
    REGISTERED_EXPRESSION,
    TARGET_OUTPUT,
    TARGET_PATH_DETECTED,
    UNRESOLVED,
    UNRESOLVED_ALGEBRAIC_PROVENANCE,
    UNRESOLVED_PROVENANCE_EVIDENCE,
    BridgeEvaluation,
    BridgeValidationError,
    EstimatorTerm,
    MeasurementModel,
    ProvenanceEdge,
    audit_registered_target_path,
    build_inverse_square_model,
    build_model_dependency_catalog,
    evaluate_measurement_model,
    measurement_model_record,
    validate_measurement_model,
)


Mutation = Callable[[MeasurementModel], MeasurementModel]
PostAssertion = Callable[
    [unittest.TestCase, MeasurementModel, BridgeEvaluation],
    None,
]


@dataclass(frozen=True, slots=True)
class LeakageCase:
    identifier: str
    category: str
    attack: str
    mutate: Mutation
    expected_outcome: str
    expected_gate: str
    reason: str
    exception_fragment: str | None = None
    expected_statuses: tuple[tuple[str, str], ...] = ()
    target_quantity_id: str | None = None
    expected_target_status: str | None = None
    expected_target_power: Fraction | None = None
    post_assertion: PostAssertion | None = None


def _identity(model: MeasurementModel) -> MeasurementModel:
    return model


def _replace_quantity(
    model: MeasurementModel,
    identifier: str,
    **changes: object,
) -> MeasurementModel:
    quantities = tuple(
        replace(quantity, **changes)
        if quantity.identifier == identifier
        else quantity
        for quantity in model.quantities
    )
    return replace(model, quantities=quantities)


def _registered_expression(
    identifier: str,
    signature: tuple[tuple[str, Fraction], ...],
) -> Mutation:
    def mutate(model: MeasurementModel) -> MeasurementModel:
        return _replace_quantity(
            model,
            identifier,
            algebraic_provenance_kind=REGISTERED_EXPRESSION,
            registered_dependency_signature=signature,
        )

    return mutate


def _estimator_role(identifier: str, role: str) -> Mutation:
    def mutate(model: MeasurementModel) -> MeasurementModel:
        return _replace_quantity(model, identifier, role=role)

    return mutate


def _append_metrological_edges(*edges: ProvenanceEdge) -> Mutation:
    def mutate(model: MeasurementModel) -> MeasurementModel:
        return replace(
            model,
            metrological_edges=(*model.metrological_edges, *edges),
        )

    return mutate


def _append_definition_edge(edge: ProvenanceEdge) -> Mutation:
    def mutate(model: MeasurementModel) -> MeasurementModel:
        return replace(
            model,
            definition_edges=(*model.definition_edges, edge),
        )

    return mutate


def _unresolved_algebraic(identifier: str, *, unresolved_evidence: bool) -> Mutation:
    def mutate(model: MeasurementModel) -> MeasurementModel:
        changes: dict[str, object] = {
            "algebraic_provenance_kind": UNRESOLVED_ALGEBRAIC_PROVENANCE,
            "registered_dependency_signature": None,
        }
        if unresolved_evidence:
            changes["provenance_evidence"] = UNRESOLVED_PROVENANCE_EVIDENCE
        return _replace_quantity(model, identifier, **changes)

    return mutate


def _remove_metrological_parents(identifier: str) -> Mutation:
    def mutate(model: MeasurementModel) -> MeasurementModel:
        return replace(
            model,
            metrological_edges=tuple(
                edge
                for edge in model.metrological_edges
                if edge.child != identifier
            ),
        )

    return mutate


def _append_shadowed_registered_key(model: MeasurementModel) -> MeasurementModel:
    template = next(
        quantity
        for quantity in model.quantities
        if quantity.identifier == "mass_reference"
    )
    shadow = replace(
        template,
        identifier="m_P",
        symbol="m_P",
        registered_dependency_signature=None,
        description=(
            "Invalid local atom that collides with the registered Planck-mass key."
        ),
    )
    return replace(model, quantities=(*model.quantities, shadow))


def _duplicate_estimator_input(model: MeasurementModel) -> MeasurementModel:
    return replace(
        model,
        estimator_terms=(*model.estimator_terms, model.estimator_terms[0]),
    )


def _multistep_registered_leak(model: MeasurementModel) -> MeasurementModel:
    model = _replace_quantity(
        model,
        "angle_observation",
        algebraic_provenance_kind=REGISTERED_EXPRESSION,
        registered_dependency_signature=(
            ("m_P", Fraction(2)),
            ("m_e", Fraction(-2)),
        ),
    )
    return replace(
        model,
        metrological_edges=tuple(
            edge
            for edge in model.metrological_edges
            if not (
                edge.child == "force_estimate"
                and edge.parent == "angle_observation"
            )
        ),
    )


def _assert_terminal_reference(
    test: unittest.TestCase,
    model: MeasurementModel,
    evaluation: BridgeEvaluation,
) -> None:
    record = measurement_model_record(model)
    test.assertEqual(
        record["external_comparison"]["reference_ids"],
        ["codata_2022_G"],
    )
    reference_audit = record["target_path_audit"][
        "isolated_comparison_reference_assessments"
    ][0]
    test.assertEqual(reference_audit["identifier"], "codata_2022_G")
    test.assertEqual(reference_audit["status"], TARGET_PATH_DETECTED)
    test.assertEqual(evaluation.registered_target_path_status, NO_REGISTERED_TARGET_PATH)


def _assert_unresolved_is_not_independent(
    test: unittest.TestCase,
    model: MeasurementModel,
    evaluation: BridgeEvaluation,
) -> None:
    del model
    test.assertEqual(evaluation.registered_target_path_status, UNRESOLVED)
    test.assertNotIn("independent", evaluation.registered_target_path_status)


LEAKAGE_CASES = (
    LeakageCase(
        "direct_g_positive_power",
        "direct_algebraic_leakage",
        "Use G^1 as the registered expression for an immediate estimator input.",
        _registered_expression("mass_1", (("G", Fraction(1)),)),
        "rejection",
        "registered_target_path_gate",
        "The target cannot be one of the algebraic ingredients used to estimate itself.",
        "estimator ancestry reaches G",
        target_quantity_id="mass_1",
        expected_target_status=TARGET_PATH_DETECTED,
        expected_target_power=Fraction(1),
    ),
    LeakageCase(
        "direct_g_negative_power",
        "direct_algebraic_leakage",
        "Use G^-1 as the registered expression for an immediate estimator input.",
        _registered_expression("mass_1", (("G", Fraction(-1)),)),
        "rejection",
        "registered_target_path_gate",
        "Inversion does not remove circular dependence on the target.",
        "estimator ancestry reaches G",
        target_quantity_id="mass_1",
        expected_target_status=TARGET_PATH_DETECTED,
        expected_target_power=Fraction(-1),
    ),
    LeakageCase(
        "direct_g_rational_power",
        "direct_algebraic_leakage",
        "Use G^(1/2) as the registered expression for an estimator input.",
        _registered_expression("mass_1", (("G", Fraction(1, 2)),)),
        "rejection",
        "registered_target_path_gate",
        "Exact rational expansion must catch fractional-power target leakage.",
        "estimator ancestry reaches G",
        target_quantity_id="mass_1",
        expected_target_status=TARGET_PATH_DETECTED,
        expected_target_power=Fraction(1, 2),
    ),
    *(
        LeakageCase(
            f"registered_planck_quantity_{key}",
            "direct_algebraic_leakage",
            f"Use registered Planck quantity {key} directly as an estimator input.",
            _registered_expression("mass_1", ((key, Fraction(1)),)),
            "rejection",
            "registered_target_path_gate",
            "Every registered Planck quantity inherits G through its definition.",
            "estimator ancestry reaches G",
            target_quantity_id="mass_1",
            expected_target_status=TARGET_PATH_DETECTED,
            expected_target_power=power,
        )
        for key, power in (
            ("l_P", Fraction(1, 2)),
            ("m_P", Fraction(-1, 2)),
            ("t_P", Fraction(1, 2)),
            ("T_P", Fraction(-1, 2)),
        )
    ),
    LeakageCase(
        "target_dependent_registered_expression_as_term",
        "direct_algebraic_leakage",
        "Use m_P^2/m_e as a dimensionally valid mass input to the estimator.",
        _registered_expression(
            "mass_1",
            (("m_P", Fraction(2)), ("m_e", Fraction(-1))),
        ),
        "rejection",
        "registered_target_path_gate",
        "A compound expression remains target-dependent even when G is not textual.",
        "estimator ancestry reaches G",
        target_quantity_id="mass_1",
        expected_target_status=TARGET_PATH_DETECTED,
        expected_target_power=Fraction(-1),
    ),
    LeakageCase(
        "external_reference_role_as_estimator_term",
        "direct_algebraic_leakage",
        "Relabel an immediate estimator input as an external comparison reference.",
        _estimator_role("mass_1", EXTERNAL_COMPARISON_REFERENCE),
        "rejection",
        "estimator_role_gate",
        "Reference values belong only after estimation, never in the estimator.",
        "forbidden estimator input role",
    ),
    LeakageCase(
        "target_output_role_as_estimator_term",
        "direct_algebraic_leakage",
        "Relabel an immediate estimator input as a target output.",
        _estimator_role("mass_1", TARGET_OUTPUT),
        "rejection",
        "estimator_role_gate",
        "An output cannot be recycled as one of its own estimator terms.",
        "forbidden estimator input role",
    ),
    LeakageCase(
        "target_expression_in_immediate_ancestor",
        "inherited_leakage",
        "Hide m_P^2/m_e in the observation upstream of mass_1.",
        _registered_expression(
            "mass_1_observation",
            (("m_P", Fraction(2)), ("m_e", Fraction(-1))),
        ),
        "rejection",
        "registered_target_path_gate",
        "The gate must audit estimator ancestry, not only immediate terms.",
        "estimator ancestry reaches G",
        target_quantity_id="mass_1_observation",
        expected_target_status=TARGET_PATH_DETECTED,
        expected_target_power=Fraction(-1),
    ),
    LeakageCase(
        "reference_g_through_intermediate_node",
        "inherited_leakage",
        "Route CODATA G through angle_observation and mass_reference toward mass_1.",
        _append_metrological_edges(
            ProvenanceEdge(
                "angle_observation",
                "codata_2022_G",
                "model_input",
                "Forbidden reference input hidden behind an intermediate node.",
            ),
            ProvenanceEdge(
                "mass_reference",
                "angle_observation",
                "model_input",
                "Intermediate laundering path toward an estimator ancestor.",
            ),
        ),
        "rejection",
        "calibration_reference_gate",
        "Multi-hop metrological indirection cannot launder a reference target.",
        "reference G is used in calibration or correction",
    ),
    LeakageCase(
        "reference_g_feeds_calibration",
        "inherited_leakage",
        "Feed CODATA G into the declared length calibration source.",
        _append_metrological_edges(
            ProvenanceEdge(
                "length_reference",
                "codata_2022_G",
                "calibration",
                "Forbidden target reference in a calibration chain.",
            ),
        ),
        "rejection",
        "calibration_reference_gate",
        "A target reference in calibration makes the eventual estimate circular.",
        "reference G is used in calibration or correction",
    ),
    LeakageCase(
        "reference_g_feeds_correction",
        "inherited_leakage",
        "Feed CODATA G into the alignment correction.",
        _append_metrological_edges(
            ProvenanceEdge(
                "alignment_correction",
                "codata_2022_G",
                "correction",
                "Forbidden target reference in a correction chain.",
            ),
        ),
        "rejection",
        "calibration_reference_gate",
        "A correction cannot be tuned using the value it helps estimate.",
        "reference G is used in calibration or correction",
    ),
    LeakageCase(
        "comparison_result_flows_back_to_estimator",
        "inherited_leakage",
        "Feed the terminal comparison result back into the mass calibration chain.",
        _append_metrological_edges(
            ProvenanceEdge(
                "mass_reference",
                "post_estimation_comparison",
                "model_input",
                "Forbidden feedback from comparison into estimator ancestry.",
            ),
        ),
        "rejection",
        "combined_cycle_gate",
        "Post-estimation comparison must remain terminal rather than become feedback.",
        "cyclic combined provenance",
    ),
    LeakageCase(
        "mixed_definitional_metrological_path_to_target",
        "inherited_leakage",
        "Make force_reference depend metrologically on G_hat across graph layers.",
        _append_metrological_edges(
            ProvenanceEdge(
                "force_reference",
                "G_hat",
                "model_input",
                "Forbidden mixed-layer path back to the target output.",
            ),
        ),
        "rejection",
        "combined_cycle_gate",
        "Separate acyclic graphs can still form a circular combined dependency.",
        "cyclic combined provenance",
    ),
    LeakageCase(
        "multistep_inherited_registered_expression",
        "inherited_leakage",
        "Hide m_P^2/m_e^2 two hops above force_estimate through a correction.",
        _multistep_registered_leak,
        "rejection",
        "registered_target_path_gate",
        "The target path must be inherited across a nontrivial ancestor chain.",
        "estimator ancestry reaches G",
        target_quantity_id="angle_observation",
        expected_target_status=TARGET_PATH_DETECTED,
        expected_target_power=Fraction(-1),
    ),
    LeakageCase(
        "missing_registered_provenance",
        "fail_closed_provenance",
        "Remove the registered algebraic provenance from mass_1.",
        _unresolved_algebraic("mass_1", unresolved_evidence=False),
        "status",
        "registered_target_path_status",
        "Missing algebraic records must remain unresolved rather than clean.",
        expected_statuses=(("registered_target_path_status", UNRESOLVED),),
    ),
    LeakageCase(
        "unresolved_algebraic_ancestor",
        "fail_closed_provenance",
        "Make the mass reference algebraically unresolved upstream of mass_1.",
        _unresolved_algebraic("mass_reference", unresolved_evidence=False),
        "status",
        "registered_target_path_status",
        "Unresolved ancestry propagates to the estimator assessment.",
        expected_statuses=(("registered_target_path_status", UNRESOLVED),),
    ),
    LeakageCase(
        "undocumented_metrological_ancestor",
        "fail_closed_provenance",
        "Mark the angle observation's metrological evidence unresolved.",
        lambda model: _replace_quantity(
            model,
            "angle_observation",
            provenance_evidence=UNRESOLVED_PROVENANCE_EVIDENCE,
        ),
        "status",
        "metrological_provenance_status",
        "Algebraic cleanliness cannot substitute for missing physical provenance.",
        expected_statuses=(("metrological_provenance_status", UNRESOLVED),),
    ),
    LeakageCase(
        "local_atom_shadows_registered_key",
        "fail_closed_provenance",
        "Declare a local atom named m_P alongside the registered Planck-mass key.",
        _append_shadowed_registered_key,
        "rejection",
        "registered_catalog_identity_gate",
        "A local declaration must not override or obscure a registered dependency key.",
        "local atom shadows registered key: m_P",
    ),
    LeakageCase(
        "duplicate_estimator_input",
        "fail_closed_provenance",
        "Repeat force_estimate in the exact estimator-term sequence.",
        _duplicate_estimator_input,
        "rejection",
        "estimator_identity_gate",
        "Each estimator input identifier must occur exactly once.",
        "duplicate estimator input identifier",
    ),
    LeakageCase(
        "unknown_provenance_parent",
        "fail_closed_provenance",
        "Add a metrological edge whose parent is undeclared.",
        _append_metrological_edges(
            ProvenanceEdge(
                "force_estimate",
                "missing_parent",
                "calibration",
                "Unknown parent probe.",
            ),
        ),
        "rejection",
        "graph_identity_gate",
        "Every provenance parent must resolve to a declared quantity.",
        "unknown parent or child",
    ),
    LeakageCase(
        "unknown_provenance_child",
        "fail_closed_provenance",
        "Add a metrological edge whose child is undeclared.",
        _append_metrological_edges(
            ProvenanceEdge(
                "missing_child",
                "force_reference",
                "calibration",
                "Unknown child probe.",
            ),
        ),
        "rejection",
        "graph_identity_gate",
        "Every provenance child must resolve to a declared quantity.",
        "unknown parent or child",
    ),
    LeakageCase(
        "definitional_cycle",
        "fail_closed_provenance",
        "Add force_estimate -> G_hat to reverse an existing definition edge.",
        _append_definition_edge(
            ProvenanceEdge(
                "force_estimate",
                "G_hat",
                "definition",
                "Definitional cycle probe.",
            )
        ),
        "rejection",
        "definitional_cycle_gate",
        "Definitions must form an acyclic dependency graph.",
        "cyclic definitional provenance",
    ),
    LeakageCase(
        "metrological_cycle",
        "fail_closed_provenance",
        "Add angle_observation -> force_estimate to reverse an existing edge.",
        _append_metrological_edges(
            ProvenanceEdge(
                "angle_observation",
                "force_estimate",
                "observation_derivation",
                "Metrological cycle probe.",
            ),
        ),
        "rejection",
        "metrological_cycle_gate",
        "Physical provenance must not recursively justify itself.",
        "cyclic metrological provenance",
    ),
    LeakageCase(
        "combined_cross_layer_cycle",
        "fail_closed_provenance",
        "Add a metrological force_estimate -> G_hat edge across graph layers.",
        _append_metrological_edges(
            ProvenanceEdge(
                "force_estimate",
                "G_hat",
                "model_input",
                "Combined graph cycle probe.",
            ),
        ),
        "rejection",
        "combined_cycle_gate",
        "The union of valid-looking graph layers must also remain acyclic.",
        "cyclic combined provenance",
    ),
    LeakageCase(
        "missing_calibrated_measurement_ancestry",
        "fail_closed_provenance",
        "Remove every metrological parent of mass_1.",
        _remove_metrological_parents("mass_1"),
        "rejection",
        "required_provenance_gate",
        "A calibrated measurement cannot be accepted without its calibration ancestry.",
        "required provenance is missing for mass_1",
    ),
    LeakageCase(
        "missing_correction_ancestry",
        "fail_closed_provenance",
        "Remove every metrological parent of alignment_correction.",
        _remove_metrological_parents("alignment_correction"),
        "rejection",
        "required_provenance_gate",
        "A correction cannot be accepted without records explaining its derivation.",
        "required provenance is missing for alignment_correction",
    ),
    LeakageCase(
        "terminal_codata_comparison_allowed",
        "positive_control",
        "Keep CODATA G isolated in its declared terminal comparison node.",
        _identity,
        "status",
        "external_reference_boundary",
        "The boundary must permit a reference after estimation rather than reject all models.",
        expected_statuses=(
            ("registered_target_path_status", NO_REGISTERED_TARGET_PATH),
        ),
        post_assertion=_assert_terminal_reference,
    ),
    LeakageCase(
        "target_clean_registered_expression_allowed",
        "positive_control",
        "Represent mass_1 by the target-clean registered expression m_e.",
        _registered_expression("mass_1", (("m_e", Fraction(1)),)),
        "status",
        "registered_target_path_status",
        "A registered expression with no catalog path to G must be able to pass the gate.",
        expected_statuses=(
            ("registered_target_path_status", NO_REGISTERED_TARGET_PATH),
        ),
        target_quantity_id="mass_1",
        expected_target_status=NO_REGISTERED_TARGET_PATH,
        expected_target_power=Fraction(0),
    ),
    LeakageCase(
        "algebraic_cleanliness_does_not_promote_metrology",
        "positive_control",
        "Evaluate the target-clean but structurally unpopulated baseline.",
        _identity,
        "status",
        "orthogonal_assessment_axes",
        "Algebraic status must not silently satisfy physical provenance.",
        expected_statuses=(
            ("registered_target_path_status", NO_REGISTERED_TARGET_PATH),
            ("metrological_provenance_status", INCOMPLETE),
        ),
    ),
    LeakageCase(
        "unresolved_never_becomes_independent",
        "positive_control",
        "Leave both algebraic and metrological ancestry unresolved for mass_1.",
        _unresolved_algebraic("mass_1", unresolved_evidence=True),
        "status",
        "fail_closed_status_language",
        "Unknown ancestry must retain the explicit unresolved status.",
        expected_statuses=(
            ("registered_target_path_status", UNRESOLVED),
            ("metrological_provenance_status", UNRESOLVED),
        ),
        post_assertion=_assert_unresolved_is_not_independent,
    ),
    LeakageCase(
        "unpopulated_structural_example_remains_incomplete",
        "positive_control",
        "Evaluate the unchanged Milestone 4 structural example.",
        _identity,
        "status",
        "empirical_population_status",
        "A schema placeholder must never be promoted to empirical evidence.",
        expected_statuses=(
            ("uncertainty_status", INCOMPLETE),
            ("empirical_population_status", INCOMPLETE),
            ("replication_status", NOT_APPLICABLE),
        ),
    ),
)


class PhysicalBridgeLeakageCorpusTests(unittest.TestCase):
    def test_case_catalog_has_stable_complete_metadata(self) -> None:
        identifiers = [case.identifier for case in LEAKAGE_CASES]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(len(LEAKAGE_CASES), 34)
        self.assertEqual(
            {
                category: sum(
                    case.category == category for case in LEAKAGE_CASES
                )
                for category in (
                    "direct_algebraic_leakage",
                    "inherited_leakage",
                    "fail_closed_provenance",
                    "positive_control",
                )
            },
            {
                "direct_algebraic_leakage": 10,
                "inherited_leakage": 7,
                "fail_closed_provenance": 12,
                "positive_control": 5,
            },
        )
        for case in LEAKAGE_CASES:
            with self.subTest(case=case.identifier):
                self.assertTrue(case.category)
                self.assertTrue(case.attack)
                self.assertIn(case.expected_outcome, {"rejection", "status"})
                self.assertTrue(case.expected_gate)
                self.assertTrue(case.reason)

    def test_parameterized_leakage_and_positive_control_corpus(self) -> None:
        for case in LEAKAGE_CASES:
            with self.subTest(case=case.identifier, category=case.category):
                model = case.mutate(build_inverse_square_model())

                if case.target_quantity_id is not None:
                    quantity = next(
                        item
                        for item in model.quantities
                        if item.identifier == case.target_quantity_id
                    )
                    self.assertIsNotNone(quantity.registered_dependency_signature)
                    assert quantity.registered_dependency_signature is not None
                    audit = audit_registered_target_path(
                        quantity.registered_dependency_signature,
                        identifier=quantity.identifier,
                        catalog=build_model_dependency_catalog(model),
                    )
                    self.assertEqual(audit.identifier, case.target_quantity_id)
                    self.assertEqual(audit.status, case.expected_target_status)
                    self.assertEqual(audit.power_of_target, case.expected_target_power)

                if case.expected_outcome == "rejection":
                    with self.assertRaises(BridgeValidationError) as raised:
                        validate_measurement_model(model)
                    self.assertIsNotNone(case.exception_fragment)
                    assert case.exception_fragment is not None
                    self.assertIn(case.exception_fragment, str(raised.exception))
                    continue

                evaluation = evaluate_measurement_model(model)
                for field, expected in case.expected_statuses:
                    self.assertEqual(getattr(evaluation, field), expected)
                if case.post_assertion is not None:
                    case.post_assertion(self, model, evaluation)


if __name__ == "__main__":
    unittest.main()
