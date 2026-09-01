from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import unittest

from Discovery import physical_bridge as bridge_facade
from Discovery import physical_bridge_schema as bridge_schema
from Discovery import physical_bridge_validation as bridge_validation
from Discovery.dependency_analysis import build_artifact as build_dependency_artifact
from Discovery.dependency_definitions import DEFAULT_DEPENDENCY_CATALOG
from Discovery.dimensions import GRAVITATIONAL_CONSTANT
from Discovery.physical_bridge import (
    COVARIANCE_MATRIX,
    DEFAULT_CONTRACT_OUTPUT,
    DEFAULT_EXAMPLE_OUTPUT,
    EXPLICIT_ZERO_ASSUMPTION,
    INCOMPLETE,
    LEAN_THEOREMS_BY_ID,
    NO_REGISTERED_TARGET_PATH,
    REGISTERED_EXPRESSION,
    SATISFIED,
    STRUCTURAL_PLACEHOLDER,
    TARGET_PATH_DETECTED,
    UNRESOLVED,
    UNRESOLVED_ALGEBRAIC_PROVENANCE,
    UNRESOLVED_PROVENANCE_EVIDENCE,
    BridgeValidationError,
    CorrelationDeclaration,
    EstimatorTerm,
    ProvenanceEdge,
    QuantityRecord,
    audit_registered_target_path,
    build_contract_artifact,
    build_example_artifact,
    build_inverse_square_model,
    build_model_dependency_catalog,
    evaluate_measurement_model,
    measurement_model_record,
    serialize_artifact,
    validate_measurement_model,
)


def replace_quantity(model, identifier: str, **changes):
    quantities = tuple(
        replace(quantity, **changes)
        if quantity.identifier == identifier
        else quantity
        for quantity in model.quantities
    )
    return replace(model, quantities=quantities)


