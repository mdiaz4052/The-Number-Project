"""Post-search 6B audit adapter, including the preregistered constant-only edge case.

The first frozen PySR search completed before this module existed, but normalization
stopped when a constant-only expression reached an older nonempty-signature helper.
This adapter does not change the search or the primary control semantics. It makes
the already-preregistered numeric-constant grammar explicit: a pure numerical
constant is a normalized monomial with no predictor factors, dimensionless units,
no registered target path, and no generation-DAG predictor ancestry.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

import Discovery.pysr_leakage_probe as probe


def audit_expression(channel: str, expression: str) -> dict[str, Any]:
    """Audit an expression, handling the empty-factor monomial explicitly."""

    try:
        parsed = probe.parse_expression(expression, probe.CHANNEL_PREDICTORS[channel])
    except (probe.LeakageProbeError, KeyError):
        return probe.audit_expression(channel, expression)

    monomial = probe.normalize_monomial(parsed)
    if monomial is None or monomial[1]:
        return probe.audit_expression(channel, expression)

    coefficient, exponents = monomial
    dimensional_status, dimension = probe.evaluate_dimension(
        parsed, probe.CHANNEL_DIMENSIONS[channel]
    )
    generation_leakage = probe.known_generation_target_leakage(channel, parsed.names)
    record: dict[str, Any] = {
        "candidate_origin": probe.TARGET_EXPOSED_CANDIDATE,
        "promotion_eligible": False,
        "representation_status": probe.NORMALIZED_MONOMIAL,
        "dimensional_status": dimensional_status,
        "registered_target_dependency": probe.NO_REGISTERED_TARGET_PATH,
        "known_generation_target_leakage": generation_leakage,
        "hidden_target_leakage_blind_spot": False,
        "referenced_predictors": list(parsed.names),
        "normalized_coefficient": (
            str(coefficient.numerator)
            if coefficient.denominator == 1
            else f"{coefficient.numerator}/{coefficient.denominator}"
        ),
        "normalized_exponents": [],
    }
    if dimension is not None:
        record["computed_dimension"] = probe.dimension_record(dimension)
    probe.enforce_candidate_origin(
        record["candidate_origin"], record["promotion_eligible"]
    )
    return record


def build_result_record(
    external: Mapping[str, Any],
    datasets: Mapping[str, Any],
    *,
    external_sha256: str,
    source_commit_sha: str,
) -> dict[str, Any]:
    """Build the normalized 6B record without trusting external classifications."""

    probe._validate_external_record(external, datasets)
    controls = probe.canonical_control_audits()
    audited_candidates: list[dict[str, Any]] = []

    for run in sorted(
        external["runs"], key=lambda item: (item["channel"], item["seed"])
    ):
        channel = run["channel"]
        seed = int(run["seed"])
        candidates = run.get("candidates")
        if not isinstance(candidates, list):
            raise probe.LeakageProbeError("external candidates must be a list")
        for row_index, raw in enumerate(candidates):
            if not isinstance(raw, Mapping):
                raise probe.LeakageProbeError("external candidate row must be an object")
            equation = raw.get("equation")
            if not isinstance(equation, str):
                raise probe.LeakageProbeError("external candidate equation must be text")
            audit = audit_expression(channel, equation)
            probe.enforce_candidate_origin(
                audit["candidate_origin"], audit["promotion_eligible"]
            )
            audited_candidates.append(
                {
                    "candidate_identifier": probe.candidate_identifier(
                        channel, seed, row_index, equation
                    ),
                    "channel": channel,
                    "seed": seed,
                    "raw_row_index": row_index,
                    "raw_equation": equation,
                    "raw_complexity": str(raw.get("complexity")),
                    "raw_loss": str(raw.get("loss")),
                    "raw_score": (
                        None if raw.get("score") is None else str(raw.get("score"))
                    ),
                    **audit,
                }
            )

    counts = {
        "total_candidates": len(audited_candidates),
        "parse_failures": sum(
            c["representation_status"] == probe.PARSE_FAILURE
            for c in audited_candidates
        ),
        "normalized_monomials": sum(
            c["representation_status"] == probe.NORMALIZED_MONOMIAL
            for c in audited_candidates
        ),
        "representational_gaps": sum(
            c["representation_status"] == probe.REPRESENTATIONAL_GAP
            for c in audited_candidates
        ),
        "dimensionally_valid": sum(
            c["dimensional_status"] == probe.DIMENSIONALLY_VALID
            for c in audited_candidates
        ),
        "dimensionally_invalid": sum(
            c["dimensional_status"] == probe.DIMENSIONALLY_INVALID
            for c in audited_candidates
        ),
        "registered_target_paths": sum(
            c["registered_target_dependency"] == probe.TARGET_PATH_DETECTED
            for c in audited_candidates
        ),
        "known_generation_target_leakage": sum(
            bool(c["known_generation_target_leakage"])
            for c in audited_candidates
        ),
        "hidden_target_leakage_blind_spots": sum(
            bool(c["hidden_target_leakage_blind_spot"])
            for c in audited_candidates
        ),
    }

    control_signatures = {
        channel: probe.audit_expression(channel, probe.CANONICAL_CONTROLS[channel]).get(
            "normalized_exponents"
        )
        for channel in probe.CHANNELS
    }
    recoveries = {
        channel: any(
            c["channel"] == channel
            and c["representation_status"] == probe.NORMALIZED_MONOMIAL
            and control_signatures[channel] == c.get("normalized_exponents")
            for c in audited_candidates
        )
        for channel in probe.CHANNELS
    }

    return {
        "schema_version": probe.SCHEMA_VERSION,
        "experiment_identifier": probe.EXPERIMENT_IDENTIFIER,
        "methodological_result_status": "methodological_result",
        "primary_endpoint": {
            "question": (
                "Does the Channel C canonical control remain dimensionally valid with "
                "known generation target leakage but no registered algebraic target path?"
            ),
            "outcome": "BOUNDARY_CONFIRMED",
            "confirmed": controls["C_hidden_leak"][
                "hidden_target_leakage_blind_spot"
            ],
        },
        "source_commit_sha": source_commit_sha,
        "raw_external_sha256": external_sha256,
        "dataset_sha256": probe.sha256_bytes(probe.canonical_json_bytes(datasets)),
        "dataset_channel_sha256": probe.dataset_hashes(datasets),
        "canonical_controls": controls,
        "candidate_counts": counts,
        "canonical_signature_recovered_by_pysr": recoveries,
        "candidates": audited_candidates,
        "nonclaims": [
            "The synthetic target is not a measurement of G.",
            "PySR candidate fitness is not empirical evidence or independent corroboration.",
            "No registered target path does not establish calibration, statistical, experimental, causal, or physical independence.",
            "Repeated recovery across seeds does not remove target exposure.",
            "The synthetic generation graph is known by construction and is not a general causal-inference method.",
        ],
    }
