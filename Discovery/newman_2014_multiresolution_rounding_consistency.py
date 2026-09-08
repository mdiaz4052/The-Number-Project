"""Formalize Newman 2014 multi-resolution terminal rounding constraints."""

from __future__ import annotations

import argparse
from datetime import datetime
from fractions import Fraction
from pathlib import Path
import re
import subprocess
import sys

from Discovery import multiresolution_rounding as mr
from Discovery import newman_2014_table11_rounding_consistency as j
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import (
    SourceStateViolationError, SourceVerificationError, exit_for_source_verification_error,
)

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "newman_2014_multiresolution_rounding_consistency_preregistration_v1.json"
TERMINAL_ATTESTATION_PATH = DIRECTORY / "newman_2014_multiresolution_terminal_attestation_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "newman_2014_multiresolution_rounding_consistency_v1.json"
BASELINE = "1fd38d8f009c2b23b6d419f7817acc730cc57812"
PREREGISTRATION_COMMIT = "f0a3edc9a889382292040281e1b693ce99a28cbc"
PREREGISTRATION_SHA256 = "6e92eea837b6b84aae4b485bd33e5d0528962d68b15de343368291b12c731767"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/43",
    "created_at": "2026-09-08T15:47:46Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "scope": (
        "Implementation chronology anchor only. The real-data multi-resolution outcome "
        "was already known from the PR #42 audit before this freeze."
    ),
    "outcome_blind": False,
}
STATUS_LABELS = {
    "compatible": "representable_under_the_declared_multiresolution_reporting_model",
    "incompatible": "not_representable_under_the_declared_multiresolution_reporting_model",
    "unresolved": "undetermined_under_the_frozen_tensor_schedule_and_reporting_model",
}
SOURCE_PATHS = (
    "Discovery/multiresolution_rounding.py",
    "Discovery/newman_2014_multiresolution_rounding_consistency.py",
    "Notes/Newman2014MultiResolutionRoundingConsistencySpecification.md",
    "Notes/Newman2014MultiResolutionRoundingConsistency.md",
    PREREGISTRATION_PATH.as_posix(),
    TERMINAL_ATTESTATION_PATH.as_posix(),
    "Experiments/GMeasurements/newman_2014_source_attestation_v1.json",
    "Discovery/newman_2014_table11_rounding_consistency.py",
    "Discovery/rounding_consistency.py",
    "Discovery/preregistration_history.py",
    "Discovery/source_history.py",
)


def serialize_artifact(value) -> str:
    return j.serialize_artifact(value)


def digest(data: bytes) -> str:
    return j.digest(data)


def read_json(data: bytes):
    return j.read_json(data)


def load_protocol(root: Path = ROOT) -> dict:
    data = (root / PREREGISTRATION_PATH).read_bytes()
    if digest(data) != PREREGISTRATION_SHA256:
        raise j.RoundingError("multi-resolution preregistration bytes changed")
    protocol = read_json(data)
    if protocol.get("intended_base_sha") != BASELINE:
        raise j.RoundingError("multi-resolution intended base changed")
    if protocol.get("known_prior_information", {}).get("outcome_blind") is not False:
        raise j.RoundingError("known prior outcome must remain explicit")
    spec = protocol["specification"]
    spec_data = (root / spec["path"]).read_bytes()
    if digest(spec_data) != spec["sha256"] or len(spec_data) != spec["byte_length"]:
        raise j.RoundingError("multi-resolution bounded specification differs from freeze")
    return protocol


def verify_preregistration(root: Path = ROOT) -> dict:
    verify_preregistration_freeze(
        root,
        baseline=BASELINE,
        commit=PREREGISTRATION_COMMIT,
        path=PREREGISTRATION_PATH.as_posix(),
        sha256=PREREGISTRATION_SHA256,
    )
    return load_protocol(root)


def load_component_source(protocol: dict, root: Path = ROOT) -> dict:
    pin = protocol["component_model"]
    path = Path(pin["component_source_path"])
    data = (root / path).read_bytes()
    if digest(data) != pin["component_source_sha256"]:
        raise j.RoundingError("parent Newman component source bytes changed")
    source = read_json(data)
    if source.get("record_id") != "newman_2014_source_attestation_v1":
        raise j.RoundingError("unexpected parent Newman source record")
    if digest(serialize_artifact(source["input_projection"]).encode()) != source["input_projection_sha256"]:
        raise j.RoundingError("parent Newman input projection hash mismatch")
    if digest(serialize_artifact(source["terminal_comparisons"]).encode()) != source["terminal_projection_sha256"]:
        raise j.RoundingError("parent Newman Table 11 terminal projection hash mismatch")
    return source


