"""Source-bounded HUST AAF combination feasibility; never a MeasurementModel.

Section 6, supplement pp. 12-13, prescribes marginal inverse-variance
weights, followed by correlated uncertainty propagation. It does not prescribe
an inverse-covariance (GLS) estimator. All authoritative arithmetic is Decimal.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess
import sys


from Discovery.source_history import SourceVerificationError, verify_preregistration_freeze


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "hust_2018_aaf_combined_feasibility_preregistration_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "hust_2018_aaf_combined_feasibility_v1.json"
BASELINE = "86479a55dfdc0c631845910ce92679c152c9f0af"
PREREGISTRATION_COMMIT = "9c5a30361af60bfc9831da6c5c6bb867727b1b70"
LOCAL_FREEZE_COMMIT = "607143cb15528f19b670d66910833ce79d7982b9"
LOCAL_FREEZE_OBJECT = (
    "tree 62f670ffbe610c014f6b30c2f8c27aafc3b11a2c\n"
    "parent 86479a55dfdc0c631845910ce92679c152c9f0af\n"
    "author Codex <codex@openai.com> 1788661298 -0400\n"
    "committer Codex <codex@openai.com> 1788661298 -0400\n\n"
    "Preregister HUST AAF combined-estimator feasibility audit\n"
)
PREREGISTRATION_SHA256 = "14cda7a63b8f5ad2c40455300465a3c5b169e14f4ac7390742a172db30ba750a"
INPUT_PROJECTION_SHA256 = "2213beecdd9a83e0cf5117a16dd4dc5a32e4bb043e2104be95f25052a4ffe595"
SUPPLEMENT_SHA256 = "5b61d5c831be98c46e47fcc32f1ade0a680b4af6354d2bc34859d94b22279ffb"
GRAPH_NAME = "hust_2018_aaf_required_inputs_depth_2b_v2.json"
MODELS_NAME = "hust_2018_aaf_depth_2b_measurement_models_v2.json"
SCOPES = ("AAF-I", "AAF-II", "AAF-III")
COMPONENT_IDS = (
    "pendulum_dimensions", "pendulum_attitude", "pendulum_density_inhomogeneity",
    "coating_layer", "clamp_and_ferrule", "other_pendulum_effects",
    "source_mass_masses", "horizontal_source_mass_distance",
    "vertical_source_mass_distance", "source_mass_positions_alignment",
    "fibre_anelasticity", "thermal_effect", "time_base", "rotating_gravity_gradient",
    "shelf_deformation", "magnetic_damper", "air_density", "magnetic_field",
    "angle_encoder", "residual_twist_angle", "statistical_angular_acceleration",
)
STATISTICAL = COMPONENT_IDS[-1]
ARITHMETIC = Context(prec=50, rounding=ROUND_HALF_EVEN)
ROUNDING_BOUND = Decimal("1e-47")
RULE_ID = "section_6_marginal_inverse_variance_then_correlated_propagation"
WEIGHT_RULE = "p_i = (1 / C_ii) / sum_j(1 / C_jj); G_AAF = sum_i(p_i * G_i)"
UNCERTAINTY_RULE = (
    "u_AAF^2 = sum_nonstat_k(sum_i(p_i*u_k_i)^2) "
    "+ sum_i((p_i*u_stat_i)^2) = p^T C p"
)
REQUIRED_CLAIMS = (
    "individual_determinations", "component_inventory", "statistical_classification",
    "cross_run_correlations", "combination_rule", "normalization_or_weighting",
    "singularity_treatment_if_relevant", "sufficient_target_independent_numerical_inputs",
)
NONCLAIMS = (
    "No new measurement of G or physical prediction.",
    "No independent validation of the experiment, apparatus, or completeness of its systematic-error model.",
    "No raw-data or run-level replication; no replication status is promoted.",
    "No TOS authorization or physical independence claim for the AAF runs.",
    "Source-reported correlations are modelling assumptions, not theorems about nature.",
    "Agreement with a terminal published value is not evidence of uniqueness of the procedure.",
    "No combined MeasurementModel or physical-bridge schema change is emitted or authorized by this audit.",
    "No Lean certification of the apparatus or combination procedure.",
)


class FeasibilityError(ValueError):
    """A controlled provenance, input-isolation, or numerical contract failure."""


def serialize_artifact(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise FeasibilityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(data: bytes) -> dict:
    return json.loads(data, object_pairs_hook=_unique_object)


def _keys(value: dict, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise FeasibilityError(f"{label}: missing or undeclared fields (including target inputs)")


def _decimal(value: str, label: str, *, positive: bool = False) -> Decimal:
    if not isinstance(value, str):
        raise FeasibilityError(f"{label}: authoritative numbers must be strings")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise FeasibilityError(f"{label}: malformed decimal") from error
    if not result.is_finite() or (positive and result <= 0):
        raise FeasibilityError(f"{label}: non-finite or non-positive decimal")
    return result


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False
    )
    if result.returncode:
        raise FeasibilityError(f"Git history unavailable or ancestry check failed: {' '.join(args)}")
    return result.stdout


def verify_preregistration(root: Path = ROOT) -> dict:
    """Bind current bytes, frozen commit, its parent, ancestry and intervening history."""
    try:
        current = verify_preregistration_freeze(
            root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
            path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256,
        )
    except SourceVerificationError as error:
        raise FeasibilityError(str(error)) from error
    # Preserve the original local freeze object despite Git push being unavailable.
    # This authenticates its object identity/tree, not an externally attested timestamp.
    body = LOCAL_FREEZE_OBJECT.encode()
    object_id = hashlib.sha1(f"commit {len(body)}\0".encode() + body).hexdigest()
    remote_tree = _git(root, "rev-parse", f"{PREREGISTRATION_COMMIT}^{{tree}}").decode().strip()
    if object_id != LOCAL_FREEZE_COMMIT or not LOCAL_FREEZE_OBJECT.startswith(f"tree {remote_tree}\nparent {BASELINE}\n"):
        raise FeasibilityError("local freeze object identity/tree differs from published preregistration")
    return _json(current)


def load_frozen_records(root: Path = ROOT, *, input_paths: list[str] | None = None) -> tuple[dict, dict]:
    prereg = verify_preregistration(root)
    pins = prereg["allowed_input_artifacts"]
    if input_paths is not None and input_paths != [pin["path"] for pin in pins]:
        raise FeasibilityError("undeclared, missing or reordered input artifact")
    # Only byte identities of protected history are checked; no old experiment is rerun.
    for pin in prereg["preserved_baseline_files"] + pins:
        data = (root / pin["path"]).read_bytes()
        if len(data) != pin["byte_length"] or _hash(data) != pin["sha256"]:
            raise FeasibilityError(f"frozen input/history changed: {pin['path']}")
    records = {Path(pin["path"]).name: _json((root / pin["path"]).read_bytes()) for pin in pins}
    return prereg, records


def project_inputs(records: dict) -> dict:
    """Explicit projection: terminal comparisons/totals never reach the calculator."""
    graph = records[GRAPH_NAME]
    models = records[MODELS_NAME]["models"]
    if len(models) != 3 or tuple(row["component_id"] for row in graph["components"]) != COMPONENT_IDS:
        raise FeasibilityError("source inventory is incomplete, duplicated or mis-scoped")
    runs = []
    for scope, model in zip(SCOPES, models):
        source = model["uncertainty_reconstruction"]
        if source["scope"] != scope:
            raise FeasibilityError("model scopes differ from the declared order")
        components = []
        for row in graph["components"]:
            components.append({
                "component_id": row["component_id"],
                "quantity_id": f"{scope}:u_ppm:{row['component_id']}",
                "value_ppm": row[scope],
            })
        if components != source["components_in_source_order"]:
            raise FeasibilityError("source and individual-model component transcriptions differ")
        runs.append({"scope": scope, "G_hat_decimal": source["G_hat_decimal"], "components": components})
    result = {"runs": runs}
    validate_inputs(result)
    return result


def validate_inputs(inputs: dict) -> None:
    _keys(inputs, {"runs"}, "upstream projection")
    if not isinstance(inputs["runs"], list) or len(inputs["runs"]) != 3:
        raise FeasibilityError("exactly three distinct AAF scopes required")
    for scope, run in zip(SCOPES, inputs["runs"]):
        _keys(run, {"scope", "G_hat_decimal", "components"}, scope)
        if run["scope"] != scope:
            raise FeasibilityError("renamed, duplicated or mis-scoped AAF run")
        _decimal(run["G_hat_decimal"], scope, positive=True)
        if not isinstance(run["components"], list) or len(run["components"]) != 21:
            raise FeasibilityError("missing or duplicated uncertainty component")
        for component_id, component in zip(COMPONENT_IDS, run["components"]):
            _keys(component, {"component_id", "quantity_id", "value_ppm"}, "component")
            if component["component_id"] != component_id or component["quantity_id"] != f"{scope}:u_ppm:{component_id}":
                raise FeasibilityError("renamed, duplicated or mis-scoped component")
            _decimal(component["value_ppm"], component_id, positive=True)
    if _hash(serialize_artifact(inputs).encode()) != INPUT_PROJECTION_SHA256:
        raise FeasibilityError("source transcription/central value changed")


def source_evidence() -> dict:
    """Reviewed equations and short excerpts; deductions are explicitly identified."""
    def claim(source, locator, quotes, interpretation):
        return {"status": "supported", "source_id": source, "locator": locator,
                "quote_ids": quotes, "interpretation": interpretation}

    supplement = "supplementary_information"
    table = "official_nature_table_1"
    return {
        "individual_determinations": claim(supplement, "Supplementary Table 3, printed p. 20; Section 6, printed p. 13, AAF paragraph", ["runs"], "Ga, Gb, Gc refer in order to the three AAF runs; reuse their pinned reconstructed central values."),
        "component_inventory": claim(table, "Table 1, Nature 560, p. 584; AAF-I/II/III columns and 21 applicable rows", ["ppm"], "Use the complete per-run direct relative standard-uncertainty inventory already authorized at depth 2b, excluding displayed totals."),
        "statistical_classification": claim(supplement, "Section 6, printed p. 13, AAF paragraph, sentences 2-3", ["independent"], "Only the statistical angular-acceleration row is independent across runs; the remaining 20 rows are non-statistical."),
        "cross_run_correlations": claim(supplement, "Section 6, printed p. 13: AAF paragraph and preceding simplified combined-uncertainty equation", ["correlated", "method"], "Same non-statistical item has rho=1 across runs; statistical row has rho=0 off diagonal. Different items do not mix in the source's sum over itemwise squares. This is the published model, not physical independence."),
        "combination_rule": claim(supplement, "Section 6, printed p. 12: two-run weights and final p_k/G_ToS equations; printed p. 13: uncertainty equation and final AAF sentence", ["method"], "The AAF sentence incorporates the preceding explicit method. Both weighting equations normalize inverse marginal total variances; the uncertainty equation propagates same-item correlations. Deduction: apply those same equations to three AAF determinations, without TOS-specific intermediate fibre/background terms."),
        "normalization_or_weighting": claim(supplement, "Section 6, printed p. 12, p_k equation immediately before G_ToS", ["weight", "method"], WEIGHT_RULE + ". u_i is the total standard uncertainty of G_i, so C_ii=u_i^2; use reconstructed absolute contributions, not displayed ppm totals or statistical-only weights."),
        "singularity_treatment_if_relevant": claim(supplement, "Section 6, printed pp. 12-13, weight and uncertainty equations", ["method"], "Mathematical deduction: no covariance-matrix inverse occurs. Positive individual variances make all weight denominators nonzero; singularity requires no additional matrix procedure for this prescription."),
        "sufficient_target_independent_numerical_inputs": claim(table, "Table 1 AAF columns; Supplementary Table 3 and existing pinned depth-2b models", ["ppm"], "The existing central reconstructions and 63 source decimal contributions supply every numerical operand. No final target or fitted coefficient is required."),
    }


QUOTES = {
    "runs": "three values of G",
    "independent": "independent between the three experiments",
    "correlated": "100% correlation",
    "method": "With the same method as discussed above",
    "weight": "relative weight",
    "ppm": "parts per million",
}


def assess_evidence(evidence: dict) -> tuple[list[str], dict]:
    if not isinstance(evidence, dict) or set(evidence) - set(REQUIRED_CLAIMS):
        raise FeasibilityError("undeclared source claim or estimator option")
    canonical = source_evidence()
    reasons = []
    inventory = {}
    for name in REQUIRED_CLAIMS:
        record = evidence.get(name, {"status": "missing"})
        if not isinstance(record, dict):
            raise FeasibilityError("malformed evidence record")
        status = record.get("status")
        if status not in {"supported", "missing", "ambiguous", "unverified"}:
            raise FeasibilityError("invalid evidence status")
        if status == "supported":
            if record != canonical[name]:
                raise FeasibilityError("unreviewed source rule, normalization or weight tuning")
        elif status == "unverified":
            reasons.append("SOURCE_UNVERIFIED")
        elif name in {"combination_rule", "normalization_or_weighting"}:
            reasons.append("AMBIGUOUS_COMBINATION_RULE" if status == "ambiguous" else "MISSING_COMBINATION_RULE")
        elif name in {"component_inventory", "statistical_classification", "cross_run_correlations"}:
            reasons.append("AMBIGUOUS_COVARIANCE_MAPPING" if status == "ambiguous" else "INCOMPLETE_COVARIANCE_MAPPING")
        elif name == "singularity_treatment_if_relevant":
            reasons.append("UNAUTHORIZED_MATRIX_PROCEDURE")
        else:
            reasons.append("MISSING_NUMERICAL_INPUT")
        inventory[name] = deepcopy(record)
    return sorted(set(reasons)), inventory


def correlation_inventory() -> list[dict]:
    return [{"component_id": name, "off_diagonal_rho": "0" if name == STATISTICAL else "1"}
            for name in COMPONENT_IDS]


def validate_correlations(correlations: list[dict]) -> None:
    if not isinstance(correlations, list) or len(correlations) != 21:
        raise FeasibilityError("missing or undeclared covariance term")
    for expected, entry in zip(correlation_inventory(), correlations):
        _keys(entry, {"component_id", "off_diagonal_rho"}, "covariance term")
        rho = _decimal(entry["off_diagonal_rho"], "correlation")
        if not Decimal("-1") <= rho <= Decimal("1"):
            raise FeasibilityError("correlation outside [-1,1]")
        if entry != expected:
            raise FeasibilityError("covariance component or source correlation rule changed")


def _absolute_components(inputs: dict) -> list[list[Decimal]]:
    return [[Decimal(run["G_hat_decimal"]).copy_abs() * Decimal(c["value_ppm"]) * Decimal("1e-6")
             for c in run["components"]] for run in inputs["runs"]]


def matrix_diagnostics(matrix: list[list[str]]) -> dict:
    """All principal minors, computed exactly from serialized finite Decimals."""
    if not isinstance(matrix, list) or len(matrix) != 3 or any(not isinstance(row, list) or len(row) != 3 for row in matrix):
        raise FeasibilityError("covariance matrix must be 3 by 3")
    decimals = [[_decimal(x, "covariance") for x in row] for row in matrix]
    if any(decimals[i][j] != decimals[j][i] for i in range(3) for j in range(3)):
        raise FeasibilityError("asymmetric covariance matrix")
    f = [[Fraction(x) for x in row] for row in decimals]
    minors = []
    for size in (1, 2, 3):
        for indices in combinations(range(3), size):
            if size == 1:
                value = f[indices[0]][indices[0]]
            elif size == 2:
                i, j = indices
                value = f[i][i] * f[j][j] - f[i][j] * f[j][i]
            else:
                value = (f[0][0] * (f[1][1]*f[2][2] - f[1][2]*f[2][1])
                         - f[0][1] * (f[1][0]*f[2][2] - f[1][2]*f[2][0])
                         + f[0][2] * (f[1][0]*f[2][1] - f[1][1]*f[2][0]))
            if value < 0:
                raise FeasibilityError("negative/non-PSD covariance: negative principal minor")
            minors.append({"scopes": [SCOPES[i] for i in indices], "exact_fraction": str(value),
                           "sign": "positive" if value > 0 else "zero"})
    return {"symmetric": True, "positive_semidefinite": True,
            "positive_definite": all(x["sign"] == "positive" for x in minors),
            "invertible": minors[-1]["sign"] == "positive", "principal_minors": minors,
            "inverse_required": False, "inverse_or_regularization_used": False}


def construct_covariance(inputs: dict, correlations: list[dict]) -> dict:
    validate_inputs(inputs)
    validate_correlations(correlations)
    with localcontext(ARITHMETIC):
        u = _absolute_components(inputs)
        matrix = [[Decimal("0") for _ in SCOPES] for _ in SCOPES]
        terms = []
        for k, entry in enumerate(correlations):
            rho = Decimal(entry["off_diagonal_rho"])
            for i in range(3):
                for j in range(3):
                    matrix[i][j] += (Decimal("1") if i == j else rho) * u[i][k] * u[j][k]
            terms.append({**entry, "absolute_standard_contributions": [str(u[i][k]) for i in range(3)]})
        serialized = [[str(x) for x in row] for row in matrix]
    diagnostics = matrix_diagnostics(serialized)
    return {"scopes": list(SCOPES), "unit": "(m^3 kg^-1 s^-2)^2", "matrix": serialized,
            "component_terms": terms, "diagnostics": diagnostics}


def validate_covariance(matrix: list[list[str]], inputs: dict, correlations: list[dict]) -> dict:
    diagnostics = matrix_diagnostics(matrix)
    expected = construct_covariance(inputs, correlations)["matrix"]
    for i in range(3):
        if Decimal(matrix[i][i]) != Decimal(expected[i][i]):
            raise FeasibilityError("incorrect diagonal variance")
    if [[Decimal(x) for x in row] for row in matrix] != [[Decimal(x) for x in row] for row in expected]:
        raise FeasibilityError("covariance does not equal declared component contributions")
    return diagnostics


def combine_by_source_rule(inputs: dict, covariance: dict, *, rule_id: str = RULE_ID) -> dict:
    if rule_id != RULE_ID:
        raise FeasibilityError("unreviewed estimator; no GLS, weight tuning or matrix procedure authorized")
    _keys(covariance, {"scopes", "unit", "matrix", "component_terms", "diagnostics"}, "covariance")
    for term in covariance["component_terms"]:
        _keys(term, {"component_id", "off_diagonal_rho", "absolute_standard_contributions"}, "covariance component")
    correlations = [{k: term[k] for k in ("component_id", "off_diagonal_rho")}
                    for term in covariance["component_terms"]]
    validate_covariance(covariance["matrix"], inputs, correlations)
    if covariance != construct_covariance(inputs, correlations):
        raise FeasibilityError("covariance component trace or diagnostics changed")
    with localcontext(ARITHMETIC):
        matrix = [[Decimal(x) for x in row] for row in covariance["matrix"]]
        if any(matrix[i][i] <= 0 for i in range(3)):
            raise FeasibilityError("non-positive marginal variance; source weights undefined")
        inverse_variances = [Decimal("1") / matrix[i][i] for i in range(3)]
        normalizer = sum(inverse_variances, Decimal("0"))
        weights = [x / normalizer for x in inverse_variances]
        estimate = sum((p * Decimal(run["G_hat_decimal"]) for p, run in zip(weights, inputs["runs"])), Decimal("0"))
        # Author's componentwise equation is the primary uncertainty calculation.
        u = _absolute_components(inputs)
        variance = sum((sum((weights[i] * u[i][k] for i in range(3)), Decimal("0")) ** 2
                        for k in range(20)), Decimal("0"))
        variance += sum(((weights[i] * u[i][20]) ** 2 for i in range(3)), Decimal("0"))
        quadratic = sum((weights[i] * matrix[i][j] * weights[j] for i in range(3) for j in range(3)), Decimal("0"))
        relative_delta = abs(variance - quadratic) / variance
        if relative_delta > ROUNDING_BOUND:
            raise FeasibilityError("componentwise and quadratic uncertainty calculations disagree")
        if abs(sum(weights, Decimal("0")) - Decimal("1")) > ROUNDING_BOUND:
            raise FeasibilityError("weights are not normalized")
        standard = variance.sqrt()
        return {"rule_id": RULE_ID, "weights": [str(x) for x in weights],
                "weight_sum": str(sum(weights, Decimal("0"))),
                "G_hat_decimal": str(estimate), "standard_uncertainty_decimal": str(standard),
                "unit": "m^3 kg^-1 s^-2", "variance_decimal": str(variance),
                "quadratic_form_variance_decimal": str(quadratic),
                "relative_arithmetic_disagreement": str(relative_delta),
                "relative_standard_uncertainty_ppm": str(standard / abs(estimate) * Decimal("1e6"))}


def audit(inputs: dict, evidence: dict | None = None, *, terminal_comparison: dict | None = None) -> dict:
    validate_inputs(inputs)
    reasons, inventory = assess_evidence(source_evidence() if evidence is None else evidence)
    covariance_requirements = ("individual_determinations", "component_inventory",
                               "statistical_classification", "cross_run_correlations",
                               "sufficient_target_independent_numerical_inputs")
    covariance = None
    if all(inventory[key]["status"] == "supported" for key in covariance_requirements):
        covariance = construct_covariance(inputs, correlation_inventory())
    reconstruction = None
    if not reasons:
        reconstruction = combine_by_source_rule(inputs, covariance)
    # Terminal information is attached only after all authoritative calculations.
    result = {"decision": "NO-GO" if reasons else "GO", "reason_codes": reasons,
              "required_source_claims": inventory, "covariance": covariance,
              "combination_rule": None if reasons else {"id": RULE_ID, "weights_and_estimate": WEIGHT_RULE,
                                                         "uncertainty": UNCERTAINTY_RULE},
              "reconstructed_combined_result": reconstruction,
              "terminal_published_comparison": deepcopy(terminal_comparison),
              "nonclaims": list(NONCLAIMS)}
    return result


def individual_diagnostics(inputs: dict, records: dict) -> list[dict]:
    result = []
    with localcontext(ARITHMETIC):
        u = _absolute_components(inputs)
        for i, (run, model) in enumerate(zip(inputs["runs"], records[MODELS_NAME]["models"])):
            squares = sum((Decimal(c["value_ppm"]) ** 2 for c in run["components"]), Decimal("0"))
            rss = squares.sqrt()
            absolute = abs(Decimal(run["G_hat_decimal"])) * rss * Decimal("1e-6")
            diagonal = sum((v*v for v in u[i]), Decimal("0"))
            relative_delta = abs(diagonal.sqrt() - absolute) / absolute
            historical = model["uncertainty_reconstruction"]
            if (str(squares) != historical["sum_of_squares"]
                    or str(rss) != historical["relative_standard_uncertainty_ppm"]
                    or str(absolute) != historical["absolute_standard_uncertainty_decimal"]
                    or relative_delta > ROUNDING_BOUND):
                raise FeasibilityError("individual variance/RSS reconstruction changed")
            result.append({"scope": run["scope"], "G_hat_decimal": run["G_hat_decimal"],
                           "component_count": 21, "sum_of_squares_ppm": str(squares),
                           "relative_standard_uncertainty_ppm": str(rss),
                           "absolute_standard_uncertainty_decimal": str(absolute),
                           "diagonal_variance": str(diagonal),
                           "diagonal_rss_relative_rounding_difference": str(relative_delta),
                           "historical_reconstruction_preserved": True})
    return result


def build_artifact(root: Path = ROOT) -> dict:
    prereg, records = load_frozen_records(root)
    inputs = project_inputs(records)
    result = audit(inputs)
    if result["decision"] == "GO":
        result["terminal_published_comparison"] = terminal_comparison(result["reconstructed_combined_result"])
    result.update({
        "schema_version": 1, "audit_id": "hust_2018_aaf_combined_feasibility_v1",
        "baseline_main_sha": BASELINE,
        "preregistration": {"path": PREREGISTRATION_PATH.as_posix(), "sha256": PREREGISTRATION_SHA256,
                            "commit_sha": PREREGISTRATION_COMMIT, "local_pre_review_freeze_commit": LOCAL_FREEZE_COMMIT,
                            "local_freeze_commit_object": LOCAL_FREEZE_OBJECT,
                            "transport_note": "Identical preregistration-only tree published through the connector after direct push failed; local freeze precedes source review, remote publication precedes all arithmetic."},
        "source_and_individual_artifact_dependencies": prereg["allowed_input_artifacts"],
        "historical_preservation": {"baseline": BASELINE, "all_hashes_unchanged": True,
                                    "files": prereg["preserved_baseline_files"]},
        "scopes": list(SCOPES), "input_projection_sha256": INPUT_PROJECTION_SHA256,
        "component_inventory": inputs,
        "individual_reconstructions": individual_diagnostics(inputs, records),
        "source_review": {"supplement_sha256": SUPPLEMENT_SHA256,
                          "supplement_byte_length": 2711453,
                          "verification": "Official publisher PDF recovered during this audit and matched the existing binary pin; equations on printed pp. 12-13 visually inspected. Table 1 and individual inputs reused under their existing official-source authorization pins.",
                          "review_scope": "Supplement Section 6 (printed pp. 12-13; PDF pages 13-14), Table 3 and the existing pinned Table 1/individual reconstruction records. Sufficient evidence found without raw-data intake.",
                          "short_quotes": QUOTES},
        "arithmetic_policy": prereg["arithmetic_policy"],
        "authorization_boundary": {"combined_measurement_model_emitted": False,
                                   "combined_measurement_model_authorized": False,
                                   "next_step": "A separate preregistration may design the combined-result contract after independent audit of this feasibility GO."},
    })
    return result


def terminal_comparison(reconstructed: dict) -> dict:
    """Downstream comparison only; never called by any computational function."""
    published_g = "6.674484e-11"
    published_u = "0.000078e-11"
    published_ppm = "11.61"
    with localcontext(ARITHMETIC):
        return {
            "source_url": "https://www.nature.com/articles/s41586-018-0431-5",
            "locator": "Abstract (central value and relative uncertainty). Absolute uncertainty retained in frozen hust_2018_aaf_source_audit_v1.md, Fail-closed disposition, combined AAF paragraph.",
            "published_G_decimal": published_g,
            "published_standard_uncertainty_decimal": published_u,
            "published_relative_standard_uncertainty_ppm": published_ppm,
            "G_delta_decimal": str(Decimal(reconstructed["G_hat_decimal"]) - Decimal(published_g)),
            "standard_uncertainty_delta_decimal": str(Decimal(reconstructed["standard_uncertainty_decimal"]) - Decimal(published_u)),
            "relative_uncertainty_delta_ppm": str(Decimal(reconstructed["relative_standard_uncertainty_ppm"]) - Decimal(published_ppm)),
            "used_as_input_or_decision_criterion": False,
            "qualification": "Nominal reconstruction from rounded published inputs. All differences are retained; no coefficient or weight is adjusted to match a terminal number. The extra Decimal digits are computational precision, not additional measurement precision.",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        artifact = build_artifact()
        expected = serialize_artifact(artifact).encode()
        output = ROOT / DEFAULT_OUTPUT
        if args.check:
            if not output.exists() or output.read_bytes() != expected:
                raise FeasibilityError("combined feasibility artifact is missing or stale")
        else:
            output.write_bytes(expected)
    except (FeasibilityError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"HUST combined feasibility failed: {error}", file=sys.stderr)
        return 1
    print(f"HUST AAF combined feasibility: {artifact['decision']}; artifact {'current' if args.check else 'written'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
