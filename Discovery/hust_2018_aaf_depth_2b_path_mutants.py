"""Run isolated source-path mutants for the HUST AAF terminal-input boundary."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


BUILDER_PATH = Path("Discovery/hust_2018_aaf_depth_2b_measurement_models.py")
TEST_CLASS = (
    "tests.test_hust_2018_aaf_depth_2b_measurement_models."
    "HUST2018AAFDepth2BMeasurementModelTests"
)


class HUSTDepth2BPathMutationError(ValueError):
    """A source mutant was invalid, non-isolated, or non-discriminating."""


@dataclass(frozen=True)
class PathMutationSpec:
    mutation_id: str
    old_source: str
    new_source: str
    designated_test_id: str
    intended_behavioral_guard: str


DISPLAYED_TOTAL_SPEC = PathMutationSpec(
    mutation_id="displayed_total_as_input",
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
        TEST_CLASS + ".test_displayed_total_is_not_an_uncertainty_input"
    ),
    intended_behavioral_guard="target uncertainty",
)

PUBLISHED_UNCERTAINTY_SPEC = PathMutationSpec(
    mutation_id="published_final_uncertainty_as_input",
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
        TEST_CLASS + ".test_published_final_uncertainty_is_not_an_uncertainty_input"
    ),
    intended_behavioral_guard="target uncertainty",
)

PATH_MUTATION_SPECS = (DISPLAYED_TOTAL_SPEC, PUBLISHED_UNCERTAINTY_SPEC)


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


def _import_probe(root: Path) -> None:
    expected = (root / BUILDER_PATH).resolve()
    script = (
        "import importlib, pathlib, sys\n"
        f"root = pathlib.Path({str(root)!r}).resolve()\n"
        "sys.path.insert(0, str(root))\n"
        "module = importlib.import_module("
        "'Discovery.hust_2018_aaf_depth_2b_measurement_models')\n"
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
        raise HUSTDepth2BPathMutationError("mutated builder did not import cleanly")
    try:
        actual = Path(completed.stdout.strip()).resolve()
    except (OSError, RuntimeError) as error:
        raise HUSTDepth2BPathMutationError(
            "mutated builder import path could not be resolved"
        ) from error
    if actual != expected:
        raise HUSTDepth2BPathMutationError(
            "mutated test resolved the canonical builder instead of the isolated copy"
        )


def _run_named_test(root: Path, test_id: str) -> subprocess.CompletedProcess[str]:
    script = (
        "import importlib, pathlib, sys, unittest\n"
        f"root = pathlib.Path({str(root)!r}).resolve()\n"
        "sys.path.insert(0, str(root))\n"
        "module = importlib.import_module("
        "'Discovery.hust_2018_aaf_depth_2b_measurement_models')\n"
        "expected = (root / "
        "'Discovery/hust_2018_aaf_depth_2b_measurement_models.py').resolve()\n"
        "if pathlib.Path(module.__file__).resolve() != expected:\n"
        "    print('wrong isolated import', file=sys.stderr)\n"
        "    raise SystemExit(4)\n"
        f"test_id = {test_id!r}\n"
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
    """Run one valid isolated builder mutant and require its named test to kill it."""

    root = root.resolve()
    canonical_builder = root / BUILDER_PATH
    canonical_hash_before = _sha256(canonical_builder)
    canonical_status_before = _git_status(root)
    temporary: Path | None = None
    try:
        canonical = _run_named_test(root, spec.designated_test_id)
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
        mutated_builder = isolated / BUILDER_PATH
        source = mutated_builder.read_text(encoding="utf-8")
        mutated = apply_exact_source_replacement(source, spec)
        compile(mutated, mutated_builder.as_posix(), "exec")
        mutated_builder.write_text(mutated, encoding="utf-8")
        _import_probe(isolated)

        completed = _run_named_test(isolated, spec.designated_test_id)
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
        if _sha256(canonical_builder) != canonical_hash_before:
            raise HUSTDepth2BPathMutationError(
                "canonical builder bytes changed during mutation"
            )
        if _git_status(root) != canonical_status_before:
            raise HUSTDepth2BPathMutationError(
                "canonical Git worktree changed during mutation"
            )

    return {
        "mutation_id": spec.mutation_id,
        "category": "terminal_leakage",
        "mutation_kind": "source_path",
        "designated_test_id": spec.designated_test_id,
        "mutant_applied": True,
        "mutant_importable": True,
        "intended_behavioral_guard": spec.intended_behavioral_guard,
        "sentinels_fired": [],
        "cleanup_confirmed": True,
        "canonical_builder_unchanged": True,
        "canonical_worktree_unchanged": True,
        "outcome": "KILLED",
    }


def run_source_path_mutants(root: Path = Path(".")) -> list[dict[str, object]]:
    return [run_source_path_mutant(root, spec) for spec in PATH_MUTATION_SPECS]
