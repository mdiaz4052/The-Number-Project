"""Deterministic source-availability audit for HUST 2018 AAF.

This module classifies how deeply the retrieved public HUST 2018
angular-acceleration-feedback record has been assessed. It is deliberately not a
MeasurementModel and does not change the physical-bridge schema.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


AUDIT_SCHEMA_VERSION = 2
AUDIT_IDENTIFIER = "hust_2018_aaf_source_availability_v1"
PREREGISTRATION_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_preregistration_v1.md"
)
PREREGISTRATION_SHA256 = (
    "fa297ecfa4cc4ae2ee7737e413dc8bf0f6ad63c70ca2d1ff070ae81dd2ec8885"
)
SOURCE_CAPTURE_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_external_sources_v1.json"
)
REQUIRED_INPUTS_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_required_inputs_v1.json"
)
SOURCE_AUDIT_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.md"
)
POST_AUDIT_CLARIFICATION_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_post_audit_clarification_v1.md"
)
POST_AUDIT_CLARIFICATION_SHA256 = (
    "5e36d76f243603aabf05e37e52061831988fa5e680afd568e487ce87b1499b95"
)
SEMANTIC_REVIEW_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_semantic_source_review_v1.json"
)
SEMANTIC_REVIEW_SHA256 = (
    "1628e7a3eac2fadddf75f892e8128807fd07bed7b51b920672826e4915c68b1f"
)
DEFAULT_OUTPUT = Path(
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.manifest.json"
)

PUBLIC_DIRECT = "PUBLIC_DIRECT"
PUBLIC_DERIVABLE = "PUBLIC_DERIVABLE"
REQUEST_ONLY = "REQUEST_ONLY"
UNPUBLISHED_OR_AMBIGUOUS = "UNPUBLISHED_OR_AMBIGUOUS"
TARGET_DERIVED = "TARGET_DERIVED"
EVIDENCE_TYPES = frozenset(
    {
        PUBLIC_DIRECT,
        PUBLIC_DERIVABLE,
        REQUEST_ONLY,
        UNPUBLISHED_OR_AMBIGUOUS,
        TARGET_DERIVED,
    }
)
CLEAN_EVIDENCE_TYPES = frozenset({PUBLIC_DIRECT, PUBLIC_DERIVABLE})

EXPECTED_EXPERIMENTS = ("AAF-I", "AAF-II", "AAF-III")
EXPECTED_NATURE_RESOURCE_LABELS = (
    "Supplementary Information",
    "Supplementary Data",
    "Source Data Fig. 2",
    "Source Data Fig. 3",
    "Source Data Extended Data Fig. 2",
    "Source Data Extended Data Fig. 4",
    "Source Data Extended Data Fig. 5",
)
EXPECTED_SUPPLEMENT = {
    "source_id": "supplementary_information",
    "retrieval_status": "retrieved_binary",
    "content_type": "application/pdf",
    "byte_length": 2711453,
    "sha256": "5b61d5c831be98c46e47fcc32f1ade0a680b4af6354d2bc34859d94b22279ffb",
}
EXPECTED_SUPPLEMENTARY_DATA = {
    "source_id": "supplementary_data",
    "retrieval_status": "retrieved_binary",
    "byte_length": 1152664,
    "sha256": "9e419d1150b6f7897a1352cee50a9721fed48254279e13fe2847200e677547ba",
}
EXPECTED_EXTENDED_FIG_2_SOURCE_DATA = {
    "source_id": "source_data_extended_fig_2",
    "retrieval_status": "retrieved_binary",
    "byte_length": 36733,
    "sha256": "08af72bca3f7861ac63c6e7695687cd71d3a3b9b631187ce9ce1417e09c66da3",
}
EXPECTED_FAILED_SOURCE_DATA = frozenset(
    {
        "source_data_fig_2",
        "source_data_fig_3",
        "source_data_extended_fig_4",
        "source_data_extended_fig_5",
    }
)
EXPECTED_SEMANTIC_REVIEW_CLAIMS = (
    "p_g_definition_excludes_G",
    "magnetic_damper_direction",
    "table3_scope_and_air_density",
)
EXPECTED_DIRECT_TRANSCRIPTIONS = {
    "AAF-I:p_sum": {
        "value": "6926.352",
        "printed_value": "6926.352(74)",
        "standard_uncertainty": "0.074",
        "unit": "kg m^-3",
        "source_scope_tokens": ["AAF-I"],
    },
    "AAF-I:alpha_corrected": {
        "value": "462.0912",
        "printed_value": "462.0912(16)",
        "standard_uncertainty": "0.0016",
        "unit": "nrad s^-2",
        "source_scope_tokens": ["AAF-I"],
    },
    "AAF-I:magnetic_damper_ppm": {
        "value": "455.40",
        "printed_value": "455.40(1.95)",
        "standard_uncertainty": "1.95",
        "unit": "ppm",
        "source_scope_tokens": ["AAF-I", "AAF-II"],
        "correction_direction": "increase_G",
        "correction_operator": "multiply_by_1_plus_delta",
        "direction_evidence_text": "(1 + ΔG_MD/G)",
    },
    "AAF-II:p_sum": {
        "value": "6926.334",
        "printed_value": "6926.334(75)",
        "standard_uncertainty": "0.075",
        "unit": "kg m^-3",
        "source_scope_tokens": ["AAF-II"],
    },
    "AAF-II:alpha_corrected": {
        "value": "462.0791",
        "printed_value": "462.0791(12)",
        "standard_uncertainty": "0.0012",
        "unit": "nrad s^-2",
        "source_scope_tokens": ["AAF-II"],
    },
    "AAF-II:magnetic_damper_ppm": {
        "value": "455.40",
        "printed_value": "455.40(1.95)",
        "standard_uncertainty": "1.95",
        "unit": "ppm",
        "source_scope_tokens": ["AAF-I", "AAF-II"],
        "correction_direction": "increase_G",
        "correction_operator": "multiply_by_1_plus_delta",
        "direction_evidence_text": "(1 + ΔG_MD/G)",
    },
    "AAF-III:p_sum": {
        "value": "6926.415",
        "printed_value": "6926.415(74)",
        "standard_uncertainty": "0.074",
        "unit": "kg m^-3",
        "source_scope_tokens": ["AAF-III"],
    },
    "AAF-III:alpha_corrected": {
        "value": "462.2941",
        "printed_value": "462.2941(6)",
        "standard_uncertainty": "0.0006",
        "unit": "nrad s^-2",
        "source_scope_tokens": ["AAF-III"],
    },
    "AAF-III:magnetic_damper_ppm": {
        "value": "25.74",
        "printed_value": "25.74(8)",
        "standard_uncertainty": "0.08",
        "unit": "ppm",
        "source_scope_tokens": ["AAF-III"],
        "correction_direction": "increase_G",
        "correction_operator": "multiply_by_1_plus_delta",
        "direction_evidence_text": "(1 + ΔG_MD/G)",
    },
}
MEASUREMENT_NOTATION_RE = re.compile(
    r"^(?P<value>[+-]?\d+(?:\.\d+)?)\((?P<unc>\d+(?:\.\d+)?)\)$"
)

NONCLAIMS = (
    "This audit does not establish that the HUST value of G is correct.",
    "GO/2a is a public-summary central-value reconstruction, not an independent laboratory measurement.",
    "Depth 2a does not authorize the combined AAF value or an uncertainty-qualified reproduction.",
    "No MeasurementModel is created and no physical-bridge schema is extended by this audit.",
    "The source-data HTTP fallback findings do not prove that the files cannot be obtained by another public retrieval path.",
    "Depths above 2a were not assessed from the four source-data files that were not successfully retrieved.",
)


class SourceAuditError(ValueError):
    """Controlled validation failure for the HUST source audit."""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceAuditError(f"unavailable or invalid JSON: {path}") from error
    if not isinstance(record, dict):
        raise SourceAuditError(f"JSON root must be an object: {path}")
    return record


def _require_nonempty_string(
    record: Mapping[str, Any], key: str, *, context: str
) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SourceAuditError(f"{context} requires nonempty {key}")
    return value


def _verify_pinned_file(
    root: Path, path: Path, expected_sha256: str, *, label: str
) -> dict[str, str]:
    try:
        content = (root / path).read_bytes()
    except OSError as error:
        raise SourceAuditError(f"{label} is unavailable") from error
    actual = sha256_bytes(content)
    if actual != expected_sha256:
        raise SourceAuditError(f"{label} hash mismatch")
    return {"path": path.as_posix(), "sha256": expected_sha256}


def verify_preregistration(root: Path = Path(".")) -> dict[str, str]:
    return _verify_pinned_file(
        root,
        PREREGISTRATION_PATH,
        PREREGISTRATION_SHA256,
        label="HUST preregistration",
    )


def verify_post_audit_clarification(root: Path = Path(".")) -> dict[str, str]:
    return _verify_pinned_file(
        root,
        POST_AUDIT_CLARIFICATION_PATH,
        POST_AUDIT_CLARIFICATION_SHA256,
        label="HUST post-audit clarification",
    )


def verify_semantic_review(root: Path = Path(".")) -> dict[str, Any]:
    pin = _verify_pinned_file(
        root,
        SEMANTIC_REVIEW_PATH,
        SEMANTIC_REVIEW_SHA256,
        label="HUST semantic source review",
    )
    record = _read_json(root / SEMANTIC_REVIEW_PATH)
    if record.get("schema_version") != 1:
        raise SourceAuditError("unexpected HUST semantic-review schema version")
    if record.get("source_id") != "supplementary_information":
        raise SourceAuditError("semantic review source mismatch")
    if record.get("source_sha256") != EXPECTED_SUPPLEMENT["sha256"]:
        raise SourceAuditError("semantic review is not bound to the reviewed supplement")
    checks = record.get("checks")
    if not isinstance(checks, list):
        raise SourceAuditError("semantic review checks must be a list")
    claim_ids = []
    for check in checks:
        if not isinstance(check, dict):
            raise SourceAuditError("semantic review check must be an object")
        claim_ids.append(
            _require_nonempty_string(check, "claim_id", context="semantic review check")
        )
        if check.get("status") != "confirmed_by_second_reader":
            raise SourceAuditError("semantic review contains an unconfirmed required claim")
        _require_nonempty_string(check, "locator", context="semantic review check")
        _require_nonempty_string(check, "finding", context="semantic review check")
    if tuple(claim_ids) != EXPECTED_SEMANTIC_REVIEW_CLAIMS:
        raise SourceAuditError("semantic review claim inventory changed")
    return {**pin, "claim_ids": claim_ids}


def _resource_index(
    source_capture: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    resources = source_capture.get("resources")
    if not isinstance(resources, list):
        raise SourceAuditError("source capture resources must be a list")
    index: dict[str, Mapping[str, Any]] = {}
    for raw in resources:
        if not isinstance(raw, dict):
            raise SourceAuditError("source capture resource must be an object")
        source_id = _require_nonempty_string(
            raw, "source_id", context="source resource"
        )
        if source_id in index:
            raise SourceAuditError(f"duplicate source resource: {source_id}")
        index[source_id] = raw
    return index


def _check_expected_resource(
    index: Mapping[str, Mapping[str, Any]], expected: Mapping[str, Any]
) -> None:
    source_id = str(expected["source_id"])
    record = index.get(source_id)
    if record is None:
        raise SourceAuditError(f"required source is missing: {source_id}")
    for key, value in expected.items():
        if record.get(key) != value:
            raise SourceAuditError(
                f"source {source_id} field {key} does not match reviewed capture"
            )
    _require_nonempty_string(record, "offered_url", context=source_id)
    _require_nonempty_string(record, "retrieval_date", context=source_id)


def validate_source_capture(record: Mapping[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != 2:
        raise SourceAuditError("unexpected HUST source-capture schema version")

    labels = record.get("reviewed_nature_resource_labels")
    if labels != list(EXPECTED_NATURE_RESOURCE_LABELS):
        raise SourceAuditError("Nature resource-label inventory changed")

    listing_status = record.get("resource_listing_capture_status")
    if (
        not isinstance(listing_status, str)
        or "verified_from_primary_nature_page" not in listing_status
    ):
        raise SourceAuditError("Nature resource-listing review status is missing")

    index = _resource_index(record)
    _check_expected_resource(index, EXPECTED_SUPPLEMENT)
    _check_expected_resource(index, EXPECTED_SUPPLEMENTARY_DATA)
    _check_expected_resource(index, EXPECTED_EXTENDED_FIG_2_SOURCE_DATA)

    failed: list[str] = []
    for source_id in sorted(EXPECTED_FAILED_SOURCE_DATA):
        resource = index.get(source_id)
        if resource is None:
            raise SourceAuditError(
                f"reviewed failed source-data attempt missing: {source_id}"
            )
        if resource.get("retrieval_status") != "html_fallback_not_source_file":
            raise SourceAuditError(
                f"source-data fallback must not be classified as retrieved: {source_id}"
            )
        if resource.get("content_type") != "text/html":
            raise SourceAuditError(
                f"unexpected failed source-data content type: {source_id}"
            )
        if resource.get("sha256") != record.get("article_capture", {}).get("sha256"):
            raise SourceAuditError(
                f"expected fallback-byte identity is absent: {source_id}"
            )
        failed.append(source_id)

    return {
        "required_summary_source": "supplementary_information",
        "retrieved_binary_sources": sorted(
            source_id
            for source_id, resource in index.items()
            if resource.get("retrieval_status") == "retrieved_binary"
        ),
        "failed_source_data_attempts": failed,
        "resource_listing_capture_status": listing_status,
    }


def load_source_capture(path: Path = SOURCE_CAPTURE_PATH) -> dict[str, Any]:
    return _read_json(path)


def load_required_inputs(path: Path = REQUIRED_INPUTS_PATH) -> dict[str, Any]:
    return _read_json(path)


def _parse_printed_measurement(text: str) -> tuple[Decimal, Decimal]:
    match = MEASUREMENT_NOTATION_RE.fullmatch(text)
    if match is None:
        raise SourceAuditError(f"invalid printed measurement notation: {text}")
    value_text = match.group("value")
    uncertainty_text = match.group("unc")
    value = Decimal(value_text)
    if "." in uncertainty_text:
        uncertainty = Decimal(uncertainty_text)
    else:
        decimal_places = len(value_text.partition(".")[2])
        uncertainty = Decimal(uncertainty_text) * (Decimal(10) ** -decimal_places)
    return value, uncertainty


def _validate_direct_transcription(
    node_id: str, node: Mapping[str, Any], scope: str
) -> None:
    expected = EXPECTED_DIRECT_TRANSCRIPTIONS.get(node_id)
    if expected is None:
        return
    for key, expected_value in expected.items():
        if node.get(key) != expected_value:
            raise SourceAuditError(
                f"reviewed source transcription mismatch on {node_id}: {key}"
            )
    printed = _require_nonempty_string(node, "printed_value", context=node_id)
    parsed_value, parsed_uncertainty = _parse_printed_measurement(printed)
    if parsed_value != Decimal(str(node.get("value"))):
        raise SourceAuditError(f"printed central value mismatch on {node_id}")
    if parsed_uncertainty != Decimal(str(node.get("standard_uncertainty"))):
        raise SourceAuditError(f"printed uncertainty mismatch on {node_id}")
    tokens = node.get("source_scope_tokens")
    if not isinstance(tokens, list) or scope not in tokens:
        raise SourceAuditError(f"source-scope token mismatch on {node_id}")
    if node_id.endswith(":magnetic_damper_ppm"):
        _require_nonempty_string(
            node, "direction_evidence_locator", context=node_id
        )


def _flatten_nodes(
    graph: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    experiments = graph.get("experiments")
    if not isinstance(experiments, list):
        raise SourceAuditError("required-input graph experiments must be a list")
    experiment_ids = [
        _require_nonempty_string(exp, "experiment_id", context="experiment")
        if isinstance(exp, dict)
        else ""
        for exp in experiments
    ]
    if tuple(experiment_ids) != EXPECTED_EXPERIMENTS:
        raise SourceAuditError(
            "AAF experiment taxonomy/order does not match preregistration"
        )

    nodes: dict[str, Mapping[str, Any]] = {}
    scopes: dict[str, str] = {}
    for experiment in experiments:
        if not isinstance(experiment, dict):
            raise SourceAuditError("experiment record must be an object")
        scope = str(experiment["experiment_id"])
        raw_nodes = experiment.get("nodes")
        if not isinstance(raw_nodes, list):
            raise SourceAuditError(f"{scope} nodes must be a list")
        for node in raw_nodes:
            if not isinstance(node, dict):
                raise SourceAuditError(f"{scope} node must be an object")
            node_id = _require_nonempty_string(
                node, "node_id", context=f"{scope} node"
            )
            if node_id in nodes:
                raise SourceAuditError(f"duplicate graph node: {node_id}")
            if not node_id.startswith(scope + ":"):
                raise SourceAuditError(f"graph node scope mismatch: {node_id}")
            evidence_type = _require_nonempty_string(
                node, "evidence_type", context=node_id
            )
            if evidence_type not in EVIDENCE_TYPES:
                raise SourceAuditError(
                    f"unsupported evidence type on {node_id}"
                )
            if node.get("result_driving"):
                _require_nonempty_string(node, "locator", context=node_id)
                _require_nonempty_string(node, "source_id", context=node_id)
                source_scope_tokens = node.get("source_scope_tokens")
                if (
                    not isinstance(source_scope_tokens, list)
                    or not all(
                        isinstance(token, str) and token
                        for token in source_scope_tokens
                    )
                    or scope not in source_scope_tokens
                ):
                    raise SourceAuditError(
                        f"{node_id} requires exact source-scope tokens including {scope}"
                    )
            parents = node.get("parents")
            if not isinstance(parents, list) or not all(
                isinstance(parent, str) and parent for parent in parents
            ):
                raise SourceAuditError(
                    f"{node_id} parents must be a string list"
                )
            _validate_direct_transcription(node_id, node, scope)
            nodes[node_id] = node
            scopes[node_id] = scope

    for node_id, node in nodes.items():
        for parent in node["parents"]:
            if parent not in nodes:
                raise SourceAuditError(
                    f"missing graph parent {parent} for {node_id}"
                )
            if scopes[parent] != scopes[node_id]:
                raise SourceAuditError(
                    f"cross-experiment dependency is forbidden: {parent} -> {node_id}"
                )
    return nodes, scopes


def validate_required_inputs_graph(graph: Mapping[str, Any]) -> None:
    if graph.get("schema_version") != 2:
        raise SourceAuditError(
            "unexpected required-input graph schema version"
        )
    if graph.get("audit_target") != "hust_2018_aaf":
        raise SourceAuditError("required-input graph target mismatch")
    definition_check = graph.get("source_definition_check")
    if not isinstance(definition_check, dict):
        raise SourceAuditError("P_g source-definition check is missing")
    if (
        definition_check.get("target_dependency_status")
        != "no_G_in_registered_source_definition"
    ):
        raise SourceAuditError(
            "P_g target-dependency boundary is unresolved"
        )
    _require_nonempty_string(
        definition_check, "locator", context="P_g definition check"
    )

    nodes, _ = _flatten_nodes(graph)
    for scope in EXPECTED_EXPERIMENTS:
        required_suffixes = {
            "p_sum",
            "alpha_corrected",
            "magnetic_damper_ppm",
            "G_reconstructed",
            "complete_uncertainty_model",
        }
        actual_suffixes = {
            node_id.split(":", 1)[1]
            for node_id in nodes
            if node_id.startswith(scope + ":")
        }
        missing = required_suffixes - actual_suffixes
        if missing:
            raise SourceAuditError(
                f"{scope} missing required nodes: {sorted(missing)}"
            )
        candidate = nodes[f"{scope}:G_reconstructed"]
        if candidate.get("replication_role") != "depth_2a_candidate":
            raise SourceAuditError(
                f"{scope} central reconstruction role is missing"
            )
        uncertainty = nodes[f"{scope}:complete_uncertainty_model"]
        if uncertainty.get("replication_role") != "depth_2b_requirement":
            raise SourceAuditError(
                f"{scope} uncertainty-depth role is missing"
            )


def _ancestor_ids(
    node_id: str, nodes: Mapping[str, Mapping[str, Any]]
) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(current: str) -> None:
        if current in visiting:
            raise SourceAuditError(
                f"dependency cycle detected at {current}"
            )
        if current in visited:
            return
        visiting.add(current)
        for parent in nodes[current]["parents"]:
            visit(parent)
        visiting.remove(current)
        visited.add(current)

    visit(node_id)
    visited.remove(node_id)
    return visited


def _candidate_is_target_clean(
    node_id: str, nodes: Mapping[str, Mapping[str, Any]]
) -> tuple[bool, list[str]]:
    blocked: list[str] = []
    for ancestor_id in sorted(_ancestor_ids(node_id, nodes)):
        ancestor = nodes[ancestor_id]
        if ancestor.get("evidence_type") not in CLEAN_EVIDENCE_TYPES:
            blocked.append(ancestor_id)
    if nodes[node_id].get("evidence_type") not in CLEAN_EVIDENCE_TYPES:
        blocked.append(node_id)
    return not blocked, blocked


def reconstruct_experiment(
    experiment_id: str, graph: Mapping[str, Any]
) -> Decimal:
    if experiment_id not in EXPECTED_EXPERIMENTS:
        raise SourceAuditError(
            f"unknown AAF experiment: {experiment_id}"
        )
    nodes, _ = _flatten_nodes(graph)
    try:
        p_sum = Decimal(str(nodes[f"{experiment_id}:p_sum"]["value"]))
        alpha = Decimal(
            str(nodes[f"{experiment_id}:alpha_corrected"]["value"])
        )
        magnetic_node = nodes[f"{experiment_id}:magnetic_damper_ppm"]
        magnetic_ppm = Decimal(str(magnetic_node["value"]))
    except (KeyError, ArithmeticError) as error:
        raise SourceAuditError(
            f"invalid numeric input for {experiment_id}"
        ) from error
    if p_sum == 0:
        raise SourceAuditError(f"zero P_g sum for {experiment_id}")
    if magnetic_node.get("correction_operator") != "multiply_by_1_plus_delta":
        raise SourceAuditError(
            f"magnetic-damper correction direction is unresolved for {experiment_id}"
        )
    with localcontext() as context:
        context.prec = 50
        return alpha * Decimal("1e-9") / p_sum * (
            Decimal(1) + magnetic_ppm * Decimal("1e-6")
        )


def _published_comparisons(
    graph: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    comparisons: dict[str, Mapping[str, Any]] = {}
    experiments = graph["experiments"]
    for experiment in experiments:
        scope = experiment["experiment_id"]
        comparison = experiment.get("published_comparison")
        if not isinstance(comparison, dict):
            raise SourceAuditError(
                f"published comparison missing for {scope}"
            )
        _require_nonempty_string(
            comparison, "locator", context=f"{scope} comparison"
        )
        _require_nonempty_string(
            comparison, "value", context=f"{scope} comparison"
        )
        comparisons[scope] = comparison
    return comparisons


def classify_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    validate_required_inputs_graph(graph)
    nodes, _ = _flatten_nodes(graph)
    comparisons = _published_comparisons(graph)

    authorized: list[str] = []
    blocked_candidates: dict[str, list[str]] = {}
    reconstructed: dict[str, dict[str, str]] = {}
    for scope in EXPECTED_EXPERIMENTS:
        candidate_id = f"{scope}:G_reconstructed"
        clean, blocked = _candidate_is_target_clean(candidate_id, nodes)
        if clean:
            authorized.append(scope)
        else:
            blocked_candidates[scope] = blocked

        reconstructed_value = reconstruct_experiment(scope, graph)
        published = (
            Decimal(str(comparisons[scope]["value"]))
            * Decimal("1e-11")
        )
        with localcontext() as context:
            context.prec = 50
            difference_ppm = (
                reconstructed_value / published - Decimal(1)
            ) * Decimal("1e6")
        reconstructed[scope] = {
            "reconstructed_G": str(reconstructed_value),
            "published_comparison_G": str(published),
            "difference_ppm": str(difference_ppm),
        }

    depth_2b_authorized: list[str] = []
    depth_2b_blockers: dict[str, list[str]] = {}
    for scope in authorized:
        uncertainty_id = f"{scope}:complete_uncertainty_model"
        uncertainty_clean, blocked = _candidate_is_target_clean(
            uncertainty_id, nodes
        )
        if uncertainty_clean:
            depth_2b_authorized.append(scope)
        else:
            depth_2b_blockers[scope] = blocked

    if depth_2b_authorized:
        assessed_depth = "2b"
    elif authorized:
        assessed_depth = "2a"
    else:
        assessed_depth = "1"

    if assessed_depth in {"2a", "2b"}:
        decision = "GO"
    elif assessed_depth in {"0", "1"}:
        decision = "PARTIAL"
    else:
        decision = "NO_GO"

    authorized_count = len(authorized)
    candidate_count = len(EXPECTED_EXPERIMENTS)
    return {
        "decision": decision,
        "decision_summary": (
            f"{decision} / {assessed_depth} "
            f"({authorized_count} of {candidate_count} AAF determinations authorized)"
        ),
        "maximum_assessed_replication_depth": assessed_depth,
        "depth_2a_authorized_count": authorized_count,
        "depth_2a_candidate_count": candidate_count,
        "depth_2a_authorized_experiments": authorized,
        "depth_2a_blocked_candidates": blocked_candidates,
        "depth_2b_authorized_experiments": depth_2b_authorized,
        "depth_2b_blockers": depth_2b_blockers,
        "combined_aaf_reconstruction_authorized": False,
        "central_value_reconstructions": reconstructed,
    }


def _file_record(root: Path, path: Path) -> dict[str, Any]:
    try:
        content = (root / path).read_bytes()
    except OSError as error:
        raise SourceAuditError(
            f"audit document unavailable: {path}"
        ) from error
    return {
        "path": path.as_posix(),
        "byte_length": len(content),
        "sha256": sha256_bytes(content),
    }


def build_audit_manifest(root: Path = Path(".")) -> dict[str, Any]:
    preregistration = verify_preregistration(root)
    clarification = verify_post_audit_clarification(root)
    semantic_review = verify_semantic_review(root)
    source_capture = load_source_capture(root / SOURCE_CAPTURE_PATH)
    source_summary = validate_source_capture(source_capture)
    graph = load_required_inputs(root / REQUIRED_INPUTS_PATH)
    classification = classify_graph(graph)

    audit_path = root / SOURCE_AUDIT_PATH
    try:
        audit_text = audit_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SourceAuditError(
            "HUST source-audit prose record is unavailable"
        ) from error
    expected_decision_line = (
        f"**Decision: `{classification['decision']}` — assessed replication depth: "
        f"`{classification['maximum_assessed_replication_depth']}` "
        f"({classification['depth_2a_authorized_count']} of "
        f"{classification['depth_2a_candidate_count']} AAF determinations authorized)**"
    )
    decision_lines = [
        line.rstrip()
        for line in audit_text.splitlines()
        if line.startswith("**Decision:")
    ]
    if decision_lines != [expected_decision_line]:
        raise SourceAuditError(
            "source-audit decision line does not match classifier"
        )

    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "audit_identifier": AUDIT_IDENTIFIER,
        "target_publication_doi": "10.1038/s41586-018-0431-5",
        "target_method": "AAF",
        "preregistration": preregistration,
        "post_audit_clarification": clarification,
        "semantic_source_review": semantic_review,
        "documents": [
            _file_record(root, SOURCE_CAPTURE_PATH),
            _file_record(root, REQUIRED_INPUTS_PATH),
            _file_record(root, SOURCE_AUDIT_PATH),
            _file_record(root, POST_AUDIT_CLARIFICATION_PATH),
            _file_record(root, SEMANTIC_REVIEW_PATH),
        ],
        "source_capture_summary": source_summary,
        **classification,
        "depths_above_assessed": {
            "status": "not_assessed",
            "reason": (
                "four listed Source Data files returned HTML fallbacks to the GitHub "
                "runner and were not read as source-data workbooks"
            ),
            "unretrieved_source_ids": sorted(EXPECTED_FAILED_SOURCE_DATA),
        },
        "preregistration_label_clarification": (
            "The frozen preregistration used maximum_supported_replication_depth; "
            "post-audit review narrows the current output to maximum_assessed_replication_depth."
        ),
        "nonclaims": list(NONCLAIMS),
    }


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    return json.dumps(
        artifact, indent=2, sort_keys=True, ensure_ascii=False
    ) + "\n"


def load_audit_manifest(
    path: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    return _read_json(path)


def validate_audit_manifest_record(
    record: Mapping[str, Any], *, root: Path = Path(".")
) -> None:
    expected = build_audit_manifest(root)
    if record != expected:
        raise SourceAuditError(
            "HUST source-audit manifest is stale or inconsistent"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify frozen preregistration and committed deterministic audit artifacts",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        artifact = build_audit_manifest()
        rendered = serialize_artifact(artifact)
        if args.check:
            if not args.output.exists():
                raise SourceAuditError(
                    f"HUST audit manifest is missing: {args.output}"
                )
            record = load_audit_manifest(args.output)
            validate_audit_manifest_record(record)
            if args.output.read_text(encoding="utf-8") != rendered:
                raise SourceAuditError(
                    "HUST audit manifest serialization is stale"
                )
            print(
                "HUST 2018 AAF source audit is current: "
                f"{artifact['decision']}/"
                f"{artifact['maximum_assessed_replication_depth']} "
                f"({artifact['depth_2a_authorized_count']} of "
                f"{artifact['depth_2a_candidate_count']})."
            )
            return

        if args.output.exists():
            if args.output.read_text(encoding="utf-8") != rendered:
                raise SourceAuditError(
                    "refusing to overwrite existing HUST audit manifest; review a new version"
                )
            print(
                f"HUST audit manifest already exists unchanged: {args.output}."
            )
            return
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote HUST source-audit manifest to {args.output}.")
    except SourceAuditError as error:
        print(
            f"invalid HUST source audit: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
