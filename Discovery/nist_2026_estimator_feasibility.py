"""Source-bound feasibility audit for the NIST 2026 G estimator layers."""

from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext, Context
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
PREREGISTRATION_PATH = DIRECTORY / "nist_2026_estimator_feasibility_preregistration_v1.json"
SOURCE_ATTESTATION_PATH = DIRECTORY / "nist_2026_estimator_source_attestation_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "nist_2026_estimator_feasibility_v1.json"
BASELINE = "151b9c920cadb90a9fd02766cc8def7ba9348f61"
PREREGISTRATION_COMMIT = "18815807c9dfffb5bb3251f1a0331c5c2c752a04"
PREREGISTRATION_SHA256 = "c60e6d838054f430a1a7f8c05da9807fb03dcf48d0eca243476acc8bf48a59fe"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/45",
    "created_at": "2026-09-08T22:45:21Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "outcome_blind": False,
}
SOURCE_PATHS = (
    "Discovery/nist_2026_estimator_feasibility.py",
    "Notes/NIST2026EstimatorFeasibilitySpecification.md",
    "Notes/NIST2026EstimatorFeasibility.md",
    PREREGISTRATION_PATH.as_posix(),
    SOURCE_ATTESTATION_PATH.as_posix(),
)
E001_FORBIDDEN = (
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.manifest.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v1.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v2.json",
)
INPUT_ORDER = ("copper_servo", "copper_free", "sapphire_servo", "sapphire_free")
TABLE18_SIGMAS = ("23.2", "30.3", "37.5", "93.9")
CONSENSUS_MISSING_IDS = (
    "epsilon_likelihood_distribution",
    "posterior_sampler_algorithm",
    "posterior_sampling_controls",
    "robust_estimator_computational_conventions",
    "dark_correlation_matrix_identity",
)
DECIMAL_CONTEXT = Context(prec=60)


class NISTFeasibilityError(ValueError):
    """Invalid source, chronology, covariance geometry, or feasibility artifact."""