def validate_terminal_attestation(attestation: dict, parent_source: dict) -> None:
    required = {
        "schema_version", "record_id", "publication", "parent_source_attestation",
        "reporting_model", "scope_order", "terminal_representations",
        "source_verification", "known_prior_auditor_information",
    }
    if set(attestation) != required:
        raise j.RoundingError("terminal attestation schema changed")
    if (
        attestation["schema_version"] != 1
        or attestation["record_id"] != "newman_2014_multiresolution_terminal_attestation_v1"
        or attestation["scope_order"] != list(j.SCOPES)
        or set(attestation["terminal_representations"]) != set(j.SCOPES)
        or attestation["reporting_model"]["kind"] != "intersection_of_closed_rounding_consistency_bins"
        or attestation["reporting_model"]["tie_breaking_assumption"] != "none"
        or attestation["reporting_model"]["terminal_values_must_not_enter_candidate_generation"] is not True
    ):
        raise j.RoundingError("terminal attestation identity or reporting model changed")
    parent = attestation["parent_source_attestation"]
    if (
        parent["path"] != "Experiments/GMeasurements/newman_2014_source_attestation_v1.json"
        or parent["sha256"] != "a787f63e4c4377a6daf778d5402c065743e2f1b61d3a0c3a469f915e461653a6"
    ):
        raise j.RoundingError("terminal attestation parent source pin changed")
    for scope in j.SCOPES:
        items = attestation["terminal_representations"][scope]
        if not isinstance(items, list) or len(items) != 2:
            raise j.RoundingError("each fibre requires exactly two terminal representations")
        if tuple(item.get("id") for item in items) != ("table11_one_decimal", "conclusion_integer"):
            raise j.RoundingError("terminal representation order or identity changed")
        for index, item in enumerate(items):
            if set(item) != {
                "id", "value_ppm", "half_width_ppm", "printed_decimal_places",
                "source_locator", "role",
            } or item["role"] != "terminal_constraint":
                raise j.RoundingError("terminal representation schema changed")
            pattern = r"[0-9]+\.[0-9]" if index == 0 else r"[0-9]+"
            expected_places = 1 if index == 0 else 0
            expected_half = "0.05" if index == 0 else "0.5"
            if (
                not isinstance(item["value_ppm"], str)
                or re.fullmatch(pattern, item["value_ppm"]) is None
                or item["printed_decimal_places"] != expected_places
                or item["half_width_ppm"] != expected_half
                or j.decimal_fraction(item["value_ppm"]) <= 0
            ):
                raise j.RoundingError("terminal representation precision differs from freeze")
        old = parent_source["terminal_comparisons"][scope]
        first = items[0]
        if first["value_ppm"] != old["value_ppm"] or first["half_width_ppm"] != old["half_width_ppm"]:
            raise j.RoundingError("Table 11 value differs between parent and multi-resolution attestations")


def load_terminal_attestation(protocol: dict, parent_source: dict, root: Path = ROOT) -> dict:
    pin = protocol["terminal_attestation"]
    data = (root / pin["path"]).read_bytes()
    if digest(data) != pin["sha256"] or len(data) != pin["byte_length"]:
        raise j.RoundingError("multi-resolution terminal attestation bytes differ from freeze")
    attestation = read_json(data)
    if attestation != pin["projection"]:
        raise j.RoundingError("multi-resolution terminal attestation projection differs from freeze")
    validate_terminal_attestation(attestation, parent_source)
    return attestation


