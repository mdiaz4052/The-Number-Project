"""Authorize the three HUST 2018 AAF depth-2b uncertainty reconstructions.

This module is the production boundary between the historical feasibility audit and
the new uncertainty-qualified records.  It validates an official Nature source pin,
strict clarification and input schemas, exact component second keys, derivation
arithmetic, and byte preservation of the historical artifacts.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping
import unicodedata

from Discovery.source_history import (
    VERIFIED,
    SourceMetadataError,
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)


AUTHORIZATION_ARTIFACT_SCHEMA_VERSION = 2
SCOPES = ("AAF-I", "AAF-II", "AAF-III")
PUBLIC_DIRECT = "PUBLIC_DIRECT"
PUBLIC_DERIVABLE = "PUBLIC_DERIVABLE"

PREREGISTRATION_COMMIT = "c153b1a2079a5112f28e43263fb7986f393c19ca"
REMOTE_ANCHOR_COMMIT = "d0eaaa7b36817e9381fb45c7655df01ece149f70"

PREREGISTRATION_PATH = Path(
    "Experiments/GMeasurements/"
    "hust_2018_aaf_depth_2b_measurement_model_preregistration_v1.md"
)
PREREGISTRATION_SHA256 = (
    "05913514c25be9bf722454f6369261f529b7bd19c97d1ee81cf054a9bc9bb49f"
)
ANCHOR_PATH = Path(
    "Experiments/GMeasurements/"
    "hust_2018_aaf_depth_2b_measurement_model_preregistration_v1.anchor.json"
)
ANCHOR_SHA256 = (
    "54556b9bfc9cf855c100c6049285612baaa8885eb4e0ba7bc455a6cc9f8d83b9"
)
OFFICIAL_SOURCE_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_official_source_v1.json"
)
OFFICIAL_SOURCE_RECORD_SHA256 = (
    "de73536119564f28b61f330eea5ce8841fd5e2ba21f52dc3ce6a7f44b620476d"
)
CLARIFICATION_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_clarification_v1.json"
)
CLARIFICATION_SHA256 = (
    "7b193a70fa1ccbf3097dba0f9316fe446e5b8f8c4073f440ea7e25bba18276b4"
)
REQUIRED_INPUTS_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_required_inputs_depth_2b_v2.json"
)
REQUIRED_INPUTS_SHA256 = (
    "ef8a23cee8d1d7c7e417ca69d8b0e75a66d5cf272e6fcd59ba92fb84d1468326"
)
DEFAULT_OUTPUT = Path(
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v2.json"
)

OFFICIAL_TABLE_SHA256 = (
    "21dfa4fc6631c835d1d1b275fdf1d7c77b7447d7880b309bcb4cd1701401c0cf"
)
SUPPLEMENT_SHA256 = (
    "5b61d5c831be98c46e47fcc32f1ade0a680b4af6354d2bc34859d94b22279ffb"
)
CANONICAL_ARTICLE_URL = "https://www.nature.com/articles/s41586-018-0431-5"
CANONICAL_TABLE_URL = CANONICAL_ARTICLE_URL + "/tables/1"
HISTORICAL_MIRROR_URL = (
    "https://mctoon.net/wp-content/uploads/2019/07/"
    "measurements-of-the-gravitational-constant-using-two-independent-methods.pdf"
)
TABLE_LOCATOR = "Table 1, Nature 560, p. 584; dedicated Nature Table 1 page"
SECTION_6_LOCATOR = "Supplementary Information Section 6, pp. 12-14"

HISTORICAL_ARTIFACT_SHA256 = {
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_feasibility_v1.json": (
        "e2969a0223641d8a13d2199e3ea34879a4ed437a8f23c09e510cec327b7a72d8"
    ),
    "Experiments/GMeasurements/hust_2018_aaf_measurement_models_v1.json": (
        "6da4917504be9b3db944c8be8b4e86ad2643ab383f68e83d2cfb920680cd02bb"
    ),
    "Experiments/GMeasurements/hust_2018_aaf_required_inputs_v1.json": (
        "8328bec85e5356d833d7f36b9e16833edc0d3c415bdd1eba59c7a01790c7f37a"
    ),
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.manifest.json": (
        "867bff124fbd6b46a1ae1710aeaa13fb19698455c5fbaa8971bb3c08f10b162a"
    ),
}

FROZEN_MILESTONE_7_V1_SHA256 = {
    PREREGISTRATION_PATH.as_posix(): PREREGISTRATION_SHA256,
    ANCHOR_PATH.as_posix(): ANCHOR_SHA256,
    OFFICIAL_SOURCE_PATH.as_posix(): OFFICIAL_SOURCE_RECORD_SHA256,
    CLARIFICATION_PATH.as_posix(): CLARIFICATION_SHA256,
    "Experiments/GMeasurements/hust_2018_aaf_required_inputs_depth_2b_v1.json": (
        "624d84db3ef855edc9f126a8f5f974b2aa799600e94d2fb39f1d048ffa7afe5b"
    ),
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v1.json": (
        "06338de9b24ead21f5b24da12d1cd0c94ba584ad740368b128d6f552023ec6f3"
    ),
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_measurement_models_v1.json": (
        "a13944b8a6f8691c46398b4374cfb29df94f8cdfc698a70ad47addcf05cad0a3"
    ),
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_mutation_results_v1.json": (
        "82f6715fa40a9d951d8f4b4e7f9d5f5e64ae9d80c645027acda08f39becc79ba"
    ),
}

EXPECTED_REVISION = {
    "predecessor_graph_id": "hust_2018_aaf_required_inputs_depth_2b_v1",
    "predecessor_path": (
        "Experiments/GMeasurements/hust_2018_aaf_required_inputs_depth_2b_v1.json"
    ),
    "change_summary": (
        "Post-audit migration to exact printed row labels and stronger verification "
        "metadata."
    ),
    "numerical_values_changed": False,
    "scientific_authorization_changed": False,
    "scope_boundaries_changed": False,
}

EXPECTED_OFFICIAL_SOURCE_NONCLAIMS = [
    "This record does not claim byte identity with a Nature PDF or raw HTTP response.",
    "The captured publisher serialization is not redistributed by the repository.",
    (
        "A source hash and locator do not independently validate the apparatus or the "
        "completeness of the published uncertainty budget."
    ),
]

EXPECTED_ANCHOR_RECORD = {
    "event": "pull_request",
    "github_pr_number": 34,
    "jobs": {
        "Lean build and proof audit": "success",
        "Python tests and bounded search": "success",
    },
    "observation_basis": (
        "GitHub workflow query restricted to pull-request-triggered runs for the exact "
        "preregistration commit"
    ),
    "observed_at_utc": "2026-09-05T02:09:03Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "preregistration_path": PREREGISTRATION_PATH.as_posix(),
    "preregistration_sha256": PREREGISTRATION_SHA256,
    "schema_version": 1,
    "workflow_conclusion": "success",
    "workflow_id": 345072294,
    "workflow_name": "Verify",
    "workflow_run_id": 33898036414,
    "workflow_run_number": 173,
    "workflow_status": "completed",
}

EXPECTED_COMPONENTS = (
    ("pendulum_dimensions", "Dimensions", "0.16", "0.16", "0.16"),
    ("pendulum_attitude", "Attitude", "0.06", "0.06", "0.03"),
    (
        "pendulum_density_inhomogeneity",
        "Density inhomogeneity",
        "0.46",
        "0.46",
        "0.46",
    ),
    ("coating_layer", "Coating layer", "0.34", "0.34", "0.34"),
    ("clamp_and_ferrule", "Clamp and ferrule", "0.70", "1.05", "0.48"),
    ("other_pendulum_effects", "Others", "0.29", "0.29", "0.29"),
    ("source_mass_masses", "Masses", "0.32", "0.31", "0.31"),
    (
        "horizontal_source_mass_distance",
        "Horizontal distance",
        "8.98",
        "8.98",
        "8.98",
    ),
    (
        "vertical_source_mass_distance",
        "Vertical distance",
        "5.79",
        "5.79",
        "5.79",
    ),
    (
        "source_mass_positions_alignment",
        "Positions, alignment",
        "0.57",
        "0.62",
        "0.35",
    ),
    ("fibre_anelasticity", "Fibre anelasticity", "0.01", "0.01", "0.01"),
    ("thermal_effect", "Thermal effect", "0.91", "0.91", "0.91"),
    ("time_base", "Time base", "0.01", "0.01", "0.01"),
    (
        "rotating_gravity_gradient",
        "Rotating gravity gradient",
        "1.86",
        "1.35",
        "1.72",
    ),
    ("shelf_deformation", "Shelf deformation", "1.51", "1.51", "1.51"),
    ("magnetic_damper", "Magnetic damper", "1.95", "1.95", "0.08"),
    ("air_density", "Air density", "1.00", "1.51", "1.13"),
    ("magnetic_field", "Magnetic field", "3.98", "3.98", "0.90"),
    ("angle_encoder", "Angle encoder", "0.72", "0.72", "0.72"),
    (
        "residual_twist_angle",
        "Residual twist angle",
        "0.03",
        "0.61",
        "0.45",
    ),
    (
        "statistical_angular_acceleration",
        "Statistical error of Δω² or αₜ",
        "3.44",
        "2.60",
        "1.34",
    ),
)
EXPECTED_NOT_APPLICABLE = (
    "fibre_nonlinearity",
    "gravitational_nonlinearity",
    "electrostatic_field",
)
EXPECTED_SUMS_OF_SQUARES = {
    "AAF-I": Decimal("155.0861"),
    "AAF-II": Decimal("150.6924"),
    "AAF-III": Decimal("125.7279"),
}
EXPECTED_RSS_PPM = {
    "AAF-I": Decimal(
        "12.453356977136727047866320298865297714729175627210"
    ),
    "AAF-II": Decimal(
        "12.275683280371809918505072305209443766741467830010"
    ),
    "AAF-III": Decimal(
        "11.212845312408443280940946155017027106000868654421"
    ),
}
EXPECTED_RHO_APPROXIMATIONS = {
    "AAF-I": "0.0032",
    "AAF-II": "0.0032",
    "AAF-III": "0.0025",
}


class HUSTDepth2BAuthorizationError(ValueError):
    """Controlled failure of a depth-2b authorization invariant."""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _require_exact_keys(
    record: Mapping[str, Any], expected: Iterable[str], label: str
) -> None:
    expected_set = set(expected)
    actual_set = set(record)
    if actual_set != expected_set:
        missing = sorted(expected_set - actual_set)
        unknown = sorted(actual_set - expected_set)
        raise HUSTDepth2BAuthorizationError(
            f"{label} keys differ; missing={missing}, unknown={unknown}"
        )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HUSTDepth2BAuthorizationError(
            f"required JSON record is unavailable or invalid: {path}"
        ) from error
    if not isinstance(record, dict):
        raise HUSTDepth2BAuthorizationError(f"required JSON record is not an object: {path}")
    return record


def _verify_pinned_file(
    root: Path, path: Path, expected_sha256: str, label: str
) -> dict[str, Any]:
    try:
        content = (root / path).read_bytes()
    except OSError as error:
        raise HUSTDepth2BAuthorizationError(f"{label} is unavailable") from error
    actual = sha256_bytes(content)
    if actual != expected_sha256:
        raise HUSTDepth2BAuthorizationError(f"{label} hash mismatch")
    return {
        "path": path.as_posix(),
        "byte_length": len(content),
        "sha256": actual,
    }


def _decimal_text(value: object, label: str) -> Decimal:
    if not isinstance(value, str) or not value:
        raise HUSTDepth2BAuthorizationError(f"{label} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise HUSTDepth2BAuthorizationError(f"{label} is not a decimal string") from error
    if not parsed.is_finite():
        raise HUSTDepth2BAuthorizationError(f"{label} must be finite")
    return parsed


def _normalized_claim(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    for hyphen in "‐‑‒–—―−﹘﹣－-":
        normalized = normalized.replace(hyphen, " ")
    return " ".join(normalized.split())


def byte_identity_claim_is_forbidden(text: str) -> bool:
    """Return whether one text leaf makes a bounded positive byte-equivalence claim."""

    normalized = _normalized_claim(text)
    canonical_negative = _normalized_claim(EXPECTED_OFFICIAL_SOURCE_NONCLAIMS[0])
    if normalized == canonical_negative:
        return False
    return any(
        pattern in normalized
        for pattern in (
            "byte identity",
            "byte identical",
            "identical to the raw",
            "exactly the same bytes",
            "bytes are exactly the same",
            "bit for bit",
        )
    )


def _text_leaves(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for nested in value.values():
            yield from _text_leaves(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _text_leaves(nested)


def _reject_byte_identity_overclaim(record: Mapping[str, Any], label: str) -> None:
    for text in _text_leaves(record):
        if byte_identity_claim_is_forbidden(text):
            raise HUSTDepth2BAuthorizationError(
                f"{label} contains an unqualified byte-identity overclaim"
            )


def validate_anchor_record(record: Mapping[str, Any]) -> None:
    """Validate the frozen remote anchor as strict source-history metadata."""

    if record != EXPECTED_ANCHOR_RECORD:
        expected_keys = set(EXPECTED_ANCHOR_RECORD)
        actual_keys = set(record)
        missing = sorted(expected_keys - actual_keys)
        unknown = sorted(actual_keys - expected_keys)
        detail = f"missing={missing}, unknown={unknown}"
        if not missing and not unknown:
            detail = "one or more values or value types differ"
        raise SourceMetadataError(
            f"depth-2b preregistration remote anchor metadata is invalid; {detail}"
        )


def validate_official_source_record(record: Mapping[str, Any]) -> None:
    _require_exact_keys(
        record,
        ("schema_version", "record_id", "decision", "source", "capture", "validation", "nonclaims"),
        "official source record",
    )
    if (
        record["schema_version"] != 1
        or record["record_id"] != "hust_2018_aaf_depth_2b_official_source_v1"
        or record["decision"] != "SATISFIED"
    ):
        raise HUSTDepth2BAuthorizationError("official source authorization header changed")

    source = record["source"]
    if not isinstance(source, dict):
        raise HUSTDepth2BAuthorizationError("official source metadata is not an object")
    _require_exact_keys(
        source,
        (
            "citation",
            "doi",
            "canonical_article_url",
            "canonical_table_url",
            "historical_public_mirror_url",
            "publisher_host",
            "table_locator",
        ),
        "official source metadata",
    )
    expected_source = {
        "citation": "Q. Li et al., Measurements of the gravitational constant using two independent methods, Nature 560, 582-588 (2018)",
        "doi": "10.1038/s41586-018-0431-5",
        "canonical_article_url": CANONICAL_ARTICLE_URL,
        "canonical_table_url": CANONICAL_TABLE_URL,
        "historical_public_mirror_url": HISTORICAL_MIRROR_URL,
        "publisher_host": "www.nature.com",
        "table_locator": TABLE_LOCATOR,
    }
    if source != expected_source:
        raise HUSTDepth2BAuthorizationError("official source metadata failed its second key")

    capture = record["capture"]
    if not isinstance(capture, dict):
        raise HUSTDepth2BAuthorizationError("official source capture is not an object")
    _require_exact_keys(
        capture,
        (
            "access_date",
            "response_content_type",
            "character_encoding",
            "capture_representation",
            "byte_length",
            "sha256",
            "pdf_magic_validation",
            "repository_storage",
            "delivery_caveat",
        ),
        "official source capture",
    )
    expected_capture = {
        "access_date": "2026-09-05",
        "response_content_type": "text/html",
        "character_encoding": "UTF-8",
        "capture_representation": (
            "browser-rendered first <table> outerHTML encoded as UTF-8"
        ),
        "byte_length": 10305,
        "sha256": OFFICIAL_TABLE_SHA256,
        "pdf_magic_validation": "not_applicable_html",
        "repository_storage": "hash_only; publisher-rendered HTML bytes are not stored",
        "delivery_caveat": (
            "The hash covers the browser-rendered table serialization, not the raw "
            "HTTP response body. Equivalent publisher delivery or rendering paths "
            "may produce different bytes."
        ),
    }
    if capture != expected_capture:
        raise HUSTDepth2BAuthorizationError("official Nature capture pin changed")

    validation = record["validation"]
    if not isinstance(validation, dict):
        raise HUSTDepth2BAuthorizationError("official source validation is not an object")
    _require_exact_keys(
        validation,
        (
            "page_title",
            "first_table_row_count",
            "expected_headers",
            "official_nature_delivery",
            "table_1_present",
        ),
        "official source validation",
    )
    expected_validation = {
        "page_title": "Table 1 Contributions of various experimental parameters to the main error budget of the measurements, expressed in parts per million | Nature",
        "first_table_row_count": 29,
        "expected_headers": [
            "Parameter",
            "TOS",
            "TOS",
            "TOS",
            "TOS",
            "AAF-I",
            "AAF-II",
            "AAF-III",
        ],
        "official_nature_delivery": True,
        "table_1_present": True,
    }
    if validation != expected_validation:
        raise HUSTDepth2BAuthorizationError("official Table 1 validation changed")
    if record["nonclaims"] != EXPECTED_OFFICIAL_SOURCE_NONCLAIMS:
        raise HUSTDepth2BAuthorizationError(
            "official source nonclaims failed their exact ordered second key"
        )
    _reject_byte_identity_overclaim(record, "official source record")


def validate_clarification_record(record: Mapping[str, Any]) -> None:
    _require_exact_keys(
        record,
        (
            "schema_version",
            "record_id",
            "status",
            "chronology",
            "direct_statements",
            "project_derivation",
            "correlation_policy",
            "boundaries",
            "nonclaims",
        ),
        "clarification record",
    )
    if (
        record["schema_version"] != 1
        or record["record_id"] != "hust_2018_aaf_depth_2b_clarification_v1"
        or record["status"] != "AUTHORITATIVE_FOR_DEPTH_2B"
    ):
        raise HUSTDepth2BAuthorizationError("clarification header changed")

    chronology = record["chronology"]
    if not isinstance(chronology, dict):
        raise HUSTDepth2BAuthorizationError("clarification chronology is not an object")
    _require_exact_keys(
        chronology,
        ("initial_transcription_origin", "production_transcription"),
        "clarification chronology",
    )
    if "does not establish" not in chronology["initial_transcription_origin"]:
        raise HUSTDepth2BAuthorizationError("historical transcription uncertainty was erased")
    if "official Nature Table 1 page" not in chronology["production_transcription"]:
        raise HUSTDepth2BAuthorizationError("production transcription source changed")

    direct = record["direct_statements"]
    if not isinstance(direct, dict):
        raise HUSTDepth2BAuthorizationError("direct statements are not an object")
    _require_exact_keys(direct, ("article", "supplement"), "direct statements")
    article = direct["article"]
    supplement = direct["supplement"]
    if not isinstance(article, dict) or not isinstance(supplement, dict):
        raise HUSTDepth2BAuthorizationError("direct statement entry is not an object")
    _require_exact_keys(
        article,
        ("evidence_type", "source_record_id", "locator", "claim"),
        "article direct statement",
    )
    _require_exact_keys(
        supplement,
        ("evidence_type", "source_id", "sha256", "locator", "claim"),
        "supplement direct statement",
    )
    if (
        article["evidence_type"] != PUBLIC_DIRECT
        or article["source_record_id"]
        != "hust_2018_aaf_depth_2b_official_source_v1"
        or article["locator"] != TABLE_LOCATOR
    ):
        raise HUSTDepth2BAuthorizationError("article direct-statement binding changed")
    if (
        supplement["evidence_type"] != PUBLIC_DIRECT
        or supplement["source_id"] != "supplementary_information"
        or supplement["sha256"] != SUPPLEMENT_SHA256
        or supplement["locator"] != SECTION_6_LOCATOR
    ):
        raise HUSTDepth2BAuthorizationError("supplement direct-statement binding changed")

    derivation = record["project_derivation"]
    if not isinstance(derivation, dict):
        raise HUSTDepth2BAuthorizationError("project derivation is not an object")
    _require_exact_keys(
        derivation,
        (
            "evidence_type",
            "dependencies",
            "decimal_precision",
            "displayed_component_resolution_ppm",
            "rounding_half_interval_ppm",
            "rss_rule",
            "rounding_envelope_rule",
            "dominant_pair_rule",
            "absolute_rule",
        ),
        "project derivation",
    )
    if derivation != {
        "evidence_type": PUBLIC_DERIVABLE,
        "dependencies": [
            "hust_2018_aaf_depth_2b_official_source_v1",
            "hust_2018_aaf_required_inputs_depth_2b_v1",
        ],
        "decimal_precision": 50,
        "displayed_component_resolution_ppm": "0.01",
        "rounding_half_interval_ppm": "0.005",
        "rss_rule": "sum_of_squares = sum(u_i^2); u_relative_ppm = sqrt(sum_of_squares)",
        "rounding_envelope_rule": "For each displayed component x, independently evaluate max(0, x - 0.005) and x + 0.005; compare the resulting squared-budget bounds with the squared budget from x.",
        "dominant_pair_rule": "rho_bound = max(nominal_sum_of_squares - lower_sum_of_squares, upper_sum_of_squares - nominal_sum_of_squares) / (2 * u_largest * u_second_largest)",
        "absolute_rule": "u_absolute_G = abs(G_hat) * u_relative_ppm * 1e-6",
    }:
        raise HUSTDepth2BAuthorizationError("project derivation contract changed")

    correlation = record["correlation_policy"]
    if not isinstance(correlation, dict):
        raise HUSTDepth2BAuthorizationError("correlation policy is not an object")
    _require_exact_keys(
        correlation,
        ("evidence_type", "representation", "qualification", "cross_run_scope"),
        "correlation policy",
    )
    if (
        correlation["evidence_type"] != PUBLIC_DERIVABLE
        or correlation["representation"] != "EXPLICIT_ZERO_ASSUMPTION"
        or "not a claim" not in correlation["qualification"]
        or "physical systematic sources are independent"
        not in correlation["qualification"]
        or "separately authorized combined estimator" not in correlation["cross_run_scope"]
    ):
        raise HUSTDepth2BAuthorizationError("qualified correlation policy changed")

    boundaries = record["boundaries"]
    if not isinstance(boundaries, dict):
        raise HUSTDepth2BAuthorizationError("clarification boundaries are not an object")
    _require_exact_keys(
        boundaries,
        (
            "combined_aaf_reconstruction_authorized",
            "raw_or_run_level_replication_established",
            "apparatus_validity_established",
            "lean_apparatus_theorem_registered",
        ),
        "clarification boundaries",
    )
    if any(boundaries.values()):
        raise HUSTDepth2BAuthorizationError("clarification overstates an authorization boundary")
    if not isinstance(record["nonclaims"], list) or not record["nonclaims"]:
        raise HUSTDepth2BAuthorizationError("clarification nonclaims are missing")
    _reject_byte_identity_overclaim(record, "clarification record")


def validate_required_inputs_graph(graph: Mapping[str, Any]) -> None:
    _require_exact_keys(
        graph,
        (
            "schema_version",
            "graph_id",
            "decision",
            "revision",
            "source_pins",
            "scopes",
            "components",
            "not_applicable_aaf_rows",
            "authorizations",
            "terminal_comparisons",
            "nonclaims",
        ),
        "depth-2b required-input graph",
    )
    if (
        graph["schema_version"] != 2
        or graph["graph_id"] != "hust_2018_aaf_required_inputs_depth_2b_v2"
        or graph["decision"] != "GO"
    ):
        raise HUSTDepth2BAuthorizationError("required-input graph header changed")
    if graph["revision"] != EXPECTED_REVISION:
        raise HUSTDepth2BAuthorizationError(
            "required-input graph revision metadata changed"
        )

    pins = graph["source_pins"]
    if not isinstance(pins, dict):
        raise HUSTDepth2BAuthorizationError("source pins are not an object")
    _require_exact_keys(
        pins,
        (
            "official_table_1_record",
            "official_table_1_source_id",
            "supplement_source_id",
            "clarification_record",
        ),
        "source pins",
    )
    if pins != {
        "official_table_1_record": "hust_2018_aaf_depth_2b_official_source_v1",
        "official_table_1_source_id": "official_nature_table_1",
        "supplement_source_id": "supplementary_information",
        "clarification_record": "hust_2018_aaf_depth_2b_clarification_v1",
    }:
        raise HUSTDepth2BAuthorizationError("required-input source pins changed")

    scopes = graph["scopes"]
    if not isinstance(scopes, list):
        raise HUSTDepth2BAuthorizationError("required-input scopes are not a list")
    expected_scopes = [
        {"scope_id": scope, "maximum_assessed_replication_depth": "2b"}
        for scope in SCOPES
    ]
    if scopes != expected_scopes:
        raise HUSTDepth2BAuthorizationError("depth-2b scope authorization changed")

    components = graph["components"]
    if not isinstance(components, list):
        raise HUSTDepth2BAuthorizationError("component table is not a list")
    actual: list[tuple[str, str, str, str, str]] = []
    for index, row in enumerate(components):
        if not isinstance(row, dict):
            raise HUSTDepth2BAuthorizationError(f"component row {index} is not an object")
        _require_exact_keys(
            row,
            (
                "component_id",
                "printed_row_label",
                "unit",
                "evidence_type",
                "source_id",
                "AAF-I",
                "AAF-II",
                "AAF-III",
            ),
            f"component row {index}",
        )
        if row["unit"] != "ppm" or row["evidence_type"] != PUBLIC_DIRECT:
            raise HUSTDepth2BAuthorizationError(f"component row {index} role or unit changed")
        if row["source_id"] != "official_nature_table_1":
            raise HUSTDepth2BAuthorizationError(f"component row {index} source changed")
        for scope in SCOPES:
            if _decimal_text(row[scope], f"component row {index} {scope}") < 0:
                raise HUSTDepth2BAuthorizationError("uncertainty contribution is negative")
        actual.append(
            (
                row["component_id"],
                row["printed_row_label"],
                row["AAF-I"],
                row["AAF-II"],
                row["AAF-III"],
            )
        )
    if tuple(actual) != EXPECTED_COMPONENTS:
        raise HUSTDepth2BAuthorizationError(
            "component inventory, order, labels, or cross-column values changed"
        )
    if tuple(graph["not_applicable_aaf_rows"]) != EXPECTED_NOT_APPLICABLE:
        raise HUSTDepth2BAuthorizationError("not-applicable AAF rows changed")

    authorizations = graph["authorizations"]
    if not isinstance(authorizations, dict):
        raise HUSTDepth2BAuthorizationError("authorizations are not an object")
    _require_exact_keys(
        authorizations,
        (
            "component_table",
            "individual_rss_rule",
            "within_result_correlation_policy",
            "complete_uncertainty_model",
            "combined_aaf_reconstruction_authorized",
        ),
        "depth-2b authorizations",
    )
    complete = authorizations["complete_uncertainty_model"]
    if not isinstance(complete, dict):
        raise HUSTDepth2BAuthorizationError("complete model authorization is not an object")
    _require_exact_keys(complete, SCOPES, "complete model authorizations")
    component_authorization = authorizations["component_table"]
    rss_authorization = authorizations["individual_rss_rule"]
    correlation_authorization = authorizations["within_result_correlation_policy"]
    for label, authorization in (
        ("component table", component_authorization),
        ("individual RSS rule", rss_authorization),
        ("within-result correlation policy", correlation_authorization),
    ):
        if not isinstance(authorization, dict):
            raise HUSTDepth2BAuthorizationError(f"{label} authorization is not an object")
        _require_exact_keys(authorization, ("evidence_type", "depends_on"), label)
    if component_authorization != {
        "evidence_type": PUBLIC_DIRECT,
        "depends_on": ["hust_2018_aaf_depth_2b_official_source_v1"],
    }:
        raise HUSTDepth2BAuthorizationError("component-table authorization changed")
    derivation_dependencies = [
        "component_table",
        "hust_2018_aaf_depth_2b_clarification_v1",
    ]
    if rss_authorization != {
        "evidence_type": PUBLIC_DERIVABLE,
        "depends_on": derivation_dependencies,
    } or correlation_authorization != {
        "evidence_type": PUBLIC_DERIVABLE,
        "depends_on": derivation_dependencies,
    }:
        raise HUSTDepth2BAuthorizationError(
            "RSS or correlation derivation dependency changed"
        )
    complete_dependencies = [
        "component_table",
        "individual_rss_rule",
        "within_result_correlation_policy",
        "hust_2018_aaf_depth_2b_clarification_v1",
    ]
    for scope in SCOPES:
        scope_authorization = complete[scope]
        if not isinstance(scope_authorization, dict):
            raise HUSTDepth2BAuthorizationError(
                f"{scope} complete-model authorization is not an object"
            )
        _require_exact_keys(
            scope_authorization,
            ("evidence_type", "depends_on"),
            f"{scope} complete-model authorization",
        )
        if scope_authorization != {
            "evidence_type": PUBLIC_DERIVABLE,
            "depends_on": complete_dependencies,
        }:
            raise HUSTDepth2BAuthorizationError(
                f"{scope} complete-model derivation dependency changed"
            )
    if authorizations["combined_aaf_reconstruction_authorized"] is not False:
        raise HUSTDepth2BAuthorizationError("depth-2b authorization classification changed")

    comparisons = graph["terminal_comparisons"]
    if not isinstance(comparisons, dict):
        raise HUSTDepth2BAuthorizationError("terminal comparisons are not an object")
    _require_exact_keys(comparisons, SCOPES, "terminal comparisons")
    comparison_keys = (
        "published_g_m3_kg-1_s-2",
        "published_standard_uncertainty_m3_kg-1_s-2",
        "displayed_total_ppm",
    )
    for scope in SCOPES:
        comparison = comparisons[scope]
        if not isinstance(comparison, dict):
            raise HUSTDepth2BAuthorizationError(f"{scope} terminal comparison is not an object")
        _require_exact_keys(comparison, comparison_keys, f"{scope} terminal comparison")
        for key in comparison_keys:
            if _decimal_text(comparison[key], f"{scope} {key}") < 0:
                raise HUSTDepth2BAuthorizationError(f"{scope} terminal comparison is negative")
    if not isinstance(graph["nonclaims"], list) or not graph["nonclaims"]:
        raise HUSTDepth2BAuthorizationError("required-input nonclaims are missing")


def component_values(
    graph: Mapping[str, Any], scope: str
) -> tuple[tuple[str, Decimal], ...]:
    if scope not in SCOPES:
        raise HUSTDepth2BAuthorizationError(f"unsupported or combined AAF scope: {scope}")
    validate_required_inputs_graph(graph)
    return tuple(
        (row["component_id"], Decimal(row[scope])) for row in graph["components"]
    )


def calculate_scope_diagnostics(
    graph: Mapping[str, Any], scope: str
) -> dict[str, str]:
    values = component_values(graph, scope)
    half_interval = Decimal("0.005")
    with localcontext() as context:
        context.prec = 50
        sum_of_squares = sum(value * value for _, value in values)
        rss = sum_of_squares.sqrt()
        lower_sum = sum(
            max(Decimal(0), value - half_interval) ** 2 for _, value in values
        )
        upper_sum = sum((value + half_interval) ** 2 for _, value in values)
        rounding_envelope = max(
            sum_of_squares - lower_sum,
            upper_sum - sum_of_squares,
        )
        dominant = sorted(values, key=lambda item: item[1], reverse=True)[:2]
        rho_bound = rounding_envelope / (
            Decimal(2) * dominant[0][1] * dominant[1][1]
        )
    if sum_of_squares != EXPECTED_SUMS_OF_SQUARES[scope]:
        raise HUSTDepth2BAuthorizationError(f"{scope} sum of squares failed its check")
    if rss != EXPECTED_RSS_PPM[scope]:
        raise HUSTDepth2BAuthorizationError(f"{scope} RSS failed its precision-50 check")
    return {
        "sum_of_squares": str(sum_of_squares),
        "relative_standard_uncertainty_ppm": str(rss),
        "rounding_lower_sum_of_squares": str(lower_sum),
        "rounding_upper_sum_of_squares": str(upper_sum),
        "rounding_squared_budget_envelope": str(rounding_envelope),
        "dominant_component_1": dominant[0][0],
        "dominant_component_2": dominant[1][0],
        "dominant_pair_rho_sensitivity_bound": str(rho_bound),
        "dominant_pair_rho_disclosed_approximation": EXPECTED_RHO_APPROXIMATIONS[scope],
    }


def load_authorized_records(
    root: Path = Path("."),
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _verify_pinned_file(
        root,
        OFFICIAL_SOURCE_PATH,
        OFFICIAL_SOURCE_RECORD_SHA256,
        "official Nature source record",
    )
    _verify_pinned_file(
        root,
        CLARIFICATION_PATH,
        CLARIFICATION_SHA256,
        "depth-2b clarification",
    )
    _verify_pinned_file(
        root,
        REQUIRED_INPUTS_PATH,
        REQUIRED_INPUTS_SHA256,
        "depth-2b required-input graph",
    )
    source = _read_json(root / OFFICIAL_SOURCE_PATH)
    clarification = _read_json(root / CLARIFICATION_PATH)
    graph = _read_json(root / REQUIRED_INPUTS_PATH)
    validate_official_source_record(source)
    validate_clarification_record(clarification)
    validate_required_inputs_graph(graph)
    return source, clarification, graph


def verify_depth_2b_source_history(root: Path = Path(".")) -> dict[str, Any]:
    """Verify both freeze-before-implementation anchors against the current HEAD."""

    git_root = repository_root(root)
    preregistration_status = verify_committed_source_state(
        git_root,
        PREREGISTRATION_COMMIT,
        source_paths=(PREREGISTRATION_PATH.as_posix(),),
        artifact_label="depth-2b preregistration",
    )
    anchor_status = verify_committed_source_state(
        git_root,
        REMOTE_ANCHOR_COMMIT,
        source_paths=(ANCHOR_PATH.as_posix(),),
        artifact_label="depth-2b preregistration remote anchor",
    )
    return {
        "preregistration": {
            "status": preregistration_status,
            "commit": PREREGISTRATION_COMMIT,
            "path": PREREGISTRATION_PATH.as_posix(),
        },
        "remote_anchor": {
            "status": anchor_status,
            "commit": REMOTE_ANCHOR_COMMIT,
            "path": ANCHOR_PATH.as_posix(),
        },
    }


def build_authorization_artifact(root: Path = Path(".")) -> dict[str, Any]:
    preregistration = _verify_pinned_file(
        root,
        PREREGISTRATION_PATH,
        PREREGISTRATION_SHA256,
        "depth-2b preregistration",
    )
    anchor = _verify_pinned_file(
        root,
        ANCHOR_PATH,
        ANCHOR_SHA256,
        "depth-2b preregistration remote anchor",
    )
    anchor_record = _read_json(root / ANCHOR_PATH)
    validate_anchor_record(anchor_record)
    source_history = verify_depth_2b_source_history(root)
    if any(
        record["status"] != VERIFIED for record in source_history.values()
    ):
        raise SourceMetadataError("depth-2b source history did not verify")
    source, clarification, graph = load_authorized_records(root)
    input_records = [
        _verify_pinned_file(
            root,
            OFFICIAL_SOURCE_PATH,
            OFFICIAL_SOURCE_RECORD_SHA256,
            "official Nature source record",
        ),
        _verify_pinned_file(
            root,
            CLARIFICATION_PATH,
            CLARIFICATION_SHA256,
            "depth-2b clarification",
        ),
        _verify_pinned_file(
            root,
            REQUIRED_INPUTS_PATH,
            REQUIRED_INPUTS_SHA256,
            "depth-2b required-input graph",
        ),
    ]
    historical_records = [
        _verify_pinned_file(root, Path(path), digest, f"historical artifact {path}")
        for path, digest in sorted(HISTORICAL_ARTIFACT_SHA256.items())
    ]
    frozen_milestone_7_v1_records = [
        _verify_pinned_file(root, Path(path), digest, f"frozen Milestone 7 v1 {path}")
        for path, digest in sorted(FROZEN_MILESTONE_7_V1_SHA256.items())
    ]
    scope_records = [
        {
            "scope": scope,
            "maximum_assessed_replication_depth": "2b",
            "complete_uncertainty_model_authorization": PUBLIC_DERIVABLE,
            "component_count": len(EXPECTED_COMPONENTS),
            "diagnostics": calculate_scope_diagnostics(graph, scope),
        }
        for scope in SCOPES
    ]
    return {
        "artifact_schema_version": AUTHORIZATION_ARTIFACT_SCHEMA_VERSION,
        "artifact": "HUST 2018 AAF individual depth-2b authorization",
        "revision": {
            "predecessor_path": (
                "Experiments/GMeasurements/"
                "hust_2018_aaf_depth_2b_authorization_v1.json"
            ),
            "change_summary": (
                "Post-audit migration for exact printed labels, source-history "
                "verification, and explicit attestation limits."
            ),
            "numerical_values_changed": False,
            "scientific_authorization_changed": False,
            "scope_boundaries_changed": False,
        },
        "decision": "GO",
        "baseline_commit": "715c189818dea258f3c6d447d7854226c1f2a575",
        "preregistration": preregistration,
        "remote_anchor": anchor,
        "source_history_verification": source_history,
        "input_records": input_records,
        "official_source_precondition": {
            "status": "SATISFIED",
            "official_nature_delivery": source["validation"]["official_nature_delivery"],
            "canonical_table_url": source["source"]["canonical_table_url"],
            "capture_sha256": source["capture"]["sha256"],
            "capture_representation": source["capture"]["capture_representation"],
            "publisher_bytes_committed": False,
            "independently_reproducible_from_repository_contents": False,
            "attestation_role": "official_source_attestation",
            "delivery_caveat": source["capture"]["delivery_caveat"],
            "secondary_source_authorized_as_official": False,
        },
        "derivation_classification": {
            "component_table": PUBLIC_DIRECT,
            "individual_rss_rule": PUBLIC_DERIVABLE,
            "within_result_correlation_policy": PUBLIC_DERIVABLE,
            "complete_uncertainty_models": PUBLIC_DERIVABLE,
            "clarification_record_id": clarification["record_id"],
        },
        "scopes": scope_records,
        "historical_artifact_preservation": historical_records,
        "frozen_milestone_7_v1_preservation": frozen_milestone_7_v1_records,
        "authorization_boundaries": {
            "individual_scopes_only": list(SCOPES),
            "combined_aaf_reconstruction_authorized": False,
            "raw_or_run_level_replication_established": False,
            "apparatus_validity_established": False,
            "lean_apparatus_theorem_registered": False,
        },
        "nonclaims": [
            "Authorization reconstructs published individual uncertainty budgets; it does not validate the apparatus.",
            "The zero-covariance representation is qualified and does not establish physical independence of every systematic source.",
            "The displayed totals, published final uncertainties, and combined AAF result are terminal only.",
        ],
    }


def serialize_artifact(record: Mapping[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify source pins, schemas, derivations, historical bytes, and artifact freshness",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        rendered = serialize_artifact(build_authorization_artifact(Path(".")))
        if args.check:
            try:
                existing = args.output.read_text(encoding="utf-8")
            except OSError as error:
                raise HUSTDepth2BAuthorizationError(
                    f"authorization artifact is unavailable: {args.output}"
                ) from error
            if existing != rendered:
                raise HUSTDepth2BAuthorizationError(
                    f"authorization artifact is stale: {args.output}"
                )
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except HUSTDepth2BAuthorizationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
