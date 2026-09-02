"""Post-6B hardening checks for preregistration fidelity and future audit semantics.

This module is intentionally additive. It does not rewrite the frozen Milestone 6B
result or its source anchors. Instead it validates that the committed external run
matches the preregistered search contract and checks the future-facing v3 semantics
for predictor-free target-exposed candidates.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping

import Discovery.pysr_leakage_audit_v3 as audit_v3
import Discovery.pysr_leakage_check_v2 as historical_v2
import Discovery.pysr_leakage_probe as probe


class PySRHardeningError(ValueError):
    """Raised when post-6B hardening detects contract drift."""


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PySRHardeningError(f"{label} must be an object")
    return value


def _canonical_subrecord(value: object) -> bytes:
    return probe.canonical_json_bytes(value)


def validate_search_contract(
    preregistration: Mapping[str, Any],
    external: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed unless external execution matches the frozen search configuration."""

    prereg_search = _mapping(
        preregistration.get("search_configuration"),
        "preregistered search_configuration",
    )
    external_search = _mapping(
        external.get("search_configuration"),
        "external search_configuration",
    )
    if _canonical_subrecord(prereg_search) != _canonical_subrecord(external_search):
        raise PySRHardeningError(
            "external search_configuration does not match preregistration"
        )

    prereg_seeds = prereg_search.get("seeds")
    if (
        not isinstance(prereg_seeds, list)
        or not prereg_seeds
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in prereg_seeds)
        or len(set(prereg_seeds)) != len(prereg_seeds)
    ):
        raise PySRHardeningError("preregistered seed list is malformed")

    runs = external.get("runs")
    if not isinstance(runs, list):
        raise PySRHardeningError("external runs must be a list")
    observed_pairs: list[tuple[str, int]] = []
    for run in runs:
        if not isinstance(run, Mapping):
            raise PySRHardeningError("external run entry is malformed")
        channel = run.get("channel")
        seed = run.get("seed")
        if not isinstance(channel, str) or isinstance(seed, bool) or not isinstance(seed, int):
            raise PySRHardeningError("external run channel/seed is malformed")
        observed_pairs.append((channel, seed))

    expected_pairs = [
        (channel, seed)
        for channel in probe.CHANNELS
        for seed in prereg_seeds
    ]
    if sorted(observed_pairs) != sorted(expected_pairs):
        raise PySRHardeningError(
            "external channel/seed coverage does not match preregistration"
        )
    if len(observed_pairs) != len(set(observed_pairs)):
        raise PySRHardeningError("external channel/seed coverage contains duplicates")

    prereg_engine = _mapping(preregistration.get("external_engine"), "external_engine")
    external_source = _mapping(external.get("external_source"), "external_source")
    source_contract = {
        "repository": prereg_engine.get("repository"),
        "pysr_commit": prereg_engine.get("pysr_commit"),
        "pysr_version": prereg_engine.get("pysr_version"),
        "pyproject_blob": prereg_engine.get("pyproject_blob"),
        "juliapkg_blob": prereg_engine.get("juliapkg_blob"),
        "license_blob": prereg_engine.get("license_blob"),
    }
    observed_source = {key: external_source.get(key) for key in source_contract}
    if _canonical_subrecord(source_contract) != _canonical_subrecord(observed_source):
        raise PySRHardeningError("external PySR source pin does not match preregistration")

    return {
        "search_configuration_match": True,
        "observed_seeds": list(prereg_seeds),
        "observed_run_count": len(observed_pairs),
        "external_source_pin_match": True,
    }


def validate_future_constant_semantics(external: Mapping[str, Any]) -> dict[str, Any]:
    """Ensure predictor-free fitted constants are never presented as leakage-negative."""

    constant_only_count = 0
    for run in external.get("runs", []):
        if not isinstance(run, Mapping):
            continue
        channel = run.get("channel")
        candidates = run.get("candidates")
        if not isinstance(channel, str) or not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            equation = candidate.get("equation")
            if not isinstance(equation, str):
                continue
            audit = audit_v3.audit_expression(channel, equation)
            if (
                audit.get("generation_ancestry_assessment")
                == audit_v3.GENERATION_ANCESTRY_NOT_APPLICABLE
            ):
                constant_only_count += 1
                if audit.get("candidate_origin") != probe.TARGET_EXPOSED_CANDIDATE:
                    raise PySRHardeningError("predictor-free candidate lost target-exposed origin")
                if audit.get("promotion_eligible") is not False:
                    raise PySRHardeningError("predictor-free target-exposed candidate became promotable")
                if audit.get("known_generation_target_leakage") is not None:
                    raise PySRHardeningError(
                        "predictor-free generation ancestry must be explicitly not applicable"
                    )
                if audit.get("hidden_target_leakage_blind_spot") is not None:
                    raise PySRHardeningError(
                        "predictor-free blind-spot result must be explicitly not applicable"
                    )

    if constant_only_count == 0:
        raise PySRHardeningError("frozen 6B evidence contains no constant-only control cases")
    return {
        "constant_only_candidates": constant_only_count,
        "future_generation_ancestry_semantics": audit_v3.GENERATION_ANCESTRY_NOT_APPLICABLE,
    }


def check_committed_hardening() -> dict[str, Any]:
    # First require the frozen historical evidence to remain valid under its own v2 gate.
    historical_v2.check_committed_artifacts()

    preregistration = probe.load_json(probe.PREREGISTRATION_PATH)
    try:
        external = json.loads(probe.EXTERNAL_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PySRHardeningError(f"cannot load external artifact: {error}") from error
    if not isinstance(external, dict):
        raise PySRHardeningError("external artifact must contain an object")

    search = validate_search_contract(preregistration, external)
    constants = validate_future_constant_semantics(external)
    return {**search, **constants}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("use --check")
    try:
        result = check_committed_hardening()
    except (PySRHardeningError, probe.LeakageProbeError, OSError, json.JSONDecodeError) as error:
        print(f"Post-6B hardening check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(
        "Post-6B hardening is current: preregistered search contract matched; "
        f"{result['constant_only_candidates']} predictor-free candidates use explicit N/A ancestry semantics."
    )


if __name__ == "__main__":
    main()
