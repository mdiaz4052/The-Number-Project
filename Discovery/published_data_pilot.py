"""Deterministic integrity manifest for the first published-data pilot.

The manifest pins the exact governing preregistration, its explicit clarification,
and the resulting source audit.  This is tamper evidence for review and CI; it is
not protection against a knowing editor who changes code and artifacts together.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


PILOT_MANIFEST_SCHEMA_VERSION = 1
PILOT_IDENTIFIER = "uw_2000_published_data_reproduction_v1"
DECISION = "NO-GO"
OUTCOME_CLASS = "INCOMPLETE_REPRODUCTION"
EMPIRICAL_RECORD_CREATED = False
PREREGISTRATION_PATH = Path(
    "Experiments/GMeasurements/uw_2000_published_data_preregistration_v1.md"
)
CLARIFICATION_PATH = Path(
    "Experiments/GMeasurements/"
    "uw_2000_published_data_preregistration_v1_clarification_1.md"
)
SOURCE_AUDIT_PATH = Path(
    "Experiments/GMeasurements/uw_2000_source_audit_v1.md"
)
DEFAULT_OUTPUT = Path(
    "Experiments/GMeasurements/uw_2000_published_data_pilot_v1.manifest.json"
)

# These literal digests are the reviewed content pins. Regeneration must not silently
# bless changed prose; a content change requires an explicit code review of this table.
DOCUMENT_SPECS = (
    (
        "governing_preregistration",
        PREREGISTRATION_PATH,
        "487d4d584e412b404815d8f22eb90d7b4690465d4984d91aa072fb1520326971",
    ),
    (
        "normative_clarification",
        CLARIFICATION_PATH,
        "f2bac432714e8d480c51daf090d69463df2239deb704f0283c4b3274db5c5735",
    ),
    (
        "source_availability_audit",
        SOURCE_AUDIT_PATH,
        "1ff8b755a1eb2c68af1a51c670fa81a5caa7a39a8e3b627cfa962707f00cc6b5",
    ),
)
ESSENTIAL_MISSING_INPUTS = (
    "fitted_2omega_d_gravitational_angular_acceleration",
    "complete_numerical_attractor_multipole_coupling",
)
NEXT_CANDIDATE = "hust_2018_angular_acceleration_feedback"
NONCLAIMS = (
    "The UW publication is not disputed by this source-availability decision.",
    "No UW empirical measurement record, G estimate, or replication claim was created.",
    (
        "The hashes make reviewed document changes visible; they do not make the "
        "repository unforgeable against a knowing editor."
    ),
)


def sha256_bytes(content: bytes) -> str:
    """Return the lowercase SHA-256 digest of exact document bytes."""

    return hashlib.sha256(content).hexdigest()


def _expected_source_audit_decision_line() -> str:
    return f"**Decision: `{DECISION} ({OUTCOME_CLASS})`**"


def _document_records(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for role, relative_path, expected_sha256 in DOCUMENT_SPECS:
        try:
            content = (root / relative_path).read_bytes()
        except OSError as error:
            raise ValueError(f"pinned pilot document is unavailable: {relative_path}") from error
        actual_sha256 = sha256_bytes(content)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"pinned pilot document hash mismatch: {relative_path}"
            )
        if relative_path == SOURCE_AUDIT_PATH:
            try:
                audit_text = content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError("pinned source audit is not valid UTF-8") from error
            decision_lines = [
                line.rstrip()
                for line in audit_text.splitlines()
                if line.startswith("**Decision:")
            ]
            if decision_lines != [_expected_source_audit_decision_line()]:
                raise ValueError(
                    "pinned source-audit decision line does not match canonical decision"
                )
        records.append(
            {
                "role": role,
                "path": relative_path.as_posix(),
                "sha256": expected_sha256,
            }
        )
    return records


def build_pilot_manifest(root: Path = Path(".")) -> dict[str, Any]:
    """Build the canonical manifest after verifying every document content pin."""

    return {
        "pilot_manifest_schema_version": PILOT_MANIFEST_SCHEMA_VERSION,
        "pilot_identifier": PILOT_IDENTIFIER,
        "decision": DECISION,
        "outcome_class": OUTCOME_CLASS,
        "go_authorized": False,
        "empirical_record_created": EMPIRICAL_RECORD_CREATED,
        "documents": _document_records(root),
        "essential_missing_inputs": list(ESSENTIAL_MISSING_INPUTS),
        "next_candidate": NEXT_CANDIDATE,
        "nonclaims": list(NONCLAIMS),
    }


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    """Serialize deterministic JSON with exactly one final newline."""

    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def load_pilot_manifest(path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Load one manifest without treating its self-assertions as validation."""

    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("pilot manifest is unavailable or is not valid UTF-8 JSON") from error
    if not isinstance(record, dict):
        raise ValueError("pilot manifest root must be an object")
    return record


def validate_pilot_manifest_record(
    record: Mapping[str, Any],
    *,
    root: Path = Path("."),
) -> None:
    """Compare the artifact and current documents with canonical reviewed values."""

    expected = build_pilot_manifest(root)
    if record != expected:
        raise ValueError("pilot manifest does not match canonical reviewed fields")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed manifest and pinned document bytes without rewriting",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        artifact = build_pilot_manifest()
        rendered = serialize_artifact(artifact)
        if args.check:
            if not args.output.exists():
                raise ValueError(f"pilot manifest is missing: {args.output}")
            record = load_pilot_manifest(args.output)
            validate_pilot_manifest_record(record)
            if args.output.read_text(encoding="utf-8") != rendered:
                raise ValueError("pilot manifest serialization is stale")
            print(
                "Published-data pilot manifest and pinned documents are current: "
                f"{args.output}."
            )
            return

        if args.output.exists():
            if args.output.read_text(encoding="utf-8") != rendered:
                raise ValueError(
                    "refusing to overwrite an existing pilot manifest; review a new version"
                )
            print(f"Published-data pilot manifest already exists unchanged: {args.output}.")
            return
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote published-data pilot manifest to {args.output}.")
    except ValueError as error:
        print(f"invalid published-data pilot: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
