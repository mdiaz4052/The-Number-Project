"""Empirical central-value MeasurementModels for the HUST 2018 AAF experiments.

The source-availability audit remains the authorization boundary.  This module
populates three separate depth-2a MeasurementModels from the already audited
public summary inputs.  It does not construct the combined AAF estimator and it
does not manufacture a target uncertainty.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from Discovery.dimensions import (
    DIMENSIONLESS,
    GRAVITATIONAL_CONSTANT,
    LENGTH,
    MASS,
    TIME,
)
from Discovery.hust_2018_aaf_source_audit import (
    DEFAULT_OUTPUT as SOURCE_AUDIT_OUTPUT,
    EXPECTED_EXPERIMENTS,
    PUBLIC_DIRECT,
    REQUIRED_INPUTS_PATH,
    load_audit_manifest,
    load_required_inputs,
    validate_audit_manifest_record,
    validate_required_inputs_graph,
)
from Discovery.physical_bridge import measurement_model_record
from Discovery.physical_bridge_schema import (
    CORRECTION,
    DECLARED_LOCAL_ATOM,
    DERIVED_QUANTITY,
    DIRECT_OBSERVATION,
    DOCUMENTED,
    EMPIRICAL_RECORD,
    EXTERNAL_COMPARISON_REFERENCE,
    MODEL_PARAMETER,
    NO_REGISTERED_TARGET_PATH,
    REGISTERED_EXPRESSION,
    TARGET_OUTPUT,
    BridgeValidationError,
    EstimatorTerm,
    MeasurementModel,
    ProvenanceEdge,
    QuantityRecord,
)
from Discovery.physical_bridge_validation import evaluate_measurement_model


MODEL_ARTIFACT_SCHEMA_VERSION = 1
PREREGISTRATION_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_measurement_model_preregistration_v1.md"
)
PREREGISTRATION_SHA256 = (
    "5becdb7cfc6daed8a1a6c47cfeede18d5349ee2820197d8c3d17a5b61b705a62"
)
DEFAULT_OUTPUT = Path(
    "Experiments/GMeasurements/hust_2018_aaf_measurement_models_v1.json"
)
SOURCE_IDENTIFIER = "doi:10.1038/s41586-018-0431-5"
SOURCE_EDITION = "Li et al. 2018 Nature 560 Supplementary Information"
SOURCE_ACCESS_DATE = "2026-09-03"
PROJECT_EDITION = "The Number Project HUST AAF MeasurementModel preregistration v1"
P_SUM_DIMENSION = MASS / LENGTH**3
ANGULAR_ACCELERATION_DIMENSION = TIME**-2

EXPECTED_ASSESSMENTS = {
    "dimensional_status": "satisfied",
    "algebraic_model_status": "satisfied",
    "registered_target_path_status": NO_REGISTERED_TARGET_PATH,
    "metrological_provenance_status": "satisfied",
    "uncertainty_status": "incomplete",
    "empirical_population_status": "satisfied",
    "replication_status": "incomplete",
}

NONCLAIMS = (
    "These records reconstruct published HUST AAF central values; they are not new laboratory measurements.",
    "Depth 2a does not reconstruct or propagate the complete HUST uncertainty budget.",
    "No target standard uncertainty is reported for G_hat.",
    "No combined AAF estimator is authorized or constructed.",
    "No replication claim is made by these records.",
    "Published HUST G values are isolated terminal comparison references and never estimator inputs.",
    "Numerical agreement with the publication is not an acceptance criterion.",
)


class HUSTMeasurementModelError(ValueError):
    """Controlled failure of the HUST-specific empirical model contract."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def verify_preregistration(root: Path = Path(".")) -> dict[str, str]:
    path = root / PREREGISTRATION_PATH
    try:
        content = path.read_bytes()
    except OSError as error:
        raise HUSTMeasurementModelError("HUST MeasurementModel preregistration is unavailable") from error
    actual = _sha256_bytes(content)
    if actual != PREREGISTRATION_SHA256:
        raise HUSTMeasurementModelError("HUST MeasurementModel preregistration hash mismatch")
    return {"path": PREREGISTRATION_PATH.as_posix(), "sha256": actual}


