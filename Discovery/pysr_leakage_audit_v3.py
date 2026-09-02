"""Future-facing PySR leakage audit semantics after post-6B hardening.

Milestone 6B's committed result remains frozen under the historical v2 adapter.
This module is deliberately additive: new candidate-auditing code should use v3.
Do not substitute v3 into the historical v2 artifact checker; doing so would rewrite
frozen audit semantics and invalidate the source-pinned Milestone 6B evidence chain.

Generation ancestry in v3 describes the exact normalized candidate, not incidental
predictor names that cancel out of that candidate. Search-process exposure remains a
separate permanent fact: every PySR-produced candidate is still
``target_exposed_candidate`` and promotion-ineligible because the search saw the
target.

A normalized candidate with no surviving predictor factors therefore has no
structural predictor-ancestry question to answer. Returning a bare ``False`` would be
easy to misread as evidence of independence, so v3 records that case as explicitly
not applicable. Raw predictor names remain available diagnostically.

External candidate text is untrusted. Numeric literals or expression shapes that
cannot be represented safely are converted into a controlled parse-failure record
rather than allowed to escape through implementation exceptions.
"""

from __future__ import annotations

from typing import Any

import Discovery.pysr_leakage_audit as v2
import Discovery.pysr_leakage_probe as probe

GENERATION_ANCESTRY_DETECTED = "target_ancestry_detected"
GENERATION_ANCESTRY_NOT_DETECTED = "target_ancestry_not_detected"
GENERATION_ANCESTRY_NOT_APPLICABLE = "not_applicable_no_predictor_reference"
GENERATION_ANCESTRY_UNRESOLVED = "unresolved"


def _controlled_parse_failure(diagnostic: str) -> dict[str, Any]:
    """Return a forward-facing controlled record for unrepresentable candidate text."""

    return {
        "candidate_origin": probe.TARGET_EXPOSED_CANDIDATE,
        "promotion_eligible": False,
        "representation_status": probe.PARSE_FAILURE,
        "dimensional_status": probe.DIMENSION_UNRESOLVED,
        "registered_target_dependency": probe.NOT_APPLICABLE_REPRESENTATION_GAP,
        "known_generation_target_leakage": None,
        "hidden_target_leakage_blind_spot": None,
        "referenced_predictors": [],
        "parse_diagnostic": diagnostic,
        "generation_ancestry_assessment": GENERATION_ANCESTRY_UNRESOLVED,
    }


def audit_expression(channel: str, expression: str) -> dict[str, Any]:
    """Audit with frozen-v2 compatibility plus forward-facing v3 semantics."""

    if channel not in probe.CHANNELS:
        raise probe.LeakageProbeError(f"unknown channel: {channel}")

    try:
        record = dict(v2.audit_expression(channel, expression))
    except (probe.LeakageProbeError, ValueError, OverflowError) as error:
        return _controlled_parse_failure(
            f"non-finite, unsupported, or unrepresentable candidate expression: {error}"
        )

    representation = record.get("representation_status")
    referenced = record.get("referenced_predictors")

    if representation == probe.PARSE_FAILURE:
        record["known_generation_target_leakage"] = None
        record["hidden_target_leakage_blind_spot"] = None
        record["generation_ancestry_assessment"] = GENERATION_ANCESTRY_UNRESOLVED
        return record

    if not isinstance(referenced, list):
        raise probe.LeakageProbeError("candidate referenced-predictor record is malformed")

    # Structural generation ancestry follows the normalized mathematical candidate.
    # Raw names may show that predictors appeared syntactically, but if every factor
    # cancels exactly there is no surviving predictor path in the resulting expression.
    is_empty_factor_monomial = (
        representation == probe.NORMALIZED_MONOMIAL
        and record.get("normalized_exponents") == []
    )
    if is_empty_factor_monomial:
        record["known_generation_target_leakage"] = None
        record["hidden_target_leakage_blind_spot"] = None
        record["generation_ancestry_assessment"] = GENERATION_ANCESTRY_NOT_APPLICABLE
        return record

    if record.get("known_generation_target_leakage") is True:
        record["generation_ancestry_assessment"] = GENERATION_ANCESTRY_DETECTED
    elif record.get("known_generation_target_leakage") is False:
        record["generation_ancestry_assessment"] = GENERATION_ANCESTRY_NOT_DETECTED
    else:
        record["generation_ancestry_assessment"] = GENERATION_ANCESTRY_UNRESOLVED
    return record
