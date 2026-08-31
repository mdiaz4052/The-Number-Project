"""Run preregistered, provenance-stratified Milestone 5B null controls.

Exact dimensions and dependency signatures come from the existing symbolic machinery.
Binary floating point is confined here to log-space numerical navigation, Monte Carlo
sampling, and the independent geometric CDF oracle.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

from Discovery.constants import DEFAULT_SEARCH_CONSTANTS, GRAVITATIONAL_CONSTANT_G
from Discovery.dependency_analysis import (
    NO_REGISTERED_TARGET_DEPENDENCY,
    TARGET_DEPENDENT,
    TARGET_RECONSTRUCTION,
    UNRESOLVED_PROVENANCE,
    AnalyzedCandidate,
    analyze_default_candidates,
    fraction_text,
    signature_record,
)
from Discovery.falsification_preregistration import (
    DEFAULT_OUTPUT as DEFAULT_PREREGISTRATION_OUTPUT,
    EXPERIMENT_IDENTIFIER,
    load_preregistration,
    preregistration_sha256_bytes,
)
from Discovery.planck_identities import ExponentSignature


RESULT_SCHEMA_VERSION = 1
DEFAULT_OUTPUT = Path("Experiments/Falsification/milestone_5b_core_v1.null_results.json")
TIE_TOLERANCE = 1e-12
NUMERICAL_TOLERANCE = 1e-12
TRIAL_CHUNK_SIZE = 1000
SOURCE_PATHS = (
    "Discovery/constants.py",
    "Discovery/dimensions.py",
    "Discovery/dimensional_search.py",
    "Discovery/dependency_definitions.py",
    "Discovery/dependency_analysis.py",
    "Discovery/planck_identities.py",
    "Discovery/falsification_preregistration.py",
    "Discovery/null_experiments.py",
    str(DEFAULT_PREREGISTRATION_OUTPUT),
)


def _float_text(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("result contains a non-finite floating-point value")
    return format(value, ".17g")


def _float_record(value: float) -> dict[str, str]:
    return {"decimal": _float_text(value), "hex": value.hex()}


def _constant_log_positions() -> dict[str, float]:
    constants = (GRAVITATIONAL_CONSTANT_G, *DEFAULT_SEARCH_CONSTANTS)
    return {constant.key: math.log10(constant.value_si) for constant in constants}


def evaluate_signature_log10(
    signature: ExponentSignature,
    *,
    constant_logs: Mapping[str, float] | None = None,
) -> float:
    """Evaluate a fully expanded signature only in the numerical layer."""

    logs = _constant_log_positions() if constant_logs is None else constant_logs
    missing = {factor for factor, _ in signature} - set(logs)
    if missing:
        raise ValueError(f"missing numerical magnitude for factor(s): {sorted(missing)}")
    result = sum(float(exponent) * logs[factor] for factor, exponent in signature)
    if not math.isfinite(result):
        raise ValueError("class log position is not finite")
    return result


@dataclass(frozen=True, slots=True)
class CandidateClass:
    identifier: str
    dependency_status: str
    expanded_signature: ExponentSignature
    member_expressions: tuple[str, ...]
    log10_magnitude: float


def build_candidate_classes(
    candidates: Sequence[AnalyzedCandidate],
) -> tuple[CandidateClass, ...]:
    """Collapse surface candidates using the existing exact equivalence identifiers."""

    grouped: dict[str, list[AnalyzedCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.equivalence_group_identifier, []).append(candidate)

    classes: list[CandidateClass] = []
    for identifier, members in sorted(grouped.items()):
        statuses = {member.dependency_status for member in members}
        signatures = {member.expanded_dependency_signature for member in members}
        if len(statuses) != 1 or len(signatures) != 1:
            raise RuntimeError(
                f"equivalence class {identifier} mixes provenance classifications"
            )
        representative = members[0]
        if representative.unresolved_factors:
            log_position = math.nan
        else:
            log_position = evaluate_signature_log10(
                representative.expanded_dependency_signature
            )
        classes.append(
            CandidateClass(
                identifier=identifier,
                dependency_status=representative.dependency_status,
                expanded_signature=representative.expanded_dependency_signature,
                member_expressions=tuple(
                    sorted(member.candidate.expression for member in members)
                ),
                log10_magnitude=log_position,
            )
        )
    return tuple(classes)


def stratify_classes(
    classes: Sequence[CandidateClass],
) -> tuple[tuple[CandidateClass, ...], tuple[CandidateClass, ...], tuple[CandidateClass, ...]]:
    """Return primary, circularity-control, and unresolved strata without pooling."""

    primary = tuple(
        item
        for item in classes
        if item.dependency_status == NO_REGISTERED_TARGET_DEPENDENCY
    )
    circularity = tuple(
        item
        for item in classes
        if item.dependency_status in {TARGET_RECONSTRUCTION, TARGET_DEPENDENT}
    )
    unresolved = tuple(
        item for item in classes if item.dependency_status == UNRESOLVED_PROVENANCE
    )
    accounted = set(primary) | set(circularity) | set(unresolved)
    if accounted != set(classes):
        raise RuntimeError("unrecognized dependency status in candidate classes")
    if not primary:
        raise RuntimeError("the primary null has no eligible equivalence classes")
    return primary, circularity, unresolved


def unique_log_positions(classes: Sequence[CandidateClass]) -> tuple[float, ...]:
    """Deduplicate identical geometric locations without changing class trial counts."""

    positions = {item.log10_magnitude for item in classes}
    if any(not math.isfinite(position) for position in positions):
        raise ValueError("eligible class has no finite log position")
    return tuple(sorted(positions))


def derive_global_interval(
    eligible_positions: Sequence[float],
    local_interval: tuple[float, float],
) -> tuple[float, float]:
    if not eligible_positions:
        raise ValueError("global bounds require at least one eligible position")
    local_lower, local_upper = local_interval
    return (
        min(min(eligible_positions) - 3.0, local_lower),
        max(max(eligible_positions) + 3.0, local_upper),
    )


def nearest_classes(
    target_log10: float,
    classes: Sequence[CandidateClass],
    *,
    tie_tolerance: float = TIE_TOLERANCE,
) -> tuple[float, tuple[str, ...]]:
    distances = [
        (abs(target_log10 - item.log10_magnitude), item.identifier)
        for item in classes
    ]
    best = min(distance for distance, _ in distances)
    winners = tuple(
        sorted(
            identifier
            for distance, identifier in distances
            if abs(distance - best) <= tie_tolerance
        )
    )
    return best, winners


def sample_uniform_log_targets(
    lower: float,
    upper: float,
    *,
    count: int,
    seed: int,
) -> tuple[float, ...]:
    """Monte Carlo sampler; deliberately independent from the analytic oracle."""

    if not lower < upper:
        raise ValueError("null interval must have positive width")
    if count < 1:
        raise ValueError("target count must be positive")
    generator = random.Random(seed)
    width = upper - lower
    return tuple(lower + width * generator.random() for _ in range(count))


def analytic_nearest_distance_cdf(
    distance: float,
    lower: float,
    upper: float,
    candidate_positions: Sequence[float],
) -> float:
    """Geometric interval-union oracle; it never calls the sampling path."""

    if not lower < upper:
        raise ValueError("analytic interval must have positive width")
    if distance < 0:
        return 0.0
    intervals = sorted(
        (max(lower, position - distance), min(upper, position + distance))
        for position in set(candidate_positions)
        if position + distance >= lower and position - distance <= upper
    )
    if not intervals:
        return 0.0
    covered = 0.0
    current_lower, current_upper = intervals[0]
    for next_lower, next_upper in intervals[1:]:
        if next_lower <= current_upper:
            current_upper = max(current_upper, next_upper)
        else:
            covered += current_upper - current_lower
            current_lower, current_upper = next_lower, next_upper
    covered += current_upper - current_lower
    return min(1.0, max(0.0, covered / (upper - lower)))


def maximum_cdf_deviation(
    distances: Sequence[float],
    lower: float,
    upper: float,
    candidate_positions: Sequence[float],
) -> float:
    """Two-sided empirical/analytic sup distance at all sample discontinuities."""

    if not distances:
        raise ValueError("CDF comparison requires at least one distance")
    ordered = sorted(distances)
    count = len(ordered)
    maximum = 0.0
    for index, distance in enumerate(ordered, start=1):
        analytic = analytic_nearest_distance_cdf(
            distance, lower, upper, candidate_positions
        )
        maximum = max(
            maximum,
            abs((index - 1) / count - analytic),
            abs(index / count - analytic),
        )
    return maximum


def _class_record(item: CandidateClass) -> dict[str, Any]:
    return {
        "identifier": item.identifier,
        "dependency_status": item.dependency_status,
        "expanded_dependency_signature": signature_record(item.expanded_signature),
        "member_expressions": list(item.member_expressions),
        "log10_magnitude": _float_record(item.log10_magnitude),
    }


def _null_run_record(
    identifier: str,
    classes: Sequence[CandidateClass],
    lower: float,
    upper: float,
    *,
    count: int,
    seed: int,
    tolerance: float,
) -> dict[str, Any]:
    samples = sample_uniform_log_targets(
        lower, upper, count=count, seed=seed
    )
    trial_lines: list[str] = []
    distances: list[float] = []
    tie_count = 0
    for index, target_log10 in enumerate(samples):
        distance, winners = nearest_classes(target_log10, classes)
        distances.append(distance)
        tie_count += len(winners) > 1
        trial_lines.append(
            "\t".join(
                (
                    str(index),
                    target_log10.hex(),
                    (10.0**target_log10).hex(),
                    distance.hex(),
                    ",".join(winners),
                )
            )
        )
    positions = unique_log_positions(classes)
    deviation = maximum_cdf_deviation(distances, lower, upper, positions)
    return {
        "identifier": identifier,
        "status": "valid" if deviation <= tolerance else "invalid",
        "invalid_reason": (
            None
            if deviation <= tolerance
            else "Monte Carlo/analytic CDF calibration exceeded preregistered tolerance"
        ),
        "seed": seed,
        "target_count": count,
        "interval_log10": {
            "lower": _float_record(lower),
            "upper": _float_record(upper),
        },
        "eligible_class_count": len(classes),
        "unique_numerical_position_count": len(positions),
        "tie_trial_count": tie_count,
        "calibration": {
            "statistic": "two_sided_maximum_empirical_analytic_cdf_deviation",
            "observed": _float_record(deviation),
            "tolerance": _float_record(tolerance),
            "passed": deviation <= tolerance,
        },
        "trial_encoding": {
            "format": "tab_separated_utf8_chunks_v1",
            "columns": [
                "zero_based_index",
                "target_log10_float_hex",
                "target_magnitude_float_hex",
                "nearest_distance_float_hex",
                "comma_separated_winning_class_identifiers",
            ],
            "chunk_size": TRIAL_CHUNK_SIZE,
            "record_separator": "newline",
            "final_newline_in_digest_payload": True,
            "payload_sha256": hashlib.sha256(
                ("\n".join(trial_lines) + "\n").encode("utf-8")
            ).hexdigest(),
            "chunks": [
                "\n".join(trial_lines[start : start + TRIAL_CHUNK_SIZE])
                for start in range(0, len(trial_lines), TRIAL_CHUNK_SIZE)
            ],
        },
    }


def iter_trial_rows(run: Mapping[str, Any]) -> Iterable[tuple[str, ...]]:
    """Decode every recorded target row from the deterministic chunk representation."""

    encoding = run.get("trial_encoding")
    if not isinstance(encoding, Mapping) or encoding.get("format") != "tab_separated_utf8_chunks_v1":
        raise ValueError("unknown or missing null-trial encoding")
    chunks = encoding.get("chunks")
    if not isinstance(chunks, list) or any(not isinstance(chunk, str) for chunk in chunks):
        raise ValueError("null-trial chunks are malformed")
    lines = [line for chunk in chunks for line in chunk.splitlines()]
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    if hashlib.sha256(payload).hexdigest() != encoding.get("payload_sha256"):
        raise ValueError("null-trial payload hash mismatch")
    if len(lines) != run.get("target_count"):
        raise ValueError("null-trial count does not match recorded target count")
    for expected_index, line in enumerate(lines):
        fields = tuple(line.split("\t"))
        if len(fields) != 5 or fields[0] != str(expected_index):
            raise ValueError("null-trial row is malformed or out of order")
        yield fields


def _clearance(item: CandidateClass, classes: Sequence[CandidateClass]) -> float:
    other_positions = {
        other.log10_magnitude
        for other in classes
        if other.log10_magnitude != item.log10_magnitude
    }
    return (
        math.inf
        if not other_positions
        else min(abs(item.log10_magnitude - other) for other in other_positions)
    )


def _planted_controls(
    classes: Sequence[CandidateClass],
    epsilon_values: Sequence[str],
) -> dict[str, Any]:
    ranked = sorted(classes, key=lambda item: (-_clearance(item, classes), item.identifier))
    selected: set[str] = set()
    records = []
    for epsilon_text in epsilon_values:
        epsilon = float(epsilon_text)
        if epsilon == 0 or epsilon <= -1:
            raise ValueError("planted epsilon must be nonzero and greater than -1")
        expected = abs(math.log10(1.0 + epsilon))
        intended = next(
            (
                item
                for item in ranked
                if item.identifier not in selected
                and _clearance(item, classes) > expected + TIE_TOLERANCE
            ),
            None,
        )
        if intended is None:
            raise RuntimeError("no eligible planted class has sufficient clearance")
        selected.add(intended.identifier)
        target_log10 = intended.log10_magnitude + math.log10(1.0 + epsilon)
        measured, winners = nearest_classes(target_log10, classes)
        recovered = intended.identifier in winners
        distance_matches = abs(measured - expected) <= NUMERICAL_TOLERANCE
        records.append(
            {
                "intended_class_identifier": intended.identifier,
                "epsilon": epsilon_text,
                "class_log10_magnitude": _float_record(intended.log10_magnitude),
                "target_log10_magnitude": _float_record(target_log10),
                "target_magnitude": _float_record(10.0**target_log10),
                "class_clearance_log10": _float_record(_clearance(intended, classes)),
                "expected_distance": _float_record(expected),
                "measured_distance": _float_record(measured),
                "winning_class_identifiers": list(winners),
                "recovered": recovered,
                "distance_matches": distance_matches,
                "passed": recovered and distance_matches,
            }
        )
    return {
        "status": "valid" if all(record["passed"] for record in records) else "invalid",
        "controls": records,
    }


def _git_output(arguments: Sequence[str], *, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_source_state(
    source_commit_sha: str,
    *,
    repository_root: Path = Path("."),
    source_paths: Sequence[str] = SOURCE_PATHS,
) -> None:
    """Verify that result-driving files still match the recorded committed source."""

    if len(source_commit_sha) != 40 or any(c not in "0123456789abcdef" for c in source_commit_sha):
        raise ValueError("result source commit SHA is invalid")
    resolved = _git_output(["rev-parse", source_commit_sha], cwd=repository_root)
    if resolved != source_commit_sha:
        raise ValueError("result source commit SHA does not resolve exactly")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit_sha, "HEAD"],
        cwd=repository_root,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("result source commit is not an ancestor of HEAD")
    changed = subprocess.run(
        ["git", "diff", "--quiet", source_commit_sha, "--", *source_paths],
        cwd=repository_root,
        check=False,
    )
    if changed.returncode != 0:
        raise ValueError("result-driving source differs from recorded source commit")


def _preregistration_commit_sha(
    path: Path,
    *,
    repository_root: Path,
) -> str:
    return _git_output(
        ["log", "-1", "--format=%H", "--", str(path)],
        cwd=repository_root,
    )


def build_result(
    *,
    source_commit_sha: str,
    preregistration_path: Path = DEFAULT_PREREGISTRATION_OUTPUT,
    repository_root: Path = Path("."),
    verify_git: bool = True,
) -> dict[str, Any]:
    """Execute the frozen null and planted-control specification exactly once."""

    preregistration, preregistration_bytes = load_preregistration(preregistration_path)
    if verify_git:
        verify_source_state(source_commit_sha, repository_root=repository_root)
    candidates = analyze_default_candidates()
    classes = build_candidate_classes(candidates)
    primary, circularity, unresolved = stratify_classes(classes)
    primary_positions = unique_log_positions(primary)
    g_log10 = math.log10(GRAVITATIONAL_CONSTANT_G.value_si)
    local_interval = (g_log10 - 3.0, g_log10 + 3.0)
    global_interval = derive_global_interval(primary_positions, local_interval)

    randomness = preregistration["randomness"]
    count = randomness["target_count_per_null"]
    seeds = randomness["seeds"]
    tolerance = preregistration["analytic_calibration"]["tolerance"]
    local = _null_run_record(
        "local_null_primary",
        primary,
        *local_interval,
        count=count,
        seed=seeds["local_null"],
        tolerance=tolerance,
    )
    global_run = _null_run_record(
        "global_null_contextual",
        primary,
        *global_interval,
        count=count,
        seed=seeds["global_null"],
        tolerance=tolerance,
    )
    planted = _planted_controls(
        primary,
        preregistration["planted_controls"]["epsilon_values"],
    )

    real_distance, real_winners = nearest_classes(g_log10, primary)
    real_empirical_cdf = sum(
        float.fromhex(trial[3]) <= real_distance for trial in iter_trial_rows(local)
    ) / count
    real_analytic_cdf = analytic_nearest_distance_cdf(
        real_distance, *local_interval, primary_positions
    )
    circular_distance, circular_winners = nearest_classes(g_log10, circularity)

    valid = (
        local["status"] == "valid"
        and global_run["status"] == "valid"
        and planted["status"] == "valid"
    )
    result = {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "methodological_result_status": "valid" if valid else "invalid",
        "invalid_reasons": [
            reason
            for reason in (
                local["invalid_reason"],
                global_run["invalid_reason"],
                None if planted["status"] == "valid" else "planted-target control failed",
            )
            if reason is not None
        ],
        "integrity": {
            "preregistration_path": str(preregistration_path),
            "preregistration_sha256": preregistration_sha256_bytes(
                preregistration_bytes
            ),
            "preregistration_commit_sha": (
                _preregistration_commit_sha(
                    preregistration_path, repository_root=repository_root
                )
                if verify_git
                else None
            ),
            "source_commit_sha": source_commit_sha,
            "source_commit_semantics": (
                "Committed source state used to generate this result; the later commit "
                "containing the result artifact necessarily has a different SHA."
            ),
            "source_paths": list(SOURCE_PATHS),
            "seeds": dict(seeds),
        },
        "trial_accounting": {
            "raw_surface_candidate_count": len(candidates),
            "total_equivalence_class_count": len(classes),
            "eligible_primary_stratum_class_count": len(primary),
            "eligible_unique_numerical_position_count": len(primary_positions),
            "excluded_target_dependent_class_count": len(circularity),
            "excluded_unresolved_class_count": len(unresolved),
        },
        "candidate_classes": {
            "primary_no_registered_target_dependency": [
                _class_record(item) for item in primary
            ],
            "circularity_control": [_class_record(item) for item in circularity],
            "unresolved": [_class_record(item) for item in unresolved],
        },
        "real_G_navigation": {
            "target_log10_magnitude": _float_record(g_log10),
            "primary_nearest_distance": _float_record(real_distance),
            "primary_winning_class_identifiers": list(real_winners),
            "local_null_empirical_cdf_at_distance": _float_record(real_empirical_cdf),
            "local_null_analytic_cdf_at_distance": _float_record(real_analytic_cdf),
            "interpretation": (
                "This comparison calibrates the grammar; neither tail is physical evidence."
            ),
        },
        "circularity_control": {
            "target_dependent_classes_were_excluded_from_primary": True,
            "nearest_distance_to_G": _float_record(circular_distance),
            "winning_class_identifiers": list(circular_winners),
            "interpretation": (
                "Registered G-dependent definitions can reconstruct or closely track G; "
                "pooling them into the primary null would leak the target."
            ),
        },
        "local_null": local,
        "global_null": global_run,
        "planted_target_controls": planted,
        "nonclaims": [
            "This result does not measure or derive G.",
            "This result does not establish physical independence of any candidate.",
            "Neither null tail is evidence for or against a physical theory.",
            "Planted recovery is a software-method control, not a physical observation.",
            "Passing these controls does not prove that the project cannot fool itself.",
        ],
    }
    return result


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def validate_result_integrity(
    result: Mapping[str, Any],
    *,
    preregistration_path: Path = DEFAULT_PREREGISTRATION_OUTPUT,
) -> None:
    preregistration, content = load_preregistration(preregistration_path)
    if result.get("result_schema_version") != RESULT_SCHEMA_VERSION:
        raise ValueError("stale null-result schema version")
    if result.get("experiment_identifier") != preregistration["experiment_identifier"]:
        raise ValueError("preregistration/result experiment mismatch")
    integrity = result.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ValueError("null-result integrity metadata is missing")
    if integrity.get("preregistration_sha256") != preregistration_sha256_bytes(content):
        raise ValueError("preregistration/result hash mismatch")
    if integrity.get("seeds") != preregistration["randomness"]["seeds"]:
        raise ValueError("preregistration/result seed mismatch")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--preregistration",
        type=Path,
        default=DEFAULT_PREREGISTRATION_OUTPUT,
    )
    parser.add_argument("--source-commit-sha")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify integrity and deterministic regeneration without overwriting",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.check:
        if not args.output.exists():
            print(f"missing null-result artifact: {args.output}", file=sys.stderr)
            raise SystemExit(1)
        existing = json.loads(args.output.read_text(encoding="utf-8"))
        validate_result_integrity(existing, preregistration_path=args.preregistration)
        source_sha = existing["integrity"]["source_commit_sha"]
        verify_source_state(source_sha)
        expected = serialize_artifact(
            build_result(
                source_commit_sha=source_sha,
                preregistration_path=args.preregistration,
            )
        )
        if args.output.read_text(encoding="utf-8") != expected:
            print(f"stale null-result artifact: {args.output}", file=sys.stderr)
            raise SystemExit(1)
        print("Null and planted-control result is current and integrity-checked.")
        return

    if args.source_commit_sha is None:
        print("--source-commit-sha is required for a new result", file=sys.stderr)
        raise SystemExit(2)
    rendered = serialize_artifact(
        build_result(
            source_commit_sha=args.source_commit_sha,
            preregistration_path=args.preregistration,
        )
    )
    if args.output.exists():
        print(
            "refusing to overwrite an existing result; create a new experiment version",
            file=sys.stderr,
        )
        raise SystemExit(1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote preregistered null result to {args.output}.")


if __name__ == "__main__":
    main()