def _load_authorized_records(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_audit_manifest(root / SOURCE_AUDIT_OUTPUT)
    validate_audit_manifest_record(manifest, root=root)
    graph = load_required_inputs(root / REQUIRED_INPUTS_PATH)
    validate_required_inputs_graph(graph)
    return manifest, graph


def _depth_at_least_2a(depth: object) -> bool:
    return depth in {"2a", "2b", "3", "4"}


def _authorize_scope(scope: str, audit_manifest: Mapping[str, Any]) -> None:
    if scope not in EXPECTED_EXPERIMENTS:
        raise HUSTMeasurementModelError(f"unsupported or combined AAF scope: {scope}")
    if audit_manifest.get("decision") != "GO":
        raise HUSTMeasurementModelError("HUST source audit does not authorize empirical modeling")
    if not _depth_at_least_2a(audit_manifest.get("maximum_assessed_replication_depth")):
        raise HUSTMeasurementModelError("HUST source audit is below depth 2a")
    authorized = audit_manifest.get("depth_2a_authorized_experiments")
    if not isinstance(authorized, list) or scope not in authorized:
        raise HUSTMeasurementModelError(f"source audit does not authorize {scope}")
    if audit_manifest.get("combined_aaf_reconstruction_authorized") is not False:
        raise HUSTMeasurementModelError("combined AAF authorization boundary changed")


def _experiment_record(graph: Mapping[str, Any], scope: str) -> Mapping[str, Any]:
    experiments = graph.get("experiments")
    if not isinstance(experiments, list):
        raise HUSTMeasurementModelError("HUST required-input graph has no experiment list")
    matches = [
        record
        for record in experiments
        if isinstance(record, dict) and record.get("experiment_id") == scope
    ]
    if len(matches) != 1:
        raise HUSTMeasurementModelError(f"expected exactly one source record for {scope}")
    return matches[0]


def _node_map(experiment: Mapping[str, Any], scope: str) -> dict[str, Mapping[str, Any]]:
    nodes = experiment.get("nodes")
    if not isinstance(nodes, list):
        raise HUSTMeasurementModelError(f"{scope} has no source nodes")
    result: dict[str, Mapping[str, Any]] = {}
    for raw in nodes:
        if not isinstance(raw, dict):
            raise HUSTMeasurementModelError(f"{scope} source node is not an object")
        node_id = raw.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            raise HUSTMeasurementModelError(f"{scope} source node is missing its identifier")
        if node_id in result:
            raise HUSTMeasurementModelError(f"duplicate source node: {node_id}")
        result[node_id] = raw
    return result


def _direct_node(
    nodes: Mapping[str, Mapping[str, Any]], scope: str, suffix: str
) -> Mapping[str, Any]:
    node_id = f"{scope}:{suffix}"
    node = nodes.get(node_id)
    if node is None:
        raise HUSTMeasurementModelError(f"required HUST source node is missing: {node_id}")
    if node.get("evidence_type") != PUBLIC_DIRECT:
        raise HUSTMeasurementModelError(f"{node_id} is not PUBLIC_DIRECT")
    if node.get("source_id") != "supplementary_information":
        raise HUSTMeasurementModelError(f"{node_id} is not bound to Supplementary Information")
    tokens = node.get("source_scope_tokens")
    if not isinstance(tokens, list) or scope not in tokens:
        raise HUSTMeasurementModelError(f"source scope mismatch on {node_id}")
    return node


def _decimal_field(node: Mapping[str, Any], key: str, node_id: str) -> Decimal:
    try:
        return Decimal(str(node[key]))
    except (KeyError, ArithmeticError) as error:
        raise HUSTMeasurementModelError(f"invalid decimal field {key} on {node_id}") from error


def _published_uncertainty(comparison: Mapping[str, Any], scope: str) -> Decimal:
    value_text = comparison.get("value")
    digits = comparison.get("standard_uncertainty_last_digits")
    if not isinstance(value_text, str) or not isinstance(digits, str) or not digits.isdigit():
        raise HUSTMeasurementModelError(f"invalid published uncertainty record for {scope}")
    decimal_places = len(value_text.partition(".")[2])
    return Decimal(digits) * (Decimal(10) ** -decimal_places) * Decimal("1e-11")


def _certificate(scope: str, suffix: str) -> str:
    slug = scope.lower().replace("-", "-")
    return f"certificate:number-project/hust-2018-{slug}-{suffix}-v1"


def _source_description(node: Mapping[str, Any], label: str) -> str:
    locator = node.get("locator")
    if not isinstance(locator, str) or not locator:
        raise HUSTMeasurementModelError(f"{label} is missing its reviewed source locator")
    return f"Published HUST 2018 AAF summary input. Reviewed locator: {locator}"


def _build_model_from_records(
    scope: str,
    audit_manifest: Mapping[str, Any],
    graph: Mapping[str, Any],
) -> MeasurementModel:
    """Pure constructor used after the caller has supplied source-audit records."""

    _authorize_scope(scope, audit_manifest)
    validate_required_inputs_graph(graph)
    experiment = _experiment_record(graph, scope)
    nodes = _node_map(experiment, scope)
    p_node = _direct_node(nodes, scope, "p_sum")
    alpha_node = _direct_node(nodes, scope, "alpha_corrected")
    magnetic_node = _direct_node(nodes, scope, "magnetic_damper_ppm")

    if magnetic_node.get("correction_operator") != "multiply_by_1_plus_delta":
        raise HUSTMeasurementModelError(f"magnetic-damper operator changed for {scope}")
    if magnetic_node.get("correction_direction") != "increase_G":
        raise HUSTMeasurementModelError(f"magnetic-damper direction changed for {scope}")

    p_sum = _decimal_field(p_node, "value", f"{scope}:p_sum")
    alpha_table = _decimal_field(alpha_node, "value", f"{scope}:alpha_corrected")
    magnetic_ppm = _decimal_field(
        magnetic_node, "value", f"{scope}:magnetic_damper_ppm"
    )
    if p_sum == 0:
        raise HUSTMeasurementModelError(f"zero P_g sum for {scope}")

    with localcontext() as context:
        context.prec = 50
        correction_factor = Decimal(1) + magnetic_ppm * Decimal("1e-6")
        alpha_si = alpha_table * Decimal("1e-9")
        g_hat = alpha_si / p_sum * correction_factor

    comparison = experiment.get("published_comparison")
    if not isinstance(comparison, dict):
        raise HUSTMeasurementModelError(f"published comparison is missing for {scope}")
    try:
        published_g = Decimal(str(comparison["value"])) * Decimal("1e-11")
    except (KeyError, ArithmeticError) as error:
        raise HUSTMeasurementModelError(f"invalid published G comparison for {scope}") from error
    published_u = _published_uncertainty(comparison, scope)
    comparison_delta = g_hat - published_g

    p_id = f"{scope}:p_sum"
    alpha_table_id = f"{scope}:alpha_corrected"
    magnetic_id = f"{scope}:magnetic_damper_ppm"
    correction_id = f"{scope}:correction_factor"
    alpha_si_id = f"{scope}:alpha_si"
    target_id = f"{scope}:G_hat"
    published_id = f"{scope}:published_G"
    comparison_id = f"{scope}:comparison_delta"
    tag = scope.replace("-", "_")
    local = DECLARED_LOCAL_ATOM

    quantities = (
        QuantityRecord(
            p_id,
            f"P_sum_{tag}",
            MODEL_PARAMETER,
            P_SUM_DIMENSION,
            "kg m^-3",
            local,
            None,
            DOCUMENTED,
            _source_description(p_node, p_id),
            value=p_sum,
            standard_uncertainty=_decimal_field(p_node, "standard_uncertainty", p_id),
            uncertainty_unit="kg m^-3",
            source_identifier=SOURCE_IDENTIFIER,
            edition=SOURCE_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        ),
        QuantityRecord(
            alpha_table_id,
            f"alpha_table_{tag}",
            DIRECT_OBSERVATION,
            ANGULAR_ACCELERATION_DIMENSION,
            "nrad s^-2",
            local,
            None,
            DOCUMENTED,
            (
                _source_description(alpha_node, alpha_table_id)
                + " This is a published summary observable already stated to be air-density corrected; it is not raw time-series data."
            ),
            value=alpha_table,
            standard_uncertainty=_decimal_field(
                alpha_node, "standard_uncertainty", alpha_table_id
            ),
            uncertainty_unit="nrad s^-2",
            source_identifier=SOURCE_IDENTIFIER,
            edition=SOURCE_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        ),
        QuantityRecord(
            magnetic_id,
            f"delta_MD_ppm_{tag}",
            MODEL_PARAMETER,
            DIMENSIONLESS,
            "ppm",
            local,
            None,
            DOCUMENTED,
            (
                _source_description(magnetic_node, magnetic_id)
                + " The source audit separately pins the + correction direction."
            ),
            value=magnetic_ppm,
            standard_uncertainty=_decimal_field(
                magnetic_node, "standard_uncertainty", magnetic_id
            ),
            uncertainty_unit="ppm",
            source_identifier=SOURCE_IDENTIFIER,
            edition=SOURCE_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        ),
        QuantityRecord(
            correction_id,
            f"c_MD_{tag}",
            CORRECTION,
            DIMENSIONLESS,
            "1",
            local,
            None,
            DOCUMENTED,
            "Project-derived dimensionless correction factor c_MD = 1 + delta_MD_ppm * 1e-6 under the frozen preregistration.",
            value=correction_factor,
            source_identifier=_certificate(scope, "correction-factor"),
            edition=PROJECT_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        ),
        QuantityRecord(
            alpha_si_id,
            f"alpha_SI_{tag}",
            DERIVED_QUANTITY,
            ANGULAR_ACCELERATION_DIMENSION,
            "s^-2",
            local,
            None,
            DOCUMENTED,
            "Project-derived SI angular acceleration using the exact decimal conversion alpha_SI = alpha_table * 1e-9.",
            value=alpha_si,
            source_identifier=_certificate(scope, "alpha-si"),
            edition=PROJECT_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        ),
        QuantityRecord(
            target_id,
            f"G_hat_{tag}",
            TARGET_OUTPUT,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            local,
            None,
            DOCUMENTED,
            "Depth-2a reconstructed central value. No reconstructed combined standard uncertainty is authorized.",
            value=g_hat,
            standard_uncertainty=None,
            uncertainty_unit=None,
            exact=False,
        ),
        QuantityRecord(
            published_id,
            f"G_published_{tag}",
            EXTERNAL_COMPARISON_REFERENCE,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            REGISTERED_EXPRESSION,
            (("G", 1),),
            DOCUMENTED,
            "Published HUST 2018 individual AAF value, isolated for terminal post-estimation comparison only.",
            value=published_g,
            standard_uncertainty=published_u,
            uncertainty_unit="m^3 kg^-1 s^-2",
            source_identifier=SOURCE_IDENTIFIER,
            edition=SOURCE_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        ),
        QuantityRecord(
            comparison_id,
            f"delta_G_comparison_{tag}",
            DERIVED_QUANTITY,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            local,
            None,
            DOCUMENTED,
            "Terminal arithmetic difference G_hat - G_published. It is descriptive only and cannot feed acceptance or estimation.",
            value=comparison_delta,
        ),
    )

    definition_edges = (
        ProvenanceEdge(
            target_id,
            alpha_si_id,
            "definition",
            "The frozen estimator numerator contains the SI angular acceleration.",
        ),
        ProvenanceEdge(
            target_id,
            correction_id,
            "definition",
            "The frozen estimator multiplies by the magnetic-damper correction factor.",
        ),
        ProvenanceEdge(
            target_id,
            p_id,
            "definition",
            "The frozen estimator divides by the published P_g interaction sum.",
        ),
    )
    metrological_edges = (
        ProvenanceEdge(
            alpha_si_id,
            alpha_table_id,
            "observation_derivation",
            "Exact nrad-to-rad decimal unit conversion by 1e-9.",
        ),
        ProvenanceEdge(
            correction_id,
            magnetic_id,
            "correction",
            "Construct c_MD = 1 + delta_MD_ppm * 1e-6 with the audited positive correction direction.",
        ),
        ProvenanceEdge(
            comparison_id,
            target_id,
            "comparison",
            "Terminal comparison consumes the reconstructed central value only after estimation.",
        ),
        ProvenanceEdge(
            comparison_id,
            published_id,
            "comparison",
            "Terminal comparison consumes the published HUST value only after estimation.",
        ),
    )

    model = MeasurementModel(
        identifier=f"hust_2018_{tag.lower()}_central_value_v1",
        target_measurand_id=target_id,
        target_symbolic_key="G",
        theoretical_relation=(
            "For the HUST AAF summary estimator, G = alpha_t(2omega_d) / |sum_l P_g,l,2| with the documented magnetic-damper correction applied."
        ),
        estimator_relation="G_hat = alpha_SI * c_MD / p_sum",
        domain_and_approximation_regime=(
            f"HUST 2018 {scope} published AAF summary-observable reconstruction",
            "Supplementary Table 3 angular acceleration is used at the documented air-density-corrected summary level",
            "magnetic-damper correction uses the source-audited positive multiplicative direction",
            "raw time-series/run-level reduction is outside depth 2a",
        ),
        required_hypotheses=(
            "the source-audit GO/depth-2a authorization for this exact AAF scope remains current",
            "the published P_g interaction sum is nonzero",
            "the Supplementary Information estimator relation is adequate for the published summary quantities",
            "the exact 1e-9 and 1e-6 unit conversions are applied as preregistered",
            "the published comparison G is not used upstream of G_hat",
        ),
        quantities=quantities,
        estimator_terms=(
            EstimatorTerm(alpha_si_id, 1),
            EstimatorTerm(correction_id, 1),
            EstimatorTerm(p_id, -1),
        ),
        definition_edges=definition_edges,
        metrological_edges=metrological_edges,
        calibration_source_ids=(),
        correction_ids=(correction_id,),
        comparison_reference_ids=(published_id,),
        comparison_node_ids=(comparison_id,),
        uncertainty_model=None,
        lean_link_identifier=None,
        evidence_level=EMPIRICAL_RECORD,
        replication_identifiers=(),
        limitations=(
            "Depth 2a reconstructs only the published central value; the complete uncertainty/covariance budget is not reconstructed.",
            "The model begins from published summary quantities rather than raw torsion-balance time series.",
            "Input standard uncertainties are retained as source evidence but are not propagated into G_hat in this milestone.",
            "The Supplementary Information currently has one byte-pinned human semantic attestation in the project workflow.",
        ),
        nonclaims=NONCLAIMS,
    )
    validate_hust_aaf_model(model, scope)
    return model


def _quantity_map(model: MeasurementModel) -> dict[str, QuantityRecord]:
    return {quantity.identifier: quantity for quantity in model.quantities}


def validate_hust_aaf_model(model: MeasurementModel, scope: str) -> None:
    """Apply HUST-specific semantic gates in addition to generic bridge validation."""

    if scope not in EXPECTED_EXPERIMENTS:
        raise HUSTMeasurementModelError(f"invalid HUST model scope: {scope}")
    evaluation = evaluate_measurement_model(model)
    if model.evidence_level != EMPIRICAL_RECORD:
        raise HUSTMeasurementModelError("HUST central-value model must be an empirical_record")
    if model.uncertainty_model is not None:
        raise HUSTMeasurementModelError("depth-2a HUST model cannot claim a completed uncertainty model")
    if model.replication_identifiers:
        raise HUSTMeasurementModelError("depth-2a HUST model cannot claim replication")
    if model.lean_link_identifier is not None:
        raise HUSTMeasurementModelError("no Lean theorem is registered for the apparatus-specific AAF estimator")

    expected_prefix = scope + ":"
    cross_scope = [
        identifier
        for identifier in evaluation.estimator_upstream_ids
        if not identifier.startswith(expected_prefix)
    ]
    if cross_scope:
        raise HUSTMeasurementModelError(
            f"cross-scope estimator ancestry is forbidden for {scope}: {sorted(cross_scope)}"
        )

    quantities = _quantity_map(model)
    p_id = f"{scope}:p_sum"
    alpha_table_id = f"{scope}:alpha_corrected"
    magnetic_id = f"{scope}:magnetic_damper_ppm"
    correction_id = f"{scope}:correction_factor"
    alpha_si_id = f"{scope}:alpha_si"
    target_id = f"{scope}:G_hat"
    published_id = f"{scope}:published_G"
    comparison_id = f"{scope}:comparison_delta"
    required = {
        p_id,
        alpha_table_id,
        magnetic_id,
        correction_id,
        alpha_si_id,
        target_id,
        published_id,
        comparison_id,
    }
    if set(quantities) != required:
        raise HUSTMeasurementModelError(f"unexpected HUST quantity inventory for {scope}")

    target = quantities[target_id]
    if target.standard_uncertainty is not None or target.uncertainty_unit is not None:
        raise HUSTMeasurementModelError("depth-2a G_hat must not carry a reconstructed standard uncertainty")
    if target.exact:
        raise HUSTMeasurementModelError("reconstructed G_hat cannot be marked exact")
    if target.value is None:
        raise HUSTMeasurementModelError("reconstructed G_hat is unpopulated")

    p_sum = quantities[p_id].value
    alpha_table = quantities[alpha_table_id].value
    magnetic_ppm = quantities[magnetic_id].value
    correction_factor = quantities[correction_id].value
    alpha_si = quantities[alpha_si_id].value
    published_g = quantities[published_id].value
    comparison_delta = quantities[comparison_id].value
    if None in {
        p_sum,
        alpha_table,
        magnetic_ppm,
        correction_factor,
        alpha_si,
        published_g,
        comparison_delta,
    }:
        raise HUSTMeasurementModelError("HUST model contains an unpopulated required numerical value")
    assert p_sum is not None
    assert alpha_table is not None
    assert magnetic_ppm is not None
    assert correction_factor is not None
    assert alpha_si is not None
    assert published_g is not None
    assert comparison_delta is not None
    if p_sum == 0:
        raise HUSTMeasurementModelError("HUST P_g sum cannot be zero")

    with localcontext() as context:
        context.prec = 50
        expected_correction = Decimal(1) + magnetic_ppm * Decimal("1e-6")
        expected_alpha_si = alpha_table * Decimal("1e-9")
        expected_g = expected_alpha_si / p_sum * expected_correction
    if correction_factor != expected_correction:
        raise HUSTMeasurementModelError("magnetic-damper correction factor does not match the preregistered rule")
    if alpha_si != expected_alpha_si:
        raise HUSTMeasurementModelError("SI angular acceleration does not match the preregistered exact unit conversion")
    if target.value != expected_g:
        raise HUSTMeasurementModelError("G_hat does not match the preregistered central-value estimator")
    if comparison_delta != target.value - published_g:
        raise HUSTMeasurementModelError("terminal published-G comparison value is inconsistent")

    assessments = {
        "dimensional_status": evaluation.dimensional_status,
        "algebraic_model_status": evaluation.algebraic_model_status,
        "registered_target_path_status": evaluation.registered_target_path_status,
        "metrological_provenance_status": evaluation.metrological_provenance_status,
        "uncertainty_status": evaluation.uncertainty_status,
        "empirical_population_status": evaluation.empirical_population_status,
        "replication_status": evaluation.replication_status,
    }
    if assessments != EXPECTED_ASSESSMENTS:
        raise HUSTMeasurementModelError(
            f"unexpected HUST assessment axes for {scope}: {assessments}"
        )


def build_hust_aaf_model(scope: str, *, root: Path = Path(".")) -> MeasurementModel:
    """Build one authorized HUST AAF central-value model from pinned repository evidence."""

    verify_preregistration(root)
    manifest, graph = _load_authorized_records(root)
    return _build_model_from_records(scope, manifest, graph)


def _empirical_model_record(model: MeasurementModel, scope: str) -> dict[str, Any]:
    validate_hust_aaf_model(model, scope)
    record = measurement_model_record(model)
    record["artifact"] = "HUST 2018 AAF published empirical central-value reconstruction"
    record["scope_and_evidence_level"] = {
        "evidence_level": EMPIRICAL_RECORD,
        "classification": "published_empirical_central_value_reconstruction",
        "empirical_population": True,
        "new_laboratory_measurement": False,
        "uncertainty_qualified": False,
        "replication_claim": False,
        "statement": (
            "This record uses source-audited published HUST AAF summary inputs to reconstruct one individual central value of G. It is not a new laboratory measurement and it does not reconstruct the complete uncertainty budget."
        ),
    }
    quantities = _quantity_map(model)
    target = quantities[f"{scope}:G_hat"]
    published = quantities[f"{scope}:published_G"]
    delta = quantities[f"{scope}:comparison_delta"]
    assert target.value is not None
    assert published.value is not None
    assert delta.value is not None
    with localcontext() as context:
        context.prec = 50
        difference_ppm = (target.value / published.value - Decimal(1)) * Decimal("1e6")
    record["central_value_reconstruction"] = {
        "scope": scope,
        "G_hat_decimal": str(target.value),
        "G_hat_standard_uncertainty_decimal": None,
        "published_G_decimal": str(published.value),
        "published_G_standard_uncertainty_decimal": str(published.standard_uncertainty),
        "difference_G_decimal": str(delta.value),
        "difference_ppm": str(difference_ppm),
        "agreement_is_acceptance_criterion": False,
    }
    return record


def build_artifact(root: Path = Path(".")) -> dict[str, Any]:
    preregistration = verify_preregistration(root)
    manifest, graph = _load_authorized_records(root)
    if manifest.get("combined_aaf_reconstruction_authorized") is not False:
        raise HUSTMeasurementModelError("combined AAF authorization boundary changed")

    models = [
        _build_model_from_records(scope, manifest, graph)
        for scope in EXPECTED_EXPERIMENTS
    ]
    records = [
        _empirical_model_record(model, scope)
        for model, scope in zip(models, EXPECTED_EXPERIMENTS)
    ]
    return {
        "artifact_schema_version": MODEL_ARTIFACT_SCHEMA_VERSION,
        "artifact": "HUST 2018 AAF MeasurementModel central-value reconstructions",
        "preregistration": preregistration,
        "source_audit_authorization": {
            "path": SOURCE_AUDIT_OUTPUT.as_posix(),
            "audit_identifier": manifest.get("audit_identifier"),
            "decision": manifest.get("decision"),
            "maximum_assessed_replication_depth": manifest.get(
                "maximum_assessed_replication_depth"
            ),
            "depth_2a_authorized_experiments": list(
                manifest.get("depth_2a_authorized_experiments", [])
            ),
            "combined_aaf_reconstruction_authorized": False,
        },
        "models": records,
        "global_boundaries": {
            "individual_scopes_only": list(EXPECTED_EXPERIMENTS),
            "combined_estimator_present": False,
            "target_standard_uncertainty_policy": "None at depth 2a",
            "replication_claim": False,
            "lean_apparatus_theorem_claim": False,
        },
        "nonclaims": list(NONCLAIMS),
    }


def serialize_artifact(record: Mapping[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the frozen preregistration, source authorization, models, and deterministic artifact",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        artifact = build_artifact()
        rendered = serialize_artifact(artifact)
        if args.check:
            if not args.output.exists():
                raise HUSTMeasurementModelError(
                    f"HUST MeasurementModel artifact is missing: {args.output}"
                )
            if args.output.read_text(encoding="utf-8") != rendered:
                raise HUSTMeasurementModelError(
                    "HUST MeasurementModel artifact is stale or inconsistent"
                )
            print(
                "HUST 2018 AAF MeasurementModels are current: "
                "3 individual GO/2a central-value reconstructions; uncertainty and replication incomplete."
            )
            return

        if args.output.exists():
            if args.output.read_text(encoding="utf-8") != rendered:
                raise HUSTMeasurementModelError(
                    "refusing to overwrite existing HUST MeasurementModel artifact; review a new version"
                )
            print(f"HUST MeasurementModel artifact already exists unchanged: {args.output}.")
            return
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote HUST MeasurementModel artifact to {args.output}.")
    except (HUSTMeasurementModelError, BridgeValidationError) as error:
        print(f"invalid HUST MeasurementModel: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