class PhysicalBridgeTests(unittest.TestCase):
    def test_public_facade_reexports_schema_and_validation_api(self) -> None:
        self.assertIs(bridge_facade.MeasurementModel, bridge_schema.MeasurementModel)
        self.assertIs(bridge_facade.QuantityRecord, bridge_schema.QuantityRecord)
        self.assertIs(
            bridge_facade.validate_measurement_model,
            bridge_validation.validate_measurement_model,
        )
        self.assertIs(
            bridge_facade.evaluate_measurement_model,
            bridge_validation.evaluate_measurement_model,
        )

    def test_inverse_square_estimator_dimension_is_exact(self) -> None:
        evaluation = evaluate_measurement_model(build_inverse_square_model())
        self.assertEqual(evaluation.dimensional_status, SATISFIED)
        self.assertEqual(evaluation.estimator_dimension, GRAVITATIONAL_CONSTANT)

    def test_existing_dimension_dependency_and_lean_linkages_are_explicit(self) -> None:
        model = build_inverse_square_model()
        catalog = build_model_dependency_catalog(model)
        for key in ("l_P", "m_P", "t_P", "T_P"):
            with self.subTest(key=key):
                self.assertEqual(
                    catalog.expanded_definitions[key],
                    DEFAULT_DEPENDENCY_CATALOG.expanded_definitions[key],
                )
        record = measurement_model_record(model)
        self.assertEqual(
            record["lean_linkage"]["catalog_identifier"],
            "conditional_inverse_square_estimator_correctness",
        )
        self.assertEqual(
            record["lean_linkage"]["fully_qualified_name"],
            "TheNumberProject.FormalPhysics."
            "inverseSquareEstimator_eq_gravitationalConstant",
        )
        self.assertTrue(
            record["lean_linkage"]["estimator_rearrangement_certified"]
        )

    def test_lean_catalog_distinguishes_relation_from_estimator_proof(self) -> None:
        relation = LEAN_THEOREMS_BY_ID[
            "conditional_inverse_square_force_relation"
        ]
        estimator = LEAN_THEOREMS_BY_ID[
            "conditional_inverse_square_estimator_correctness"
        ]
        self.assertFalse(relation.estimator_rearrangement_certified)
        self.assertTrue(estimator.estimator_rearrangement_certified)
        self.assertEqual(
            estimator.fully_qualified_name,
            "TheNumberProject.FormalPhysics."
            "inverseSquareEstimator_eq_gravitationalConstant",
        )
        self.assertNotEqual(
            relation.fully_qualified_name,
            estimator.fully_qualified_name,
        )

    def test_m_planck_has_an_explicit_registered_target_path(self) -> None:
        audit = audit_registered_target_path(
            (("m_P", Fraction(1)),),
            identifier="m_P",
        )
        self.assertEqual(audit.status, TARGET_PATH_DETECTED)
        self.assertEqual(audit.power_of_target, Fraction(-1, 2))

    def test_other_registered_planck_quantities_have_target_paths(self) -> None:
        expected = {
            "l_P": Fraction(1, 2),
            "t_P": Fraction(1, 2),
            "T_P": Fraction(-1, 2),
        }
        for key, power in expected.items():
            with self.subTest(key=key):
                audit = audit_registered_target_path(((key, 1),), identifier=key)
                self.assertEqual(audit.status, TARGET_PATH_DETECTED)
                self.assertEqual(audit.power_of_target, power)

    def test_direct_g_or_planck_estimator_input_is_rejected(self) -> None:
        for key in ("G", "m_P", "l_P", "t_P", "T_P"):
            with self.subTest(key=key):
                model = replace_quantity(
                    build_inverse_square_model(),
                    "mass_1",
                    algebraic_provenance_kind=REGISTERED_EXPRESSION,
                    registered_dependency_signature=((key, Fraction(1)),),
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "estimator ancestry reaches G",
                ):
                    validate_measurement_model(model)

    def test_reference_g_used_in_calibration_is_rejected(self) -> None:
        model = build_inverse_square_model()
        edge = ProvenanceEdge(
            "force_reference",
            "codata_2022_G",
            "calibration",
            "Forbidden attempt to calibrate the force reference with G.",
        )
        model = replace(
            model,
            metrological_edges=(*model.metrological_edges, edge),
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "reference G is used in calibration or correction force_reference",
        ):
            validate_measurement_model(model)

    def test_reference_g_used_in_correction_is_rejected(self) -> None:
        model = build_inverse_square_model()
        edge = ProvenanceEdge(
            "alignment_correction",
            "codata_2022_G",
            "correction",
            "Forbidden attempt to derive a correction from reference G.",
        )
        model = replace(
            model,
            metrological_edges=(*model.metrological_edges, edge),
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "reference G is used in calibration or correction alignment_correction",
        ):
            validate_measurement_model(model)

    def test_codata_reference_is_allowed_only_in_terminal_comparison(self) -> None:
        record = measurement_model_record(build_inverse_square_model())
        self.assertEqual(
            record["external_comparison"]["reference_ids"],
            ["codata_2022_G"],
        )
        comparison_audit = record["target_path_audit"][
            "isolated_comparison_reference_assessments"
        ][0]
        self.assertEqual(comparison_audit["status"], TARGET_PATH_DETECTED)
        self.assertEqual(
            record["target_path_audit"]["gate_result"],
            NO_REGISTERED_TARGET_PATH,
        )

    def test_unresolved_ancestry_remains_unresolved(self) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "mass_1",
            algebraic_provenance_kind=UNRESOLVED_ALGEBRAIC_PROVENANCE,
            registered_dependency_signature=None,
            provenance_evidence=UNRESOLVED_PROVENANCE_EVIDENCE,
        )
        evaluation = evaluate_measurement_model(model)
        self.assertEqual(evaluation.registered_target_path_status, UNRESOLVED)
        self.assertEqual(evaluation.metrological_provenance_status, UNRESOLVED)
        self.assertNotIn("independent", evaluation.registered_target_path_status)

    def test_definitional_and_metrological_cycles_are_rejected(self) -> None:
        model = build_inverse_square_model()
        definition_cycle = ProvenanceEdge(
            "force_estimate",
            "G_hat",
            "definition",
            "Creates a forbidden definitional cycle for the test.",
        )
        with self.subTest(graph="definitional"):
            with self.assertRaisesRegex(BridgeValidationError, "cyclic definitional"):
                validate_measurement_model(
                    replace(
                        model,
                        definition_edges=(*model.definition_edges, definition_cycle),
                    )
                )

        metrological_cycle = ProvenanceEdge(
            "angle_observation",
            "force_estimate",
            "observation_derivation",
            "Creates a forbidden metrological cycle for the test.",
        )
        with self.subTest(graph="metrological"):
            with self.assertRaisesRegex(BridgeValidationError, "cyclic metrological"):
                validate_measurement_model(
                    replace(
                        model,
                        metrological_edges=(
                            *model.metrological_edges,
                            metrological_cycle,
                        ),
                    )
                )

        cross_layer_cycle = ProvenanceEdge(
            "force_estimate",
            "G_hat",
            "model_input",
            "Creates a forbidden cycle across both provenance layers.",
        )
        with self.subTest(graph="combined"):
            with self.assertRaisesRegex(BridgeValidationError, "cyclic combined"):
                validate_measurement_model(
                    replace(
                        model,
                        metrological_edges=(
                            *model.metrological_edges,
                            cross_layer_cycle,
                        ),
                    )
                )

    def test_unknown_provenance_parent_is_rejected_in_both_graphs(self) -> None:
        model = build_inverse_square_model()
        for graph_name, edge in (
            (
                "definition_edges",
                ProvenanceEdge(
                    "G_hat",
                    "missing_quantity",
                    "definition",
                    "Unknown definitional parent.",
                ),
            ),
            (
                "metrological_edges",
                ProvenanceEdge(
                    "force_estimate",
                    "missing_quantity",
                    "calibration",
                    "Unknown metrological parent.",
                ),
            ),
        ):
            with self.subTest(graph=graph_name):
                changed = replace(
                    model,
                    **{graph_name: (*getattr(model, graph_name), edge)},
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "unknown parent or child",
                ):
                    validate_measurement_model(changed)

    def test_algebraic_cleanliness_does_not_promote_metrological_status(self) -> None:
        evaluation = evaluate_measurement_model(build_inverse_square_model())
        self.assertEqual(
            evaluation.registered_target_path_status,
            NO_REGISTERED_TARGET_PATH,
        )
        self.assertEqual(evaluation.metrological_provenance_status, INCOMPLETE)
        self.assertEqual(evaluation.empirical_population_status, INCOMPLETE)

    def test_missing_uncertainty_produces_incomplete_not_zero(self) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "force_estimate",
            value=Decimal("1.25e-9"),
            standard_uncertainty=None,
            uncertainty_unit=None,
        )
        evaluation = evaluate_measurement_model(model)
        self.assertEqual(evaluation.uncertainty_status, INCOMPLETE)
        self.assertIn(
            "standard uncertainty is missing: force_estimate",
            evaluation.uncertainty_gaps,
        )

    def test_missing_uncertainty_model_is_incomplete(self) -> None:
        model = replace(build_inverse_square_model(), uncertainty_model=None)
        evaluation = evaluate_measurement_model(model)
        self.assertEqual(evaluation.uncertainty_status, INCOMPLETE)
        self.assertIn("uncertainty model is missing", evaluation.uncertainty_gaps)

    def test_numerical_ancestor_without_uncertainty_is_incomplete(self) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "angle_observation",
            value=Decimal("1.25e-6"),
            standard_uncertainty=None,
            uncertainty_unit=None,
        )
        evaluation = evaluate_measurement_model(model)
        self.assertEqual(evaluation.uncertainty_status, INCOMPLETE)
        self.assertIn(
            "standard uncertainty is missing: angle_observation",
            evaluation.uncertainty_gaps,
        )

    def test_correlation_policy_or_covariance_must_be_declared(self) -> None:
        uncertainty = build_inverse_square_model().uncertainty_model
        assert uncertainty is not None
        with self.assertRaisesRegex(BridgeValidationError, "correlation policy"):
            replace(uncertainty, correlation_policy="")
        with self.assertRaisesRegex(
            BridgeValidationError,
            "zero-correlation justification",
        ):
            replace(
                uncertainty,
                correlation_policy=EXPLICIT_ZERO_ASSUMPTION,
                zero_correlation_justification=None,
            )

        covariance = CorrelationDeclaration(
            "force_estimate",
            "mass_1",
            Decimal("0"),
            "N kg",
        )
        populated = replace(
            uncertainty,
            correlation_policy=COVARIANCE_MATRIX,
            correlations=(covariance,),
        )
        self.assertEqual(populated.correlations, (covariance,))
        with self.assertRaisesRegex(
            BridgeValidationError,
            "cannot contain covariance declarations",
        ):
            replace(
                uncertainty,
                correlation_policy=EXPLICIT_ZERO_ASSUMPTION,
                correlations=(covariance,),
                zero_correlation_justification="All shared sources were evaluated.",
            )

    def test_nonexact_input_cannot_fabricate_zero_uncertainty(self) -> None:
        with self.assertRaisesRegex(BridgeValidationError, "zero standard uncertainty"):
            replace_quantity(
                build_inverse_square_model(),
                "angle_observation",
                value=Decimal("1.25e-6"),
                standard_uncertainty=Decimal("0"),
                uncertainty_unit="rad",
            )

    def test_binary_float_measurements_and_exponents_are_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "binary floats"):
            QuantityRecord(
                "float_value",
                "x",
                "direct_observation",
                GRAVITATIONAL_CONSTANT,
                "m^3 kg^-1 s^-2",
                "declared_local_atom",
                None,
                STRUCTURAL_PLACEHOLDER,
                "Invalid binary floating-point measurement.",
                value=1.0,
            )
        with self.assertRaisesRegex(TypeError, "not bool or float"):
            EstimatorTerm("force_estimate", 0.5)
        with self.assertRaisesRegex(TypeError, "not bool or float"):
            EstimatorTerm("force_estimate", True)

    def test_dimensionally_inconsistent_estimator_is_rejected(self) -> None:
        model = build_inverse_square_model()
        terms = tuple(
            EstimatorTerm(term.quantity_id, 1)
            if term.quantity_id == "separation"
            else term
            for term in model.estimator_terms
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "dimensionally inconsistent estimator",
        ):
            validate_measurement_model(replace(model, estimator_terms=terms))

    def test_dimensionally_inconsistent_provenance_signature_is_rejected(self) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "mass_1",
            algebraic_provenance_kind=REGISTERED_EXPRESSION,
            registered_dependency_signature=(("c", Fraction(1)),),
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "dimensionally inconsistent algebraic provenance",
        ):
            validate_measurement_model(model)

    def test_duplicate_identifiers_and_missing_target_are_rejected(self) -> None:
        model = build_inverse_square_model()
        with self.assertRaisesRegex(BridgeValidationError, "duplicate quantity"):
            validate_measurement_model(
                replace(model, quantities=(*model.quantities, model.quantities[0]))
            )
        with self.assertRaisesRegex(BridgeValidationError, "missing its target"):
            validate_measurement_model(
                replace(model, target_measurand_id="missing_target")
            )

    def test_missing_units_and_reference_metadata_are_rejected(self) -> None:
        with self.assertRaisesRegex(BridgeValidationError, "unit for mass_1"):
            replace_quantity(build_inverse_square_model(), "mass_1", unit="")
        with self.assertRaisesRegex(BridgeValidationError, "edition for codata_2022_G"):
            replace_quantity(
                build_inverse_square_model(),
                "codata_2022_G",
                edition="",
            )

    def test_missing_measurement_model_is_rejected_clearly(self) -> None:
        with self.assertRaisesRegex(BridgeValidationError, "measurement model is missing"):
            validate_measurement_model(None)  # type: ignore[arg-type]

    def test_local_atom_display_symbol_cannot_collide_with_catalog(self) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "mass_1",
            symbol="m_P",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "display symbol collides with registered catalog symbol after "
            "normalization: m_P",
        ):
            validate_measurement_model(model)

    def test_registered_expression_display_symbol_cannot_collide_with_catalog(
        self,
    ) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "codata_2022_G",
            symbol="m_P",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "registered key m_P; quantity codata_2022_G",
        ):
            validate_measurement_model(model)

    def test_registered_display_symbol_collision_ignores_outer_whitespace(
        self,
    ) -> None:
        for symbol in (" m_P", "m_P ", "\u00a0m_P\u00a0"):
            with self.subTest(symbol=repr(symbol)):
                model = replace_quantity(
                    build_inverse_square_model(),
                    "codata_2022_G",
                    symbol=symbol,
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "registered catalog symbol after normalization: m_P",
                ):
                    validate_measurement_model(model)

    def test_duplicate_display_symbols_are_normalized(self) -> None:
        cases = (
            ("shared_symbol", " shared_symbol "),
            ("e\u0301", "\u00e9"),
        )
        for first_symbol, second_symbol in cases:
            with self.subTest(
                first_symbol=repr(first_symbol),
                second_symbol=repr(second_symbol),
            ):
                model = replace_quantity(
                    build_inverse_square_model(),
                    "mass_1",
                    symbol=first_symbol,
                )
                model = replace_quantity(
                    model,
                    "mass_2",
                    symbol=second_symbol,
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "duplicate display symbol after normalization",
                ):
                    validate_measurement_model(model)

    def test_duplicate_display_symbols_are_provenance_kind_agnostic(self) -> None:
        model = replace_quantity(
            build_inverse_square_model(),
            "mass_1",
            symbol="shared_symbol",
        )
        model = replace_quantity(
            model,
            "codata_2022_G",
            symbol="shared_symbol",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "duplicate display symbol after normalization: shared_symbol",
        ):
            validate_measurement_model(model)

    def test_unicode_format_controls_do_not_bypass_display_guards(self) -> None:
        for format_control in ("\u200b", "\u200c", "\u200d", "\ufeff"):
            with self.subTest(format_control=repr(format_control)):
                model = replace_quantity(
                    build_inverse_square_model(),
                    "codata_2022_G",
                    symbol=f"m_P{format_control}",
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "registered catalog symbol after normalization: m_P",
                ):
                    validate_measurement_model(model)

        model = replace_quantity(
            build_inverse_square_model(),
            "mass_1",
            symbol="shared_symbol",
        )
        model = replace_quantity(
            model,
            "codata_2022_G",
            symbol="shared_symbol\u200b",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "duplicate display symbol after normalization: shared_symbol",
        ):
            validate_measurement_model(model)

        model = replace_quantity(
            build_inverse_square_model(),
            "codata_2022_G",
            symbol="\u200b",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "display symbol is empty after normalization: codata_2022_G",
        ):
            validate_measurement_model(model)

    def test_model_scope_and_nonclaims_cannot_be_omitted(self) -> None:
        model = build_inverse_square_model()
        for field_name in (
            "domain_and_approximation_regime",
            "required_hypotheses",
            "limitations",
            "nonclaims",
        ):
            with self.subTest(field=field_name):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "measurement model must state",
                ):
                    replace(model, **{field_name: ()})

    def test_graph_and_artifact_ordering_are_deterministic(self) -> None:
        model = build_inverse_square_model()
        reversed_model = replace(
            model,
            quantities=tuple(reversed(model.quantities)),
            estimator_terms=tuple(reversed(model.estimator_terms)),
            definition_edges=tuple(reversed(model.definition_edges)),
            metrological_edges=tuple(reversed(model.metrological_edges)),
        )
        self.assertEqual(
            measurement_model_record(model),
            measurement_model_record(reversed_model),
        )
        first = serialize_artifact(build_contract_artifact())
        second = serialize_artifact(build_contract_artifact())
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_artifacts_regenerate_byte_identically_and_are_current(self) -> None:
        contract = serialize_artifact(build_contract_artifact())
        example = serialize_artifact(build_example_artifact())
        self.assertEqual(
            DEFAULT_CONTRACT_OUTPUT.read_text(encoding="utf-8"),
            contract,
        )
        self.assertEqual(
            DEFAULT_EXAMPLE_OUTPUT.read_text(encoding="utf-8"),
            example,
        )
        self.assertTrue(contract.endswith("\n"))
        self.assertTrue(example.endswith("\n"))

    def test_artifacts_contain_no_binary_floating_point_values(self) -> None:
        def assert_no_float(value) -> None:
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for child in value.values():
                    assert_no_float(child)
            elif isinstance(value, list):
                for child in value:
                    assert_no_float(child)

        assert_no_float(build_contract_artifact())
        assert_no_float(build_example_artifact())

    def test_milestone_three_dependency_results_are_preserved(self) -> None:
        artifact = build_dependency_artifact()
        self.assertEqual(artifact["candidate_count"], 21)
        self.assertEqual(artifact["equivalence_group_count"], 10)
        self.assertEqual(artifact["dimensional_system"]["rank"], 4)
        self.assertEqual(artifact["dimensional_system"]["nullity"], 6)


if __name__ == "__main__":
    unittest.main()
