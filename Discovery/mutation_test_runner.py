"""Isolated unittest runner used only inside disposable mutation worktrees."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys
import traceback
import types
import unittest
from typing import Iterable, Mapping


def validate_import_paths(
    mutation_root: Path,
    modules: Mapping[str, types.ModuleType],
    *,
    required_module_names: Iterable[str],
) -> dict[str, str]:
    """Prove imported project/test modules resolve underneath the mutation root."""

    root = mutation_root.resolve()
    required = set(required_module_names)
    missing = required - set(modules)
    if missing:
        raise RuntimeError(f"required mutated modules were not imported: {sorted(missing)}")

    resolved: dict[str, str] = {}
    for name, module in sorted(modules.items()):
        if not (
            name == "Discovery"
            or name.startswith("Discovery.")
            or name == "tests"
            or name.startswith("tests.")
        ):
            continue
        file_value = getattr(module, "__file__", None)
        if file_value is None:
            continue
        module_path = Path(file_value).resolve()
        if not module_path.is_relative_to(root):
            raise RuntimeError(
                f"import-path integrity failure: {name} resolved outside mutation root"
            )
        resolved[name] = str(module_path.relative_to(root))
    for name in required:
        if name not in resolved:
            raise RuntimeError(f"required module has no validated file path: {name}")
    return resolved


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mutation-root", type=Path, required=True)
    parser.add_argument("--required-module", action="append", default=[])
    parser.add_argument("test_name", nargs="+")
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        suite = unittest.defaultTestLoader.loadTestsFromNames(args.test_name)
        if unittest.defaultTestLoader.errors:
            raise RuntimeError(
                "test collection failed: "
                + " | ".join(unittest.defaultTestLoader.errors)
            )
        imported_before = validate_import_paths(
            args.mutation_root,
            sys.modules,
            required_module_names=args.required_module,
        )
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        imported_after = validate_import_paths(
            args.mutation_root,
            sys.modules,
            required_module_names=args.required_module,
        )
        record = {
            "runner_status": "completed",
            "tests_run": result.testsRun,
            "failing_tests": sorted(test.id() for test, _ in result.failures),
            "error_tests": sorted(test.id() for test, _ in result.errors),
            "skipped_tests": sorted(test.id() for test, _ in result.skipped),
            "successful": result.wasSuccessful(),
            "validated_imports_before": imported_before,
            "validated_imports_after": imported_after,
            "test_output": stream.getvalue(),
        }
    except BaseException as error:
        record = {
            "runner_status": "invalid",
            "infrastructure_error": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
        }
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
