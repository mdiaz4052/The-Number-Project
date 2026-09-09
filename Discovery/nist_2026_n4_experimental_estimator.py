"""Exact project-defined n=4 experimental-covariance estimator for NIST 2026."""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import SourceVerificationError


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "nist_2026_n4_experimental_estimator_preregistration_v1.json"
UPSTREAM_FEASIBILITY_PATH = DIRECTORY / "nist_2026_estimator_feasibility_v1.json"
UPSTREAM_ATTESTATION_PATH = DIRECTORY / "nist_2026_estimator_source_attestation_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "nist_2026_n4_experimental_estimator_v1.json"
BASELINE = "30227abeb3f6ab009b70c429e491bb015e798542"
PREREGISTRATION_COMMIT = "504200ae817a60b211decec4432b43be9087e9e3"
PREREGISTRATION_SHA256 = "e83f08f323aa1e397be1b6ef50e25d541d05307949148efbff02971e8eaf4ca6"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/47",
    "created_at": "2026-09-09T00:26:16Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "outcome_blind": False,
}
READ_CLOSURE_TEST_PATH = "tests/test_nist_2026_estimator_feasibility.py"
SOURCE_PATHS = (
    "Discovery/nist_2026_n4_experimental_estimator.py",
    "Notes/NIST2026N4ExperimentalEstimatorSpecification.md",
    "Notes/NIST2026N4ExperimentalEstimator.md",
    PREREGISTRATION_PATH.as_posix(),
    UPSTREAM_FEASIBILITY_PATH.as_posix(),
    UPSTREAM_ATTESTATION_PATH.as_posix(),
    READ_CLOSURE_TEST_PATH,
)
DECIMAL_CONTEXT = Context(prec=60)


class NISTN4EstimatorError(ValueError):
    """Invalid frozen input, upstream authorization, chronology, or estimator state."""


