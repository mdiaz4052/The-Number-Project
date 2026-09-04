"""Selected post-6B hardening mutation: parser allowlist bypass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from Discovery.mutation_harness import (
    KILLED,
    Mutant,
    canonical_head,
    canonical_status_bytes,
    run_mutant,
    verify_retired_artifact_hashes,
)
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)

RESULT_SCHEMA_VERSION = 1
EXPERIMENT_IDENTIFIER = "post_6b_hardening_mutations_v1"
DEFAULT_OUTPUT = Path(
    "Experiments/EcosystemComparison/PySRLeakage/"
    "post_6b_hardening_v1.mutation_results_v4.json"
)
RETIRED_ARTIFACT_SHA256 = {
    (
        "Experiments/EcosystemComparison/PySRLeakage/"
        "post_6b_hardening_v1.mutation_results.json"
    ): "635a7f0272bf2e7f4620a788f61e29f1562b3ff9dc6091965d083247d1c495fa",
    (
        "Experiments/EcosystemComparison/PySRLeakage/"
        "post_6b_hardening_v1.mutation_results_v2.json"
    ): "6f94d61efd89d1f180f2ec52b864157e0889c304e810f446ca2e01356534f5c2",
    (
        "Experiments/EcosystemComparison/PySRLeakage/"
        "post_6b_hardening_v1.mutation_results_v3.json"
    ): "3d0e2102d0e11e7679b6233c223d4de897d41a0ef6d3fdc683cc4ac9fb512f4e",
}
SOURCE_PATHS = (
    "Discovery/pysr_leakage_hardening_mutations.py",
    "Discovery/pysr_leakage_probe.py",
    "Discovery/mutation_harness.py",
    "Discovery/mutation_test_runner.py",
    "tests/test_pysr_leakage_hardening.py",
)

MUTANTS = (
    Mutant(
        identifier="production_bypass_expression_node_allowlist",
        category="production",
        intended_semantic_defect=(
            "Disable the AST node allowlist so unsupported call syntax can pass the parser "
            "when the called identifier is otherwise an allowed predictor name."
        ),
        relative_path="Discovery/pysr_leakage_probe.py",
        old_text="        if not isinstance(node, _ALLOWED_NODES):\n",
        new_text="        if False and not isinstance(node, _ALLOWED_NODES):\n",
        test_names=(
            "tests.test_pysr_leakage_hardening.PySRLeakageHardeningTests."
            "test_parser_rejects_call_syntax_even_when_function_name_is_allowed",
        ),
        required_modules=("Discovery.pysr_leakage_probe",),
    ),
)


class HardeningMutationError(ValueError):
    pass


def canonical_json(record: object) -> str:
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def build_result(root: Path, source_commit_sha: str) -> dict[str, Any]:
    if canonical_head(root) != source_commit_sha:
        raise HardeningMutationError("mutation source anchor must equal canonical HEAD")
    if canonical_status_bytes(root):
        raise HardeningMutationError("canonical checkout must be clean before mutations")
    records = [run_mutant(root, source_commit_sha, mutant) for mutant in MUTANTS]
    all_killed = all(record.get("classification") == KILLED for record in records)
    return {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "methodological_result_status": "all_killed" if all_killed else "incomplete",
        "source_commit_sha": source_commit_sha,
        "source_paths": list(SOURCE_PATHS),
        "mutant_count": len(MUTANTS),
        "all_mutants_killed": all_killed,
        "results": records,
        "nonclaims": [
            "Killed means only that the selected behavioral test detected the selected parser defect.",
            "One parser mutant does not establish parser safety or complete mutation coverage.",
            "This is a software-methodology result and contains no empirical evidence about gravity.",
        ],
    }


def _validate_record(record: object, mutant: Mutant, source_sha: str) -> None:
    if not isinstance(record, Mapping):
        raise HardeningMutationError("hardening mutation record is malformed")
    expected = {
        "mutant_identifier": mutant.identifier,
        "category": mutant.category,
        "intended_semantic_defect": mutant.intended_semantic_defect,
        "mutated_path": mutant.relative_path,
        "test_command": list(mutant.test_names),
        "required_import_modules": list(mutant.required_modules),
        "canonical_anchor_sha": source_sha,
        "canonical_head_before": source_sha,
        "canonical_head_after": source_sha,
        "classification": KILLED,
        "canonical_head_unchanged": True,
        "canonical_status_unchanged": True,
        "cleanup_confirmed": True,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise HardeningMutationError(
                f"post-6B mutation record mismatch for {mutant.identifier}: {key}"
            )
    killing = record.get("killing_tests")
    if not isinstance(killing, list) or not killing:
        raise HardeningMutationError("killed parser mutant lacks a killing test")
    integrity = record.get("import_path_integrity")
    if not isinstance(integrity, Mapping) or integrity.get("validated") is not True:
        raise HardeningMutationError("parser mutant import-path integrity failed")


def validate_result(result: Mapping[str, Any]) -> str:
    if result.get("result_schema_version") != RESULT_SCHEMA_VERSION:
        raise HardeningMutationError("post-6B mutation result schema mismatch")
    if result.get("experiment_identifier") != EXPERIMENT_IDENTIFIER:
        raise HardeningMutationError("post-6B mutation experiment identifier mismatch")
    source_sha = result.get("source_commit_sha")
    if not isinstance(source_sha, str) or re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise HardeningMutationError("post-6B mutation source SHA is invalid")
    if result.get("source_paths") != list(SOURCE_PATHS):
        raise HardeningMutationError("post-6B mutation source-path catalog mismatch")
    records = result.get("results")
    if not isinstance(records, list) or len(records) != len(MUTANTS):
        raise HardeningMutationError("post-6B mutation result count mismatch")
    for record, mutant in zip(records, MUTANTS):
        _validate_record(record, mutant, source_sha)
    if result.get("all_mutants_killed") is not True:
        raise HardeningMutationError("selected parser mutant was not killed")
    if result.get("methodological_result_status") != "all_killed":
        raise HardeningMutationError("post-6B mutation status mismatch")
    return source_sha


def check_committed_result() -> None:
    try:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HardeningMutationError(f"cannot load post-6B mutation artifact: {error}") from error
    if not isinstance(result, dict):
        raise HardeningMutationError("post-6B mutation artifact must contain an object")
    source_sha = validate_result(result)
    verify_committed_source_state(
        repository_root(),
        source_sha,
        source_paths=SOURCE_PATHS,
        artifact_label="Post-6B parser mutation result",
    )
    verify_retired_artifact_hashes(
        repository_root(),
        RETIRED_ARTIFACT_SHA256,
        artifact_label="Post-6B parser mutation result",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-commit-sha")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.run:
        if not args.source_commit_sha:
            parser.error("--run requires --source-commit-sha")
        result = build_result(repository_root(), args.source_commit_sha)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical_json(result), encoding="utf-8")
        print(f"Wrote post-6B parser mutation evidence: {args.output}")
        return

    if args.check:
        try:
            check_committed_result()
        except SourceVerificationError as error:
            exit_for_source_verification_error(error)
        except HardeningMutationError as error:
            print(f"Post-6B mutation check failed: {error}", file=sys.stderr)
            raise SystemExit(1)
        print("Post-6B parser mutant is current and killed.")
        return

    parser.error("use --run or --check")


if __name__ == "__main__":
    main()
