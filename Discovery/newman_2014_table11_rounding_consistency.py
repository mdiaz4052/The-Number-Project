"""Exact conditional audit of Newman et al. 2014 Table 11 quadrature sums."""

from __future__ import annotations

import argparse
from datetime import datetime
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import subprocess
import sys

from Discovery.rounding_consistency import (
    Budget, Calculation, Candidate, RoundingError, decimal_fraction,
    enclose_relative_variance, evaluate_point, interval_record, rational_record,
    rounding_bin, sqrt_display_bounds, classify, verify_witness,
)
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import (
    SourceStateViolationError, SourceVerificationError, exit_for_source_verification_error,
)

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "newman_2014_table11_rounding_consistency_preregistration_v1.json"
SOURCE_PATH = DIRECTORY / "newman_2014_source_attestation_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "newman_2014_table11_rounding_consistency_v1.json"
BASELINE = "96ec62325d2f5b5e78dee36754ed934234c5d0e1"
PREREGISTRATION_COMMIT = "77c47c4246746199a625392927d22c921e8d8985"
PREREGISTRATION_SHA256 = "a1943c7bcbd71706119e3c2a82dc85d05ea8abde33f9f2a7d124c208691e3dcd"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/42",
    "created_at": "2026-09-08T02:48:52Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "scope": "Prospective classification freeze with known source table structure; no rounding outcome computed before freeze.",
}
SCOPES = ("fibre_1", "fibre_2", "fibre_3")
COMPONENT_IDS = ("statistical", "systematic", "analysis_method")
STATUS_LABELS = {
    "compatible": "representable_under_the_declared_table11_rounding_model",
    "incompatible": "not_representable_under_the_declared_table11_rounding_model",
    "unresolved": "undetermined_under_the_frozen_tensor_schedule",
}
E001_FORBIDDEN = (
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.manifest.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v1.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v2.json",
    "Experiments/GMeasurements/hust_2018_aaf_combined_measurement_model_v1.json",
)
SOURCE_PATHS = (
    "Discovery/newman_2014_table11_rounding_consistency.py",
    "Discovery/rounding_consistency.py",
    "Discovery/__init__.py",
    "Discovery/preregistration_history.py",
    "Discovery/source_history.py",
    "Notes/Newman2014Table11RoundingConsistencySpecification.md",
    "Notes/Newman2014Table11RoundingConsistency.md",
    PREREGISTRATION_PATH.as_posix(),
    SOURCE_PATH.as_posix(),
)


