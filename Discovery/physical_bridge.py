"""Public facade, artifact builders, and CLI for the physical bridge to ``G``.

Established imports are re-exported from the dedicated schema and validation modules.
This module retains model/example construction, deterministic serialization, and
``python -m Discovery.physical_bridge`` behavior. It deliberately does not ingest
observations or calculate a measured value of ``G``.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

from Discovery.dimensions import (
    DIMENSIONLESS,
    FORCE,
    GRAVITATIONAL_CONSTANT,
    LENGTH,
    MASS,
)
from Discovery.physical_bridge_schema import (
    ALGEBRAIC_PROVENANCE_KINDS,
    CALIBRATED_MEASUREMENT,
    CORRECTION,
    CORRELATION_POLICIES,
    COVARIANCE_MATRIX,
    DECLARED_LOCAL_ATOM,
    DEFAULT_CONTRACT_OUTPUT,
    DEFAULT_EXAMPLE_OUTPUT,
    DEFINITION,
    DEFINITION_EDGE_KINDS,
    DERIVED_QUANTITY,
    DIRECT_MEASURAND_CONTRIBUTIONS,
    DIRECT_OBSERVATION,
    DOCUMENTED,
    EMPIRICAL_RECORD,
    ESTIMATOR_INPUT_PROPAGATION,
    EVIDENCE_LEVELS,
    EXPLICIT_ZERO_ASSUMPTION,
    EXTERNAL_COMPARISON_REFERENCE,
    INCOMPLETE,
    INPUT_ROLES,
    LEAN_THEOREM_CATALOG,
    LEAN_THEOREMS_BY_ID,
    METROLOGICAL_EDGE_KINDS,
    MODEL_PARAMETER,
    NO_REGISTERED_TARGET_PATH,
    NOT_APPLICABLE,
    PROVENANCE_EVIDENCE_VALUES,
    REGISTERED_EXPRESSION,
    REQUIRED_BUT_UNPOPULATED,
    SATISFIED,
    SCHEMA_VERSION,
    STRUCTURAL_EXAMPLE,
    STRUCTURAL_PLACEHOLDER,
    TARGET_KEY,
    TARGET_OUTPUT,
    TARGET_PATH_DETECTED,
    UNCERTAINTY_BASES,
    UNCERTAINTY_COMPONENT,
    UNRESOLVED,
    UNRESOLVED_ALGEBRAIC_PROVENANCE,
    UNRESOLVED_PROVENANCE_EVIDENCE,
    BridgeEvaluation,
    BridgeValidationError,
    CorrelationDeclaration,
    EstimatorTerm,
    LeanTheoremLink,
    MeasurementModel,
    ProvenanceEdge,
    QuantityRecord,
    TargetPathAudit,
    UncertaintyModel,
    decimal_text,
    dimension_record,
    fraction_text,
    signature_record,
)
from Discovery.physical_bridge_validation import (
    _audit_quantity,
    _quantity_map,
    audit_registered_target_path,
    build_model_dependency_catalog,
    evaluate_measurement_model,
    validate_measurement_model,
)


def _quantity_record(quantity: QuantityRecord) -> dict[str, Any]:
    return {
        "identifier": quantity.identifier,
        "symbol": quantity.symbol,
        "role": quantity.role,
        "dimension": dimension_record(quantity.dimension),
        "unit": quantity.unit,
        "description": quantity.description,
        "algebraic_provenance": {
            "kind": quantity.algebraic_provenance_kind,
            "surface_signature": (
                None
                if quantity.registered_dependency_signature is None
                else signature_record(quantity.registered_dependency_signature)
            ),
            "caution": (
                "Atomic or target-clean status in this catalog does not establish "
                "metrological independence."
            ),
        },
        "metrological_provenance_evidence": quantity.provenance_evidence,
        "numerical_record": {
            "value_decimal": decimal_text(quantity.value),
            "standard_uncertainty_decimal": decimal_text(
                quantity.standard_uncertainty
            ),
            "uncertainty_unit": quantity.uncertainty_unit,
            "exact": quantity.exact,
        },
        "source": {
            "identifier": quantity.source_identifier,
            "edition": quantity.edition,
            "access_date": quantity.access_date,
        },
    }


def _edge_record(edge: ProvenanceEdge) -> dict[str, str]:
    return {
        "child": edge.child,
        "parent": edge.parent,
        "kind": edge.kind,
        "explanation": edge.explanation,
    }


def _audit_record(audit: TargetPathAudit) -> dict[str, Any]:
    return {
        "identifier": audit.identifier,
        "status": audit.status,
        "surface_signature": signature_record(audit.surface_signature),
        "expanded_signature": signature_record(audit.expanded_signature),
        "unresolved_factors": list(audit.unresolved_factors),
        "power_of_G": fraction_text(audit.power_of_target),
        "explanation": audit.explanation,
    }


def _uncertainty_record(uncertainty: UncertaintyModel | None) -> dict[str, Any] | None:
    if uncertainty is None:
        return None
    record = {
        "measurand_id": uncertainty.measurand_id,
        "input_ids": sorted(uncertainty.input_ids),
        "correction_ids": sorted(uncertainty.correction_ids),
        "correlation_policy": uncertainty.correlation_policy,
        "correlations": [
            {
                "left": record.left,
                "right": record.right,
                "covariance_decimal": decimal_text(record.covariance),
                "covariance_unit": record.covariance_unit,
            }
            for record in sorted(
                uncertainty.correlations,
                key=lambda item: (min(item.left, item.right), max(item.left, item.right)),
            )
        ],
        "zero_correlation_justification": (
            uncertainty.zero_correlation_justification
        ),
        "propagation_method": uncertainty.propagation_method,
        "coverage": {
            "factor_decimal": decimal_text(uncertainty.coverage_factor),
            "probability_decimal": decimal_text(uncertainty.coverage_probability),
            "basis": uncertainty.coverage_basis,
        },
        "limitations": list(uncertainty.limitations),
    }
    if uncertainty.uncertainty_basis == DIRECT_MEASURAND_CONTRIBUTIONS:
        record["uncertainty_basis"] = uncertainty.uncertainty_basis
        record["component_ids"] = sorted(uncertainty.component_ids)
    return record


def _lean_record(identifier: str | None) -> dict[str, Any] | None:
    if identifier is None:
        return None
    theorem = LEAN_THEOREMS_BY_ID[identifier]
    return {
        "catalog_identifier": theorem.identifier,
        "fully_qualified_name": theorem.fully_qualified_name,
        "relation": theorem.relation,
        "conditional_scope": theorem.conditional_scope,
        "estimator_rearrangement_certified": (
            theorem.estimator_rearrangement_certified
        ),
        "nonclaim": (
            "The link does not certify that observations occurred, an apparatus obeyed "
            "the model, calibrations were correct, or uncertainties are complete."
        ),
    }


def measurement_model_record(model: MeasurementModel) -> dict[str, Any]:
    """Return a deterministic machine-readable model and its assessments."""

    evaluation = evaluate_measurement_model(model)
    quantities = _quantity_map(model)
    comparison_audits = []
    catalog = build_model_dependency_catalog(model)
    for identifier in sorted(model.comparison_reference_ids):
        comparison_audits.append(
            _audit_record(_audit_quantity(quantities[identifier], catalog))
        )

    target_path_audit = {
        "gate_result": evaluation.registered_target_path_status,
        "estimator_upstream_node_ids": list(evaluation.estimator_upstream_ids),
        "estimator_upstream_assessments": [
            _audit_record(audit) for audit in evaluation.target_path_audits
        ],
        "isolated_comparison_reference_assessments": comparison_audits,
        "required_caution": (
            "No registered algebraic path to G is necessary for a target-clean "
            "input, but it is not sufficient to establish experimental independence."
        ),
    }
    uncertainty = model.uncertainty_model
    if (
        uncertainty is not None
        and uncertainty.uncertainty_basis == DIRECT_MEASURAND_CONTRIBUTIONS
    ):
        target_path_audit["uncertainty_component_upstream_node_ids"] = list(
            evaluation.uncertainty_component_upstream_ids
        )
        target_path_audit["uncertainty_component_assessments"] = [
            _audit_record(audit)
            for audit in evaluation.uncertainty_component_target_path_audits
        ]

    assessments = {
        "dimensional_status": evaluation.dimensional_status,
        "algebraic_model_status": evaluation.algebraic_model_status,
        "registered_target_path_status": evaluation.registered_target_path_status,
        "metrological_provenance_status": (
            evaluation.metrological_provenance_status
        ),
        "uncertainty_status": evaluation.uncertainty_status,
        "empirical_population_status": evaluation.empirical_population_status,
        "replication_status": evaluation.replication_status,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": "inverse-square physical bridge structural example",
        "model_identifier": model.identifier,
        "scope_and_evidence_level": {
            "evidence_level": model.evidence_level,
            "classification": "structural_measurement_model_skeleton",
            "empirical_determination": False,
            "statement": (
                "This record validates a contract shape. It contains no experimental "
                "dataset and reports no measured value of G."
            ),
        },
        "target_measurand": {
            "quantity_id": model.target_measurand_id,
            "symbolic_key": model.target_symbolic_key,
            "dimension": dimension_record(
                quantities[model.target_measurand_id].dimension
            ),
            "unit": quantities[model.target_measurand_id].unit,
        },
        "measurement_model": {
            "theoretical_relation": model.theoretical_relation,
            "estimator_relation": model.estimator_relation,
            "domain_and_approximation_regime": list(
                model.domain_and_approximation_regime
            ),
            "required_hypotheses": list(model.required_hypotheses),
            "estimator_terms": [
                {
                    "quantity_id": term.quantity_id,
                    "exponent": fraction_text(term.exponent),
                }
                for term in sorted(
                    model.estimator_terms,
                    key=lambda item: item.quantity_id,
                )
            ],
            "estimator_dimension": dimension_record(
                evaluation.estimator_dimension
            ),
        },
        "quantities": [
            _quantity_record(quantities[identifier])
            for identifier in sorted(quantities)
        ],
        "provenance_graphs": {
            "edge_direction": "child depends on parent",
            "combined_cycle_status": "acyclic",
            "definitional": {
                "cycle_status": "acyclic",
                "edges": [
                    _edge_record(edge)
                    for edge in sorted(
                        model.definition_edges,
                        key=lambda item: (item.child, item.parent, item.kind),
                    )
                ],
            },
            "metrological": {
                "cycle_status": "acyclic",
                "edges": [
                    _edge_record(edge)
                    for edge in sorted(
                        model.metrological_edges,
                        key=lambda item: (item.child, item.parent, item.kind),
                    )
                ],
                "calibration_source_ids": sorted(model.calibration_source_ids),
                "correction_ids": sorted(model.correction_ids),
            },
        },
        "target_path_audit": target_path_audit,
        "external_comparison": {
            "reference_ids": sorted(model.comparison_reference_ids),
            "comparison_node_ids": sorted(model.comparison_node_ids),
            "isolation_rule": (
                "External G references may be consumed only by terminal "
                "post-estimation comparison nodes. They cannot calibrate, correct, "
                "tune, accept, or reject an estimate."
            ),
        },
        "uncertainty_model": _uncertainty_record(model.uncertainty_model),
        "uncertainty_gaps": list(evaluation.uncertainty_gaps),
        "lean_linkage": _lean_record(model.lean_link_identifier),
        "assessments": assessments,
        "replication_identifiers": list(model.replication_identifiers),
        "limitations": list(model.limitations),
        "nonclaims": list(model.nonclaims),
    }


LITERATURE_IDENTIFIERS = (
    {
        "identifier": "rothleitner_schlamminger_2017_review",
        "document_type": "peer_reviewed_review",
        "doi": "10.1063/1.4994619",
    },
    {
        "identifier": "gundlach_merkowitz_2000",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1103/PhysRevLett.85.2869",
    },
    {
        "identifier": "schlamminger_et_al_2006",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1103/PhysRevD.74.082001",
    },
    {
        "identifier": "rosi_et_al_2014",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1038/nature13433",
    },
    {
        "identifier": "li_et_al_2018",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1038/s41586-018-0431-5",
    },
    {
        "identifier": "codata_2022_adjustment",
        "document_type": "adjusted_external_comparison_reference",
        "doi": "10.1063/5.0279860",
    },
    {
        "identifier": "jcgm_100_2008",
        "document_type": "authoritative_metrology_standard",
        "url": "https://www.bipm.org/en/committees/jc/jcgm/publications",
    },
    {
        "identifier": "jcgm_200_2012",
        "document_type": "authoritative_metrology_vocabulary",
        "doi": "10.59161/JCGM200-2012",
    },
    {
        "identifier": "bipm_si_brochure_2026",
        "document_type": "authoritative_si_reference",
        "doi": "10.59161/AUEZ1291",
    },
)


def build_inverse_square_model() -> MeasurementModel:
    """Build the unpopulated educational inverse-square bridge skeleton."""

    local = DECLARED_LOCAL_ATOM
    placeholder = STRUCTURAL_PLACEHOLDER
    quantities = (
        QuantityRecord(
            "alignment_correction",
            "delta_F_align",
            CORRECTION,
            FORCE,
            "N",
            local,
            None,
            placeholder,
            (
                "Structural placeholder for an alignment correction. A real value "
                "would carry its own standard uncertainty."
            ),
        ),
        QuantityRecord(
            "angle_observation",
            "theta_obs",
            DIRECT_OBSERVATION,
            DIMENSIONLESS,
            "rad",
            local,
            None,
            placeholder,
            (
                "Example lower-level observable showing that force must not be "
                "treated as an unexplained number."
            ),
        ),
        QuantityRecord(
            "codata_2022_G",
            "G_CODATA_2022",
            EXTERNAL_COMPARISON_REFERENCE,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            REGISTERED_EXPRESSION,
            (("G", Fraction(1)),),
            DOCUMENTED,
            (
                "CODATA 2022 adjusted value, isolated for post-estimation comparison "
                "only; it is not an estimator input or acceptance threshold."
            ),
            value=Decimal("6.67430e-11"),
            standard_uncertainty=Decimal("1.5e-15"),
            uncertainty_unit="m^3 kg^-1 s^-2",
            source_identifier="doi:10.1063/5.0279860",
            edition="2022 CODATA adjustment, published 2025",
            access_date="2026-08-30",
        ),
        QuantityRecord(
            "force_estimate",
            "F_hat",
            DERIVED_QUANTITY,
            FORCE,
            "N",
            local,
            None,
            placeholder,
            (
                "Force inferred from lower-level observations, calibration, and a "
                "correction; not a direct or populated force reading."
            ),
        ),
        QuantityRecord(
            "force_reference",
            "F_ref",
            DEFINITION,
            FORCE,
            "N",
            local,
            None,
            placeholder,
            "Placeholder force-scale realization or calibration reference.",
        ),
        QuantityRecord(
            "G_hat",
            "G_hat",
            TARGET_OUTPUT,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            local,
            None,
            placeholder,
            "Unpopulated target output of the estimator.",
        ),
        QuantityRecord(
            "length_reference",
            "L_ref",
            DEFINITION,
            LENGTH,
            "m",
            local,
            None,
            placeholder,
            "Placeholder realization of the metre used by a calibration chain.",
        ),
        QuantityRecord(
            "mass_1",
            "m_1",
            CALIBRATED_MEASUREMENT,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Unpopulated calibrated estimate of the first mass.",
        ),
        QuantityRecord(
            "mass_1_observation",
            "m_1_obs",
            DIRECT_OBSERVATION,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Structural balance or comparator observation for the first mass.",
        ),
        QuantityRecord(
            "mass_2",
            "m_2",
            CALIBRATED_MEASUREMENT,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Unpopulated calibrated estimate of the second mass.",
        ),
        QuantityRecord(
            "mass_2_observation",
            "m_2_obs",
            DIRECT_OBSERVATION,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Structural balance or comparator observation for the second mass.",
        ),
        QuantityRecord(
            "mass_reference",
            "M_ref",
            DEFINITION,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Placeholder realization or calibrated standard of the kilogram.",
        ),
        QuantityRecord(
            "post_estimation_comparison",
            "G_hat_minus_G_ref",
            DERIVED_QUANTITY,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            local,
            None,
            placeholder,
            (
                "Terminal comparison node. It cannot feed the estimator, calibration, "
                "corrections, or an acceptance decision."
            ),
        ),
        QuantityRecord(
            "separation",
            "r",
            CALIBRATED_MEASUREMENT,
            LENGTH,
            "m",
            local,
            None,
            placeholder,
            "Unpopulated calibrated centre-to-centre separation estimate.",
        ),
        QuantityRecord(
            "separation_observation",
            "r_obs",
            DIRECT_OBSERVATION,
            LENGTH,
            "m",
            local,
            None,
            placeholder,
            "Structural position or distance observation.",
        ),
    )

    definition_edges = (
        ProvenanceEdge(
            "G_hat",
            "force_estimate",
            "definition",
            "The estimator numerator contains the inferred force.",
        ),
        ProvenanceEdge(
            "G_hat",
            "separation",
            "definition",
            "The estimator contains the squared separation.",
        ),
        ProvenanceEdge(
            "G_hat",
            "mass_1",
            "definition",
            "The first mass appears in the estimator denominator.",
        ),
        ProvenanceEdge(
            "G_hat",
            "mass_2",
            "definition",
            "The second mass appears in the estimator denominator.",
        ),
    )
    metrological_edges = (
        ProvenanceEdge(
            "alignment_correction",
            "angle_observation",
            "correction",
            "The alignment correction depends on the observed angular geometry.",
        ),
        ProvenanceEdge(
            "alignment_correction",
            "separation_observation",
            "correction",
            "The alignment correction also depends on measured geometry.",
        ),
        ProvenanceEdge(
            "force_estimate",
            "alignment_correction",
            "correction",
            "The inferred force includes the declared correction and its uncertainty.",
        ),
        ProvenanceEdge(
            "force_estimate",
            "angle_observation",
            "observation_derivation",
            "A real apparatus can infer force from angle, torque, or acceleration data.",
        ),
        ProvenanceEdge(
            "force_estimate",
            "force_reference",
            "calibration",
            "The force inference requires a documented scale realization.",
        ),
        ProvenanceEdge(
            "mass_1",
            "mass_1_observation",
            "observation_derivation",
            "The calibrated mass estimate derives from an instrument observation.",
        ),
        ProvenanceEdge(
            "mass_1",
            "mass_reference",
            "calibration",
            "The first mass is related to a mass reference through calibration.",
        ),
        ProvenanceEdge(
            "mass_2",
            "mass_2_observation",
            "observation_derivation",
            "The calibrated mass estimate derives from an instrument observation.",
        ),
        ProvenanceEdge(
            "mass_2",
            "mass_reference",
            "calibration",
            "The second mass is related to a mass reference through calibration.",
        ),
        ProvenanceEdge(
            "post_estimation_comparison",
            "G_hat",
            "comparison",
            "Comparison occurs only after an estimate has been produced.",
        ),
        ProvenanceEdge(
            "post_estimation_comparison",
            "codata_2022_G",
            "comparison",
            "The adjusted reference is isolated in the terminal comparison node.",
        ),
        ProvenanceEdge(
            "separation",
            "length_reference",
            "calibration",
            "The separation estimate is traceable through a length calibration.",
        ),
        ProvenanceEdge(
            "separation",
            "separation_observation",
            "observation_derivation",
            "The calibrated separation derives from an instrument observation.",
        ),
    )

    uncertainty = UncertaintyModel(
        measurand_id="G_hat",
        input_ids=("force_estimate", "mass_1", "mass_2", "separation"),
        correction_ids=("alignment_correction",),
        correlation_policy=REQUIRED_BUT_UNPOPULATED,
        correlations=(),
        zero_correlation_justification=None,
        propagation_method=REQUIRED_BUT_UNPOPULATED,
        coverage_factor=None,
        coverage_probability=None,
        coverage_basis="not applicable until an empirical estimate exists",
        limitations=(
            "The record validates required uncertainty fields but does not propagate uncertainty.",
            "A correction never implies that the corrected systematic effect has zero uncertainty.",
        ),
    )

    return MeasurementModel(
        identifier="educational_inverse_square_bridge_v1",
        target_measurand_id="G_hat",
        target_symbolic_key="G",
        theoretical_relation="F = G * m_1 * m_2 / r^2",
        estimator_relation="G_hat = F_hat * r^2 / (m_1 * m_2)",
        domain_and_approximation_regime=(
            "Newtonian weak-field, low-velocity educational scalar model",
            "masses represented by an explicitly documented geometry and separation",
            "apparatus-specific force inference and corrections must be supplied recursively",
        ),
        required_hypotheses=(
            "the stated inverse-square measurement model is adequate in the declared regime",
            "mass_1, mass_2, and separation are nonzero",
            "the force inference, geometry model, calibrations, and corrections are documented",
            "all material uncertainty contributions and correlations are evaluated",
        ),
        quantities=quantities,
        estimator_terms=(
            EstimatorTerm("force_estimate", Fraction(1)),
            EstimatorTerm("separation", Fraction(2)),
            EstimatorTerm("mass_1", Fraction(-1)),
            EstimatorTerm("mass_2", Fraction(-1)),
        ),
        definition_edges=definition_edges,
        metrological_edges=metrological_edges,
        calibration_source_ids=(
            "force_reference",
            "length_reference",
            "mass_reference",
        ),
        correction_ids=("alignment_correction",),
        comparison_reference_ids=("codata_2022_G",),
        comparison_node_ids=("post_estimation_comparison",),
        uncertainty_model=uncertainty,
        lean_link_identifier="conditional_inverse_square_estimator_correctness",
        evidence_level=STRUCTURAL_EXAMPLE,
        replication_identifiers=(),
        limitations=(
            "This is not a complete torsion-balance, beam-balance, or atom-interferometer model.",
            (
                "The force-estimation submodel is represented by provenance edges, "
                "not an apparatus equation."
            ),
            "No instrument serial number, calibration certificate, observation, or dataset is present.",
            "No acceptance threshold is defined by comparison with CODATA or any other reference G.",
        ),
        nonclaims=(
            "No value of G is measured or inferred by this artifact.",
            "No apparatus is validated.",
            "No target-clean algebraic status is called experimental independence.",
            "No Lean theorem is treated as evidence that an observation occurred.",
            "No uncertainty is fabricated as zero when information is missing.",
        ),
    )


def _theorem_catalog_record() -> list[dict[str, Any]]:
    return [
        {
            "identifier": theorem.identifier,
            "fully_qualified_name": theorem.fully_qualified_name,
            "relation": theorem.relation,
            "conditional_scope": theorem.conditional_scope,
            "estimator_rearrangement_certified": (
                theorem.estimator_rearrangement_certified
            ),
        }
        for theorem in LEAN_THEOREM_CATALOG
    ]


def build_contract_artifact() -> dict[str, Any]:
    """Build the deterministic Milestone 4 physical-bridge contract."""

    target_controls = []
    for key in ("G", "l_P", "m_P", "t_P", "T_P"):
        target_controls.append(
            _audit_record(
                audit_registered_target_path(
                    ((key, Fraction(1)),),
                    identifier=key,
                )
            )
        )
    if any(record["status"] != TARGET_PATH_DETECTED for record in target_controls):
        raise RuntimeError("a required direct or Planck target-path control changed")

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": "physical bridge contract for G",
        "scope_and_evidence_level": {
            "milestone": 4,
            "evidence_level": "contract_definition",
            "operational_definition": (
                "Produce a non-circular, traceable, uncertainty-qualified estimate of "
                "G from documented observations under an explicitly stated physical "
                "measurement model, followed by reproducibility and preferably "
                "comparison across methods with materially different systematic effects."
            ),
            "supplied_here": (
                "validated schema, graph rules, target-leakage gate, exact dimensional "
                "check, uncertainty requirements, and an unpopulated structural example"
            ),
            "not_supplied_here": (
                "observations, apparatus validation, a propagated uncertainty, an "
                "empirical estimate, or replication"
            ),
        },
        "evidence_layers": [
            {
                "layer": "dimensional_compatibility",
                "meaning": "same units as G; necessary but neither a law nor a value",
            },
            {
                "layer": "definitional_identity",
                "meaning": "exact reduction under registered definitions; may be circular",
            },
            {
                "layer": "theoretical_measurement_model",
                "meaning": "conditional relation between the measurand and operational inputs",
            },
            {
                "layer": "empirical_observation",
                "meaning": "external instrument or procedure readings; not proven by Lean",
            },
            {
                "layer": "metrological_traceability",
                "meaning": "documented calibration chain to a reference or unit realization",
            },
            {
                "layer": "uncertainty",
                "meaning": "input, correction, covariance, propagation, and coverage model",
            },
            {
                "layer": "independent_comparison",
                "meaning": "post-estimation comparison across results or methods only",
            },
        ],
        "separate_assessment_axes": {
            "dimensional_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "algebraic_model_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "registered_target_path_status": [
                TARGET_PATH_DETECTED,
                NO_REGISTERED_TARGET_PATH,
                UNRESOLVED,
                NOT_APPLICABLE,
            ],
            "metrological_provenance_status": [
                SATISFIED,
                INCOMPLETE,
                UNRESOLVED,
                NOT_APPLICABLE,
            ],
            "uncertainty_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "empirical_population_status": [
                SATISFIED,
                INCOMPLETE,
                UNRESOLVED,
                NOT_APPLICABLE,
            ],
            "replication_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "single_score": "forbidden",
            "bare_independent_status": "forbidden",
        },
        "measurement_model_required_fields": [
            "model identifier",
            "target measurand",
            "theoretical relation",
            "estimator relation",
            "domain and approximation regime",
            "required hypotheses",
            "input quantities and roles",
            "units and exact dimensions",
            "definitional and metrological provenance edges",
            "calibration sources",
            "corrections and their uncertainties",
            "uncertainty and correlation policy",
            "external comparison references",
            "Lean theorem linkage when available",
            "limitations and nonclaims",
        ],
        "input_roles": list(INPUT_ROLES),
        "provenance_graph_contract": {
            "edge_direction": "child depends on parent",
            "definitional_cycles": "rejected",
            "metrological_cycles": "rejected",
            "cross_layer_cycles": "rejected",
            "unknown_parents": "rejected",
            "missing_required_provenance": "unresolved or rejected; never clean",
            "graph_order": "deterministically sorted by child, parent, and edge kind",
        },
        "target_clean_gate": {
            "rules": [
                "reject a direct G estimator input",
                "reject any registered input expansion with nonzero power of G",
                "reject any estimator ancestor whose registered expansion reaches G",
                (
                    "reject any direct uncertainty component or component ancestor whose "
                    "registered expansion reaches G"
                ),
                "reject a calibration or correction chain that consumes reference G",
                "treat unresolved provenance as unresolved",
                "permit reference G only in isolated terminal comparison nodes",
                "fail closed when required provenance is absent",
            ],
            "required_caution": (
                "No registered algebraic path to G is necessary for a target-clean "
                "input, but it is not sufficient to establish experimental independence."
            ),
            "atomic_catalog_caution": (
                "Atomic means only that the current algebraic catalog stops expanding. "
                "It does not establish metrological independence."
            ),
            "required_target_dependent_controls": target_controls,
        },
        "uncertainty_requirements": {
            "required": [
                "measurand",
                "input estimates",
                "standard uncertainties",
                "units",
                "correlations or a documented zero-correlation justification",
                "corrections",
                "uncertainties associated with corrections",
                "propagation method",
                "coverage information when applicable",
            ],
            "missing_model_status": INCOMPLETE,
            "missing_uncertainty_is_zero": False,
            "binary_floating_point_measurement_values": "rejected",
            "exact_exponent_domain": "int or Fraction; bool and float rejected",
            "schema_extension_policy": (
                "The direct-contribution fields are additive. Legacy estimator-input "
                "records omit them and retain their existing serialization."
            ),
            "uncertainty_bases": {
                ESTIMATOR_INPUT_PROPAGATION: {
                    "meaning": (
                        "Propagate standard uncertainties from the central estimator "
                        "inputs and declared corrections."
                    ),
                    "component_ids": "forbidden",
                },
                DIRECT_MEASURAND_CONTRIBUTIONS: {
                    "meaning": (
                        "Combine published contributions already expressed for the "
                        "final measurand without relabeling them as estimator inputs."
                    ),
                    "input_ids": "must be empty",
                    "correction_ids": "must be empty",
                    "component_role": UNCERTAINTY_COMPONENT,
                    "component_dimensions": (
                        "homogeneous dimensionless relative contributions or "
                        "homogeneous target-dimension contributions"
                    ),
                    "eligibility": (
                        "chosen only when a pinned publication reports contributions "
                        "already expressed for the final measurand; validator acceptance "
                        "does not establish eligibility"
                    ),
                    "target_path_scope": (
                        "every declared component and its full provenance closure is "
                        "audited for registered paths to G"
                    ),
                    "scientific_completeness": (
                        "must be established by an apparatus-specific validator"
                    ),
                },
            },
        },
        "external_reference_boundary": {
            "allowed_role": EXTERNAL_COMPARISON_REFERENCE,
            "allowed_use": "isolated post-estimation comparison",
            "forbidden_uses": [
                "estimator input",
                "calibration",
                "correction",
                "candidate tuning",
                "acceptance threshold",
            ],
            "checked_in_metadata": [
                "edition",
                "source",
                "units",
                "standard uncertainty",
                "access date",
            ],
        },
        "lean_boundary": {
            "explicit_catalog": _theorem_catalog_record(),
            "source_parsing": "forbidden",
            "can_establish": (
                "conditional algebraic implications from explicit hypotheses and "
                "nonzero side conditions"
            ),
            "cannot_establish": [
                "that the physical model is complete",
                "that an instrument behaved as modeled",
                "that a reading occurred",
                "that calibrations are correct",
                "that every systematic effect is covered",
                "that nature selected a dimensional candidate",
            ],
        },
        "literature_identifiers": list(LITERATURE_IDENTIFIERS),
        "limitations_and_nonclaims": [
            "The contract does not contain a real experimental dataset.",
            "The contract does not report a new or recommended value of G.",
            "The structural example is not an empirical determination.",
            "Passing the algebraic target gate is weaker than experimental independence.",
            "Cross-method agreement is evidence beyond repeated algebra, not logical proof.",
        ],
    }


def build_example_artifact() -> dict[str, Any]:
    return measurement_model_record(build_inverse_square_model())


def serialize_artifact(artifact: dict[str, Any]) -> str:
    """Serialize with deterministic key order and exactly one final newline."""

    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract-output",
        type=Path,
        default=DEFAULT_CONTRACT_OUTPUT,
    )
    parser.add_argument(
        "--example-output",
        type=Path,
        default=DEFAULT_EXAMPLE_OUTPUT,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when either committed artifact is stale",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    outputs = (
        (args.contract_output, serialize_artifact(build_contract_artifact())),
        (args.example_output, serialize_artifact(build_example_artifact())),
    )
    if args.check:
        stale = [
            path
            for path, rendered in outputs
            if not path.exists() or path.read_text(encoding="utf-8") != rendered
        ]
        if stale:
            for path in stale:
                print(f"stale or missing physical bridge artifact: {path}", file=sys.stderr)
            raise SystemExit(1)
        print("Physical bridge artifacts are current and byte-stable.")
        return

    for path, rendered in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        print(f"Wrote physical bridge artifact to {path}.")
    print("The inverse-square example is structural and contains no measured value of G.")


if __name__ == "__main__":
    main()
