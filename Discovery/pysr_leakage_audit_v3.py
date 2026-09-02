"""Future-facing PySR leakage audit semantics after post-6B hardening.

Milestone 6B's committed result remains frozen under the historical v2 adapter.
This module is deliberately additive: future consumers should use it when auditing
new target-exposed candidates.

The important refinement is the empty-predictor case. A fitted numeric constant is
still target-exposed because the generating procedure saw the target, but there is
no predictor reference through which the synthetic generation DAG can answer a
predictor-ancestry question. Returning a bare ``False`` for that structural question
would be easy to misread as evidence of independence, so v3 records it as explicitly
not applicable.
"""

from __future__ import annotations

from typing import Any

import Discovery.pysr_leakage_audit as v2
import Discovery.pysr_leakage_probe as probe

GENERATION_ANCESTRY_DETECTED = "target_ancestry_detected"
GENERATION_ANCESTRY_NOT_DETECTED = "target_ancestry_not_detected"
GENERATION_ANCESTRY_NOT_APPLICABLE = "not_applicable_no_predictor_reference"
GENERATION_ANCESTRY_UNRESOLVED = "unresolved"


def audit_expression(channel: str, expression: str) -> dict[str, Any]:
    """Audit with v2 compatibility plus non-vacuous generation-ancestry semantics."""

    record = dict(v2.audit_expression(channel, expression))
    representation = record.get("representation_status")
    referenced = record.get("referenced_predictors")

    if representation == probe.PARSE_FAILURE:
        record["generation_ancestry_assessment"] = GENERATION_ANCESTRY_UNRESOLVED
        return record

    if not isinstance(referenced, list):
        raise probe.LeakageProbeError("candidate referenced-predictor record is malformed")

    is_empty_factor_monomial = (
        representation == probe.NORMALIZED_MONOMIAL
        and referenced == []
        and record.get("normalized_exponents") == []
    )
    if is_empty_factor_monomial:
        # The candidate remains target-exposed at the generation-process level, but
        # predictor ancestry is a vacuous question when the expression references no
        # predictors. Do not encode that as evidence of no leakage.
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
