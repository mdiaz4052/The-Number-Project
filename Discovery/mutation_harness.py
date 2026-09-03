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
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)


RESULT_SCHEMA_VERSION = 4
DEFAULT_OUTPUT = Path(
    "Experiments/Falsification/milestone_5b_core_v1.mutation_results_v2.json"
)
KILLED = "killed"
SURVIVED = "survived"
INVALID = "invalid"
CLASSIFICATIONS = (KILLED, SURVIVED, INVALID)
CALIBRATION_RULE = (
    "Production results are meaningful only if the known-killable mutant is "
    "killed and the behaviorally equivalent mutant survives."
)
ANTI_GOODHART_RULE = (
    "A surviving mutant may be closed only by a behavioral assertion of the "
    "intended contract, never by source-text or patch detection."
)
NONCLAIMS = (
    "Killed means only that the predefined tests detected this selected defect.",
    (
        "A killed mutant may pin a diagnostic or defense-in-depth behavior rather "
        "than an independent acceptance barrier."
    ),
    "Survived identifies a test blind spot, not correct mutated behavior.",
    "Invalid is never counted as a kill.",
    "This finite mutant set does not establish that the software is defect-free.",
    "Mutation results are methodological, not empirical evidence about physics.",
)
SOURCE_PATHS = (
    "Discovery/mutation_harness.py",
    "Discovery/mutation_test_runner.py",
    "Discovery/dimensional_search.py",
    "Discovery/dependency_analysis.py",
    "Discovery/physical_bridge_schema.py",
    "Discovery/physical_bridge_validation.py",
    "Discovery/source_history.py",
    "tests/test_dimensional_search.py",
    "tests/test_dependency_analysis.py",
    "tests/test_dependency_dimension_invariant.py",
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
        identifier="production_substitute_m_planck_with_atomic_mass",
        category="production",
        intended_semantic_defect=(
            "Substitute target-independent m_e for m_P before registered dependency "
            "expansion, hiding inherited G while preserving the mass dimension."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="    expansion = catalog.expand_signature(surface)\n",
        new_text=(
            "    expansion = catalog.expand_signature(\n"
            "        tuple(\n"
            "            (\"m_e\", exponent) if key == \"m_P\" else (key, exponent)\n"
            "            for key, exponent in surface\n"
            "        )\n"
            "    )\n"
        ),
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_m_planck_has_an_explicit_registered_target_path",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_disable_calibration_reference_diagnostic",
        category="production",
        intended_semantic_defect=(
            "Disable the dedicated calibration/correction reference diagnostic; the "
            "broader external-reference boundary still rejects the same models."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="        if leaked:\n",
        new_text="        if False and leaked:\n",
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_reference_g_used_in_calibration_is_rejected",
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_reference_g_used_in_correction_is_rejected",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_disable_empirical_source_provenance",
        category="production",
        intended_semantic_defect=(
            "Disable the fail-closed source-metadata requirement for populated "
            "empirical estimator ancestry."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="    if model.evidence_level == EMPIRICAL_RECORD:\n",
        new_text="    if False and model.evidence_level == EMPIRICAL_RECORD:\n",
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_populated_empirical_calibration_requires_source_provenance",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_disable_empirical_documented_provenance",
        category="production",
        intended_semantic_defect=(
            "Allow a populated empirical input with source fields but without the "
            "required documented-provenance classification."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="            if quantity.provenance_evidence != DOCUMENTED:\n",
        new_text=(
            "            if False and quantity.provenance_evidence != DOCUMENTED:\n"
        ),
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_populated_empirical_calibration_requires_documented_provenance",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_disable_empirical_source_metadata_requirements",
        category="production",
        intended_semantic_defect=(
            "Treat missing source identifier, edition, and access-date fields as present "
            "for populated empirical input metadata."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text="                if value is None\n",
        new_text="                if False and value is None\n",
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_each_empirical_source_metadata_field_is_required",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_limit_empirical_source_gate_to_estimator_ancestry",
        category="production",
        intended_semantic_defect=(
            "Stop checking declared calibration and correction records that sit "
            "outside estimator graph ancestry."
        ),
        relative_path="Discovery/physical_bridge_validation.py",
        old_text=(
            "        source_required_ids = (\n"
            "            estimator_upstream\n"
            "            | set(model.calibration_source_ids)\n"
            "            | set(model.correction_ids)\n"
            "        )\n"
        ),
        new_text="        source_required_ids = estimator_upstream\n",
        test_names=(
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_declared_calibration_outside_estimator_ancestry_requires_source",
            "tests.test_physical_bridge.PhysicalBridgeTests."
            "test_declared_correction_outside_estimator_ancestry_requires_source",
        ),
        required_modules=("Discovery.physical_bridge_validation",),
    ),
    Mutant(
        identifier="production_make_dependency_classification_dimension_sensitive",
        category="production",
        intended_semantic_defect=(
            "Make post-validation registered target-dependency classification depend "
            "on catalog dimension metadata instead of exact definition expansion alone."
        ),
        relative_path="Discovery/dependency_analysis.py",
        old_text=(
            "        certification_status, theorem_name = _certification(\n"
            "            surface,\n"
            "            dependency_status,\n"
            "        )\n"
            "        provisional.append(\n"
        ),
        new_text=(
            "        certification_status, theorem_name = _certification(\n"
            "            surface,\n"
            "            dependency_status,\n"
            "        )\n"
            "        if (\n"
            "            catalog.dimensions.get(TARGET_KEY)\n"
            "            != DEFAULT_DEPENDENCY_CATALOG.dimensions[TARGET_KEY]\n"
            "        ):\n"
            "            dependency_status = NO_REGISTERED_TARGET_DEPENDENCY\n"
            "            power_of_g = Fraction(0)\n"
            "        provisional.append(\n"
        ),
        test_names=(
            "tests.test_dependency_dimension_invariant."
            "DependencyDimensionInvariantTests."
            "test_dependency_classification_ignores_dimension_metadata_after_validation",
        ),
        required_modules=("Discovery.dependency_analysis",),
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
            "test_check_cli_accepts_current_and_rejects_stale_artifact",
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

    verify_committed_source_state(
        root,
        source_commit_sha,
        source_paths=source_paths,
        artifact_label="mutation result",
    )


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
        "expected_classification": mutant.expected_calibration_classification,
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


def source_path_snapshot(
    root: Path,
    source_commit_sha: str,
    *,
    source_paths: Sequence[str] = SOURCE_PATHS,
) -> dict[str, Any]:
    """Record the Git blob object for every result-driving path at the source commit."""

    try:
        object_format = _run(
            ("git", "rev-parse", "--show-object-format"), cwd=root
        ).stdout.strip()
        path_blob_oids = {
            path: _run(
                ("git", "rev-parse", f"{source_commit_sha}:{path}"), cwd=root
            ).stdout.strip()
            for path in source_paths
        }
    except subprocess.SubprocessError as error:
        raise ValueError("mutation source-path blob snapshot could not be resolved") from error
    return {
        "git_object_format": object_format,
        "path_blob_oids": path_blob_oids,
    }


def mutation_records_sha256(
    calibration_results: Sequence[Mapping[str, Any]],
    production_results: Sequence[Mapping[str, Any]],
    *,
    source_commit_sha: str,
    source_snapshot: Mapping[str, Any],
) -> str:
    """Hash records together with the exact source state they claim to describe."""

    payload = json.dumps(
        {
            "calibration_results": list(calibration_results),
            "production_results": list(production_results),
            "source_commit_sha": source_commit_sha,
            "source_snapshot": dict(source_snapshot),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
    snapshot = source_path_snapshot(canonical_root, canonical_sha)
    family = run_mutation_family(canonical_root, canonical_sha)
    records_sha256 = mutation_records_sha256(
        family["calibration_results"],
        family["production_results"],
        source_commit_sha=canonical_sha,
        source_snapshot=snapshot,
    )
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
            "source_snapshot": snapshot,
            "records_sha256": records_sha256,
            "records_sha256_semantics": (
                "SHA-256 of the canonical source commit, SOURCE_PATHS Git-blob "
                "snapshot, calibration_results, and production_results; a "
                "tamper-evidence pin, not a reproduction proof."
            ),
        },
        "classifications": list(CLASSIFICATIONS),
        "calibration_rule": CALIBRATION_RULE,
        **family,
        "anti_goodhart_rule": ANTI_GOODHART_RULE,
        "nonclaims": list(NONCLAIMS),
    }


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def _validate_mutation_record(
    record: object,
    mutant: Mutant,
    *,
    source_commit_sha: str,
) -> str:
    if not isinstance(record, Mapping):
        raise ValueError("mutation record is malformed")
    expected_fields = {
        "mutant_identifier": mutant.identifier,
        "category": mutant.category,
        "expected_classification": mutant.expected_calibration_classification,
        "intended_semantic_defect": mutant.intended_semantic_defect,
        "mutated_path": mutant.relative_path,
        "test_command": list(mutant.test_names),
        "required_import_modules": list(mutant.required_modules),
        "canonical_anchor_sha": source_commit_sha,
        "canonical_head_before": source_commit_sha,
        "canonical_head_after": source_commit_sha,
    }
    for field, expected in expected_fields.items():
        if record.get(field) != expected:
            raise ValueError(
                f"mutation record/catalog mismatch for {mutant.identifier}: {field}"
            )

    clean_status_sha256 = status_sha256(b"")
    safety_invariants = {
        "canonical_head_unchanged": True,
        "canonical_status_before_sha256": clean_status_sha256,
        "canonical_status_after_sha256": clean_status_sha256,
        "canonical_status_unchanged": True,
        "cleanup_confirmed": True,
    }
    for field, expected in safety_invariants.items():
        actual = record.get(field)
        if isinstance(expected, bool):
            matches = actual is expected
        else:
            matches = actual == expected
        if not matches:
            raise ValueError(
                f"mutation record safety invariant mismatch for "
                f"{mutant.identifier}: {field}"
            )

    classification = record.get("classification")
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"invalid classification for {mutant.identifier}")
    killing_tests = record.get("killing_tests")
    if not isinstance(killing_tests, list) or any(
        not isinstance(item, str) for item in killing_tests
    ):
        raise ValueError(f"malformed killing_tests for {mutant.identifier}")
    invalid_reason = record.get("invalid_reason")
    if invalid_reason is not None and not isinstance(invalid_reason, str):
        raise ValueError(f"malformed invalid_reason for {mutant.identifier}")

    if classification == KILLED:
        valid_killing_tests = all(
            any(
                killing_test == test_name
                or killing_test.startswith(f"{test_name} ")
                for test_name in mutant.test_names
            )
            for killing_test in killing_tests
        )
        if not killing_tests or not valid_killing_tests:
            raise ValueError(f"killed mutant lacks valid killing tests: {mutant.identifier}")
        if invalid_reason is not None:
            raise ValueError(f"killed mutant has invalid_reason: {mutant.identifier}")
    elif classification == SURVIVED:
        if killing_tests or invalid_reason is not None:
            raise ValueError(f"survived mutant has contradictory metadata: {mutant.identifier}")
    elif killing_tests or not invalid_reason:
        raise ValueError(f"invalid mutant has contradictory metadata: {mutant.identifier}")

    import_integrity = record.get("import_path_integrity")
    if not isinstance(import_integrity, Mapping) or not isinstance(
        import_integrity.get("validated"), bool
    ):
        raise ValueError(f"malformed import-path integrity for {mutant.identifier}")
    if classification in {KILLED, SURVIVED} and not import_integrity["validated"]:
        raise ValueError(f"classifiable mutant lacks import validation: {mutant.identifier}")
    return classification


def _validate_source_snapshot_record(snapshot: object) -> Mapping[str, Any]:
    if not isinstance(snapshot, Mapping):
        raise ValueError("mutation source-path blob snapshot is missing")
    object_format = snapshot.get("git_object_format")
    if object_format not in {"sha1", "sha256"}:
        raise ValueError("mutation source-path Git object format is invalid")
    blob_oids = snapshot.get("path_blob_oids")
    if not isinstance(blob_oids, Mapping) or set(blob_oids) != set(SOURCE_PATHS):
        raise ValueError("mutation source-path blob catalog mismatch")
    expected_length = 40 if object_format == "sha1" else 64
    if any(
        not isinstance(oid, str)
        or re.fullmatch(rf"[0-9a-f]{{{expected_length}}}", oid) is None
        for oid in blob_oids.values()
    ):
        raise ValueError("mutation source-path blob object ID is invalid")
    return snapshot


def verify_result_source_snapshot(
    root: Path,
    result: Mapping[str, Any],
) -> None:
    """Confirm that the hashed source snapshot matches Git at the recorded commit."""

    integrity = result.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ValueError("mutation-result integrity metadata is missing")
    source_commit_sha = integrity.get("source_commit_sha")
    if not isinstance(source_commit_sha, str):
        raise ValueError("mutation source commit SHA is missing")
    recorded = _validate_source_snapshot_record(integrity.get("source_snapshot"))
    actual = source_path_snapshot(root, source_commit_sha)
    if recorded != actual:
        raise ValueError("mutation source-path blob snapshot mismatch")


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
    if integrity.get("source_paths") != list(SOURCE_PATHS):
        raise ValueError("mutation-result source-path catalog mismatch")
    source_commit_sha = integrity.get("source_commit_sha")
    if not isinstance(source_commit_sha, str) or re.fullmatch(
        r"[0-9a-f]{40}", source_commit_sha
    ) is None:
        raise ValueError("mutation-result source commit SHA is invalid")
    snapshot = _validate_source_snapshot_record(integrity.get("source_snapshot"))
    if result.get("classifications") != list(CLASSIFICATIONS):
        raise ValueError("mutation-result classification catalog mismatch")
    pinned_methodology = {
        "calibration_rule": CALIBRATION_RULE,
        "anti_goodhart_rule": ANTI_GOODHART_RULE,
        "nonclaims": list(NONCLAIMS),
    }
    for field, expected in pinned_methodology.items():
        if result.get(field) != expected:
            raise ValueError(f"mutation-result pinned field mismatch: {field}")

    calibrations = result.get("calibration_results")
    production = result.get("production_results")
    if not isinstance(calibrations, list) or not isinstance(production, list):
        raise ValueError("mutation-result record arrays are malformed")
    expected_digest = mutation_records_sha256(
        calibrations,
        production,
        source_commit_sha=source_commit_sha,
        source_snapshot=snapshot,
    )
    if integrity.get("records_sha256") != expected_digest:
        raise ValueError("mutation-record hash mismatch")

    if len(calibrations) != len(CALIBRATION_MUTANTS):
        raise ValueError("mutation calibration-record count mismatch")
    calibration_classifications = [
        _validate_mutation_record(
            record, mutant, source_commit_sha=source_commit_sha
        )
        for record, mutant in zip(calibrations, CALIBRATION_MUTANTS)
    ]
    calibration_valid = all(
        classification == mutant.expected_calibration_classification
        for classification, mutant in zip(
            calibration_classifications, CALIBRATION_MUTANTS
        )
    )
    expected_production_count = len(PRODUCTION_MUTANTS) if calibration_valid else 0
    if len(production) != expected_production_count:
        raise ValueError("mutation production-record count contradicts calibration")
    for record, mutant in zip(production, PRODUCTION_MUTANTS):
        _validate_mutation_record(
            record, mutant, source_commit_sha=source_commit_sha
        )

    expected_family_status = "valid" if calibration_valid else INVALID
    expected_interpretation = (
        "meaningful" if calibration_valid else "withheld because calibration failed"
    )
    derived_fields = {
        "calibration_valid": calibration_valid,
        "family_status": expected_family_status,
        "methodological_result_status": expected_family_status,
        "production_interpretation": expected_interpretation,
    }
    for field, expected in derived_fields.items():
        if result.get(field) != expected:
            raise ValueError(f"mutation-result derived field mismatch: {field}")


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
    if args.check:
        try:
            if not args.output.exists():
                print(f"missing mutation-result artifact: {args.output}", file=sys.stderr)
                raise SystemExit(1)
            result = json.loads(args.output.read_text(encoding="utf-8"))
            validate_result_integrity(result, preregistration_path=args.preregistration)
            source_sha = result["integrity"]["source_commit_sha"]
            root = repository_root()
            verify_source_state(root, source_sha)
            verify_result_source_snapshot(root, result)
            if not result.get("calibration_valid"):
                raise ValueError("committed mutation family failed calibration")
        except SourceVerificationError as error:
            exit_for_source_verification_error(error)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print(f"invalid mutation result: {error}", file=sys.stderr)
            raise SystemExit(1) from None
        print(
            "Mutation result records, metadata, preregistration, and calibration "
            "are integrity-checked."
        )
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
            canonical_root=repository_root(),
            canonical_sha=args.source_commit_sha,
            preregistration_path=args.preregistration,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote ephemeral mutation result to {args.output}.")


if __name__ == "__main__":
    main()