def candidate_parameters(schedule: dict) -> tuple[Fraction, ...]:
    try:
        parameters = tuple(Fraction(value) for value in schedule["parameters"])
        if (
            schedule["kind"] != "full_independent_tensor_grid"
            or schedule["dimensions_per_scope"] != 3
            or schedule["candidate_count_per_scope"] != len(parameters) ** 3
            or schedule["total_candidate_count"] != len(j.SCOPES) * len(parameters) ** 3
            or schedule["adaptive_search"] is not False
            or schedule["all_candidates_before_terminal_interpretation"] is not True
            or not parameters
            or len(set(parameters)) != len(parameters)
            or any(not -1 < value < 1 for value in parameters)
        ):
            raise j.RoundingError("multi-resolution tensor schedule differs from freeze")
        return parameters
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise j.RoundingError("malformed multi-resolution tensor schedule") from error


def calculate_components(
    input_projection: dict, component_half_width_ppm: str, schedule: dict
) -> dict:
    """Generate all candidates from component-only inputs; terminals are not accepted here."""
    j.validate_projection(input_projection)
    half_width = j.decimal_fraction(component_half_width_ppm)
    parameters = candidate_parameters(schedule)
    return {
        scope: j.tensor_calculation(j.build_budget(input_projection, scope, half_width), parameters)
        for scope in j.SCOPES
    }


def constraint_intervals(attestation: dict, scope: str):
    if scope not in j.SCOPES:
        raise j.RoundingError("unknown Newman multi-resolution scope")
    return tuple(
        mr.printed_constraint(
            j.decimal_fraction(item["value_ppm"]),
            j.decimal_fraction(item["half_width_ppm"]),
        )
        for item in attestation["terminal_representations"][scope]
    )


def resolution_record(attestation: dict, scope: str, constraints, joint) -> dict:
    items = attestation["terminal_representations"][scope]
    constituent = [
        {"source_reference": item, "interval_ppm": j.interval_record(interval)}
        for item, interval in zip(items, constraints)
    ]
    table11_width = mr.interval_width(constraints[0])
    if joint is None:
        return {
            "constituent_intervals_ppm": constituent,
            "joint_interval_ppm": None,
            "table11_width_ppm": j.rational_record(table11_width),
            "joint_width_ppm": None,
            "joint_to_table11_width_ratio": None,
            "narrowed_by_multiresolution_constraint": None,
        }
    joint_width = mr.interval_width(joint)
    return {
        "constituent_intervals_ppm": constituent,
        "joint_interval_ppm": j.interval_record(joint),
        "table11_width_ppm": j.rational_record(table11_width),
        "joint_width_ppm": j.rational_record(joint_width),
        "joint_to_table11_width_ratio": j.rational_record(joint_width / table11_width),
        "narrowed_by_multiresolution_constraint": joint_width < table11_width,
    }


def terminal_decisions(calculations: dict, attestation: dict) -> dict:
    if set(calculations) != set(j.SCOPES):
        raise j.RoundingError("all three component calculations must precede terminal decisions")
    decisions = {}
    for scope in j.SCOPES:
        calculation = calculations[scope]
        constraints = constraint_intervals(attestation, scope)
        outcome, index, reason, joint = mr.classify_multiresolution(calculation, constraints)
        witness = None
        if index is not None:
            candidate = calculation.candidates[index]
            parameters = j.candidate_coordinates(candidate)
            witness = {
                "candidate_index": index,
                "witness_kind": (
                    "unshifted_midpoint"
                    if all(parameter == 0 for parameter in parameters)
                    else "scheduled_shifted"
                ),
                "tensor_parameters": [j.rational_record(value) for value in parameters],
                "component_values_ppm": [j.rational_record(row[0]) for row in candidate.values],
                "relative_variance_ppm_squared": j.rational_record(
                    candidate.evaluation.relative_variance_ppm_squared
                ),
                "membership_verified": mr.strict_witness(calculation, candidate, joint),
            }
        exclusion = None
        if outcome == "incompatible":
            exclusion = {
                "reason": reason,
                "component_enclosure_ppm_squared": j.interval_record(calculation.enclosure),
                "joint_terminal_squared_interval_ppm_squared": (
                    j.interval_record(joint.square()) if joint is not None else None
                ),
                "interpretation": STATUS_LABELS["incompatible"],
            }
        decisions[scope] = {
            "outcome": outcome,
            "status": STATUS_LABELS[outcome],
            "reason": reason,
            "resolution": resolution_record(attestation, scope, constraints, joint),
            "joint_terminal_squared_interval_ppm_squared": (
                j.interval_record(joint.square()) if joint is not None else None
            ),
            "witness": witness,
            "exclusion": exclusion,
        }
    return decisions


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_implementation_chronology(root: Path = ROOT) -> None:
    anchor = _timestamp(EXTERNAL_ANCHOR["created_at"])
    freeze = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%aI%x00%cI", PREREGISTRATION_COMMIT],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split("\x00")
    if len(freeze) != 2 or any(_timestamp(value) >= anchor for value in freeze):
        raise j.RoundingError("multi-resolution freeze does not precede GitHub anchor")
    added = subprocess.run(
        [
            "git", "-C", str(root), "log", "--diff-filter=A", "--reverse",
            "--format=%H%x00%aI%x00%cI", "--",
            "Discovery/newman_2014_multiresolution_rounding_consistency.py",
        ],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    if not added:
        raise j.RoundingError("multi-resolution implementation source has no committed introduction")
    fields = added[0].split("\x00")
    if len(fields) != 3 or any(_timestamp(value) <= anchor for value in fields[1:]):
        raise j.RoundingError("multi-resolution implementation source does not postdate GitHub anchor")
    ancestry = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, fields[0]],
        capture_output=True,
    )
    if ancestry.returncode:
        raise j.RoundingError("multi-resolution implementation does not descend from freeze")


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
            raise SourceStateViolationError(
                "commit multi-resolution result-driving source before emitting an artifact"
            )
        files.append({"path": path, "sha256": digest(current)})
    return {"source_commit_sha": commit, "files": files}


