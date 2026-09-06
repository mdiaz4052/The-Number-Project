"""Run isolated source-path mutants for bounded HUST AAF depth-2b guards."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


MEASUREMENT_MODEL_PATH = Path(
    "Discovery/hust_2018_aaf_depth_2b_measurement_models.py"
)
AUTHORIZATION_PATH = Path("Discovery/hust_2018_aaf_depth_2b_authorization.py")
MEASUREMENT_MODEL_MODULE = "Discovery.hust_2018_aaf_depth_2b_measurement_models"
AUTHORIZATION_MODULE = "Discovery.hust_2018_aaf_depth_2b_authorization"
MEASUREMENT_MODEL_TEST_CLASS = (
    "tests.test_hust_2018_aaf_depth_2b_measurement_models."
    "HUST2018AAFDepth2BMeasurementModelTests"
)
AUTHORIZATION_TEST_CLASS = (
    "tests.test_hust_2018_aaf_depth_2b_authorization."
    "HUST2018AAFDepth2BAuthorizationTests"
)


class HUSTDepth2BPathMutationError(ValueError):
    """A source mutant was invalid, non-isolated, or non-discriminating."""


@dataclass(frozen=True)
class PathMutationSpec:
    mutation_id: str
    category: str
    source_path: Path
    module_name: str
    old_source: str
    new_source: str
    designated_test_id: str
    intended_behavioral_guard: str


DISPLAYED_TOTAL_SPEC = PathMutationSpec(
    mutation_id="displayed_total_as_input",
    category="terminal_leakage",
    source_path=MEASUREMENT_MODEL_PATH,
    module_name=MEASUREMENT_MODEL_MODULE,
    old_source=(
        "        relative_ppm = sum_of_squares.sqrt()\n"
        "        absolute_uncertainty = abs(target.value) * relative_ppm * "
        "Decimal(\"1e-6\")\n"
    ),
    new_source=(
        "        relative_ppm = Decimal(\n"
        "            graph[\"terminal_comparisons\"][scope][\"displayed_total_ppm\"]\n"
        "        )\n"
        "        absolute_uncertainty = abs(target.value) * relative_ppm * "
        "Decimal(\"1e-6\")\n"
    ),
    designated_test_id=(
        MEASUREMENT_MODEL_TEST_CLASS
        + ".test_displayed_total_is_not_an_uncertainty_input"
    ),
    intended_behavioral_guard="target uncertainty",
)

PUBLISHED_UNCERTAINTY_SPEC = PathMutationSpec(
    mutation_id="published_final_uncertainty_as_input",
    category="terminal_leakage",
    source_path=MEASUREMENT_MODEL_PATH,
    module_name=MEASUREMENT_MODEL_MODULE,
    old_source=(
        "        absolute_uncertainty = abs(target.value) * relative_ppm * "
        "Decimal(\"1e-6\")\n"
    ),
    new_source=(
        "        published = _quantity_map(baseline_model)[f\"{scope}:published_G\"]\n"
        "        absolute_uncertainty = published.standard_uncertainty\n"
        "        if absolute_uncertainty is None:\n"
        "            raise HUSTDepth2BMeasurementModelError(\n"
        "                f\"published final uncertainty is unavailable for {scope}\"\n"
        "            )\n"
    ),
    designated_test_id=(
        MEASUREMENT_MODEL_TEST_CLASS
        + ".test_published_final_uncertainty_is_not_an_uncertainty_input"
    ),
    intended_behavioral_guard="target uncertainty",
)

CLARIFICATION_TRAVERSAL_SPEC = PathMutationSpec(
    mutation_id="clarification_byte_identity_traversal_removed",
    category="source_authorization",
    source_path=AUTHORIZATION_PATH,
    module_name=AUTHORIZATION_MODULE,
    old_source=(
        "    _reject_byte_identity_overclaim(record, \"clarification record\")\n"
    ),
    new_source="",
    designated_test_id=(
        AUTHORIZATION_TEST_CLASS
        + ".test_clarification_nested_byte_identity_traversal_rejects_overclaim"
    ),
    intended_behavioral_guard=(
        "CLARIFICATION_BYTE_IDENTITY_TRAVERSAL_GUARD_MISSING"
    ),
)

PATH_MUTATION_SPECS = (
    DISPLAYED_TOTAL_SPEC,
    PUBLISHED_UNCERTAINTY_SPEC,
    CLARIFICATION_TRAVERSAL_SPEC,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_status(root: Path) -> str:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise HUSTDepth2BPathMutationError("canonical Git worktree cannot be inspected")
    return completed.stdout


def apply_exact_source_replacement(source: str, spec: PathMutationSpec) -> str:
    """Apply exactly one bounded source replacement or reject the mutant."""

    count = source.count(spec.old_source)
    if count != 1:
        raise HUSTDepth2BPathMutationError(
            f"{spec.mutation_id} replacement count is {count}, expected 1"
        )
    return source.replace(spec.old_source, spec.new_source, 1)


def _sanitized_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT"):
        environment.pop(name, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _import_probe(root: Path, spec: PathMutationSpec) -> None:
    expected = (root / spec.source_path).resolve()
    script = (
        "import importlib, pathlib, sys\n"
        f"root = pathlib.Path({str(root)!r}).resolve()\n"
        "sys.path.insert(0, str(root))\n"
        f"module = importlib.import_module({spec.module_name!r})\n"
        "print(pathlib.Path(module.__file__).resolve())\n"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        cwd=root,
        env=_sanitized_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise HUSTDepth2BPathMutationError(
            f"mutated module did not import cleanly: {spec.module_name}"
        )
    try:
        actual = Path(completed.stdout.strip()).resolve()
    except (OSError, RuntimeError) as error:
        raise HUSTDepth2BPathMutationError(
            "mutated module import path could not be resolved"
        ) from error
    if actual != expected:
        raise HUSTDepth2BPathMutationError(
            "mutated test resolved the canonical module instead of the isolated copy"
        )


def _run_named_test(
    root: Path, spec: PathMutationSpec
) -> subprocess.CompletedProcess[str]:
    script = (
        "import importlib, pathlib, sys, unittest\n"
        f"root = pathlib.Path({str(root)!r}).resolve()\n"
        "sys.path.insert(0, str(root))\n"
        f"module = importlib.import_module({spec.module_name!r})\n"
        f"expected = (root / {spec.source_path.as_posix()!r}).resolve()\n"
        "if pathlib.Path(module.__file__).resolve() != expected:\n"
        "    print('wrong isolated import', file=sys.stderr)\n"
        "    raise SystemExit(4)\n"
        f"test_id = {spec.designated_test_id!r}\n"
        "suite = unittest.defaultTestLoader.loadTestsFromName(test_id)\n"
        "if suite.countTestCases() != 1:\n"
        "    print('wrong test discovery count', file=sys.stderr)\n"
        "    raise SystemExit(3)\n"
        "result = unittest.TextTestRunner(verbosity=2).run(suite)\n"
        "raise SystemExit(0 if result.wasSuccessful() else 1)\n"
    )
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        cwd=root,
        env=_sanitized_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


def run_source_path_mutant(root: Path, spec: PathMutationSpec) -> dict[str, object]:
    """Run one valid isolated source mutant and require its named test to kill it."""

    root = root.resolve()
    canonical_source = root / spec.source_path
    canonical_hash_before = _sha256(canonical_source)
    canonical_status_before = _git_status(root)
    temporary: Path | None = None
    try:
        canonical = _run_named_test(root, spec)
        if canonical.returncode != 0:
            raise HUSTDepth2BPathMutationError(
                f"canonical designated test failed for {spec.mutation_id}"
            )

        temporary = Path(tempfile.mkdtemp(prefix="hust-depth-2b-path-mutant-"))
        isolated = temporary / "repository"
        shutil.copytree(
            root,
            isolated,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                "venv",
                ".lake",
                "__pycache__",
                "*.pyc",
                ".pytest_cache",
                ".mypy_cache",
            ),
        )
        mutated_source = isolated / spec.source_path
        source = mutated_source.read_text(encoding="utf-8")
        mutated = apply_exact_source_replacement(source, spec)
        compile(mutated, mutated_source.as_posix(), "exec")
        mutated_source.write_text(mutated, encoding="utf-8")
        _import_probe(isolated, spec)

        completed = _run_named_test(isolated, spec)
        combined_output = completed.stdout + completed.stderr
        if completed.returncode == 0:
            raise HUSTDepth2BPathMutationError(
                f"valid source-path mutant survived: {spec.mutation_id}"
            )
        if completed.returncode != 1:
            raise HUSTDepth2BPathMutationError(
                f"{spec.mutation_id} failed outside the behavioral test"
            )
        if spec.intended_behavioral_guard not in combined_output:
            raise HUSTDepth2BPathMutationError(
                f"{spec.mutation_id} did not fail through its intended guard"
            )
    except HUSTDepth2BPathMutationError:
        raise
    except (OSError, UnicodeError, SyntaxError, subprocess.TimeoutExpired) as error:
        raise HUSTDepth2BPathMutationError(
            f"invalid source-path mutant {spec.mutation_id}: {error}"
        ) from error
    finally:
        if temporary is not None:
            try:
                shutil.rmtree(temporary, ignore_errors=False)
            except OSError as error:
                raise HUSTDepth2BPathMutationError(
                    f"temporary copy could not be removed for {spec.mutation_id}"
                ) from error
            if temporary.exists():
                raise HUSTDepth2BPathMutationError(
                    f"temporary copy was not removed for {spec.mutation_id}"
                )
        if _sha256(canonical_source) != canonical_hash_before:
            raise HUSTDepth2BPathMutationError(
                "canonical source bytes changed during mutation"
            )
        if _git_status(root) != canonical_status_before:
            raise HUSTDepth2BPathMutationError(
                "canonical Git worktree changed during mutation"
            )

    return {
        "mutation_id": spec.mutation_id,
        "category": spec.category,
        "mutation_kind": "source_path",
        "source_path": spec.source_path.as_posix(),
        "module_name": spec.module_name,
        "designated_test_id": spec.designated_test_id,
        "mutant_applied": True,
        "mutant_importable": True,
        "intended_behavioral_guard": spec.intended_behavioral_guard,
        "sentinels_fired": [],
        "cleanup_confirmed": True,
        "canonical_source_unchanged": True,
        "canonical_worktree_unchanged": True,
        "outcome": "KILLED",
    }


def run_source_path_mutants(root: Path = Path(".")) -> list[dict[str, object]]:
    return [run_source_path_mutant(root, spec) for spec in PATH_MUTATION_SPECS]
