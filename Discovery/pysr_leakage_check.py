"""Permanent fail-closed checker for the Milestone 6B PySR leakage evidence."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping

from Discovery.pysr_leakage_probe import (
    DATASETS_PATH,
    EXPERIMENT_IDENTIFIER,
    EXTERNAL_PATH,
    PREREGISTRATION_PATH,
    RESULT_PATH,
    LeakageProbeError,
    build_datasets_record,
    build_result_record,
    canonical_json_bytes,
    dataset_hashes,
    load_json,
    sha256_bytes,
)
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)

SOURCE_PATHS = (
    "Discovery/pysr_leakage_probe.py",
    "Discovery/pysr_leakage_check.py",
    "Discovery/dependency_definitions.py",
    "Discovery/dimensions.py",
    "Discovery/source_history.py",
    "tests/test_pysr_leakage_probe.py",
    str(PREREGISTRATION_PATH),
    str(DATASETS_PATH),
)


def build_dataset_manifest() -> dict[str, Any]:
    datasets = build_datasets_record()
    return {
        "schema_version": 1,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "rows_per_channel": datasets["rows_per_channel"],
        "dataset_sha256": sha256_bytes(canonical_json_bytes(datasets)),
        "channel_sha256": dataset_hashes(datasets),
        "generator": "Discovery.pysr_leakage_probe.build_datasets_record",
        "storage_note": (
            "Rows are regenerated deterministically from result-driving source; "
            "this manifest pins their canonical bytes without duplicating them."
        ),
    }


def _validate_preregistration(
    preregistration: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> None:
    if preregistration.get("schema_version") != 1:
        raise LeakageProbeError("6B preregistration schema version mismatch")
    if preregistration.get("experiment_identifier") != EXPERIMENT_IDENTIFIER:
        raise LeakageProbeError("6B preregistration experiment identifier mismatch")
    if preregistration.get("dataset_sha256") != manifest.get("dataset_sha256"):
        raise LeakageProbeError("6B preregistration dataset hash mismatch")
    scope = preregistration.get("epistemic_scope")
    if not isinstance(scope, Mapping):
        raise LeakageProbeError("6B epistemic scope missing")
    if scope.get("candidate_origin") != "target_exposed_candidate":
        raise LeakageProbeError("6B candidate-origin preregistration changed")
    if scope.get("promotion_eligible") is not False:
        raise LeakageProbeError("6B one-way promotion rule changed")


def build_expected_result(
    external_bytes: bytes,
    source_commit_sha: str,
) -> dict[str, Any]:
    try:
        external = json.loads(external_bytes)
    except json.JSONDecodeError as error:
        raise LeakageProbeError(f"external artifact is invalid JSON: {error}") from error
    if not isinstance(external, dict):
        raise LeakageProbeError("external artifact must contain an object")
    return build_result_record(
        external,
        build_datasets_record(),
        external_sha256=sha256_bytes(external_bytes),
        source_commit_sha=source_commit_sha,
    )


def check_committed_artifacts() -> dict[str, Any]:
    preregistration = load_json(PREREGISTRATION_PATH)
    manifest = load_json(DATASETS_PATH)
    expected_manifest = build_dataset_manifest()
    if canonical_json_bytes(manifest) != canonical_json_bytes(expected_manifest):
        raise LeakageProbeError("stale or tampered 6B dataset manifest")
    _validate_preregistration(preregistration, manifest)

    external_bytes = EXTERNAL_PATH.read_bytes()
    result = load_json(RESULT_PATH)
    source_sha = result.get("source_commit_sha")
    if not isinstance(source_sha, str):
        raise LeakageProbeError("6B result source commit SHA missing")

    verify_committed_source_state(
        repository_root(),
        source_sha,
        source_paths=SOURCE_PATHS,
        artifact_label="Milestone 6B PySR leakage result",
    )
    expected = build_expected_result(external_bytes, source_sha)
    if canonical_json_bytes(result) != canonical_json_bytes(expected):
        raise LeakageProbeError("stale or tampered 6B result artifact")
    if expected["primary_endpoint"]["confirmed"] is not True:
        raise LeakageProbeError("Channel C hidden-leak fixture is invalid")
    if any(candidate["promotion_eligible"] for candidate in expected["candidates"]):
        raise LeakageProbeError("target-exposed candidate became promotion-eligible")
    return expected


def write_result(source_commit_sha: str) -> None:
    external_bytes = EXTERNAL_PATH.read_bytes()
    result = build_expected_result(external_bytes, source_commit_sha)
    RESULT_PATH.write_bytes(canonical_json_bytes(result))
    print(f"Wrote normalized 6B result: {RESULT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-result", action="store_true")
    parser.add_argument("--source-commit-sha")
    args = parser.parse_args()

    if args.write_result:
        if not args.source_commit_sha:
            parser.error("--write-result requires --source-commit-sha")
        write_result(args.source_commit_sha)
        return

    if args.check:
        try:
            result = check_committed_artifacts()
        except SourceVerificationError as error:
            exit_for_source_verification_error(error)
        except (LeakageProbeError, OSError, json.JSONDecodeError) as error:
            print(f"Milestone 6B check failed: {error}", file=sys.stderr)
            raise SystemExit(1)
        print(
            "Milestone 6B target-leakage result is current: "
            f"{result['primary_endpoint']['outcome']}."
        )
        return

    parser.error("use --check or --write-result")


if __name__ == "__main__":
    main()
