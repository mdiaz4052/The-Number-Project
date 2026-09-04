from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
import unittest

from Discovery import physical_bridge as bridge_facade
from Discovery import physical_bridge_schema as bridge_schema
from Discovery import physical_bridge_validation as bridge_validation
from Discovery.dependency_analysis import build_artifact as build_dependency_artifact
from Discovery.dependency_definitions import DEFAULT_DEPENDENCY_CATALOG
from Discovery.dimensions import DIMENSIONLESS, GRAVITATIONAL_CONSTANT
from Discovery.physical_bridge import (
    CORRECTION,
    COVARIANCE_MATRIX,
    DECLARED_LOCAL_ATOM,
    DEFAULT_CONTRACT_OUTPUT,
    DEFAULT_EXAMPLE_OUTPUT,
    DEFINITION,
    DERIVED_QUANTITY,
    DIRECT_MEASURAND_CONTRIBUTIONS,
    DOCUMENTED,
    EMPIRICAL_RECORD,
    ESTIMATOR_INPUT_PROPAGATION,
    EXPLICIT_ZERO_ASSUMPTION,
    INCOMPLETE,
    LEAN_THEOREMS_BY_ID,
    MODEL_PARAMETER,
    NO_REGISTERED_TARGET_PATH,
    NOT_APPLICABLE,
    REGISTERED_EXPRESSION,
    SATISFIED,
    STRUCTURAL_PLACEHOLDER,
    TARGET_PATH_DETECTED,
    UNCERTAINTY_COMPONENT,
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


def direct_uncertainty_component(
    identifier: str,
    value: Decimal,
    *,
    dimension=DIMENSIONLESS,
    unit: str = "ppm",
    role: str = UNCERTAINTY_COMPONENT,
    provenance_evidence: str = DOCUMENTED,
    source_identifier: str | None = "doi:10.1234/direct-budget",
    edition: str | None = "example direct budget, edition 1",
    access_date: str | None = "2026-09-04",
) -> QuantityRecord:
    return QuantityRecord(
        identifier,
        f"u_{identifier}",
        role,
        dimension,
        unit,
        DECLARED_LOCAL_ATOM,
        None,
        provenance_evidence,
        "Published uncertainty contribution already expressed for the measurand.",
        value=value,
        source_identifier=source_identifier,
        edition=edition,
        access_date=access_date,
    )


def build_direct_budget_model():
    model = build_inverse_square_model()
    components = (
        direct_uncertainty_component("relative_component_b", Decimal("4")),
        direct_uncertainty_component("relative_component_a", Decimal("3")),
    )
    model = replace_quantity(
        model,
        "G_hat",
        value=Decimal("6.67e-11"),
        standard_uncertainty=Decimal("8e-16"),
        uncertainty_unit="m^3 kg^-1 s^-2",
    )
    assert model.uncertainty_model is not None
    uncertainty = replace(
        model.uncertainty_model,
        input_ids=(),
        correction_ids=(),
        correlation_policy=EXPLICIT_ZERO_ASSUMPTION,
        zero_correlation_justification=(
            "The example assumes zero pairwise covariance solely to exercise the "
            "direct-budget representation."
        ),
        propagation_method="root sum of squares of direct relative contributions",
        coverage_basis="standard uncertainty; no expanded coverage claim",
        uncertainty_basis=DIRECT_MEASURAND_CONTRIBUTIONS,
        component_ids=tuple(component.identifier for component in components),
    )
    return replace(
        model,
        quantities=(*model.quantities, *components),
        uncertainty_model=uncertainty,
    )


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

    def test_external_g_reference_cannot_be_an_estimator_input(self) -> None:
        model = build_inverse_square_model()
        terms = (
            EstimatorTerm("codata_2022_G", Fraction(1)),
            *model.estimator_terms[1:],
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "forbidden estimator input role for codata_2022_G",
        ):
            validate_measurement_model(replace(model, estimator_terms=terms))

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

    def test_reference_g_used_in_tuning_or_acceptance_is_rejected(self) -> None:
        for identifier, role in (
            ("tuning_parameter", MODEL_PARAMETER),
            ("acceptance_decision", DERIVED_QUANTITY),
        ):
            with self.subTest(path=identifier):
                model = build_inverse_square_model()
                node = QuantityRecord(
                    identifier,
                    f"{identifier}_symbol",
                    role,
                    GRAVITATIONAL_CONSTANT,
                    "m^3 kg^-1 s^-2",
                    DECLARED_LOCAL_ATOM,
                    None,
                    STRUCTURAL_PLACEHOLDER,
                    "Adversarial node that must not consume a comparison reference.",
                )
                edge = ProvenanceEdge(
                    identifier,
                    "codata_2022_G",
                    "model_input",
                    "Forbidden attempt to use reference G before terminal comparison.",
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "may feed comparison nodes only",
                ):
                    validate_measurement_model(
                        replace(
                            model,
                            quantities=(*model.quantities, node),
                            metrological_edges=(*model.metrological_edges, edge),
                        )
                    )

    def test_populated_empirical_calibration_requires_source_provenance(self) -> None:
        model = replace(
            build_inverse_square_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        model = replace_quantity(
            model,
            "force_reference",
            provenance_evidence=DOCUMENTED,
            value=Decimal("1"),
            standard_uncertainty=Decimal("0.1"),
            uncertainty_unit="N",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "source provenance metadata for force_reference",
        ):
            validate_measurement_model(model)

    def test_populated_empirical_calibration_requires_documented_provenance(self) -> None:
        model = replace(
            build_inverse_square_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        model = replace_quantity(
            model,
            "force_reference",
            provenance_evidence=STRUCTURAL_PLACEHOLDER,
            value=Decimal("1"),
            standard_uncertainty=Decimal("0.1"),
            uncertainty_unit="N",
            source_identifier="certificate:project/force-reference",
            edition="certificate edition 1",
            access_date="2026-09-01",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "missing documented provenance",
        ):
            validate_measurement_model(model)

    def test_each_empirical_source_metadata_field_is_required(self) -> None:
        complete_metadata = {
            "source_identifier": "certificate:project/force-reference",
            "edition": "certificate edition 1",
            "access_date": "2026-09-01",
        }
        for field, diagnostic in (
            ("source_identifier", "source identifier"),
            ("edition", "source edition"),
            ("access_date", "source access date"),
        ):
            with self.subTest(field=field):
                model = replace(
                    build_inverse_square_model(),
                    evidence_level=EMPIRICAL_RECORD,
                )
                metadata = dict(complete_metadata)
                metadata[field] = None
                model = replace_quantity(
                    model,
                    "force_reference",
                    provenance_evidence=DOCUMENTED,
                    value=Decimal("1"),
                    standard_uncertainty=Decimal("0.1"),
                    uncertainty_unit="N",
                    **metadata,
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    f"missing {diagnostic}",
                ):
                    validate_measurement_model(model)

    def test_exact_flag_does_not_bypass_empirical_source_metadata(self) -> None:
        model = replace(
            build_inverse_square_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        exact_record = QuantityRecord(
            "materialized_pi_factor",
            "pi_factor_numeric",
            DEFINITION,
            DIMENSIONLESS,
            "1",
            DECLARED_LOCAL_ATOM,
            None,
            DOCUMENTED,
            (
                "Adversarial materialized decimal record: exact=True must not turn "
                "an unsourced coefficient into a symbolic mathematical constant."
            ),
            value=Decimal("3.141592653589793"),
            standard_uncertainty=Decimal("0"),
            uncertainty_unit="1",
            exact=True,
        )
        uncertainty = replace(
            model.uncertainty_model,
            input_ids=(
                *model.uncertainty_model.input_ids,
                exact_record.identifier,
            ),
        )
        model = replace(
            model,
            quantities=(*model.quantities, exact_record),
            estimator_terms=(
                *model.estimator_terms,
                EstimatorTerm(exact_record.identifier, Fraction(1)),
            ),
            definition_edges=(
                *model.definition_edges,
                ProvenanceEdge(
                    "G_hat",
                    exact_record.identifier,
                    "definition",
                    "Adversarial exact numeric estimator coefficient.",
                ),
            ),
            uncertainty_model=uncertainty,
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "source provenance metadata for materialized_pi_factor",
        ):
            validate_measurement_model(model)

    def test_declared_calibration_outside_estimator_ancestry_requires_source(self) -> None:
        model = replace(
            build_inverse_square_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        calibration = QuantityRecord(
            "auxiliary_calibration",
            "aux_cal",
            DEFINITION,
            DIMENSIONLESS,
            "1",
            DECLARED_LOCAL_ATOM,
            None,
            DOCUMENTED,
            "Declared calibration intentionally disconnected from estimator ancestry.",
            value=Decimal("1"),
            standard_uncertainty=Decimal("0.1"),
            uncertainty_unit="1",
        )
        model = replace(
            model,
            quantities=(*model.quantities, calibration),
            calibration_source_ids=(
                *model.calibration_source_ids,
                calibration.identifier,
            ),
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "source provenance metadata for auxiliary_calibration",
        ):
            validate_measurement_model(model)

    def test_declared_correction_outside_estimator_ancestry_requires_source(self) -> None:
        model = replace(
            build_inverse_square_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        correction = QuantityRecord(
            "auxiliary_correction",
            "aux_corr",
            CORRECTION,
            DIMENSIONLESS,
            "1",
            UNRESOLVED_ALGEBRAIC_PROVENANCE,
            None,
            UNRESOLVED_PROVENANCE_EVIDENCE,
            "Declared correction intentionally disconnected from estimator ancestry.",
            value=Decimal("1"),
            standard_uncertainty=Decimal("0.1"),
            uncertainty_unit="1",
        )
        uncertainty = replace(
            model.uncertainty_model,
            correction_ids=(
                *model.uncertainty_model.correction_ids,
                correction.identifier,
            ),
        )
        model = replace(
            model,
            quantities=(*model.quantities, correction),
            correction_ids=(*model.correction_ids, correction.identifier),
            uncertainty_model=uncertainty,
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "source provenance metadata for auxiliary_correction",
        ):
            validate_measurement_model(model)

    def test_unpopulated_empirical_record_stays_incomplete(self) -> None:
        model = replace(
            build_inverse_square_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        evaluation = evaluate_measurement_model(model)
        self.assertEqual(evaluation.empirical_population_status, INCOMPLETE)
        self.assertEqual(evaluation.replication_status, NOT_APPLICABLE)

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

    def test_legacy_estimator_input_uncertainty_mode_is_unchanged(self) -> None:
        model = build_inverse_square_model()
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        self.assertEqual(
            uncertainty.uncertainty_basis,
            ESTIMATOR_INPUT_PROPAGATION,
        )
        self.assertEqual(uncertainty.component_ids, ())
        serialized = measurement_model_record(model)["uncertainty_model"]
        self.assertNotIn("uncertainty_basis", serialized)
        self.assertNotIn("component_ids", serialized)

    def test_contract_catalogs_both_uncertainty_bases(self) -> None:
        contract = build_contract_artifact()
        self.assertIn(UNCERTAINTY_COMPONENT, contract["input_roles"])
        bases = contract["uncertainty_requirements"]["uncertainty_bases"]
        self.assertEqual(
            set(bases),
            {
                ESTIMATOR_INPUT_PROPAGATION,
                DIRECT_MEASURAND_CONTRIBUTIONS,
            },
        )
        self.assertEqual(
            bases[DIRECT_MEASURAND_CONTRIBUTIONS]["component_role"],
            UNCERTAINTY_COMPONENT,
        )

    def test_valid_direct_measurand_budget_is_satisfied_and_serialized(self) -> None:
        model = build_direct_budget_model()
        evaluation = evaluate_measurement_model(model)
        self.assertEqual(evaluation.uncertainty_status, SATISFIED)
        self.assertEqual(evaluation.uncertainty_gaps, ())
        serialized = measurement_model_record(model)["uncertainty_model"]
        self.assertEqual(
            serialized["uncertainty_basis"],
            DIRECT_MEASURAND_CONTRIBUTIONS,
        )
        self.assertEqual(
            serialized["component_ids"],
            ["relative_component_a", "relative_component_b"],
        )

    def test_direct_budget_component_inventory_fails_closed(self) -> None:
        model = build_direct_budget_model()
        uncertainty = model.uncertainty_model
        assert uncertainty is not None

        with self.subTest(defect="empty"):
            with self.assertRaisesRegex(
                BridgeValidationError,
                "requires at least one component",
            ):
                validate_measurement_model(
                    replace(
                        model,
                        uncertainty_model=replace(uncertainty, component_ids=()),
                    )
                )

        with self.subTest(defect="duplicate"):
            with self.assertRaisesRegex(
                BridgeValidationError,
                "duplicate uncertainty component identifier",
            ):
                replace(
                    uncertainty,
                    component_ids=("relative_component_a", "relative_component_a"),
                )

        with self.subTest(defect="unknown"):
            with self.assertRaisesRegex(
                BridgeValidationError,
                "unknown quantity or quantities",
            ):
                validate_measurement_model(
                    replace(
                        model,
                        uncertainty_model=replace(
                            uncertainty,
                            component_ids=("missing_component",),
                        ),
                    )
                )

        with self.subTest(defect="negative"):
            changed = replace_quantity(
                model,
                "relative_component_a",
                value=Decimal("-1"),
            )
            with self.assertRaisesRegex(
                BridgeValidationError,
                "component cannot be negative",
            ):
                validate_measurement_model(changed)

        with self.subTest(defect="unpopulated"):
            changed = replace_quantity(
                model,
                "relative_component_a",
                value=None,
            )
            with self.assertRaisesRegex(
                BridgeValidationError,
                "component is unpopulated",
            ):
                validate_measurement_model(changed)

        with self.subTest(defect="wrong_role"):
            changed = replace_quantity(
                model,
                "relative_component_a",
                role=MODEL_PARAMETER,
            )
            with self.assertRaisesRegex(
                BridgeValidationError,
                "must have uncertainty_component role",
            ):
                validate_measurement_model(changed)

        with self.subTest(defect="binary_float"):
            with self.assertRaisesRegex(TypeError, "binary floats"):
                replace_quantity(
                    model,
                    "relative_component_a",
                    value=1.0,
                )

    def test_direct_budget_components_must_have_one_allowed_dimension(self) -> None:
        model = build_direct_budget_model()
        mixed = replace_quantity(
            model,
            "relative_component_a",
            dimension=GRAVITATIONAL_CONSTANT,
            unit="m^3 kg^-1 s^-2",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "components must be homogeneous",
        ):
            validate_measurement_model(mixed)

        target_dimension = replace_quantity(
            model,
            "relative_component_a",
            dimension=GRAVITATIONAL_CONSTANT,
            unit="m^3 kg^-1 s^-2",
        )
        target_dimension = replace_quantity(
            target_dimension,
            "relative_component_b",
            dimension=GRAVITATIONAL_CONSTANT,
            unit="m^3 kg^-1 s^-2",
        )
        self.assertEqual(
            evaluate_measurement_model(target_dimension).uncertainty_status,
            SATISFIED,
        )

    def test_direct_component_cannot_carry_uncertainty_on_uncertainty(self) -> None:
        model = replace_quantity(
            build_direct_budget_model(),
            "relative_component_a",
            standard_uncertainty=Decimal("0.1"),
            uncertainty_unit="ppm",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "cannot carry uncertainty-on-uncertainty",
        ):
            validate_measurement_model(model)

    def test_direct_component_and_ancestor_cannot_enter_estimator_ancestry(self) -> None:
        model = build_direct_budget_model()
        cases = (
            ProvenanceEdge(
                "force_estimate",
                "relative_component_a",
                "model_input",
                "Forbidden direct contribution to the central estimator.",
            ),
            ProvenanceEdge(
                "relative_component_a",
                "angle_observation",
                "model_input",
                "Forbidden shared ancestor with the central estimator.",
            ),
        )
        for edge in cases:
            with self.subTest(edge=edge):
                changed = replace(
                    model,
                    metrological_edges=(*model.metrological_edges, edge),
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "component or component ancestor enters central estimator ancestry",
                ):
                    validate_measurement_model(changed)

    def test_external_comparison_record_cannot_be_a_direct_component(self) -> None:
        model = build_direct_budget_model()
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        for identifier in ("codata_2022_G", "post_estimation_comparison"):
            with self.subTest(identifier=identifier):
                changed = replace(
                    model,
                    uncertainty_model=replace(
                        uncertainty,
                        component_ids=(identifier,),
                    ),
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "external comparison reference or comparison node cannot be",
                ):
                    validate_measurement_model(changed)

    def test_empirical_direct_component_requires_source_metadata(self) -> None:
        model = replace(
            build_direct_budget_model(),
            evidence_level=EMPIRICAL_RECORD,
        )
        cases = (
            ({"provenance_evidence": STRUCTURAL_PLACEHOLDER}, "documented provenance"),
            ({"source_identifier": None}, "source identifier"),
            ({"edition": None}, "source edition"),
            ({"access_date": None}, "source access date"),
        )
        for changes, missing_label in cases:
            with self.subTest(missing=missing_label):
                changed = replace_quantity(
                    model,
                    "relative_component_a",
                    **changes,
                )
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "source provenance metadata for relative_component_a.*missing "
                    f"{missing_label}",
                ):
                    validate_measurement_model(changed)

    def test_direct_budget_requires_target_standard_uncertainty_and_unit(self) -> None:
        model = build_direct_budget_model()
        missing = replace_quantity(
            model,
            "G_hat",
            standard_uncertainty=None,
            uncertainty_unit=None,
        )
        evaluation = evaluate_measurement_model(missing)
        self.assertEqual(evaluation.uncertainty_status, INCOMPLETE)
        self.assertIn(
            "target standard uncertainty is missing",
            evaluation.uncertainty_gaps,
        )

        wrong_unit = replace_quantity(
            model,
            "G_hat",
            uncertainty_unit="wrong-unit",
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "uncertainty unit must match the target unit",
        ):
            evaluate_measurement_model(wrong_unit)

    def test_direct_budget_rejects_unresolved_method_and_covariance_policy(self) -> None:
        model = build_direct_budget_model()
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        cases = (
            (
                "propagation_method",
                replace(uncertainty, propagation_method="required_but_unpopulated"),
                "propagation method is unpopulated",
            ),
            (
                "correlation_policy",
                replace(
                    uncertainty,
                    correlation_policy="required_but_unpopulated",
                    zero_correlation_justification=None,
                ),
                "empty direct-measurand covariance table requires",
            ),
        )
        for label, changed_uncertainty, diagnostic in cases:
            with self.subTest(field=label):
                with self.assertRaisesRegex(BridgeValidationError, diagnostic):
                    evaluate_measurement_model(
                        replace(model, uncertainty_model=changed_uncertainty)
                    )

        with self.assertRaisesRegex(
            BridgeValidationError,
            "covariance_matrix policy requires covariance declarations",
        ):
            replace(
                uncertainty,
                correlation_policy=COVARIANCE_MATRIX,
                correlations=(),
                zero_correlation_justification=None,
            )

    def test_direct_budget_covariances_may_reference_components_only(self) -> None:
        model = build_direct_budget_model()
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        covariance = CorrelationDeclaration(
            "relative_component_a",
            "relative_component_b",
            Decimal("0.25"),
            "ppm^2",
        )
        populated = replace(
            uncertainty,
            correlation_policy=COVARIANCE_MATRIX,
            correlations=(covariance,),
            zero_correlation_justification=None,
        )
        self.assertEqual(
            evaluate_measurement_model(
                replace(model, uncertainty_model=populated)
            ).uncertainty_status,
            SATISFIED,
        )

        forbidden = replace(
            populated,
            correlations=(
                CorrelationDeclaration(
                    "relative_component_a",
                    "force_estimate",
                    Decimal("0.25"),
                    "ppm N",
                ),
            ),
        )
        with self.assertRaisesRegex(
            BridgeValidationError,
            "covariance refers to unknown uncertainty input",
        ):
            validate_measurement_model(
                replace(model, uncertainty_model=forbidden)
            )

    def test_uncertainty_basis_fields_cannot_be_mixed(self) -> None:
        direct = build_direct_budget_model()
        uncertainty = direct.uncertainty_model
        assert uncertainty is not None
        for field, identifiers in (
            ("input_ids", ("force_estimate",)),
            ("correction_ids", ("alignment_correction",)),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    BridgeValidationError,
                    "cannot declare estimator inputs or corrections",
                ):
                    validate_measurement_model(
                        replace(
                            direct,
                            uncertainty_model=replace(
                                uncertainty,
                                **{field: identifiers},
                            ),
                        )
                    )

        legacy = build_inverse_square_model()
        legacy_uncertainty = legacy.uncertainty_model
        assert legacy_uncertainty is not None
        with self.assertRaisesRegex(
            BridgeValidationError,
            "unknown uncertainty basis",
        ):
            replace(legacy_uncertainty, uncertainty_basis="unknown")
        with self.assertRaisesRegex(
            BridgeValidationError,
            "component IDs require direct_measurand_contributions",
        ):
            validate_measurement_model(
                replace(
                    legacy,
                    uncertainty_model=replace(
                        legacy_uncertainty,
                        component_ids=("force_estimate",),
                    ),
                )
            )

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
