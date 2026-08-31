"""Ephemeral semantic mutation testing for Milestone 5B-core.

Every mutation is applied in a detached disposable Git worktree. The canonical checkout
is fingerprinted before and after each run, and the isolated test process proves that all
relevant project imports resolve under the disposable root.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence

from Discovery.falsification_preregistration import (
    DEFAULT_OUTPUT as DEFAULT_PREREGISTRATION_OUTPUT,
    EXPERIMENT_IDENTIFIER,
    load_preregistration,
    preregistration_sha256_bytes,
)


RESULT_SCHEMA_VERSION = 1
DEFAULT_OUTPUT = Path(
    "Experiments/Falsification/milestone_5b_core_v1.mutation_results.json"
)
KILLED = "killed"
SURVIVED = "survived"
INVALID = "invalid"
CLASSIFICATIONS = (KILLED, SURVIVED, INVALID)
SOURCE_PATHS = (
    "Discovery/mutation_harness.py",
    "Discovery/mutation_test_runner.py",
    "Discovery/dimensional_search.py",
    "Discovery/dependency_analysis.py",
    "Discovery/physical_bridge_validation.py",
    "tests/test_dimensional_search.py",
    "tests/test_dependency_analysis.py",
    "tests/test_physical_bridge.py",
    "tests/test_mutation_harness.py",
    str(DEFAULT_PREREGISTRATION_OUTPUT),
)


@dataclass(frozen=True, slots=True)
class Mutant:
    identifier: str
    category: str
    intended_semantic_defect: str
    relative_path: str
    old_text: str
    new_text: str
    test_names: tuple[str, ...]
    required_modules: tuple[str, ...]
    expected_calibration_classification: str | None = None

    def __post_init__(self) -> None:
        if self.category not in {"calibration", "production"}:
            raise ValueError("mutant category must be calibration or production")
        if not self.old_text or self.old_text == self.new_text:
            raise ValueError("mutation must replace source with different text")
        if not self.test_names or not self.required_modules:
            raise ValueError("mutants require tests and import-path modules")
        if (
            self.expected_calibration_classification is not None
            and self.expected_calibration_classification not in CLASSIFICATIONS
        ):
            raise ValueError("invalid expected calibration classification")


CALIBRATION_MUTANTS = (
    Mutant(
        identifier="calibration_known_kill_allowed_power_zero_only",
        category="calibration",
        intended_semantic_defect=(
            "Replace the nonzero rational exponent domain with zero-only powers."
        ),
        relative_path="Discovery/dimensional_search.py",
        old_text="        if numerator != 0\n",
        new_text="        if numerator == 0\n",
        test_names=(
            "tests.test_dimensional_search.DimensionalSearchTests."
            "test_power_bound_can_include_half_integers",
        ),
        required_modules=("Discovery.dimensional_search",),
        expected_calibration_classification=KILLED,
    ),
    Mutant(
        identifier="calibration_equivalent_explicit_sort_direction",
        category="calibration",
        intended_semantic_defect=(
            "Make the existing ascending sort direction explicit without changing behavior."
        ),
        relative_path="Discovery/dimensional_search.py",
        old_text="    return tuple(sorted(powers))\n",
        new_text="    return tuple(sorted(powers, reverse=False))\n",
        test_names=(
            "tests.test_dimensional_search.DimensionalSearchTests."
            "test_power_bound_can_include_half_integers",
        ),
        required_modules=("Discovery.dimensional_search",),
        expected_calibration_classification=SURVIVED,
    ),
)


PRODUCTION_MUTANTS = (
    Mutant(
        identifier="production_disable_registered_target_rejection",
        category="production",
        intended_semantic_defect=(
            "Disable the validator decision that rejects estimator ancestry reaching G."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="        if audit.status == TARGET_PATH_DETECTED:\n",
        new_text="        if False and audit.status == TARGET_PATH_DETECTED:\n",
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_direct_g_or_planck_estimator_input_is_rejected",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_skip_inherited_m_planck_traversal",
        category="production",
        intended_semantic_defect=(
            "Drop m_P terms before registered dependency expansion, hiding inherited G."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="    expansion = catalog.expand_signature(surface)\n",
        new_text=(
            "    expansion = catalog.expand_signature(\n"
            "        tuple(term for term in surface if term[0] != \"m_P\")\n"
            "    )\n"
        ),
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_m_planck_has_an_explicit_registered_target_path",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_disable_calibration_reference_guard",
        category="production",
        intended_semantic_defect=(
            "Disable the explicit guard against reference G in calibration or corrections."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="        if leaked:\n",
        new_text="        if False and leaked:\n",
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_reference_g_used_in_calibration_is_rejected",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_invert_dependency_artifact_freshness",
        category="production",
        intended_semantic_defect=(
            "Invert the dependency-artifact byte comparison used by --check."
        ),
        relative_path="Discovery/dependency_analysis.py",
        old_text=(
            "        if not args.output.exists() or "
            "args.output.read_text(encoding=\"utf-8\") != rendered:\n"
        ),
        new_text=(
            "        if not args.output.exists() or "
            "args.output.read_text(encoding=\"utf-8\") == rendered:\n"
        ),
        test_names=(
            "tests.test_dependency_analysis.DependencyAnalysisTests."
            "test_artifact_is_byte_deterministic_and_current",
        ),
        required_modules=("Discovery.dependency_analysis",),
    ),
)


def _run(
    arguments: Sequence[str],
    *,
    cwd: Path,
    check: bool = True,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def repository_root(path: Path = Path(".")) -> Path:
    return Path(_run(("git", "rev-parse", "--show-toplevel"), cwd=path).stdout.strip()).resolve()


def canonical_head(root: Path) -> str:
    return _run(("git", "rev-parse", "HEAD"), cwd=root).stdout.strip()


def canonical_status_bytes(root: Path) -> bytes:
    completed = subprocess.run(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def status_sha256(status: bytes) -> str:
    return hashlib.sha256(status).hexdigest()


def verify_source_state(
    root: Path,
    source_commit_sha: str,
    *,
    source_paths: Sequence[str] = SOURCE_PATHS,
) -> None:
    """Detect stale mutation artifacts after any result-driving source change."""

    resolved = _run(("git", "rev-parse", source_commit_sha), cwd=root).stdout.strip()
    if resolved != source_commit_sha:
        raise ValueError("mutation source commit SHA does not resolve exactly")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", source_commit_sha, "HEAD"),
        cwd=root,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("mutation source commit is not an ancestor of HEAD")
    changed = subprocess.run(
        ("git", "diff", "--quiet", source_commit_sha, "--", *source_paths),
        cwd=root,
        check=False,
    )
    if changed.returncode != 0:
        raise ValueError("mutation result-driving source differs from recorded source")


def apply_mutation(
    mutation_root: Path,
    canonical_root: Path,
    mutant: Mutant,
) -> None:
    """Apply exactly one replacement and reject canonical or ambiguous targets."""

    root = mutation_root.resolve()
    if root == canonical_root.resolve() or not (root / ".git").exists():
        raise RuntimeError("mutation root is not an established disposable worktree")
    path = root / mutant.relative_path
    original = path.read_text(encoding="utf-8")
    occurrences = original.count(mutant.old_text)
    if occurrences != 1:
        raise RuntimeError(
            f"mutation replacement count for {mutant.identifier} is {occurrences}, not 1"
        )
    path.write_text(original.replace(mutant.old_text, mutant.new_text), encoding="utf-8")
    changed = _run(("git", "diff", "--name-only"), cwd=root).stdout.splitlines()
    if changed != [mutant.relative_path]:
        raise RuntimeError(f"mutation changed unexpected files: {changed}")


def classify_runner_record(record: Mapping[str, Any]) -> tuple[str, tuple[str, ...], str | None]:
    if record.get("runner_status") != "completed":
        return INVALID, (), str(record.get("infrastructure_error", "runner failed"))
    errors = tuple(record.get("error_tests", ()))
    failures = tuple(record.get("failing_tests", ()))
    if errors:
        return INVALID, (), f"test process reported errors: {list(errors)}"
    if failures:
        return KILLED, failures, None
    if record.get("successful") is True:
        return SURVIVED, (), None
    return INVALID, (), "test process ended without a classifiable result"


def _sanitize_diagnostic(value: object, mutation_root: Path) -> str | None:
    if value is None:
        return None
    sanitized = str(value).replace(str(mutation_root), "<DISPOSABLE_WORKTREE>")
    return re.sub(
        r"Ran ([0-9]+) tests? in [0-9.]+s",
        r"Ran \1 test(s) in <ELAPSED>",
        sanitized,
    )


def _isolated_test_command(
    python_executable: str,
    mutation_root: Path,
    mutant: Mutant,
) -> tuple[str, ...]:
    bootstrap = (
        "import sys; "
        f"sys.path.insert(0, {str(mutation_root)!r}); "
        "from Discovery.mutation_test_runner import main; main()"
    )
    command = [
        python_executable,
        "-I",
        "-c",
        bootstrap,
        "--mutation-root",
        str(mutation_root),
    ]
    for module in mutant.required_modules:
        command.extend(("--required-module", module))
    command.extend(mutant.test_names)
    return tuple(command)


def run_mutant(
    canonical_root: Path,
    canonical_sha: str,
    mutant: Mutant,
    *,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    """Run one mutant with cleanup and canonical-integrity checks in a finally block."""

    before_head = canonical_head(canonical_root)
    before_status = canonical_status_bytes(canonical_root)
    before_status_hash = status_sha256(before_status)
    if before_status:
        return {
            "mutant_identifier": mutant.identifier,
            "classification": INVALID,
            "invalid_reason": "canonical checkout was not clean before mutation",
            "canonical_anchor_sha": canonical_sha,
            "canonical_head_unchanged": True,
            "canonical_status_before_sha256": before_status_hash,
            "canonical_status_after_sha256": before_status_hash,
            "cleanup_confirmed": True,
        }

    temporary_parent = Path(tempfile.mkdtemp(prefix="tnp-mutation-"))
    mutation_root = temporary_parent / "worktree"
    cleanup_confirmed = False
    command_record: list[str] = []
    record: dict[str, Any]
    try:
        _run(
            ("git", "worktree", "add", "--detach", str(mutation_root), canonical_sha),
            cwd=canonical_root,
        )
        if canonical_head(mutation_root) != canonical_sha:
            raise RuntimeError("disposable worktree HEAD does not match canonical anchor")
        apply_mutation(mutation_root, canonical_root, mutant)
        command = _isolated_test_command(python_executable, mutation_root, mutant)
        command_record = [
            "<PYTHON_EXECUTABLE>"
            if index == 0
            else value.replace(str(mutation_root), "<DISPOSABLE_WORKTREE>")
            for index, value in enumerate(command)
        ]
        completed = _run(command, cwd=mutation_root, check=False)
        if completed.returncode != 0:
            record = {
                "runner_status": "invalid",
                "infrastructure_error": (
                    f"isolated runner exited {completed.returncode}: {completed.stderr.strip()}"
                ),
            }
        else:
            try:
                record = json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                record = {
                    "runner_status": "invalid",
                    "infrastructure_error": f"runner emitted invalid JSON: {error}",
                }
        classification, killing_tests, invalid_reason = classify_runner_record(record)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        classification, killing_tests, invalid_reason = (
            INVALID,
            (),
            f"{type(error).__name__}: {error}",
        )
        record = {"runner_status": "invalid"}
    finally:
        subprocess.run(
            ("git", "worktree", "remove", "--force", str(mutation_root)),
            cwd=canonical_root,
            check=False,
            capture_output=True,
        )
        if temporary_parent.exists():
            shutil.rmtree(temporary_parent)
        subprocess.run(
            ("git", "worktree", "prune"),
            cwd=canonical_root,
            check=False,
            capture_output=True,
        )
        cleanup_confirmed = not temporary_parent.exists()

    after_head = canonical_head(canonical_root)
    after_status = canonical_status_bytes(canonical_root)
    after_status_hash = status_sha256(after_status)
    canonical_unchanged = before_head == after_head and before_status == after_status
    if not canonical_unchanged:
        classification = INVALID
        killing_tests = ()
        invalid_reason = "canonical HEAD or status changed during mutation run"
    if not cleanup_confirmed:
        classification = INVALID
        killing_tests = ()
        invalid_reason = "disposable worktree cleanup was not confirmed"

    return {
        "mutant_identifier": mutant.identifier,
        "category": mutant.category,
        "intended_semantic_defect": mutant.intended_semantic_defect,
        "mutated_path": mutant.relative_path,
        "test_command": list(mutant.test_names),
        "isolated_test_process_command": command_record,
        "required_import_modules": list(mutant.required_modules),
        "classification": classification,
        "killing_tests": list(killing_tests),
        "invalid_reason": invalid_reason,
        "canonical_anchor_sha": canonical_sha,
        "canonical_head_before": before_head,
        "canonical_head_after": after_head,
        "canonical_head_unchanged": before_head == after_head,
        "canonical_status_before_sha256": before_status_hash,
        "canonical_status_after_sha256": after_status_hash,
        "canonical_status_unchanged": before_status == after_status,
        "checkout_metadata": {
            "mode": "git_worktree_detached",
            "path_recording": "ephemeral path intentionally omitted",
        },
        "import_path_integrity": {
            "validated": record.get("runner_status") == "completed",
            "validated_imports": record.get("validated_imports_after", {}),
        },
        "runner_diagnostic": (
            _sanitize_diagnostic(
                record.get("test_output")
                or record.get("traceback")
                or record.get("infrastructure_error"),
                mutation_root,
            )
            if classification == INVALID
            else None
        ),
        "cleanup_confirmed": cleanup_confirmed,
    }


def run_mutation_family(
    canonical_root: Path,
    canonical_sha: str,
) -> dict[str, Any]:
    calibrations = [
        run_mutant(canonical_root, canonical_sha, mutant)
        for mutant in CALIBRATION_MUTANTS
    ]
    calibration_valid = all(
        record["classification"] == mutant.expected_calibration_classification
        for record, mutant in zip(calibrations, CALIBRATION_MUTANTS)
    )
    if calibration_valid:
        production = [
            run_mutant(canonical_root, canonical_sha, mutant)
            for mutant in PRODUCTION_MUTANTS
        ]
    else:
        production = []
    return {
        "family_status": "valid" if calibration_valid else INVALID,
        "calibration_valid": calibration_valid,
        "calibration_results": calibrations,
        "production_results": production,
        "production_interpretation": (
            "meaningful" if calibration_valid else "withheld because calibration failed"
        ),
    }


def _git_log_sha(root: Path, path: Path) -> str:
    return _run(
        ("git", "log", "-1", "--format=%H", "--", str(path)),
        cwd=root,
    ).stdout.strip()


def build_result(
    *,
    canonical_root: Path,
    canonical_sha: str,
    preregistration_path: Path = DEFAULT_PREREGISTRATION_OUTPUT,
) -> dict[str, Any]:
    preregistration, preregistration_bytes = load_preregistration(preregistration_path)
    if canonical_head(canonical_root) != canonical_sha:
        raise ValueError("canonical HEAD does not equal the recorded mutation anchor")
    if canonical_status_bytes(canonical_root):
        raise ValueError("canonical checkout must be clean before mutation-family execution")
    family = run_mutation_family(canonical_root, canonical_sha)
    return {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "methodological_result_status": family["family_status"],
        "integrity": {
            "preregistration_path": str(preregistration_path),
            "preregistration_sha256": preregistration_sha256_bytes(
                preregistration_bytes
            ),
            "preregistration_commit_sha": _git_log_sha(
                canonical_root, preregistration_path
            ),
            "source_commit_sha": canonical_sha,
            "source_commit_semantics": (
                "Committed harness, mutant catalog, tests, and project source anchored "
                "into every disposable worktree."
            ),
            "seeds": dict(preregistration["randomness"]["seeds"]),
            "mutation_randomness": "none",
            "source_paths": list(SOURCE_PATHS),
        },
        "classifications": list(CLASSIFICATIONS),
        "calibration_rule": (
            "Production results are meaningful only if the known-killable mutant is "
            "killed and the behaviorally equivalent mutant survives."
        ),
        **family,
        "anti_goodhart_rule": (
            "A surviving mutant may be closed only by a behavioral assertion of the "
            "intended contract, never by source-text or patch detection."
        ),
        "nonclaims": [
            "Killed means only that the predefined tests detected this selected defect.",
            "Survived identifies a test blind spot, not correct mutated behavior.",
            "Invalid is never counted as a kill.",
            "This finite mutant set does not establish that the software is defect-free.",
            "Mutation results are methodological, not empirical evidence about physics.",
        ],
    }


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def validate_result_integrity(
    result: Mapping[str, Any],
    *,
    preregistration_path: Path = DEFAULT_PREREGISTRATION_OUTPUT,
) -> None:
    preregistration, content = load_preregistration(preregistration_path)
    if result.get("result_schema_version") != RESULT_SCHEMA_VERSION:
        raise ValueError("stale mutation-result schema version")
    if result.get("experiment_identifier") != preregistration["experiment_identifier"]:
        raise ValueError("preregistration/mutation-result experiment mismatch")
    integrity = result.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ValueError("mutation-result integrity metadata is missing")
    if integrity.get("preregistration_sha256") != preregistration_sha256_bytes(content):
        raise ValueError("preregistration/mutation-result hash mismatch")
    if integrity.get("seeds") != preregistration["randomness"]["seeds"]:
        raise ValueError("preregistration/mutation-result seed mismatch")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--preregistration", type=Path, default=DEFAULT_PREREGISTRATION_OUTPUT
    )
    parser.add_argument("--source-commit-sha")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed mutation metadata without mutating the canonical checkout",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    root = repository_root()
    if args.check:
        if not args.output.exists():
            print(f"missing mutation-result artifact: {args.output}", file=sys.stderr)
            raise SystemExit(1)
        result = json.loads(args.output.read_text(encoding="utf-8"))
        validate_result_integrity(result, preregistration_path=args.preregistration)
        source_sha = result["integrity"]["source_commit_sha"]
        verify_source_state(root, source_sha)
        if not result.get("calibration_valid"):
            raise ValueError("committed mutation family failed calibration")
        print("Mutation result metadata, preregistration, and calibration are valid.")
        return

    if args.source_commit_sha is None:
        print("--source-commit-sha is required for a new mutation result", file=sys.stderr)
        raise SystemExit(2)
    if args.output.exists():
        print(
            "refusing to overwrite an existing mutation result; create a new version",
            file=sys.stderr,
        )
        raise SystemExit(1)
    rendered = serialize_artifact(
        build_result(
            canonical_root=root,
            canonical_sha=args.source_commit_sha,
            preregistration_path=args.preregistration,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote ephemeral mutation result to {args.output}.")


if __name__ == "__main__":
    main()
