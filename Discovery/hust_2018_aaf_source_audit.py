"""Deterministic source-availability audit for HUST 2018 AAF.

This module classifies how deeply the public HUST 2018 angular-acceleration-feedback
record can be reconstructed.  It is deliberately not a MeasurementModel and does not
change the physical-bridge schema.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


AUDIT_SCHEMA_VERSION = 1
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

NONCLAIMS = (
    "This audit does not establish that the HUST value of G is correct.",
    "GO/2a is a public-summary central-value reconstruction, not an independent laboratory measurement.",
    "Depth 2a does not authorize the combined AAF value or an uncertainty-qualified reproduction.",
    "No MeasurementModel is created and no physical-bridge schema is extended by this audit.",
    "The source-data HTTP fallback findings do not prove that the files cannot be obtained by another public retrieval path.",
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


def _require_nonempty_string(record: Mapping[str, Any], key: str, *, context: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SourceAuditError(f"{context} requires nonempty {key}")
    return value


def verify_preregistration(root: Path = Path(".")) -> dict[str, str]:
    path = root / PREREGISTRATION_PATH
    try:
        content = path.read_bytes()
    except OSError as error:
        raise SourceAuditError("HUST preregistration is unavailable") from error
    actual = sha256_bytes(content)
    if actual != PREREGISTRATION_SHA256:
        raise SourceAuditError("HUST preregistration hash mismatch")
    return {
        "path": PREREGISTRATION_PATH.as_posix(),
        "sha256": PREREGISTRATION_SHA256,
    }


def _resource_index(source_capture: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    resources = source_capture.get("resources")
    if not isinstance(resources, list):
        raise SourceAuditError("source capture resources must be a list")
    index: dict[str, Mapping[str, Any]] = {}
    for raw in resources:
        if not isinstance(raw, dict):
            raise SourceAuditError("source capture resource must be an object")
        source_id = _require_nonempty_string(raw, "source_id", context="source resource")
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
    if not isinstance(listing_status, str) or "verified_from_primary_nature_page" not in listing_status:
        raise SourceAuditError("Nature resource-listing review status is missing")

    index = _resource_index(record)
    _check_expected_resource(index, EXPECTED_SUPPLEMENT)
    _check_expected_resource(index, EXPECTED_SUPPLEMENTARY_DATA)
    _check_expected_resource(index, EXPECTED_EXTENDED_FIG_2_SOURCE_DATA)

    failed: list[str] = []
    for source_id in sorted(EXPECTED_FAILED_SOURCE_DATA):
        resource = index.get(source_id)
        if resource is None:
            raise SourceAuditError(f"reviewed failed source-data attempt missing: {source_id}")
        if resource.get("retrieval_status") != "html_fallback_not_source_file":
            raise SourceAuditError(
                f"source-data fallback must not be classified as retrieved: {source_id}"
            )
        if resource.get("content_type") != "text/html":
            raise SourceAuditError(f"unexpected failed source-data content type: {source_id}")
        if resource.get("sha256") != record.get("article_capture", {}).get("sha256"):
            raise SourceAuditError(f"expected fallback-byte identity is absent: {source_id}")
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


def _flatten_nodes(graph: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
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
        raise SourceAuditError("AAF experiment taxonomy/order does not match preregistration")

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
            node_id = _require_nonempty_string(node, "node_id", context=f"{scope} node")
            if node_id in nodes:
                raise SourceAuditError(f"duplicate graph node: {node_id}")
            if not node_id.startswith(scope + ":"):
                raise SourceAuditError(f"graph node scope mismatch: {node_id}")
            evidence_type = _require_nonempty_string(
                node, "evidence_type", context=node_id
            )
            if evidence_type not in EVIDENCE_TYPES:
                raise SourceAuditError(f"unsupported evidence type on {node_id}")
            if node.get("result_driving"):
                _require_nonempty_string(node, "locator", context=node_id)
                _require_nonempty_string(node, "source_id", context=node_id)
            parents = node.get("parents")
            if not isinstance(parents, list) or not all(
                isinstance(parent, str) and parent for parent in parents
            ):
                raise SourceAuditError(f"{node_id} parents must be a string list")
            nodes[node_id] = node
            scopes[node_id] = scope

    for node_id, node in nodes.items():
        for parent in node["parents"]:
            if parent not in nodes:
                raise SourceAuditError(f"missing graph parent {parent} for {node_id}")
            if scopes[parent] != scopes[node_id]:
                raise SourceAuditError(
                    f"cross-experiment dependency is forbidden: {parent} -> {node_id}"
                )
    return nodes, scopes


def validate_required_inputs_graph(graph: Mapping[str, Any]) -> None:
    if graph.get("schema_version") != 1:
        raise SourceAuditError("unexpected required-input graph schema version")
    if graph.get("audit_target") != "hust_2018_aaf":
        raise SourceAuditError("required-input graph target mismatch")
    definition_check = graph.get("source_definition_check")
    if not isinstance(definition_check, dict):
        raise SourceAuditError("P_g source-definition check is missing")
    if definition_check.get("target_dependency_status") != "no_G_in_registered_source_definition":
        raise SourceAuditError("P_g target-dependency boundary is unresolved")
    _require_nonempty_string(definition_check, "locator", context="P_g definition check")

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
            raise SourceAuditError(f"{scope} missing required nodes: {sorted(missing)}")
        candidate = nodes[f"{scope}:G_reconstructed"]
        if candidate.get("replication_role") != "depth_2a_candidate":
            raise SourceAuditError(f"{scope} central reconstruction role is missing")
        uncertainty = nodes[f"{scope}:complete_uncertainty_model"]
        if uncertainty.get("replication_role") != "depth_2b_requirement":
            raise SourceAuditError(f"{scope} uncertainty-depth role is missing")


def _ancestor_ids(node_id: str, nodes: Mapping[str, Mapping[str, Any]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(current: str) -> None:
        if current in visiting:
            raise SourceAuditError(f"dependency cycle detected at {current}")
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
        raise SourceAuditError(f"unknown AAF experiment: {experiment_id}")
    nodes, _ = _flatten_nodes(graph)
    try:
        p_sum = Decimal(str(nodes[f"{experiment_id}:p_sum"]["value"]))
        alpha = Decimal(str(nodes[f"{experiment_id}:alpha_corrected"]["value"]))
        magnetic_ppm = Decimal(
            str(nodes[f"{experiment_id}:magnetic_damper_ppm"]["value"])
        )
    except (KeyError, ArithmeticError) as error:
        raise SourceAuditError(f"invalid numeric input for {experiment_id}") from error
    if p_sum == 0:
        raise SourceAuditError(f"zero P_g sum for {experiment_id}")
    with localcontext() as context:
        context.prec = 50
        return alpha * Decimal("1e-9") / p_sum * (
            Decimal(1) + magnetic_ppm * Decimal("1e-6")
        )


def _published_comparisons(graph: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    comparisons: dict[str, Mapping[str, Any]] = {}
    experiments = graph["experiments"]
    for experiment in experiments:
        scope = experiment["experiment_id"]
        comparison = experiment.get("published_comparison")
        if not isinstance(comparison, dict):
            raise SourceAuditError(f"published comparison missing for {scope}")
        _require_nonempty_string(comparison, "locator", context=f"{scope} comparison")
        _require_nonempty_string(comparison, "value", context=f"{scope} comparison")
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
        published = Decimal(str(comparisons[scope]["value"])) * Decimal("1e-11")
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
        uncertainty_clean, blocked = _candidate_is_target_clean(uncertainty_id, nodes)
        if uncertainty_clean:
            depth_2b_authorized.append(scope)
        else:
            depth_2b_blockers[scope] = blocked

    if depth_2b_authorized:
        maximum_depth = "2b"
    elif authorized:
        maximum_depth = "2a"
    else:
        # The HUST publication and comparison rows are still provenance-complete in this
        # audit graph even when a planted mutation destroys estimator reconstruction.
        maximum_depth = "1"

    if maximum_depth in {"2a", "2b", "3", "4"}:
        decision = "GO"
    elif maximum_depth in {"0", "1"}:
        decision = "PARTIAL"
    else:
        decision = "NO_GO"

    return {
        "decision": decision,
        "maximum_supported_replication_depth": maximum_depth,
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
        raise SourceAuditError(f"audit document unavailable: {path}") from error
    return {
        "path": path.as_posix(),
        "byte_length": len(content),
        "sha256": sha256_bytes(content),
    }


def build_audit_manifest(root: Path = Path(".")) -> dict[str, Any]:
    preregistration = verify_preregistration(root)
    source_capture = load_source_capture(root / SOURCE_CAPTURE_PATH)
    source_summary = validate_source_capture(source_capture)
    graph = load_required_inputs(root / REQUIRED_INPUTS_PATH)
    classification = classify_graph(graph)

    audit_path = root / SOURCE_AUDIT_PATH
    try:
        audit_text = audit_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SourceAuditError("HUST source-audit prose record is unavailable") from error
    expected_decision_line = (
        f"**Decision: `{classification['decision']}` — maximum supported replication depth: "
        f"`{classification['maximum_supported_replication_depth']}`**"
    )
    decision_lines = [
        line.rstrip()
        for line in audit_text.splitlines()
        if line.startswith("**Decision:")
    ]
    if decision_lines != [expected_decision_line]:
        raise SourceAuditError("source-audit decision line does not match classifier")

    return {
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "audit_identifier": AUDIT_IDENTIFIER,
        "target_publication_doi": "10.1038/s41586-018-0431-5",
        "target_method": "AAF",
        "preregistration": preregistration,
        "documents": [
            _file_record(root, SOURCE_CAPTURE_PATH),
            _file_record(root, REQUIRED_INPUTS_PATH),
            _file_record(root, SOURCE_AUDIT_PATH),
        ],
        "source_capture_summary": source_summary,
        **classification,
        "depth_3_4_status": "not_authorized_from_retrieved_public_set",
        "nonclaims": list(NONCLAIMS),
    }


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def load_audit_manifest(path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    return _read_json(path)


def validate_audit_manifest_record(
    record: Mapping[str, Any], *, root: Path = Path(".")
) -> None:
    expected = build_audit_manifest(root)
    if record != expected:
        raise SourceAuditError("HUST source-audit manifest is stale or inconsistent")


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
                raise SourceAuditError(f"HUST audit manifest is missing: {args.output}")
            record = load_audit_manifest(args.output)
            validate_audit_manifest_record(record)
            if args.output.read_text(encoding="utf-8") != rendered:
                raise SourceAuditError("HUST audit manifest serialization is stale")
            print(
                "HUST 2018 AAF source audit is current: "
                f"{artifact['decision']}/{artifact['maximum_supported_replication_depth']}."
            )
            return

        if args.output.exists():
            if args.output.read_text(encoding="utf-8") != rendered:
                raise SourceAuditError(
                    "refusing to overwrite existing HUST audit manifest; review a new version"
                )
            print(f"HUST audit manifest already exists unchanged: {args.output}.")
            return
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote HUST source-audit manifest to {args.output}.")
    except SourceAuditError as error:
        print(f"invalid HUST source audit: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