def serialize_artifact(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise NISTFeasibilityError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def decimal_fraction(value: str) -> Fraction:
    if not isinstance(value, str):
        raise NISTFeasibilityError("authoritative decimal must be a string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise NISTFeasibilityError("malformed authoritative decimal") from error
    if not number.is_finite():
        raise NISTFeasibilityError("authoritative decimal must be finite")
    return Fraction(number)


def fraction_record(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def decimal_text(value: Fraction, places: int = 12) -> str:
    with localcontext(DECIMAL_CONTEXT):
        number = Decimal(value.numerator) / Decimal(value.denominator)
        return f"{number:.{places}f}"


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
        raise NISTFeasibilityError(str(error)) from error
    protocol = _json(data)
    if protocol["known_prior_information"]["outcome_blind"] is not False:
        raise NISTFeasibilityError("NIST feasibility PR must not claim outcome blindness")
    if protocol["intended_base_sha"] != BASELINE:
        raise NISTFeasibilityError("NIST intended base differs from implementation baseline")
    return protocol


def _frozen_correlation_matrix(protocol: dict) -> list[list[str]]:
    upper = protocol["source_projection"]["experimental_layer"]["table_18"]["correlation_upper_triangle"]
    if not isinstance(upper, list) or len(upper) != 4 or any(not isinstance(row, list) or len(row) != 4 for row in upper):
        raise NISTFeasibilityError("frozen Table 18 correlation triangle malformed")
    matrix = [[None for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(i, 4):
            value = upper[i][j]
            if not isinstance(value, str):
                raise NISTFeasibilityError("frozen Table 18 upper triangle is incomplete")
            matrix[i][j] = value
            matrix[j][i] = value
    return matrix


def load_source_attestation(protocol: dict, root: Path = ROOT) -> dict:
    data = _json((root / SOURCE_ATTESTATION_PATH).read_bytes())
    source = data.get("source", {})
    if source.get("doi") != protocol["primary_source"]["doi"]:
        raise NISTFeasibilityError("NIST source DOI differs from frozen protocol")
    if source.get("nist_pdf") != protocol["primary_source"]["nist_pdf"]:
        raise NISTFeasibilityError("NIST PDF locator differs from frozen protocol")
    if source.get("raw_pdf_hash_claim") is not False or source.get("raw_pdf_persisted") is not False:
        raise NISTFeasibilityError("NIST attestation overclaims raw PDF custody")

    experimental = data.get("experimental_layer", {})
    if tuple(experimental.get("input_order", ())) != INPUT_ORDER:
        raise NISTFeasibilityError("NIST experimental input order differs")
    frozen_measurements = protocol["source_projection"]["experimental_layer"]["table_16"]["measurements"]
    attested_measurements = experimental.get("table_16", {}).get("measurements", [])
    if len(frozen_measurements) != 4 or len(attested_measurements) != 4:
        raise NISTFeasibilityError("NIST Table 16 measurement inventory incomplete")
    for frozen, attested, identifier in zip(frozen_measurements, attested_measurements, INPUT_ORDER):
        if frozen.get("id") != identifier or attested.get("id") != identifier:
            raise NISTFeasibilityError("NIST Table 16 measurement identity differs")
        if frozen.get("G_decimal_in_1e_minus_11_units") != attested.get("G_decimal_in_1e_minus_11_units"):
            raise NISTFeasibilityError("NIST Table 16 central value differs from freeze")
        if frozen.get("relative_standard_uncertainty_ppm") != attested.get("displayed_relative_standard_uncertainty_ppm"):
            raise NISTFeasibilityError("NIST Table 16 displayed uncertainty differs from freeze")
        decimal_fraction(attested["G_decimal_in_1e_minus_11_units"])
        if decimal_fraction(attested["displayed_relative_standard_uncertainty_ppm"]) <= 0:
            raise NISTFeasibilityError("NIST Table 16 displayed uncertainty must be positive")

    table18 = experimental.get("table_18", {})
    if table18.get("diagonal_relative_standard_uncertainty_ppm") != list(TABLE18_SIGMAS):
        raise NISTFeasibilityError("NIST Table 18 precise uncertainty diagonal differs from attested source")
    if table18.get("correlation_matrix") != _frozen_correlation_matrix(protocol):
        raise NISTFeasibilityError("NIST Table 18 correlation matrix differs from freeze")

    consensus = data.get("consensus_layer", {})
    missing = consensus.get("not_uniquely_specified_in_primary_paper", [])
    if tuple(item.get("id") for item in missing) != CONSENSUS_MISSING_IDS:
        raise NISTFeasibilityError("NIST Bayesian missing-information inventory differs")
    if data.get("authority_resolution", {}).get("controlling_scientific_source") != (
        "peer-reviewed journal article PDF served by the NIST local-download endpoint"
    ):
        raise NISTFeasibilityError("NIST source authority resolution differs")
    return data


def correlation_matrix(attestation: dict) -> list[list[Fraction]]:
    raw = attestation["experimental_layer"]["table_18"]["correlation_matrix"]
    matrix = [[decimal_fraction(value) for value in row] for row in raw]
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise NISTFeasibilityError("NIST correlation matrix must be 4x4")
    for i in range(4):
        if matrix[i][i] != 1:
            raise NISTFeasibilityError("NIST correlation diagonal must be one")
        for j in range(4):
            if matrix[i][j] != matrix[j][i]:
                raise NISTFeasibilityError("NIST correlation matrix must be symmetric")
            if abs(matrix[i][j]) > 1:
                raise NISTFeasibilityError("NIST correlation coefficient outside [-1,1]")
    return matrix


def relative_covariance_matrix(attestation: dict) -> list[list[Fraction]]:
    sigmas = tuple(decimal_fraction(value) for value in TABLE18_SIGMAS)
    if any(value <= 0 for value in sigmas):
        raise NISTFeasibilityError("NIST Table 18 standard uncertainties must be positive")
    rho = correlation_matrix(attestation)
    return [[rho[i][j] * sigmas[i] * sigmas[j] for j in range(4)] for i in range(4)]


def determinant(matrix: list[list[Fraction]]) -> Fraction:
    n = len(matrix)
    if not n or any(len(row) != n for row in matrix):
        raise NISTFeasibilityError("determinant requires a nonempty square matrix")
    work = [row[:] for row in matrix]
    result = Fraction(1)
    for column in range(n):
        pivot = next((row for row in range(column, n) if work[row][column] != 0), None)
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


def experimental_covariance_audit(attestation: dict) -> dict:
    matrix = relative_covariance_matrix(attestation)
    minors = leading_principal_minors(matrix)
    positive_definite = all(value > 0 for value in minors)
    if not positive_definite:
        raise NISTFeasibilityError("NIST experimental covariance matrix is not positive definite")
    return {
        "verdict": "GO",
        "reason": "four_values_uncertainties_and_correlations_uniquely_define_positive_definite_covariance",
        "input_order": list(INPUT_ORDER),
        "standard_uncertainty_ppm": list(TABLE18_SIGMAS),
        "correlation_matrix": [
            [fraction_record(value) for value in row] for row in correlation_matrix(attestation)
        ],
        "relative_covariance_matrix_ppm_squared": [
            [fraction_record(value) for value in row] for row in matrix
        ],
        "leading_principal_minors": [
            {"order": index + 1, "exact": fraction_record(value), "decimal": decimal_text(value, 12)}
            for index, value in enumerate(minors)
        ],
        "positive_definite": True,
        "source_precision_policy": attestation["experimental_layer"]["table_18"]["precision_policy"],
    }


def bayesian_consensus_audit(protocol: dict, attestation: dict) -> dict:
    missing = attestation["consensus_layer"]["not_uniquely_specified_in_primary_paper"]
    missing_ids = [item["id"] for item in missing]
    if tuple(missing_ids) != CONSENSUS_MISSING_IDS:
        raise NISTFeasibilityError("NIST Bayesian blocker inventory is not canonical")
    required = protocol["feasibility_questions"]["B_published_bayesian_consensus"]["GO_requirements"]
    if not required or not missing_ids:
        raise NISTFeasibilityError("NIST Bayesian feasibility audit lacks a fail-closed blocker")
    return {
        "verdict": "NO_GO",
        "reason": "primary_paper_does_not_uniquely_specify_deterministic_equation_64_reproduction",
        "specified": attestation["consensus_layer"]["specified"],
        "missing_result_driving_information": missing,
        "go_requirements": required,
        "nonclaim": "No generalized least-squares or conventional Bayesian implementation is substituted for the published equation (64) consensus.",
    }


def source_authority_audit(attestation: dict) -> dict:
    authority = attestation["authority_resolution"]
    journal = authority["journal_pdf_result"]
    landing = authority["landing_page_displayed_result"]
    if journal["G_decimal_in_1e_minus_11_units"] == landing["G_decimal_in_1e_minus_11_units"]:
        raise NISTFeasibilityError("NIST landing/PDF conflict sentinel no longer distinguishes sources")
    return {
        "controlling_source": authority["controlling_scientific_source"],
        "landing_page_numerical_role": authority["landing_page_role"],
        "numerical_conflict_present": True,
        "journal_pdf_result": journal,
        "landing_page_displayed_result": landing,
        "resolution": "peer_reviewed_article_pdf_controls_scientific_transcription",
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
        raise NISTFeasibilityError("NIST feasibility freeze does not precede GitHub anchor")
    added = subprocess.run(
        [
            "git", "-C", str(root), "log", "--diff-filter=A", "--reverse",
            "--format=%H%x00%aI%x00%cI", "--", "Discovery/nist_2026_estimator_feasibility.py",
        ], capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    if not added:
        raise NISTFeasibilityError("NIST feasibility implementation has no committed introduction")
    fields = added[0].split("\x00")
    if len(fields) != 3 or any(_timestamp(value) <= anchor for value in fields[1:]):
        raise NISTFeasibilityError("NIST feasibility implementation does not postdate anchor")
    ancestry = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, fields[0]],
        capture_output=True,
    )
    if ancestry.returncode:
        raise NISTFeasibilityError("NIST feasibility implementation does not descend from freeze")


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
            raise NISTFeasibilityError("commit NIST feasibility result-driving source before artifact emission")
        files.append({"path": path, "sha256": digest(current)})
    return {"source_commit_sha": commit, "files": files}


def verify_e001_isolation() -> None:
    if set(E001_FORBIDDEN) & set(SOURCE_PATHS):
        raise NISTFeasibilityError("E-001 artifact entered NIST feasibility source inventory")


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    attestation = load_source_attestation(protocol, root)
    experimental = experimental_covariance_audit(attestation)
    bayesian = bayesian_consensus_audit(protocol, attestation)
    authority = source_authority_audit(attestation)
    if experimental["verdict"] != "GO" or bayesian["verdict"] != "NO_GO":
        raise NISTFeasibilityError("NIST feasibility result differs from frozen decision branch")
    return {
        "schema_version": 1,
        "artifact_id": "nist_2026_estimator_feasibility_v1",
        "kind": "source_and_estimator_reconstructability_audit",
        "integrity": {
            "baseline_main_sha": BASELINE,
            "preregistration_commit_sha": PREREGISTRATION_COMMIT,
            "preregistration_sha256": PREREGISTRATION_SHA256,
            "external_anchor": EXTERNAL_ANCHOR,
            "source_snapshot": source_snapshot(root),
        },
        "known_prior_information": protocol["known_prior_information"],
        "source": {
            "doi": protocol["primary_source"]["doi"],
            "nist_pdf": protocol["primary_source"]["nist_pdf"],
            "source_attestation_path": SOURCE_ATTESTATION_PATH.as_posix(),
            "raw_pdf_persisted": False,
            "raw_pdf_hash_claim": False,
        },
        "source_authority": authority,
        "experimental_covariance_layer": experimental,
        "published_bayesian_consensus_layer": bayesian,
        "decision": {
            "experimental_covariance": "GO",
            "published_bayesian_consensus": "NO_GO",
            "authorized_next_step": "preregister_n4_experimental_covariance_correlated_estimator_certificate",
            "common_constant_comparison": "NOT_EVALUATED",
            "equation_64_reproduction": "NOT_AUTHORIZED",
        },
        "claim_limits": [
            "This audit establishes deterministic reconstructability of the four-dimensional experimental covariance object only.",
            "It does not reproduce equation (64), the dark-uncertainty posterior, or the paper's final Bayesian consensus.",
            "It does not compare NIST-26 with BIPM-14, CODATA, or any common-constant model.",
            "The source-authority discrepancy between the NIST landing page and peer-reviewed PDF is resolved in favor of the journal PDF without numerical reconciliation.",
            "No HUST AAF E-001 evidence boundary is used.",
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
        text = serialize_artifact(artifact)
        if args.check:
            verify_e001_isolation()
            path = ROOT / DEFAULT_OUTPUT
            if not path.exists() or path.read_text() != text:
                raise NISTFeasibilityError("NIST 2026 feasibility artifact is missing or stale")
            print("NIST 2026 estimator feasibility verified: covariance GO; Bayesian consensus NO-GO")
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        else:
            print(text, end="")
    except (NISTFeasibilityError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"nist_2026_estimator_feasibility_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