def serialize_artifact(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fraction_record(value: Fraction) -> dict:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise NISTN4EstimatorError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(data, object_pairs_hook=unique)
    except json.JSONDecodeError as error:
        raise NISTN4EstimatorError("malformed JSON") from error


def decimal_fraction(value: str) -> Fraction:
    if not isinstance(value, str):
        raise NISTN4EstimatorError("authoritative decimal must be a string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise NISTN4EstimatorError("malformed authoritative decimal") from error
    if not number.is_finite():
        raise NISTN4EstimatorError("authoritative decimal must be finite")
    return Fraction(number)


def _decimal_text(value: Fraction, places: int = 15) -> str:
    with localcontext(DECIMAL_CONTEXT):
        number = Decimal(value.numerator) / Decimal(value.denominator)
        return f"{number:.{places}f}"


def _sqrt_decimal(value: Fraction, places: int = 18) -> str:
    if value < 0:
        raise NISTN4EstimatorError("cannot take square root of negative variance")
    with localcontext(DECIMAL_CONTEXT):
        number = (Decimal(value.numerator) / Decimal(value.denominator)).sqrt()
        return f"{number:.{places}f}"


def _exact_keys(value: dict, expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise NISTN4EstimatorError(f"{label} keys differ from frozen schema")


def validate_input_projection(projection: dict) -> dict:
    if not isinstance(projection, dict):
        raise NISTN4EstimatorError("input projection must be an object")
    _exact_keys(projection, {"order", "measurements", "correlation_matrix", "precision_policy"}, "projection")
    order = projection["order"]
    rows = projection["measurements"]
    matrix = projection["correlation_matrix"]
    if not isinstance(order, list) or len(order) != 4 or len(set(order)) != 4:
        raise NISTN4EstimatorError("input order must contain four distinct ids")
    if not isinstance(rows, list) or len(rows) != 4:
        raise NISTN4EstimatorError("four measurements are required")
    expected_row_keys = {
        "id", "G_decimal_in_1e_minus_11_units", "printed_decimal_places",
        "relative_standard_uncertainty_ppm",
    }
    values = []
    relative = []
    places = []
    for ident, row in zip(order, rows):
        if not isinstance(row, dict):
            raise NISTN4EstimatorError("measurement row must be an object")
        _exact_keys(row, expected_row_keys, "measurement")
        if row["id"] != ident:
            raise NISTN4EstimatorError("measurement order differs from frozen order")
        value = decimal_fraction(row["G_decimal_in_1e_minus_11_units"])
        uncertainty = decimal_fraction(row["relative_standard_uncertainty_ppm"])
        digits = row["printed_decimal_places"]
        if value <= 0 or uncertainty <= 0:
            raise NISTN4EstimatorError("measurement and standard uncertainty must be positive")
        if not isinstance(digits, int) or digits < 0:
            raise NISTN4EstimatorError("printed decimal places must be a nonnegative integer")
        text = row["G_decimal_in_1e_minus_11_units"]
        if "." not in text or len(text.rsplit(".", 1)[1]) != digits:
            raise NISTN4EstimatorError("display precision differs from frozen decimal text")
        values.append(value)
        relative.append(uncertainty)
        places.append(digits)
    if not isinstance(matrix, list) or len(matrix) != 4 or any(not isinstance(row, list) or len(row) != 4 for row in matrix):
        raise NISTN4EstimatorError("correlation matrix must be 4x4")
    correlation = [[decimal_fraction(cell) for cell in row] for row in matrix]
    for i in range(4):
        if correlation[i][i] != 1:
            raise NISTN4EstimatorError("correlation diagonal must be one")
        for j in range(4):
            if correlation[i][j] != correlation[j][i] or abs(correlation[i][j]) > 1:
                raise NISTN4EstimatorError("invalid correlation geometry")
    return {
        "order": tuple(order),
        "values": tuple(values),
        "relative_uncertainties_ppm": tuple(relative),
        "printed_decimal_places": tuple(places),
        "correlation": tuple(tuple(row) for row in correlation),
    }


def verify_preregistration(root: Path = ROOT) -> dict:
    try:
        data = verify_preregistration_freeze(
            root,
            baseline=BASELINE,
            commit=PREREGISTRATION_COMMIT,
            path=PREREGISTRATION_PATH.as_posix(),
            sha256=PREREGISTRATION_SHA256,
        )
    except SourceVerificationError as error:
        raise NISTN4EstimatorError(str(error)) from error
    protocol = _json(data)
    if protocol.get("schema_version") != 1 or protocol.get("experiment_id") != "nist_2026_n4_experimental_correlated_estimator_v1":
        raise NISTN4EstimatorError("frozen experiment identity differs")
    if protocol.get("intended_base_sha") != BASELINE:
        raise NISTN4EstimatorError("frozen base differs")
    if protocol.get("known_prior_information", {}).get("outcome_blind") is not False:
        raise NISTN4EstimatorError("n=4 estimator must not claim outcome blindness")
    validate_input_projection(protocol.get("input_projection"))
    required = protocol.get("preregistered_preconditions", {})
    if "DM-073" not in required.get("freeze_control", "") or "DM-077" not in required.get("read_closure_repair", ""):
        raise NISTN4EstimatorError("frozen prerequisite declarations are incomplete")
    return protocol


def validate_upstream_records(protocol: dict, feasibility: dict, attestation: dict) -> dict:
    upstream = protocol["upstream_authorization"]
    required_decisions = upstream["required_decisions"]
    if feasibility.get("decision") != {
        "experimental_covariance": required_decisions["experimental_covariance"],
        "published_bayesian_consensus": required_decisions["published_bayesian_consensus"],
        "authorized_next_step": feasibility.get("decision", {}).get("authorized_next_step"),
        "common_constant_comparison": required_decisions["common_constant_comparison"],
        "equation_64_reproduction": required_decisions["equation_64_reproduction"],
    }:
        raise NISTN4EstimatorError("upstream feasibility decisions differ from frozen authorization")
    if feasibility["decision"].get("authorized_next_step") != "preregister_n4_experimental_covariance_correlated_estimator_certificate":
        raise NISTN4EstimatorError("upstream feasibility does not authorize the n=4 estimator")
    blockers = tuple(
        item.get("id") for item in feasibility.get("published_bayesian_consensus_layer", {}).get(
            "missing_result_driving_information", []
        )
    )
    if blockers != tuple(upstream["required_bayesian_blocker_ids"]):
        raise NISTN4EstimatorError("Bayesian NO-GO blocker inventory differs from freeze")
    source = attestation.get("source", {})
    if source.get("doi") != protocol["source"]["doi"] or source.get("nist_pdf") != protocol["source"]["nist_pdf"]:
        raise NISTN4EstimatorError("upstream source identity differs from freeze")
    frozen = validate_input_projection(protocol["input_projection"])
    experimental = attestation.get("experimental_layer", {})
    if tuple(experimental.get("input_order", [])) != frozen["order"]:
        raise NISTN4EstimatorError("attested input order differs from freeze")
    table16 = experimental.get("table_16", {}).get("measurements", [])
    if len(table16) != 4:
        raise NISTN4EstimatorError("attested Table 16 inventory incomplete")
    for ident, expected, row in zip(frozen["order"], frozen["values"], table16):
        if row.get("id") != ident or decimal_fraction(row.get("G_decimal_in_1e_minus_11_units")) != expected:
            raise NISTN4EstimatorError("attested Table 16 value differs from freeze")
    table18 = experimental.get("table_18", {})
    diagonal = tuple(decimal_fraction(value) for value in table18.get("diagonal_relative_standard_uncertainty_ppm", []))
    if diagonal != frozen["relative_uncertainties_ppm"]:
        raise NISTN4EstimatorError("attested Table 18 diagonal differs from freeze")
    attested_correlation = tuple(
        tuple(decimal_fraction(cell) for cell in row) for row in table18.get("correlation_matrix", [])
    )
    if attested_correlation != frozen["correlation"]:
        raise NISTN4EstimatorError("attested Table 18 correlation differs from freeze")
    return {
        "feasibility_artifact_id": feasibility.get("artifact_id"),
        "source_attestation_id": attestation.get("artifact_id"),
        "decisions": dict(required_decisions),
        "bayesian_blocker_ids": list(blockers),
    }


def load_upstream_authorization(protocol: dict, root: Path = ROOT) -> dict:
    feasibility = _json((root / UPSTREAM_FEASIBILITY_PATH).read_bytes())
    attestation = _json((root / UPSTREAM_ATTESTATION_PATH).read_bytes())
    return validate_upstream_records(protocol, feasibility, attestation)


def determinant(matrix: list[list[Fraction]]) -> Fraction:
    n = len(matrix)
    if not n or any(len(row) != n for row in matrix):
        raise NISTN4EstimatorError("square matrix required")
    work = [row[:] for row in matrix]
    result = Fraction(1)
    for column in range(n):
        pivot = next((row for row in range(column, n) if work[row][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            result = -result
        pivot_value = work[column][column]
        result *= pivot_value
        for row in range(column + 1, n):
            factor = work[row][column] / pivot_value
            for index in range(column, n):
                work[row][index] -= factor * work[column][index]
    return result


def leading_principal_minors(matrix: list[list[Fraction]]) -> tuple[Fraction, ...]:
    return tuple(determinant([row[:size] for row in matrix[:size]]) for size in range(1, len(matrix) + 1))


def solve_exact(matrix: list[list[Fraction]], rhs: list[Fraction]) -> tuple[Fraction, ...]:
    n = len(matrix)
    if not n or len(rhs) != n or any(len(row) != n for row in matrix):
        raise NISTN4EstimatorError("linear system dimensions differ")
    work = [matrix[row][:] + [rhs[row]] for row in range(n)]
    for column in range(n):
        pivot = next((row for row in range(column, n) if work[row][column]), None)
        if pivot is None:
            raise NISTN4EstimatorError("singular estimator covariance")
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
        pivot_value = work[column][column]
        work[column] = [value / pivot_value for value in work[column]]
        for row in range(n):
            if row == column:
                continue
            factor = work[row][column]
            if factor:
                work[row] = [
                    work[row][index] - factor * work[column][index]
                    for index in range(n + 1)
                ]
    return tuple(work[row][-1] for row in range(n))


def decimal_cell(value: str, places: int) -> tuple[Fraction, Fraction]:
    midpoint = decimal_fraction(value)
    half_width = Fraction(1, 2 * (10 ** places))
    return midpoint - half_width, midpoint + half_width


def linear_enclosure(cells: tuple[tuple[Fraction, Fraction], ...], weights: tuple[Fraction, ...]) -> tuple[Fraction, Fraction]:
    if len(cells) != len(weights) or not cells:
        raise NISTN4EstimatorError("linear enclosure dimensions differ")
    low = Fraction(0)
    high = Fraction(0)
    for (left, right), weight in zip(cells, weights):
        if left > right:
            raise NISTN4EstimatorError("invalid input cell")
        if weight >= 0:
            low += weight * left
            high += weight * right
        else:
            low += weight * right
            high += weight * left
    return low, high


def estimator_state(input_projection: dict) -> dict:
    """Build the estimator from frozen experimental summaries only."""
    inputs = validate_input_projection(input_projection)
    values = inputs["values"]
    relative = inputs["relative_uncertainties_ppm"]
    correlation = inputs["correlation"]
    absolute_uncertainties = tuple(
        values[index] * relative[index] / 1_000_000 for index in range(4)
    )
    covariance = [
        [correlation[i][j] * absolute_uncertainties[i] * absolute_uncertainties[j] for j in range(4)]
        for i in range(4)
    ]
    minors = leading_principal_minors(covariance)
    if not all(value > 0 for value in minors):
        raise NISTN4EstimatorError("absolute estimator covariance is not positive definite")
    solution = solve_exact(covariance, [Fraction(1)] * 4)
    normalization = sum(solution)
    if normalization == 0:
        raise NISTN4EstimatorError("estimator normalization denominator is zero")
    weights = tuple(value / normalization for value in solution)
    if sum(weights) != 1:
        raise NISTN4EstimatorError("estimator weights do not sum to one")
    estimate = sum(weight * value for weight, value in zip(weights, values))
    variance = Fraction(1, 1) / normalization
    quadratic = sum(
        weights[i] * sum(covariance[i][j] * weights[j] for j in range(4))
        for i in range(4)
    )
    if variance != quadratic or variance <= 0:
        raise NISTN4EstimatorError("estimator variance identities disagree")
    rows = input_projection["measurements"]
    cells = tuple(
        decimal_cell(row["G_decimal_in_1e_minus_11_units"], row["printed_decimal_places"])
        for row in rows
    )
    enclosure = linear_enclosure(cells, weights)
    return {
        "order": inputs["order"],
        "values": values,
        "relative_uncertainties_ppm": relative,
        "absolute_uncertainties": absolute_uncertainties,
        "correlation": correlation,
        "covariance": tuple(tuple(row) for row in covariance),
        "leading_principal_minors": minors,
        "weights": weights,
        "normalization": normalization,
        "estimate": estimate,
        "variance": variance,
        "input_cells": cells,
        "aggregate_enclosure": enclosure,
    }


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_implementation_chronology(root: Path = ROOT) -> None:
    anchor = _timestamp(EXTERNAL_ANCHOR["created_at"])
    freeze = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%aI%x00%cI", PREREGISTRATION_COMMIT],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split("\x00")
    if len(freeze) != 2 or any(_timestamp(value) >= anchor for value in freeze):
        raise NISTN4EstimatorError("freeze does not precede GitHub anchor")
    test_changes = subprocess.run(
        ["git", "-C", str(root), "log", "--full-history", "--reverse", "--format=%H%x00%aI%x00%cI", f"{PREREGISTRATION_COMMIT}..HEAD", "--", READ_CLOSURE_TEST_PATH],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    if not test_changes:
        raise NISTN4EstimatorError("read-closure prerequisite was not committed")
    prerequisite = test_changes[0].split("\x00")
    if len(prerequisite) != 3 or any(_timestamp(value) <= anchor for value in prerequisite[1:]):
        raise NISTN4EstimatorError("read-closure prerequisite does not postdate anchor")
    added = subprocess.run(
        ["git", "-C", str(root), "log", "--full-history", "--diff-filter=A", "--reverse", "--format=%H%x00%aI%x00%cI", "--", "Discovery/nist_2026_n4_experimental_estimator.py"],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    if not added:
        raise NISTN4EstimatorError("n=4 estimator source has no committed introduction")
    fields = added[0].split("\x00")
    if len(fields) != 3 or any(_timestamp(value) <= anchor for value in fields[1:]):
        raise NISTN4EstimatorError("n=4 estimator implementation does not postdate anchor")
    if subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, fields[0]], capture_output=True).returncode:
        raise NISTN4EstimatorError("n=4 estimator does not descend from freeze")
    if subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", prerequisite[0], fields[0]], capture_output=True).returncode or prerequisite[0] == fields[0]:
        raise NISTN4EstimatorError("read-closure repair was not established before estimator source")
    parent_test = subprocess.run(
        ["git", "-C", str(root), "show", f"{fields[0]}^:{READ_CLOSURE_TEST_PATH}"],
        capture_output=True, check=True,
    ).stdout
    if b"test_build_artifact_read_closure_is_exact" not in parent_test:
        raise NISTN4EstimatorError("estimator parent does not contain permanent read-closure test")


def source_snapshot(root: Path = ROOT) -> dict:
    commit = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", *SOURCE_PATHS],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    files = []
    for path in SOURCE_PATHS:
        current = (root / path).read_bytes()
        recorded = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True,
        )
        if recorded.returncode or recorded.stdout != current:
            raise NISTN4EstimatorError("commit n=4 result-driving source before artifact emission")
        files.append({"path": path, "sha256": digest(current)})
    return {"source_commit_sha": commit, "files": files}


def _matrix_records(matrix) -> list[list[dict]]:
    return [[fraction_record(value) for value in row] for row in matrix]


def _interval_record(interval) -> dict:
    return {"low": fraction_record(interval[0]), "high": fraction_record(interval[1])}


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    authorization = load_upstream_authorization(protocol, root)
    state = estimator_state(protocol["input_projection"])
    estimate_decimal = _decimal_text(state["estimate"], 15)
    sd_decimal = _sqrt_decimal(state["variance"], 18)
    with localcontext(DECIMAL_CONTEXT):
        relative_ppm = (
            (Decimal(state["variance"].numerator) / Decimal(state["variance"].denominator)).sqrt()
            / (Decimal(state["estimate"].numerator) / Decimal(state["estimate"].denominator))
            * Decimal(1_000_000)
        )
    return {
        "schema_version": 1,
        "artifact_id": "nist_2026_n4_experimental_estimator_v1",
        "kind": "project_defined_n4_experimental_covariance_generalized_mean",
        "integrity": {
            "baseline_main_sha": BASELINE,
            "preregistration_commit_sha": PREREGISTRATION_COMMIT,
            "preregistration_sha256": PREREGISTRATION_SHA256,
            "external_anchor": EXTERNAL_ANCHOR,
            "source_snapshot": source_snapshot(root),
        },
        "known_prior_information": protocol["known_prior_information"],
        "upstream_authorization": authorization,
        "source": {
            "doi": protocol["source"]["doi"],
            "locators": protocol["source"]["locators"],
            "source_attestation_path": UPSTREAM_ATTESTATION_PATH.as_posix(),
            "feasibility_artifact_path": UPSTREAM_FEASIBILITY_PATH.as_posix(),
        },
        "estimator": {
            "input_order": list(state["order"]),
            "displayed_values_in_1e_minus_11_units": [fraction_record(value) for value in state["values"]],
            "relative_standard_uncertainty_ppm": [fraction_record(value) for value in state["relative_uncertainties_ppm"]],
            "absolute_standard_uncertainty_in_1e_minus_11_units": [fraction_record(value) for value in state["absolute_uncertainties"]],
            "correlation_matrix": _matrix_records(state["correlation"]),
            "absolute_covariance_matrix_in_1e_minus_11_units_squared": _matrix_records(state["covariance"]),
            "leading_principal_minors": [fraction_record(value) for value in state["leading_principal_minors"]],
            "positive_definite": True,
            "weights": [fraction_record(value) for value in state["weights"]],
            "weight_decimals": [_decimal_text(value, 15) for value in state["weights"]],
            "weight_sum": fraction_record(sum(state["weights"])),
            "normalization": fraction_record(state["normalization"]),
            "point_estimate_in_1e_minus_11_units": fraction_record(state["estimate"]),
            "point_estimate_decimal": estimate_decimal,
            "combined_variance_in_1e_minus_11_units_squared": fraction_record(state["variance"]),
            "combined_standard_uncertainty_decimal_in_1e_minus_11_units": sd_decimal,
            "combined_relative_standard_uncertainty_ppm_decimal": f"{relative_ppm:.15f}",
        },
        "finite_resolution": {
            "input_cells_in_1e_minus_11_units": [_interval_record(cell) for cell in state["input_cells"]],
            "aggregate_enclosure_in_1e_minus_11_units": _interval_record(state["aggregate_enclosure"]),
            "aggregate_low_decimal": _decimal_text(state["aggregate_enclosure"][0], 15),
            "aggregate_high_decimal": _decimal_text(state["aggregate_enclosure"][1], 15),
            "weight_policy": protocol["finite_resolution_definition"]["weight_policy"],
            "claim_limit": protocol["finite_resolution_definition"]["rounding_claim_limit"],
        },
        "decision": {
            "estimator_constructed": True,
            "published_equation_64_reproduction": "NOT_CLAIMED",
            "common_constant_comparison": "NOT_EVALUATED",
            "probabilistic_compatibility": "NOT_EVALUATED",
        },
        "claim_limits": [
            "This is The Number Project's experimental-covariance generalized estimator, not NIST equation (64).",
            "Dark uncertainty, Table 19, CODATA, and BIPM measurements are not estimator inputs.",
            "The finite-resolution enclosure is conditional on weights fixed from the displayed summary values.",
            "No common-constant, p-value, apparatus-bias, or new-physics claim is made.",
        ],
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        artifact = build_artifact()
        serialized = serialize_artifact(artifact)
        output = args.output or (ROOT / DEFAULT_OUTPUT)
        if args.check:
            if not output.exists() or output.read_text() != serialized:
                raise NISTN4EstimatorError("n=4 estimator artifact is missing or stale")
            print("NIST 2026 n=4 experimental estimator verified")
            return
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized)
    except (NISTN4EstimatorError, subprocess.CalledProcessError) as error:
        print(f"nist_2026_n4_experimental_estimator_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