def serialize_artifact(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RoundingError("duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise RoundingError("nonfinite JSON value")
    return json.loads(data, object_pairs_hook=unique, parse_constant=invalid)


def load_protocol(root: Path = ROOT) -> dict:
    data = (root / PREREGISTRATION_PATH).read_bytes()
    if digest(data) != PREREGISTRATION_SHA256:
        raise RoundingError("preregistration bytes changed")
    protocol = read_json(data)
    spec = protocol["specification"]
    spec_data = (root / spec["path"]).read_bytes()
    if digest(spec_data) != spec["sha256"] or len(spec_data) != spec["byte_length"]:
        raise RoundingError("bounded specification differs from freeze")
    return protocol


def verify_preregistration(root: Path = ROOT) -> dict:
    verify_preregistration_freeze(
        root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
        path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256,
    )
    return load_protocol(root)


def verify_source_bytes(data: bytes, protocol: dict) -> dict:
    pin = protocol["source_attestation"]
    if digest(data) != pin["sha256"] or len(data) != pin["byte_length"]:
        raise RoundingError("source attestation bytes differ from freeze")
    attestation = read_json(data)
    if attestation != pin["projection"]:
        raise RoundingError("source attestation projection differs from freeze")
    for key, hash_key in (
        ("input_projection", "input_projection_sha256"),
        ("terminal_comparisons", "terminal_projection_sha256"),
    ):
        if digest(serialize_artifact(attestation[key]).encode()) != attestation[hash_key]:
            raise RoundingError("source projection hash mismatch")
    return attestation


def load_source(root: Path = ROOT) -> tuple[dict, dict]:
    protocol = load_protocol(root)
    return protocol, verify_source_bytes((root / SOURCE_PATH).read_bytes(), protocol)


def validate_projection(projection: dict) -> None:
    try:
        if (set(projection) != {"scope_order", "component_unit", "components", "central_values"}
                or projection["scope_order"] != list(SCOPES)
                or projection["component_unit"] != "ppm"
                or set(projection["components"]) != set(SCOPES)
                or set(projection["central_values"]) != set(SCOPES)):
            raise RoundingError("calculation scope inventory or unit changed")
        for scope in SCOPES:
            central = projection["central_values"][scope]
            if (set(central) != {"value", "unit", "role"}
                    or central["unit"] != "m^3 kg^-1 s^-2"
                    or central["role"] != "positive_schema_context_only"
                    or decimal_fraction(central["value"]) <= 0):
                raise RoundingError("invalid positive central context")
            rows = projection["components"][scope]
            if (not isinstance(rows, list) or len(rows) != 3
                    or tuple(row["id"] for row in rows) != COMPONENT_IDS):
                raise RoundingError("component inventory differs from Table 11")
            for row in rows:
                if (set(row) != {"id", "value_ppm"}
                        or not isinstance(row["value_ppm"], str)
                        or not re.fullmatch(r"[0-9]+\.[0-9]", row["value_ppm"])
                        or decimal_fraction(row["value_ppm"]) <= 0):
                    raise RoundingError("component must be a positive one-decimal ppm value")
    except (KeyError, TypeError, AttributeError) as error:
        raise RoundingError("malformed calculation projection") from error


def candidate_parameters(schedule: dict) -> tuple[Fraction, ...]:
    try:
        parameters = tuple(Fraction(value) for value in schedule["parameters"])
        if (schedule["kind"] != "full_independent_tensor_grid"
                or schedule["dimensions_per_scope"] != 3
                or schedule["candidate_count_per_scope"] != len(parameters) ** 3
                or schedule["total_candidate_count"] != len(SCOPES) * len(parameters) ** 3
                or schedule["adaptive_search"] is not False
                or schedule["terminal_blind_generation"] is not True
                or schedule["all_candidates_before_comparison"] is not True
                or not parameters or len(set(parameters)) != len(parameters)
                or any(not -1 < value < 1 for value in parameters)):
            raise RoundingError("tensor schedule differs from freeze")
        return parameters
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise RoundingError("malformed tensor schedule") from error


def build_budget(projection: dict, scope: str, half_width: Fraction) -> Budget:
    if scope not in SCOPES:
        raise RoundingError("unknown Newman fibre scope")
    rows = projection["components"][scope]
    central = decimal_fraction(projection["central_values"][scope]["value"])
    return Budget(
        (central,),
        tuple((rounding_bin(decimal_fraction(row["value_ppm"]), half_width),) for row in rows),
        tuple("independent" for _ in rows),
    )


def tensor_calculation(budget: Budget, parameters: tuple[Fraction, ...]) -> Calculation:
    """Construct every frozen independent grid point before any terminal comparison exists."""
    if len(budget.components) != 3 or len(budget.central_values) != 1:
        raise RoundingError("Newman tensor schedule requires exactly three one-run components")
    enclosure = enclose_relative_variance(budget)
    candidates = []
    for coordinates in product(parameters, repeat=3):
        values = tuple(
            ((domain.low + domain.high) / 2
             + coordinate * (domain.high - domain.low) / 2,)
            for row, coordinate in zip(budget.components, coordinates)
            for domain in row
        )
        evaluation = evaluate_point(budget, values)
        if not enclosure.contains(evaluation.relative_variance_ppm_squared):
            raise RoundingError("tensor candidate escapes guaranteed enclosure")
        candidates.append(Candidate(coordinates, values, evaluation))
    if len(candidates) != len(parameters) ** 3:
        raise RoundingError("tensor candidate inventory incomplete")
    return Calculation(budget, enclosure, tuple(candidates))


def calculate_scopes(projection: dict, rounding_policy: dict, schedule: dict) -> dict:
    """No terminal totals, other measurements, E-001 artifacts, or external constants enter here."""
    validate_projection(projection)
    half = decimal_fraction(rounding_policy["component_half_width_ppm"])
    parameters = candidate_parameters(schedule)
    return {scope: tensor_calculation(build_budget(projection, scope, half), parameters)
            for scope in SCOPES}


def comparison_intervals(comparisons: dict, rounding_policy: dict) -> dict:
    try:
        if not isinstance(comparisons, dict) or set(comparisons) != set(SCOPES):
            raise RoundingError("all three terminal fibre totals are required")
        expected_half = decimal_fraction(rounding_policy["terminal_half_width_ppm"])
        result = {}
        for scope in SCOPES:
            item = comparisons[scope]
            if (set(item) != {"scope", "role", "value_ppm", "half_width_ppm"}
                    or item["scope"] != scope or item["role"] != "terminal_only"
                    or not re.fullmatch(r"[0-9]+\.[0-9]", item["value_ppm"])
                    or decimal_fraction(item["half_width_ppm"]) != expected_half):
                raise RoundingError("terminal comparison scope, resolution, or role mismatch")
            result[scope] = rounding_bin(decimal_fraction(item["value_ppm"]), expected_half)
        return result
    except (KeyError, TypeError, AttributeError) as error:
        raise RoundingError("missing or malformed terminal comparison") from error


def candidate_coordinates(candidate: Candidate) -> tuple[Fraction, ...]:
    coordinates = candidate.parameter
    if (not isinstance(coordinates, tuple) or len(coordinates) != 3
            or any(not isinstance(value, Fraction) for value in coordinates)):
        raise RoundingError("tensor candidate coordinates malformed")
    return coordinates


def terminal_decisions(calculations: dict, comparisons: dict, rounding_policy: dict) -> dict:
    if set(calculations) != set(SCOPES):
        raise RoundingError("all three calculations must precede terminal decisions")
    intervals = comparison_intervals(comparisons, rounding_policy)
    decisions = {}
    for scope in SCOPES:
        calculation = calculations[scope]
        comparison = intervals[scope]
        outcome, index = classify(calculation, comparison)
        witness = None
        if index is not None:
            candidate = calculation.candidates[index]
            witness = {
                "candidate_index": index,
                "tensor_parameters": [rational_record(v) for v in candidate_coordinates(candidate)],
                "component_values_ppm": [rational_record(row[0]) for row in candidate.values],
                "relative_variance_ppm_squared": rational_record(
                    candidate.evaluation.relative_variance_ppm_squared),
                "membership_verified": verify_witness(calculation.budget, candidate, comparison),
            }
        decisions[scope] = {
            "outcome": outcome,
            "status": STATUS_LABELS[outcome],
            "comparison": {
                "role": "terminal_only",
                "source_reference": comparisons[scope],
                "interval_ppm": interval_record(comparison),
                "squared_interval_ppm_squared": interval_record(comparison.square()),
            },
            "witness": witness,
            "exclusion": ({
                "calculation_enclosure_ppm_squared": interval_record(calculation.enclosure),
                "comparison_enclosure_ppm_squared": interval_record(comparison.square()),
                "strict_disjointness": (
                    calculation.enclosure.high < comparison.low ** 2
                    or comparison.high ** 2 < calculation.enclosure.low),
                "interpretation": STATUS_LABELS["incompatible"],
            } if outcome == "incompatible" else None),
        }
    return decisions


def calculation_summary(calculation: Calculation, places: int) -> dict:
    return {
        "relative_variance_enclosure_ppm_squared": interval_record(calculation.enclosure),
        "relative_uncertainty_enclosure_ppm": sqrt_display_bounds(calculation.enclosure, places),
        "candidate_count": len(calculation.candidates),
        "schedule_kind": "full_independent_tensor_grid",
        "candidate_coordinates_are_independent": True,
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
        raise RoundingError("preregistration freeze does not precede GitHub external anchor")
    added = subprocess.run(
        ["git", "-C", str(root), "log", "--diff-filter=A", "--reverse",
         "--format=%H%x00%aI%x00%cI", "--",
         "Discovery/newman_2014_table11_rounding_consistency.py"],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    if not added:
        raise RoundingError("implementation source has no committed introduction")
    fields = added[0].split("\x00")
    if len(fields) != 3 or any(_timestamp(value) <= anchor for value in fields[1:]):
        raise RoundingError("implementation source does not postdate GitHub external anchor")
    ancestry = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor",
         PREREGISTRATION_COMMIT, fields[0]], capture_output=True,
    )
    if ancestry.returncode:
        raise RoundingError("implementation commit is not descended from preregistration freeze")


def source_snapshot(root: Path = ROOT, paths=SOURCE_PATHS) -> dict:
    commit = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", *paths],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    files = []
    for path in paths:
        current = (root / path).read_bytes()
        recorded = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True,
        )
        if recorded.returncode or recorded.stdout != current:
            raise SourceStateViolationError("commit result-driving source before emitting an artifact")
        files.append({"path": path, "sha256": digest(current)})
    return {"source_commit_sha": commit, "files": files}


def verify_preserved_files(root: Path = ROOT) -> None:
    paths = load_protocol(root)["preserved_baseline_paths"]
    if any(path in E001_FORBIDDEN for path in paths):
        raise RoundingError("E-001 path entered preserved dependency inventory")
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", BASELINE, "--", *paths],
        capture_output=True,
    )
    if result.returncode == 1:
        raise RoundingError("pre-existing scientific engine or established artifact changed")
    if result.returncode:
        raise RoundingError("preserved-path comparison failed")