def verify_preserved_files(root: Path = ROOT) -> None:
    paths = load_protocol(root)["preserved_baseline_paths"]
    if any(path in j.E001_FORBIDDEN for path in paths):
        raise j.RoundingError("E-001 path entered multi-resolution preserved inventory")
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", BASELINE, "--", *paths],
        capture_output=True,
    )
    if result.returncode == 1:
        raise j.RoundingError("preserved PR #42/shared scientific surface changed")
    if result.returncode:
        raise j.RoundingError("multi-resolution preserved-path comparison failed")


def verify_e001_isolation(root: Path = ROOT) -> None:
    protocol = load_protocol(root)
    reachable = set(SOURCE_PATHS) | set(protocol["preserved_baseline_paths"])
    if set(j.E001_FORBIDDEN) & reachable:
        raise j.RoundingError("E-001 artifact entered multi-resolution dependency inventory")


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    parent_source = load_component_source(protocol, root)

    # Candidate generation is completed before the terminal-attestation file is read.
    calculations = calculate_components(
        parent_source["input_projection"],
        protocol["component_model"]["component_half_width_ppm"],
        protocol["candidate_schedule"],
    )
    summaries = {
        scope: j.calculation_summary(calculations[scope], 6) for scope in j.SCOPES
    }

    terminal_attestation = load_terminal_attestation(protocol, parent_source, root)
    decisions = terminal_decisions(calculations, terminal_attestation)

    return {
        "schema_version": 1,
        "artifact_id": "newman_2014_multiresolution_rounding_consistency_v1",
        "kind": "conditional_multiresolution_reporting_consistency",
        "integrity": {
            "baseline_main_sha": BASELINE,
            "preregistration_commit_sha": PREREGISTRATION_COMMIT,
            "preregistration_sha256": PREREGISTRATION_SHA256,
            "external_anchor": EXTERNAL_ANCHOR,
            "component_source_sha256": protocol["component_model"]["component_source_sha256"],
            "terminal_attestation_sha256": protocol["terminal_attestation"]["sha256"],
            "source_snapshot": source_snapshot(root),
        },
        "known_prior_information": protocol["known_prior_information"],
        "scope_order": list(j.SCOPES),
        "component_model": protocol["component_model"],
        "candidate_schedule": protocol["candidate_schedule"],
        "reporting_model": protocol["reporting_model"],
        "calculations": summaries,
        "terminal_decisions": decisions,
        "resolution_reporting": protocol["resolution_reporting"],
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
                raise j.RoundingError("Newman multi-resolution result artifact is stale")
            print(
                "Newman 2014 multi-resolution source, chronology, terminal intersections "
                "and result verified"
            )
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        else:
            print(text, end="")
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except (j.RoundingError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"newman_2014_multiresolution_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
