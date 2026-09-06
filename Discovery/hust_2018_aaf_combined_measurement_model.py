"""Source-bound weighted HUST AAF MeasurementModel; published-summary reconstruction.

Only the pinned individual v2 records and component graph supply numerical inputs.
The preregistration contains a target-independent projection of PR #37's source
review. Neither the feasibility output nor a terminal comparison is loaded by the
production estimator. Coefficients condition on frozen uncertainty summaries.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from Discovery.dimensions import Dimension, GRAVITATIONAL_CONSTANT
from Discovery.hust_2018_aaf_combined_feasibility import (
    COMPONENT_IDS, SCOPES,
    correlation_inventory, matrix_diagnostics, validate_correlations,
)
from Discovery.physical_bridge import measurement_model_record
from Discovery.physical_bridge_schema import (
    BridgeValidationError, CorrelationDeclaration, MeasurementModel, ProvenanceEdge,
    QuantityRecord, UncertaintyModel, WeightedEstimatorTerm,
    COVARIANCE_MATRIX, DECLARED_LOCAL_ATOM, DERIVED_QUANTITY, DOCUMENTED,
    EMPIRICAL_RECORD, ESTIMATOR_INPUT_PROPAGATION, EXTERNAL_COMPARISON_REFERENCE,
    NORMALIZED_INVERSE_VARIANCE, TARGET_OUTPUT, UNCERTAINTY_COMPONENT,
)
from Discovery.physical_bridge_validation import (
    evaluate_measurement_model, normalized_inverse_variance_weights,
    validate_measurement_model,
)


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "hust_2018_aaf_combined_measurement_model_preregistration_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "hust_2018_aaf_combined_measurement_model_v1.json"
BASELINE = "0232b775cb34100c0ae1d15cff65459819682001"
PREREGISTRATION_COMMIT = "39f3a9f4a3b3720889ac35cbe1cebfe198ac50f6"
PREREGISTRATION_SHA256 = "284957ec010d25bc7d5e0e64696df11b8d9c1af5358670c3a7bb7d7c2cf8961f"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/38",
    "created_at": "2026-09-06T14:11:36Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "scope": "Implementation rules frozen before implementation; PR #37 numerical result already known.",
}
MODELS_NAME = "hust_2018_aaf_depth_2b_measurement_models_v2.json"
GRAPH_NAME = "hust_2018_aaf_required_inputs_depth_2b_v2.json"
TARGET_ID = "AAF-combined:G_hat"
INPUT_IDS = tuple(f"{scope}:G_hat" for scope in SCOPES)
UNIT = "m^3 kg^-1 s^-2"
COVARIANCE_UNIT = f"({UNIT})^2"
ARITHMETIC = Context(prec=50, rounding=ROUND_HALF_EVEN)
ROUNDING_BOUND = Decimal("1e-47")
NONCLAIMS = (
    "Reconstruction of published HUST 2018 summary evidence; no new laboratory measurement or novel prediction.",
    "No raw-data or run-level replication and no independent validation of the HUST apparatus.",
    "Source-prescribed correlations are modelling assumptions, not proof of physical independence or completeness of nature's error mechanisms.",
    "No Lean proof of the apparatus or the weighted estimator is claimed.",
    "Terminal agreement is not validation, source authorization, or an estimator acceptance criterion.",
)


class CombinedModelError(BridgeValidationError):
    """The source projection or source-prescribed combined model is invalid."""


def serialize_artifact(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CombinedModelError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def _decimal(value: str, label: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str):
        raise CombinedModelError(f"{label}: authoritative numbers must be decimal strings; floats forbidden")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise CombinedModelError(f"{label}: malformed decimal") from error
    if not number.is_finite() or (positive and number <= 0):
        raise CombinedModelError(f"{label}: number must be finite and positive")
    return number


def _preregistration(root: Path) -> dict:
    data = (root / PREREGISTRATION_PATH).read_bytes()
    if _hash(data) != PREREGISTRATION_SHA256:
        raise CombinedModelError("combined-model preregistration bytes changed")
    return _json(data)


def verify_preregistration(root: Path = ROOT) -> dict:
    prereg = _preregistration(root)
    def git(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
        if result.returncode:
            raise CombinedModelError(f"preregistration history unavailable or ancestry invalid: {args}")
        return result.stdout
    path = PREREGISTRATION_PATH.as_posix()
    current = (root / path).read_bytes()
    if git("show", f"{PREREGISTRATION_COMMIT}:{path}") != current:
        raise CombinedModelError("preregistration differs from its published commit")
    if git("rev-parse", f"{PREREGISTRATION_COMMIT}^").decode().strip() != BASELINE:
        raise CombinedModelError("preregistration parent differs from intended base")
    if git("diff", "--name-only", BASELINE, PREREGISTRATION_COMMIT).decode().splitlines() != [path]:
        raise CombinedModelError("first branch commit must contain the preregistration alone")
    git("merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, "HEAD")
    for commit in git("log", "--format=%H", f"{PREREGISTRATION_COMMIT}..HEAD", "--", path).decode().splitlines():
        if git("show", f"{commit}:{path}") != current:
            raise CombinedModelError("preregistration changed in intervening history")
    return prereg


def load_frozen_records(root: Path = ROOT) -> dict:
    records = {}
    for pin in _preregistration(root)["allowed_input_artifacts"]:
        data = (root / pin["path"]).read_bytes()
        if len(data) != pin["byte_length"] or _hash(data) != pin["sha256"]:
            raise CombinedModelError(f"frozen upstream source changed: {pin['path']}")
        records[Path(pin["path"]).name] = _json(data)
    return records


def _quantity_projection(quantity: dict) -> dict:
    result = {key: deepcopy(quantity[key]) for key in (
        "identifier", "symbol", "role", "dimension", "unit", "description",
        "metrological_provenance_evidence", "source", "numerical_record",
    )}
    result["algebraic_provenance"] = {
        key: deepcopy(quantity["algebraic_provenance"][key])
        for key in ("kind", "surface_signature")
    }
    return result


def _project(records: dict) -> dict:
    """Explicit allowlist; only source-bound central ancestry and budget evidence."""
    try:
        models = records[MODELS_NAME]["models"]
        graph = records[GRAPH_NAME]
        if len(models) != 3 or tuple(row["component_id"] for row in graph["components"]) != COMPONENT_IDS:
            raise CombinedModelError("missing, duplicate or misordered scopes/components")
        runs = []
        for scope, model in zip(SCOPES, models):
            reconstruction = model["uncertainty_reconstruction"]
            if reconstruction["scope"] != scope:
                raise CombinedModelError("individual MeasurementModel scope mismatch")
            quantity_list = model["quantities"]
            quantities = {q["identifier"]: q for q in quantity_list}
            if len(quantities) != len(quantity_list):
                raise CombinedModelError("duplicate upstream quantity")
            target_id = f"{scope}:G_hat"
            target = quantities[target_id]
            if target["role"] != TARGET_OUTPUT or model["target_measurand"]["quantity_id"] != target_id:
                raise CombinedModelError("upstream individual target identity changed")
            central = reconstruction["G_hat_decimal"]
            standard = reconstruction["absolute_standard_uncertainty_decimal"]
            _decimal(central, "individual G", positive=True)
            _decimal(standard, "individual total uncertainty", positive=True)
            if (central != target["numerical_record"]["value_decimal"]
                    or standard != target["numerical_record"]["standard_uncertainty_decimal"]):
                raise CombinedModelError("individual reconstruction disagrees with its target quantity")
            definition = model["provenance_graphs"]["definitional"]["edges"]
            metrological = model["provenance_graphs"]["metrological"]["edges"]
            edges = definition + metrological
            reached, pending = set(), [target_id]
            while pending:
                identifier = pending.pop()
                if identifier not in reached:
                    reached.add(identifier)
                    pending.extend(e["parent"] for e in edges if e["child"] == identifier)
            if any(quantities[q]["role"] in {EXTERNAL_COMPARISON_REFERENCE, UNCERTAINTY_COMPONENT}
                   for q in reached):
                raise CombinedModelError("forbidden comparison/component enters individual central ancestry")
            components = []
            if len(reconstruction["components_in_source_order"]) != len(COMPONENT_IDS):
                raise CombinedModelError("missing individual uncertainty component")
            for row, supplied in zip(graph["components"], reconstruction["components_in_source_order"]):
                cid = row["component_id"]
                qid = f"{scope}:u_ppm:{cid}"
                expected = {"component_id": cid, "quantity_id": qid, "value_ppm": row[scope]}
                if supplied != expected or quantities[qid]["numerical_record"]["value_decimal"] != row[scope]:
                    raise CombinedModelError("component identity/value differs between authorized records")
                _decimal(row[scope], cid, positive=True)
                components.append({**expected, "quantity": _quantity_projection(quantities[qid])})
            runs.append({
                "scope": scope, "model_identifier": model["model_identifier"],
                "target_id": target_id, "G_hat_decimal": central,
                "standard_uncertainty_decimal": standard,
                "quantities": [_quantity_projection(quantities[q]) for q in sorted(reached)],
                "definition_edges": [deepcopy(e) for e in definition if e["child"] in reached],
                "metrological_edges": [deepcopy(e) for e in metrological if e["child"] in reached],
                "components": components,
            })
        return {"runs": runs, "component_source_pins": deepcopy(graph["source_pins"])}
    except (KeyError, TypeError, IndexError) as error:
        raise CombinedModelError("incomplete or malformed authorized individual projection") from error


def project_inputs(records: dict, root: Path = ROOT) -> dict:
    projection = _project(records)
    validate_inputs(projection, root)
    return projection


def validate_inputs(inputs: dict, root: Path = ROOT) -> None:
    expected = _project(load_frozen_records(root))
    if serialize_artifact(inputs) != serialize_artifact(expected):
        raise CombinedModelError("upstream projection differs from authorized individual inputs; terminal substitutions forbidden")


def load_inputs(root: Path = ROOT) -> dict:
    return _project(load_frozen_records(root))


def construct_covariance(inputs: dict, correlations: list[dict] | None = None, *, root: Path = ROOT) -> dict:
    validate_inputs(inputs, root)
    correlations = correlation_inventory() if correlations is None else correlations
    validate_correlations(correlations)
    with localcontext(ARITHMETIC):
        contributions = [
            [_decimal(run["G_hat_decimal"], "G") * _decimal(c["value_ppm"], "component") * Decimal("1e-6")
             for c in run["components"]]
            for run in inputs["runs"]
        ]
        matrix = [[Decimal("0") for _ in SCOPES] for _ in SCOPES]
        for i, run in enumerate(inputs["runs"]):
            matrix[i][i] = _decimal(run["standard_uncertainty_decimal"], "total uncertainty", positive=True) ** 2
            component_variance = sum((x ** 2 for x in contributions[i]), Decimal("0"))
            if abs(component_variance - matrix[i][i]) / matrix[i][i] > ROUNDING_BOUND:
                raise CombinedModelError("individual total variance disagrees with its component budget")
            for j in range(i):
                matrix[i][j] = matrix[j][i] = sum((
                    _decimal(entry["off_diagonal_rho"], "correlation") * contributions[i][k] * contributions[j][k]
                    for k, entry in enumerate(correlations)
                ), Decimal("0"))
        serialized = [[str(x) for x in row] for row in matrix]
        terms = [{**entry, "absolute_standard_contributions": [str(contributions[i][k]) for i in range(3)]}
                 for k, entry in enumerate(correlations)]
    diagnostics = matrix_diagnostics(serialized)
    return {"input_ids": list(INPUT_IDS), "unit": COVARIANCE_UNIT, "matrix": serialized,
            "component_terms": terms, "diagnostics": diagnostics}


def validate_covariance(covariance: dict, inputs: dict, *, root: Path = ROOT) -> None:
    expected = construct_covariance(inputs, root=root)
    if covariance != expected:
        raise CombinedModelError("covariance differs from the authorized itemwise cross-run rule")


def reconstruct(inputs: dict, covariance: dict | None = None, *, root: Path = ROOT) -> dict:
    """Calculate from individual totals and component covariance, never a comparison."""
    if covariance is None:
        covariance = construct_covariance(inputs, root=root)
    else:
        validate_covariance(covariance, inputs, root=root)
    weights = normalized_inverse_variance_weights({
        run["target_id"]: _decimal(run["standard_uncertainty_decimal"], "individual uncertainty", positive=True)
        for run in inputs["runs"]
    })
    with localcontext(ARITHMETIC):
        estimate = sum((weights[run["target_id"]] * _decimal(run["G_hat_decimal"], "individual G")
                        for run in inputs["runs"]), Decimal("0"))
        variance = sum((weights[left] * _decimal(covariance["matrix"][i][j], "covariance") * weights[right]
                        for i, left in enumerate(INPUT_IDS) for j, right in enumerate(INPUT_IDS)), Decimal("0"))
        if variance <= 0 or not variance.is_finite():
            raise CombinedModelError("combined variance must be finite and positive")
        standard = variance.sqrt()
        return {
            "weights": [{"quantity_id": key, "coefficient_decimal": str(value)} for key, value in weights.items()],
            "weight_sum": str(sum(weights.values(), Decimal("0"))),
            "G_hat_decimal": str(estimate), "standard_uncertainty_decimal": str(standard),
            "variance_decimal": str(variance), "unit": UNIT,
            "relative_standard_uncertainty_ppm": str(standard / estimate.copy_abs() * Decimal("1e6")),
        }


def _decode_quantity(record: dict) -> QuantityRecord:
    numerical, algebraic, source = record["numerical_record"], record["algebraic_provenance"], record["source"]
    signature = algebraic["surface_signature"]
    return QuantityRecord(
        identifier=record["identifier"], symbol=record["symbol"], role=record["role"],
        dimension=Dimension(tuple(Fraction(x) for x in record["dimension"])), unit=record["unit"],
        algebraic_provenance_kind=algebraic["kind"],
        registered_dependency_signature=None if signature is None else tuple((s["factor"], Fraction(s["exponent"])) for s in signature),
        provenance_evidence=record["metrological_provenance_evidence"], description=record["description"],
        value=None if numerical["value_decimal"] is None else _decimal(numerical["value_decimal"], "quantity value"),
        standard_uncertainty=None if numerical["standard_uncertainty_decimal"] is None else _decimal(numerical["standard_uncertainty_decimal"], "quantity uncertainty"),
        uncertainty_unit=numerical["uncertainty_unit"], exact=numerical["exact"],
        source_identifier=source["identifier"], edition=source["edition"], access_date=source["access_date"],
    )


def _assemble_model(inputs: dict, covariance: dict, result: dict) -> MeasurementModel:
    quantities, definition, metrological = [], [], []
    for run in inputs["runs"]:
        scope = run["scope"]
        local = {q["identifier"]: _decode_quantity(q) for q in run["quantities"]}
        upstream = local[run["target_id"]]
        local[upstream.identifier] = replace(
            upstream, role=DERIVED_QUANTITY,
            source_identifier=f"url:https://github.com/mdiaz4052/The-Number-Project/blob/{BASELINE}/{DIRECTORY}/{MODELS_NAME}",
            edition=f"Frozen v2 individual MeasurementModel {run['model_identifier']}; scope {scope}",
            access_date="2026-09-06",
            description="Upstream empirical determination with its depth-2b total standard uncertainty; central ancestry retained.",
        )
        # Preserve the complete central ancestry without calling these ancestors
        # additional stochastic inputs. Populate two exact-transform summaries
        # from their primitive uncertainties; do not substitute a direct-G budget.
        with localcontext(ARITHMETIC):
            for suffix, parent_suffix, scale in (
                ("alpha_si", "alpha_corrected", Decimal("1e-9")),
                ("correction_factor", "magnetic_damper_ppm", Decimal("1e-6")),
            ):
                quantity = local[f"{scope}:{suffix}"]
                parent = local[f"{scope}:{parent_suffix}"]
                local[quantity.identifier] = replace(
                    quantity, standard_uncertainty=parent.standard_uncertainty * scale,
                    uncertainty_unit=quantity.unit,
                    description=quantity.description + " Standard uncertainty follows the exact affine transform of its documented parent; provenance summary only in the combined model.",
                )
        quantities.extend(local.values())
        definition.extend(ProvenanceEdge(**edge) for edge in run["definition_edges"])
        metrological.extend(ProvenanceEdge(**edge) for edge in run["metrological_edges"])
        definition.append(ProvenanceEdge(TARGET_ID, upstream.identifier, "definition", "This empirical determination is one term of the normalized weighted sum."))
        metrological.append(ProvenanceEdge(TARGET_ID, upstream.identifier, "model_input", "The source-prescribed combination consumes the frozen individual estimate and total uncertainty."))
    quantities.append(QuantityRecord(
        identifier=TARGET_ID, symbol="G_hat_AAF_combined", role=TARGET_OUTPUT,
        dimension=GRAVITATIONAL_CONSTANT, unit=UNIT, algebraic_provenance_kind=DECLARED_LOCAL_ATOM,
        registered_dependency_signature=None, provenance_evidence=DOCUMENTED,
        description="Combined published-summary reconstruction with covariance-qualified standard uncertainty.",
        value=_decimal(result["G_hat_decimal"], "combined G"),
        standard_uncertainty=_decimal(result["standard_uncertainty_decimal"], "combined uncertainty"),
        uncertainty_unit=UNIT,
    ))
    return MeasurementModel(
        identifier="hust_2018_aaf_combined_measurement_model_v1", target_measurand_id=TARGET_ID,
        target_symbolic_key="G", theoretical_relation="The three individual HUST AAF determinations estimate the same G within the source model.",
        estimator_relation="G_combined = sum_i p_i G_i; p_i = (1/u_i^2) / sum_j(1/u_j^2)",
        domain_and_approximation_regime=("HUST 2018 AAF-I/II/III published summary quantities and rounded Table 1 direct-to-G contributions.",),
        required_hypotheses=(
            "The pinned individual depth-2b central determinations and direct uncertainty budgets retain their reviewed source validity.",
            "Supplement Section 6's normalized marginal inverse-variance weights and itemwise correlation assumptions apply to these three AAF determinations.",
            "Weights condition on frozen uncertainty summaries; uncertainty in estimated weights is not modelled.",
        ),
        quantities=tuple(quantities), estimator_terms=(),
        weighted_estimator_terms=tuple(WeightedEstimatorTerm(w["quantity_id"], _decimal(w["coefficient_decimal"], "weight")) for w in result["weights"]),
        weighting_rule=NORMALIZED_INVERSE_VARIANCE,
        definition_edges=tuple(definition), metrological_edges=tuple(metrological),
        calibration_source_ids=(), correction_ids=(), comparison_reference_ids=(), comparison_node_ids=(),
        uncertainty_model=UncertaintyModel(
            measurand_id=TARGET_ID, input_ids=INPUT_IDS, correction_ids=(),
            correlation_policy=COVARIANCE_MATRIX,
            correlations=tuple(CorrelationDeclaration(INPUT_IDS[i], INPUT_IDS[j], _decimal(covariance["matrix"][i][j], "covariance"), COVARIANCE_UNIT)
                               for i in range(3) for j in range(i)),
            zero_correlation_justification=None,
            propagation_method="precision-50 Decimal sqrt(p^T C p); C_ii = u_i^2; source-prescribed itemwise cross-run covariance",
            coverage_factor=None, coverage_probability=None,
            coverage_basis="One standard uncertainty; no expanded coverage probability is claimed.",
            limitations=("The three G_i are the stochastic estimator inputs; their already incorporated corrections and deterministic weights are not extra independent stochastic inputs.",
                         "Rounded published component contributions and source correlation assumptions do not reconstruct raw apparatus metrology."),
            uncertainty_basis=ESTIMATOR_INPUT_PROPAGATION,
        ),
        lean_link_identifier=None, evidence_level=EMPIRICAL_RECORD, replication_identifiers=(),
        limitations=("Published-summary reconstruction only; no raw/run-level replication.",
                     "Source-prescribed same-item systematic covariance is a modelling assumption.",
                     "The small discrepancy from the publication's displayed relative uncertainty remains terminal."),
        nonclaims=NONCLAIMS,
    )


def validate_hust_combined_model(model: MeasurementModel, inputs: dict, covariance: dict, *, root: Path = ROOT) -> None:
    validate_measurement_model(model)
    result = reconstruct(inputs, covariance, root=root)
    expected = _assemble_model(inputs, covariance, result)
    if model != expected:
        raise CombinedModelError("combined model differs from authorized inputs, coefficients, covariance or claim scope")
    evaluation = evaluate_measurement_model(model)
    if (evaluation.uncertainty_status != "satisfied" or evaluation.empirical_population_status != "satisfied"
            or evaluation.metrological_provenance_status != "satisfied"
            or evaluation.registered_target_path_status != "no_registered_target_path"
            or evaluation.replication_status != "incomplete"):
        raise CombinedModelError("combined model evidence axes exceed or fall short of the registered scope")


def build_model(inputs: dict | None = None, *, covariance: dict | None = None, root: Path = ROOT) -> MeasurementModel:
    inputs = load_inputs(root) if inputs is None else inputs
    covariance = construct_covariance(inputs, root=root) if covariance is None else covariance
    result = reconstruct(inputs, covariance, root=root)
    model = _assemble_model(inputs, covariance, result)
    validate_hust_combined_model(model, inputs, covariance, root=root)
    return model


def terminal_comparison(result: dict, published: dict | None) -> dict | None:
    if published is None:
        return None
    with localcontext(ARITHMETIC):
        central = _decimal(published["G_decimal"], "published G")
        ppm = _decimal(published["relative_standard_uncertainty_ppm"], "published relative uncertainty")
        return {
            "published": deepcopy(published),
            "G_delta_decimal": str(_decimal(result["G_hat_decimal"], "combined G") - central),
            "relative_uncertainty_delta_ppm": str(_decimal(result["relative_standard_uncertainty_ppm"], "combined relative uncertainty") - ppm),
            "isolation": "Terminal only; no estimator, covariance, source-authorization or acceptance feedback.",
            "limitation": "The rounded-source reconstruction discrepancy is retained; no weights or uncertainty terms are tuned to terminal agreement.",
        }


DEFAULT_COMPARISON = {
    "G_decimal": "6.674484e-11", "relative_standard_uncertainty_ppm": "11.61",
    "source_identifier": "doi:10.1038/s41586-018-0431-5",
    "locator": "Published combined AAF result; Supplement Section 6 AAF paragraph, printed p. 13.",
}


def build_artifact(root: Path = ROOT, *, published: dict | None = DEFAULT_COMPARISON) -> dict:
    prereg = verify_preregistration(root)
    inputs = load_inputs(root)
    covariance = construct_covariance(inputs, root=root)
    result = reconstruct(inputs, covariance, root=root)
    model = _assemble_model(inputs, covariance, result)
    validate_hust_combined_model(model, inputs, covariance, root=root)
    record = measurement_model_record(model)
    record["artifact"] = "HUST 2018 combined AAF uncertainty-qualified empirical MeasurementModel"
    record["scope_and_evidence_level"] = {
        "evidence_level": EMPIRICAL_RECORD,
        "classification": "published_empirical_combined_uncertainty_qualified_reconstruction",
        "empirical_population": True, "uncertainty_qualified": True,
        "new_laboratory_measurement": False, "replication_claim": False,
        "statement": "Source-prescribed weighted combination of the three individually reconstructed depth-2b AAF determinations.",
    }
    artifact = {
        "schema_version": 1, "model": record, "reconstruction": result,
        "input_projection": inputs, "input_projection_sha256": _hash(serialize_artifact(inputs).encode()),
        "source_identities": prereg["allowed_input_artifacts"],
        "combination_authorization": prereg["historical_combination_authority"],
        "covariance": covariance,
        "preregistration": {"path": str(PREREGISTRATION_PATH), "sha256": PREREGISTRATION_SHA256,
                            "commit_sha": PREREGISTRATION_COMMIT, "base_sha": BASELINE,
                            "external_timestamp_anchor": EXTERNAL_ANCHOR},
        "nonclaims": list(NONCLAIMS),
    }
    # A one-way terminal operation after the full model and evidence assessment.
    artifact["terminal_published_comparison"] = terminal_comparison(result, published)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rendered = serialize_artifact(build_artifact())
        if args.check:
            if args.output.read_text() != rendered:
                raise CombinedModelError("combined MeasurementModel artifact is stale")
            print("Combined HUST AAF MeasurementModel, source projection, preregistration ancestry and artifact bytes verified.")
        else:
            if args.output.exists():
                raise CombinedModelError("refusing to overwrite a frozen combined model; create a new version")
            args.output.write_text(rendered)
            print(f"Wrote {args.output}.")
    except (OSError, ValueError, TypeError) as error:
        print(f"invalid combined HUST MeasurementModel: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