def verify_e001_isolation(root: Path = ROOT) -> None:
    protocol = load_protocol(root)
    reachable_paths = set(SOURCE_PATHS) | {
        PREREGISTRATION_PATH.as_posix(), SOURCE_PATH.as_posix(),
        protocol["specification"]["path"], protocol["source_attestation"]["path"],
        *protocol["preserved_baseline_paths"],
    }
    if set(E001_FORBIDDEN) & reachable_paths:
        raise RoundingError("E-001 artifact entered the result-driving filesystem inventory")


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    _, attestation = load_source(root)
    calculations = calculate_scopes(
        attestation["input_projection"], protocol["rounding_policy"], protocol["candidate_schedule"])
    # All 10,125 candidates exist before terminal comparisons are interpreted.
    summaries = {
        scope: calculation_summary(calculations[scope],
                                   protocol["calculation"]["output_ppm_decimal_places"])
        for scope in SCOPES
    }
    decisions = terminal_decisions(
        calculations, attestation["terminal_comparisons"], protocol["rounding_policy"])
    return {
        "schema_version": 1,
        "artifact_id": "newman_2014_table11_rounding_consistency_v1",
        "kind": "conditional_published_table_rounding_consistency",
        "integrity": {
            "baseline_main_sha": BASELINE,
            "preregistration_commit_sha": PREREGISTRATION_COMMIT,
            "preregistration_sha256": PREREGISTRATION_SHA256,
            "external_anchor": EXTERNAL_ANCHOR,
            "source_attestation_sha256": protocol["source_attestation"]["sha256"],
            "source_snapshot": source_snapshot(root),
        },
        "selection": protocol["selection"],
        "scope_order": list(SCOPES),
        "input_projection": attestation["input_projection"],
        "rounding_policy": protocol["rounding_policy"],
        "candidate_schedule": protocol["candidate_schedule"],
        "calculation_policy": protocol["calculation"],
        "calculations": summaries,
        "terminal_decisions": decisions,
        "claim_limits": protocol["claim_limits"],
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
            verify_preserved_files()
            verify_e001_isolation()
            if (ROOT / DEFAULT_OUTPUT).read_text() != text:
                raise RoundingError("Newman Table 11 result artifact is stale")
            print("Newman 2014 Table 11 source, chronology, tensor schedule and result verified")
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        else:
            print(text, end="")
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except (RoundingError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"newman_2014_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
