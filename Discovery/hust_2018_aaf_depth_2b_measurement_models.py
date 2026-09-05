"""Build three uncertainty-qualified HUST 2018 AAF depth-2b models.

Each model begins with its historical depth-2a central-value model, preserves that
central estimate exactly, and adds the 21 official Nature Table 1 contributions as
direct relative standard uncertainties of G.  Published final uncertainties,
displayed totals, and the combined AAF result remain terminal-only information.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from Discovery.dimensions import DIMENSIONLESS
from Discovery.hust_2018_aaf_depth_2b_authorization import (
    CANONICAL_TABLE_URL,
    CLARIFICATION_PATH,
    DEFAULT_OUTPUT as AUTHORIZATION_OUTPUT,
    EXPECTED_COMPONENTS,
    EXPECTED_RSS_PPM,
    EXPECTED_SUMS_OF_SQUARES,
    OFFICIAL_SOURCE_PATH,
    OFFICIAL_TABLE_SHA256,
    PUBLIC_DERIVABLE,
    REQUIRED_INPUTS_PATH,
    SCOPES,
    TABLE_LOCATOR,
    build_authorization_artifact,
    component_values,
    load_authorized_records,
    serialize_artifact as serialize_authorization_artifact,
    validate_clarification_record,
    validate_official_source_record,
    validate_required_inputs_graph,
)
from Discovery.hust_2018_aaf_measurement_models import (
    build_hust_aaf_model,
)
from Discovery.physical_bridge import measurement_model_record
from Discovery.physical_bridge_schema import (
    DECLARED_LOCAL_ATOM,
    DIRECT_MEASURAND_CONTRIBUTIONS,
    DOCUMENTED,
    EMPIRICAL_RECORD,
    EXPLICIT_ZERO_ASSUMPTION,
    NO_REGISTERED_TARGET_PATH,
    UNCERTAINTY_COMPONENT,
    MeasurementModel,
    QuantityRecord,
    UncertaintyModel,
)
from Discovery.physical_bridge_validation import evaluate_measurement_model
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
)


MODEL_ARTIFACT_SCHEMA_VERSION = 2
DEFAULT_OUTPUT = Path(
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_measurement_models_v2.json"
)
SOURCE_IDENTIFIER = "doi:10.1038/s41586-018-0431-5"
SOURCE_ACCESS_DATE = "2026-09-05"
SOURCE_EDITION = (
    "Nature 560 (2018), Table 1; official Nature table capture "
    + OFFICIAL_TABLE_SHA256
)
COMPONENT_DESCRIPTION_PREFIX = (
    "Published HUST 2018 Table 1 one-standard-deviation contribution already "
    "expressed as relative uncertainty in G. Official locator: "
    + TABLE_LOCATOR
)
ZERO_CORRELATION_JUSTIFICATION = (
    "Zero pairwise covariance is used only to represent the published individual "
    "Table 1 RSS budget established by the depth-2b derivation record; it is not a "
    "claim that all underlying physical systematic sources are independent. "
    "Cross-run covariance is outside this individual reconstruction."
)
PROPAGATION_METHOD = (
    "precision-50 Decimal root sum of squares of direct relative ppm contributions; "
    "absolute standard uncertainty = abs(G_hat) * RSS_ppm * 1e-6"
)
COVERAGE_BASIS = (
    "Published contributions are one-standard-deviation standard uncertainties; "
    "no expanded coverage factor or probability is claimed."
)

EXPECTED_ASSESSMENTS = {
    "dimensional_status": "satisfied",
    "algebraic_model_status": "satisfied",
    "registered_target_path_status": NO_REGISTERED_TARGET_PATH,
    "metrological_provenance_status": "satisfied",
    "uncertainty_status": "satisfied",
    "empirical_population_status": "satisfied",
    "replication_status": "incomplete",
}

NONCLAIMS = (
    "These records reconstruct published HUST AAF central values and individual standard uncertainties; they are not new laboratory measurements.",
    "The direct Table 1 contributions are not rederived from raw apparatus metrology.",
    "The zero-covariance representation does not establish physical independence among every systematic source.",
    "No combined AAF estimator or uncertainty is authorized or constructed.",
    "No raw or run-level replication claim is made.",
    "Published HUST G values, final uncertainties, and displayed Table 1 totals remain terminal comparison information.",
    "No Lean theorem validates the apparatus-specific AAF estimator or uncertainty budget.",
)


class HUSTDepth2BMeasurementModelError(ValueError):
    """Controlled failure of the HUST depth-2b model contract."""


def _quantity_map(model: MeasurementModel) -> dict[str, QuantityRecord]:
    return {quantity.identifier: quantity for quantity in model.quantities}


def _component_identifier(scope: str, component_id: str) -> str:
    return f"{scope}:u_ppm:{component_id}"


def _component_symbol(scope: str, component_id: str) -> str:
    return f"u_{scope.replace('-', '_')}_{component_id}_ppm"


def _source_rows(graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {row["component_id"]: row for row in graph["components"]}


def _build_depth_2b_model_from_records(
    scope: str,
    baseline_model: MeasurementModel,
    source_record: Mapping[str, Any],
    clarification: Mapping[str, Any],
    graph: Mapping[str, Any],
) -> MeasurementModel:
    """Pure constructor after its caller supplies the pinned authorization records."""

    if scope not in SCOPES:
        raise HUSTDepth2BMeasurementModelError(
            f"unsupported or combined AAF scope: {scope}"
        )
    validate_official_source_record(source_record)
    validate_clarification_record(clarification)
    validate_required_inputs_graph(graph)
    source_rows = _source_rows(graph)
    values = component_values(graph, scope)

    components = tuple(
        QuantityRecord(
            identifier=_component_identifier(scope, component_id),
            symbol=_component_symbol(scope, component_id),
            role=UNCERTAINTY_COMPONENT,
            dimension=DIMENSIONLESS,
            unit="ppm",
            algebraic_provenance_kind=DECLARED_LOCAL_ATOM,
            registered_dependency_signature=None,
            provenance_evidence=DOCUMENTED,
            description=(
                COMPONENT_DESCRIPTION_PREFIX
                + f"; row: {source_rows[component_id]['printed_row_label']}."
            ),
            value=value,
            standard_uncertainty=None,
            uncertainty_unit=None,
            exact=False,
            source_identifier=SOURCE_IDENTIFIER,
            edition=SOURCE_EDITION,
            access_date=SOURCE_ACCESS_DATE,
        )
        for component_id, value in values
    )

    baseline_quantities = _quantity_map(baseline_model)
    target_id = f"{scope}:G_hat"
    target = baseline_quantities.get(target_id)
    if target is None or target.value is None:
        raise HUSTDepth2BMeasurementModelError(
            f"depth-2a baseline target is unavailable for {scope}"
        )
    with localcontext() as context:
        context.prec = 50
        sum_of_squares = sum(value * value for _, value in values)
        relative_ppm = sum_of_squares.sqrt()
        absolute_uncertainty = abs(target.value) * relative_ppm * Decimal("1e-6")

    upgraded_quantities = tuple(
        replace(
            quantity,
            description=(
                "Depth-2b reconstructed central value with a separately derived "
                "standard uncertainty from the official Table 1 direct budget."
            ),
            standard_uncertainty=absolute_uncertainty,
            uncertainty_unit=quantity.unit,
        )
        if quantity.identifier == target_id
        else quantity
        for quantity in baseline_model.quantities
    )
    uncertainty = UncertaintyModel(
        measurand_id=target_id,
        input_ids=(),
        correction_ids=(),
        correlation_policy=EXPLICIT_ZERO_ASSUMPTION,
        correlations=(),
        zero_correlation_justification=ZERO_CORRELATION_JUSTIFICATION,
        propagation_method=PROPAGATION_METHOD,
        coverage_factor=None,
        coverage_probability=None,
        coverage_basis=COVERAGE_BASIS,
        limitations=(
            "The component values are rounded published contributions already expressed for G; their underlying apparatus reductions are not reconstructed.",
            "The individual-column RSS representation does not authorize a cross-run or combined covariance model.",
        ),
        uncertainty_basis=DIRECT_MEASURAND_CONTRIBUTIONS,
        component_ids=tuple(component.identifier for component in components),
    )
    model = replace(
        baseline_model,
        identifier=f"hust_2018_{scope.lower().replace('-', '_')}_depth_2b_v2",
        domain_and_approximation_regime=(
            *baseline_model.domain_and_approximation_regime,
            "individual Nature Table 1 one-standard-deviation budget represented as direct relative contributions to G",
        ),
        required_hypotheses=(
            *baseline_model.required_hypotheses,
            "the official Nature Table 1 source pin and depth-2b derivation authorization remain current",
            "the 21 rounded direct contributions are combined only by the qualified individual-column RSS rule",
        ),
        quantities=(*upgraded_quantities, *components),
        uncertainty_model=uncertainty,
        limitations=(
            "The model begins from published summary quantities rather than raw torsion-balance time series.",
            "Table 1 contributions are consumed at their published direct-to-G level and are not independently rederived from apparatus observations.",
            "The qualified zero-covariance representation reproduces each individual published budget; it does not establish physical independence among all error mechanisms.",
            "Cross-run covariance, combined AAF estimation, apparatus validation, and deeper replication remain outside this model.",
        ),
        nonclaims=NONCLAIMS,
    )
    validate_hust_aaf_depth_2b_model(
        model,
        scope,
        graph,
        baseline_model=baseline_model,
    )
    return model


def validate_hust_aaf_depth_2b_model(
    model: MeasurementModel,
    scope: str,
    graph: Mapping[str, Any],
    *,
    baseline_model: MeasurementModel,
) -> None:
    """Apply apparatus-specific source, inventory, isolation, and arithmetic gates."""

    if scope not in SCOPES:
        raise HUSTDepth2BMeasurementModelError(f"invalid HUST depth-2b scope: {scope}")
    validate_required_inputs_graph(graph)
    evaluation = evaluate_measurement_model(model)
    if model.evidence_level != EMPIRICAL_RECORD:
        raise HUSTDepth2BMeasurementModelError("depth-2b model must be an empirical record")
    if model.replication_identifiers:
        raise HUSTDepth2BMeasurementModelError("depth-2b model cannot claim replication")
    if model.lean_link_identifier is not None:
        raise HUSTDepth2BMeasurementModelError(
            "no Lean theorem is registered for the apparatus-specific AAF model"
        )

    baseline_quantities = _quantity_map(baseline_model)
    quantities = _quantity_map(model)
    expected_component_ids = tuple(
        _component_identifier(scope, row[0]) for row in EXPECTED_COMPONENTS
    )
    expected_inventory = tuple(baseline_quantities) + expected_component_ids
    actual_inventory = tuple(quantity.identifier for quantity in model.quantities)
    if actual_inventory != expected_inventory:
        raise HUSTDepth2BMeasurementModelError(
            "depth-2b quantity inventory, order, or component names changed"
        )

    target_id = f"{scope}:G_hat"
    for identifier, baseline in baseline_quantities.items():
        actual = quantities[identifier]
        if identifier == target_id:
            if actual.value != baseline.value:
                raise HUSTDepth2BMeasurementModelError(
                    "depth-2b construction changed the depth-2a central value"
                )
            if actual.exact or actual.unit != baseline.unit:
                raise HUSTDepth2BMeasurementModelError("depth-2b target metadata changed")
            continue
        if actual != baseline:
            raise HUSTDepth2BMeasurementModelError(
                f"depth-2b construction changed central-model quantity {identifier}"
            )
    if (
        model.estimator_terms != baseline_model.estimator_terms
        or model.definition_edges != baseline_model.definition_edges
        or model.metrological_edges != baseline_model.metrological_edges
        or model.calibration_source_ids != baseline_model.calibration_source_ids
        or model.correction_ids != baseline_model.correction_ids
        or model.comparison_reference_ids != baseline_model.comparison_reference_ids
        or model.comparison_node_ids != baseline_model.comparison_node_ids
    ):
        raise HUSTDepth2BMeasurementModelError(
            "depth-2b construction changed central estimator or comparison ancestry"
        )

    source_rows = _source_rows(graph)
    values = component_values(graph, scope)
    for (component_id, expected_value), identifier in zip(values, expected_component_ids):
        component = quantities[identifier]
        expected_description = (
            COMPONENT_DESCRIPTION_PREFIX
            + f"; row: {source_rows[component_id]['printed_row_label']}."
        )
        if (
            component.value != expected_value
            or component.role != UNCERTAINTY_COMPONENT
            or component.dimension != DIMENSIONLESS
            or component.unit != "ppm"
            or component.standard_uncertainty is not None
            or component.uncertainty_unit is not None
            or component.provenance_evidence != DOCUMENTED
            or component.source_identifier != SOURCE_IDENTIFIER
            or component.edition != SOURCE_EDITION
            or component.access_date != SOURCE_ACCESS_DATE
            or component.description != expected_description
        ):
            raise HUSTDepth2BMeasurementModelError(
                f"source binding or representation changed for component {identifier}"
            )

    uncertainty = model.uncertainty_model
    if uncertainty is None:
        raise HUSTDepth2BMeasurementModelError("depth-2b uncertainty model is missing")
    if (
        uncertainty.measurand_id != target_id
        or uncertainty.uncertainty_basis != DIRECT_MEASURAND_CONTRIBUTIONS
        or uncertainty.input_ids
        or uncertainty.correction_ids
        or uncertainty.component_ids != expected_component_ids
        or uncertainty.correlation_policy != EXPLICIT_ZERO_ASSUMPTION
        or uncertainty.correlations
        or uncertainty.zero_correlation_justification
        != ZERO_CORRELATION_JUSTIFICATION
        or uncertainty.propagation_method != PROPAGATION_METHOD
        or uncertainty.coverage_factor is not None
        or uncertainty.coverage_probability is not None
        or uncertainty.coverage_basis != COVERAGE_BASIS
    ):
        raise HUSTDepth2BMeasurementModelError(
            "depth-2b uncertainty-model contract changed"
        )

    target = quantities[target_id]
    if target.value is None:
        raise HUSTDepth2BMeasurementModelError("depth-2b target is unpopulated")
    with localcontext() as context:
        context.prec = 50
        sum_of_squares = sum(value * value for _, value in values)
        relative_ppm = sum_of_squares.sqrt()
        expected_absolute = abs(target.value) * relative_ppm * Decimal("1e-6")
    if sum_of_squares != EXPECTED_SUMS_OF_SQUARES[scope]:
        raise HUSTDepth2BMeasurementModelError("component sum of squares changed")
    if relative_ppm != EXPECTED_RSS_PPM[scope]:
        raise HUSTDepth2BMeasurementModelError("precision-50 relative RSS changed")
    if (
        target.standard_uncertainty != expected_absolute
        or target.uncertainty_unit != target.unit
    ):
        raise HUSTDepth2BMeasurementModelError(
            "target uncertainty does not match abs(G_hat) * RSS_ppm * 1e-6"
        )

    prefix = scope + ":"
    cross_scope = [
        identifier
        for identifier in (
            *evaluation.estimator_upstream_ids,
            *evaluation.uncertainty_component_upstream_ids,
        )
        if not identifier.startswith(prefix)
    ]
    if cross_scope:
        raise HUSTDepth2BMeasurementModelError(
            f"cross-scope ancestry is forbidden for {scope}: {sorted(cross_scope)}"
        )
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
        raise HUSTDepth2BMeasurementModelError(
            f"unexpected HUST depth-2b assessment axes for {scope}: {assessments}"
        )


def verify_authorization_artifact(root: Path = Path(".")) -> dict[str, Any]:
    expected = serialize_authorization_artifact(build_authorization_artifact(root))
    path = root / AUTHORIZATION_OUTPUT
    try:
        actual = path.read_text(encoding="utf-8")
    except OSError as error:
        raise HUSTDepth2BMeasurementModelError(
            "depth-2b authorization artifact is unavailable"
        ) from error
    if actual != expected:
        raise HUSTDepth2BMeasurementModelError(
            "depth-2b authorization artifact is stale"
        )
    return json.loads(actual)


def build_hust_aaf_depth_2b_model(
    scope: str, *, root: Path = Path(".")
) -> MeasurementModel:
    """Build one authorized individual depth-2b model from pinned repository evidence."""

    verify_authorization_artifact(root)
    source, clarification, graph = load_authorized_records(root)
    baseline = build_hust_aaf_model(scope, root=root)
    return _build_depth_2b_model_from_records(
        scope,
        baseline,
        source,
        clarification,
        graph,
    )


def _empirical_model_record(
    model: MeasurementModel,
    scope: str,
    graph: Mapping[str, Any],
    baseline_model: MeasurementModel,
) -> dict[str, Any]:
    validate_hust_aaf_depth_2b_model(
        model,
        scope,
        graph,
        baseline_model=baseline_model,
    )
    record = measurement_model_record(model)
    record["artifact"] = (
        "HUST 2018 AAF published empirical central-value and standard-uncertainty reconstruction"
    )
    record["scope_and_evidence_level"] = {
        "evidence_level": EMPIRICAL_RECORD,
        "classification": "published_empirical_uncertainty_qualified_reconstruction",
        "empirical_population": True,
        "new_laboratory_measurement": False,
        "uncertainty_qualified": True,
        "replication_claim": False,
        "statement": (
            "This record preserves one source-audited HUST AAF central reconstruction "
            "and derives its standard uncertainty from that scope's 21 official "
            "Nature Table 1 direct contributions."
        ),
    }
    quantities = _quantity_map(model)
    target = quantities[f"{scope}:G_hat"]
    assert target.value is not None
    assert target.standard_uncertainty is not None
    values = component_values(graph, scope)
    with localcontext() as context:
        context.prec = 50
        sum_of_squares = sum(value * value for _, value in values)
        relative_ppm = sum_of_squares.sqrt()
    record["uncertainty_reconstruction"] = {
        "scope": scope,
        "decimal_precision": 50,
        "component_classification": "PUBLIC_DIRECT",
        "rss_and_complete_model_classification": PUBLIC_DERIVABLE,
        "components_in_source_order": [
            {
                "component_id": component_id,
                "quantity_id": _component_identifier(scope, component_id),
                "value_ppm": str(value),
            }
            for component_id, value in values
        ],
        "sum_of_squares": str(sum_of_squares),
        "relative_standard_uncertainty_ppm": str(relative_ppm),
        "G_hat_decimal": str(target.value),
        "absolute_standard_uncertainty_decimal": str(target.standard_uncertainty),
        "absolute_standard_uncertainty_unit": target.uncertainty_unit,
        "official_source": {
            "doi": SOURCE_IDENTIFIER.removeprefix("doi:"),
            "canonical_table_url": CANONICAL_TABLE_URL,
            "table_capture_sha256": OFFICIAL_TABLE_SHA256,
            "table_locator": TABLE_LOCATOR,
            "source_record_path": OFFICIAL_SOURCE_PATH.as_posix(),
            "clarification_path": CLARIFICATION_PATH.as_posix(),
            "required_inputs_path": REQUIRED_INPUTS_PATH.as_posix(),
        },
        "terminal_comparisons_not_used_as_inputs": graph["terminal_comparisons"][scope],
    }
    return record


def build_artifact(root: Path = Path(".")) -> dict[str, Any]:
    authorization = verify_authorization_artifact(root)
    source, clarification, graph = load_authorized_records(root)
    baselines = [build_hust_aaf_model(scope, root=root) for scope in SCOPES]
    models = [
        _build_depth_2b_model_from_records(
            scope,
            baseline,
            source,
            clarification,
            graph,
        )
        for scope, baseline in zip(SCOPES, baselines)
    ]
    records = [
        _empirical_model_record(model, scope, graph, baseline)
        for model, scope, baseline in zip(models, SCOPES, baselines)
    ]
    return {
        "artifact_schema_version": MODEL_ARTIFACT_SCHEMA_VERSION,
        "artifact": "HUST 2018 AAF individual depth-2b MeasurementModels",
        "revision": {
            "predecessor_path": (
                "Experiments/GMeasurements/"
                "hust_2018_aaf_depth_2b_measurement_models_v1.json"
            ),
            "change_summary": (
                "Post-audit migration to exact printed labels and strengthened "
                "authorization verification."
            ),
            "numerical_values_changed": False,
            "scientific_authorization_changed": False,
            "scope_boundaries_changed": False,
        },
        "authorization": {
            "path": AUTHORIZATION_OUTPUT.as_posix(),
            "decision": authorization["decision"],
            "official_source_precondition": authorization[
                "official_source_precondition"
            ]["status"],
            "combined_aaf_reconstruction_authorized": False,
        },
        "models": records,
        "global_boundaries": {
            "individual_scopes_only": list(SCOPES),
            "combined_estimator_present": False,
            "published_final_uncertainties_used_as_inputs": False,
            "displayed_totals_used_as_inputs": False,
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
        help="verify all source gates, models, and deterministic artifact bytes",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        rendered = serialize_artifact(build_artifact(Path(".")))
        if args.check:
            try:
                existing = args.output.read_text(encoding="utf-8")
            except OSError as error:
                raise HUSTDepth2BMeasurementModelError(
                    f"depth-2b model artifact is unavailable: {args.output}"
                ) from error
            if existing != rendered:
                raise HUSTDepth2BMeasurementModelError(
                    f"depth-2b model artifact is stale: {args.output}"
                )
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except (HUSTDepth2BMeasurementModelError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
