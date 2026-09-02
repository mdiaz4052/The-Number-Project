"""Milestone 6B semantic mutations using the existing disposable-worktree engine."""

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
)
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)

RESULT_SCHEMA_VERSION = 1
EXPERIMENT_IDENTIFIER = "milestone_6b_pysr_leakage_mutations_v1"
DEFAULT_OUTPUT = Path(
    "Experiments/EcosystemComparison/PySRLeakage/"
    "milestone_6b_pysr_leakage_v1.mutation_results.json"
)
SOURCE_PATHS = (
    "Discovery/pysr_leakage_mutations.py",
    "Discovery/pysr_leakage_probe.py",
    "Discovery/mutation_harness.py",
    "Discovery/mutation_test_runner.py",
    "tests/test_pysr_leakage_probe.py",
    "tests/test_pysr_leakage_mutation_guards.py",
)

MUTANTS = (
    Mutant(
        identifier="production_allow_target_exposed_promotion",
        category="production",
        intended_semantic_defect=(
            "Disable the one-way valve that rejects promotion eligibility for a "
            "target-exposed candidate."
        ),
        relative_path="Discovery/pysr_leakage_probe.py",
        old_text="    if promotion_eligible:\n",
        new_text="    if False and promotion_eligible:\n",
        test_names=(
            "tests.test_pysr_leakage_probe.PySRLeakageProbeTests."
            "test_all_pysr_candidates_are_target_exposed_and_never_promotable",
        ),
        required_modules=("Discovery.pysr_leakage_probe",),
    ),
    Mutant(
        identifier="production_collapse_generation_leakage_into_registered_graph",
        category="production",
        intended_semantic_defect=(
            "Replace independent synthetic generation-DAG target ancestry with the "
            "registered algebraic target-path result, erasing the Channel C blind spot."
        ),
        relative_path="Discovery/pysr_leakage_probe.py",
        old_text=(
            "    generation_leakage = known_generation_target_leakage(channel, parsed.names)\n"
        ),
        new_text="    generation_leakage = registered == TARGET_PATH_DETECTED\n",
        test_names=(
            "tests.test_pysr_leakage_mutation_guards.PySRLeakageMutationGuardTests."
            "test_hidden_generation_path_remains_independent_of_registered_graph",
        ),
        required_modules=("Discovery.pysr_leakage_probe",),
    ),
)


class LeakageMutationError(ValueError):
    pass


def canonical_json(record: object) -> str:
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def build_result(root: Path, source_commit_sha: str) -> dict[str, Any]:
    if canonical_head(root) != source_commit_sha:
        raise LeakageMutationError("mutation source anchor must equal canonical HEAD")
    if canonical_status_bytes(root):
        raise LeakageMutationError("canonical checkout must be clean before mutations")
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
            "Killed means only that the selected behavioral test detected the selected defect.",
            "This two-mutant family does not establish that the 6B machinery is defect-free.",
            "Mutation results are methodological and contain no empirical evidence about gravity.",
        ],
    }


def _validate_record(record: object, mutant: Mutant, source_sha: str) -> None:
    if not isinstance(record, Mapping):
        raise LeakageMutationError("6B mutation record is malformed")
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
            raise LeakageMutationError(
                f"6B mutation record mismatch for {mutant.identifier}: {key}"
            )
    killing = record.get("killing_tests")
    if not isinstance(killing, list) or not killing:
        raise LeakageMutationError(f"killed mutant lacks killing tests: {mutant.identifier}")
    if not all(
        any(test == target or test.startswith(f"{target} ") for target in mutant.test_names)
        for test in killing
    ):
        raise LeakageMutationError(f"unexpected killing test: {mutant.identifier}")
    integrity = record.get("import_path_integrity")
    if not isinstance(integrity, Mapping) or integrity.get("validated") is not True:
        raise LeakageMutationError(f"import-path integrity failed: {mutant.identifier}")


def validate_result(result: Mapping[str, Any]) -> str:
    if result.get("result_schema_version") != RESULT_SCHEMA_VERSION:
        raise LeakageMutationError("6B mutation result schema mismatch")
    if result.get("experiment_identifier") != EXPERIMENT_IDENTIFIER:
        raise LeakageMutationError("6B mutation experiment identifier mismatch")
    source_sha = result.get("source_commit_sha")
    if not isinstance(source_sha, str) or re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise LeakageMutationError("6B mutation source SHA is invalid")
    if result.get("source_paths") != list(SOURCE_PATHS):
        raise LeakageMutationError("6B mutation source-path catalog mismatch")
    records = result.get("results")
    if not isinstance(records, list) or len(records) != len(MUTANTS):
        raise LeakageMutationError("6B mutation result count mismatch")
    for record, mutant in zip(records, MUTANTS):
        _validate_record(record, mutant, source_sha)
    if result.get("all_mutants_killed") is not True:
        raise LeakageMutationError("not every selected 6B mutant was killed")
    if result.get("methodological_result_status") != "all_killed":
        raise LeakageMutationError("6B mutation methodological status mismatch")
    return source_sha


def check_committed_result() -> None:
    try:
        result = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LeakageMutationError(f"cannot load 6B mutation artifact: {error}") from error
    if not isinstance(result, dict):
        raise LeakageMutationError("6B mutation artifact must contain an object")
    source_sha = validate_result(result)
    verify_committed_source_state(
        repository_root(),
        source_sha,
        source_paths=SOURCE_PATHS,
        artifact_label="Milestone 6B mutation result",
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
        root = repository_root()
        result = build_result(root, args.source_commit_sha)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical_json(result), encoding="utf-8")
        print(f"Wrote 6B mutation evidence: {args.output}")
        return

    if args.check:
        try:
            check_committed_result()
        except SourceVerificationError as error:
            exit_for_source_verification_error(error)
        except LeakageMutationError as error:
            print(f"Milestone 6B mutation check failed: {error}", file=sys.stderr)
            raise SystemExit(1)
        print("Milestone 6B selected semantic mutants are current and killed.")
        return

    parser.error("use --run or --check")


if __name__ == "__main__":
    main()
