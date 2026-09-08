"""Bounded mutations for Newman 2014 multi-resolution terminal constraints."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import newman_2014_multiresolution_rounding_consistency as m

DEFAULT_OUTPUT = m.DIRECTORY / "newman_2014_multiresolution_mutations_v1.json"
PRIMITIVE_PATH = "Discovery/multiresolution_rounding.py"
MODULE_PATH = "Discovery/newman_2014_multiresolution_rounding_consistency.py"
TEST_PATH = "tests/test_newman_2014_multiresolution_rounding_consistency.py"
TEST_PREFIX = (
    "tests.test_newman_2014_multiresolution_rounding_consistency."
    "NewmanMultiResolutionBehaviorTests."
)
ATTESTED_PATHS = m.SOURCE_PATHS + (
    PRIMITIVE_PATH,
    MODULE_PATH,
    "Discovery/newman_2014_multiresolution_mutations.py",
    TEST_PATH,
    "tests/test_newman_2014_multiresolution_mutations.py",
    "Discovery/mutation_test_runner.py",
)
ATTESTED_PATHS = tuple(dict.fromkeys(ATTESTED_PATHS))
COPY_PATHS = ATTESTED_PATHS + ("Discovery/__init__.py",)


def case(identifier, category, path, old, new, test, expected="KILLED"):
    return {
        "id": identifier,
        "category": category,
        "path": path,
        "old": old,
        "new": new,
        "tests": [TEST_PREFIX + test],
        "expected": expected,
    }


CASES = (
    case(
        "calibration_killable_degenerate_boundary",
        "calibration",
        PRIMITIVE_PATH,
        "return None if high < low else Interval(low, high)",
        "return None if high <= low else Interval(low, high)",
        "test_degenerate_joint_interval_is_unresolved",
    ),
    case(
        "calibration_equivalent_fraction_width",
        "calibration",
        PRIMITIVE_PATH,
        "return interval.high - interval.low",
        "return Fraction(interval.high - interval.low)",
        "test_exact_joint_intervals_and_resolution_widths",
        "SURVIVED",
    ),
    case(
        "widen_intersection_with_maximum_high",
        "production",
        PRIMITIVE_PATH,
        "high = min(interval.high for interval in intervals)",
        "high = max(interval.high for interval in intervals)",
        "test_exact_joint_intervals_and_resolution_widths",
    ),
    case(
        "ignore_coarse_resolution_constraint",
        "production",
        MODULE_PATH,
        'for item in attestation["terminal_representations"][scope]',
        'for item in attestation["terminal_representations"][scope][:1]',
        "test_exact_joint_intervals_and_resolution_widths",
    ),
    case(
        "disjoint_terminals_demoted_to_unresolved",
        "production",
        PRIMITIVE_PATH,
        'return "incompatible", None, "terminal_constraints_disjoint", None',
        'return "unresolved", None, "terminal_constraints_disjoint", None',
        "test_disjoint_terminal_constraints_are_incompatible",
    ),
    case(
        "degenerate_terminal_promoted_compatible",
        "production",
        PRIMITIVE_PATH,
        'return "unresolved", None, "degenerate_joint_terminal", joint',
        'return "compatible", 0, "degenerate_joint_terminal", joint',
        "test_degenerate_joint_interval_is_unresolved",
    ),
    case(
        "component_half_width_replaced_by_terminal_width",
        "production",
        MODULE_PATH,
        "half_width = j.decimal_fraction(component_half_width_ppm)",
        'half_width = j.decimal_fraction("0.5")',
        "test_component_half_width_parameter_controls_domain",
    ),
    case(
        "erase_model_relative_negative_qualifier",
        "production",
        MODULE_PATH,
        '"incompatible": "not_representable_under_the_declared_multiresolution_reporting_model"',
        '"incompatible": "not_representable"',
        "test_model_relative_labels_and_known_prior_status",
    ),
    case(
        "erase_multiresolution_narrowing_report",
        "production",
        MODULE_PATH,
        '"narrowed_by_multiresolution_constraint": joint_width < table11_width',
        '"narrowed_by_multiresolution_constraint": False',
        "test_exact_joint_intervals_and_resolution_widths",
    ),
)


def production_cases():
    return tuple(c for c in CASES if c["category"] == "production")


def calibration_cases():
    return tuple(c for c in CASES if c["category"] == "calibration")


def mutation_tuple(definition: dict) -> tuple:
    return definition["path"], definition["old"], definition["new"]


def source_map(root: Path) -> dict[str, str]:
    return {
        path: (root / path).read_text()
        for path in (PRIMITIVE_PATH, MODULE_PATH)
    }


def validate_definitions(sources: dict[str, str]) -> None:
    production = production_cases()
    calibration = calibration_cases()
    if (
        len(calibration) != 2
        or len(production) != 7
        or len({c["id"] for c in CASES}) != len(CASES)
    ):
        raise m.j.RoundingError("multi-resolution mutation family inventory malformed")
    production_tuples = {mutation_tuple(c) for c in production}
    production_tests = {test for c in production for test in c["tests"]}
    if (
        mutation_tuple(calibration[0]) in production_tuples
        or calibration[0]["tests"][0] in production_tests
    ):
        raise m.j.RoundingError("killable calibration must be distinct from production")
    changed_hashes = []
    for definition in CASES:
        source = sources.get(definition["path"])
        if (
            source is None
            or definition["old"] == definition["new"]
            or source.count(definition["old"]) != 1
            or not definition["tests"]
            or any(not test.startswith(TEST_PREFIX) for test in definition["tests"])
        ):
            raise m.j.RoundingError("invalid, nonunique, or nonbehavioral mutation definition")
        changed_hashes.append(
            m.digest(source.replace(definition["old"], definition["new"]).encode())
        )
    if len(set(changed_hashes)) != len(CASES):
        raise m.j.RoundingError("multi-resolution mutation byte-images are not distinct")


def assess_execution(record: dict, tests: list[str]) -> str:
    if (
        record.get("runner_status") != "completed"
        or record.get("tests_run") != len(tests)
        or record.get("error_tests")
        or record.get("skipped_tests")
        or not isinstance(record.get("failing_tests"), list)
        or not set(record["failing_tests"]).issubset(tests)
        or any(
            marker in record.get("test_output", "")
            for marker in (
                "source_state_violated",
                "commit multi-resolution result-driving source",
                "SyntaxError",
                "ImportError",
            )
        )
    ):
        raise m.j.RoundingError("invalid multi-resolution mutation execution; not a kill")
    required = {
        "Discovery.multiresolution_rounding": PRIMITIVE_PATH,
        "Discovery.newman_2014_multiresolution_rounding_consistency": MODULE_PATH,
    }
    for key in ("validated_imports_before", "validated_imports_after"):
        imports = record.get(key, {})
        if any(imports.get(module) != path for module, path in required.items()):
            raise m.j.RoundingError("multi-resolution mutation import binding missing")
    failures = bool(record["failing_tests"])
    if record.get("successful") is not (not failures):
        raise m.j.RoundingError("multi-resolution mutation evidence contradicts itself")
    return "KILLED" if failures else "SURVIVED"


def run_case(root: Path, definition: dict, *, mutate=True) -> dict:
    with TemporaryDirectory(prefix="newman-multires-mutant-") as temp:
        target = Path(temp)
        for path in COPY_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        source_path = target / (definition.get("path") or MODULE_PATH)
        source = source_path.read_text()
        if mutate:
            if source.count(definition["old"]) != 1:
                raise m.j.RoundingError("multi-resolution mutation patch is not unique")
            source = source.replace(definition["old"], definition["new"])
            source_path.write_text(source)
        bootstrap = (
            "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
            "runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')"
        )
        command = [
            sys.executable, "-I", "-B", "-c", bootstrap, str(target),
            "--mutation-root", str(target),
            "--required-module", "Discovery.multiresolution_rounding",
            "--required-module", "Discovery.newman_2014_multiresolution_rounding_consistency",
            *definition["tests"],
        ]
        process = subprocess.run(
            command,
            cwd=target,
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
            timeout=60,
        )
        if process.returncode:
            raise m.j.RoundingError("multi-resolution mutation runner process failed")
        evidence = json.loads(process.stdout)
        outcome = assess_execution(evidence, definition["tests"])
        stable = {
            key: evidence[key]
            for key in (
                "runner_status", "tests_run", "failing_tests", "error_tests",
                "skipped_tests", "successful", "validated_imports_before",
                "validated_imports_after",
            )
        }
        return {
            "id": definition["id"],
            "category": definition["category"],
            "path": definition.get("path"),
            "tests": definition["tests"],
            "expected": definition["expected"],
            "outcome": outcome,
            "applied_source_sha256": m.digest(source.encode()),
            "evidence": stable,
        }


def baseline_definition() -> dict:
    return {
        "id": "unmutated_baseline",
        "category": "baseline",
        "path": None,
        "expected": "SURVIVED",
        "tests": sorted({test for definition in CASES for test in definition["tests"]}),
    }


def validate_records(records: list, sources: dict[str, str]) -> None:
    definitions = (baseline_definition(),) + CASES
    if not isinstance(records, list) or len(records) != len(definitions):
        raise m.j.RoundingError("incomplete multi-resolution mutation inventory")
    for definition, record in zip(definitions, records):
        if any(
            record.get(key) != definition[key]
            for key in ("id", "category", "path", "tests", "expected")
        ):
            raise m.j.RoundingError("multi-resolution mutation inventory differs")
        if definition["category"] == "baseline":
            expected_hash = m.digest(sources[MODULE_PATH].encode())
        else:
            source = sources[definition["path"]]
            expected_hash = m.digest(
                source.replace(definition["old"], definition["new"]).encode()
            )
        if record.get("applied_source_sha256") != expected_hash:
            raise m.j.RoundingError("applied multi-resolution mutation source hash differs")
        outcome = assess_execution(record["evidence"], definition["tests"])
        if outcome != record.get("outcome") or outcome != definition["expected"]:
            raise m.j.RoundingError("multi-resolution mutation survived or calibration invalid")


def definitions_hash() -> str:
    return m.digest(m.serialize_artifact(CASES).encode())


def envelope(snapshot: dict, records: list) -> dict:
    production_count = len(production_cases())
    calibration = [record for record in records if record["category"] == "calibration"]
    production = [record for record in records if record["category"] == "production"]
    calibration_valid = all(
        record["outcome"] == record["expected"] for record in calibration
    )
    production_valid = (
        len(production) == production_count
        and all(record["outcome"] == "KILLED" for record in production)
    )
    return {
        "schema_version": 1,
        "artifact_id": "newman_2014_multiresolution_mutations_v1",
        "source_snapshot": snapshot,
        "definitions_sha256": definitions_hash(),
        "preregistration_sha256": m.PREREGISTRATION_SHA256,
        "family_status": "valid" if calibration_valid and production_valid else "invalid",
        "calibration_valid": calibration_valid,
        "production_count": production_count,
        "records": records,
        "scope": "Multi-resolution terminal intersection, strict-boundary semantics, isolation, and width reporting.",
        "anti_false_kill_rule": (
            "Named assertion failures only; infrastructure, import, syntax, skip, "
            "and source-freshness failures are invalid."
        ),
    }


def run_mutations(root: Path = m.ROOT) -> dict:
    m.verify_preregistration(root)
    m.verify_preserved_files(root)
    sources = source_map(root)
    validate_definitions(sources)
    snapshot = m.source_snapshot(root, ATTESTED_PATHS)
    records = [run_case(root, baseline_definition(), mutate=False)]
    if records[0]["outcome"] != "SURVIVED":
        raise m.j.RoundingError("unmutated multi-resolution behavioral baseline failed")
    records += [run_case(root, definition) for definition in CASES]
    validate_records(records, sources)
    artifact = envelope(snapshot, records)
    if artifact["family_status"] != "valid":
        raise m.j.RoundingError("multi-resolution mutation family invalid")
    return artifact


def verify_artifact(artifact: dict, root: Path = m.ROOT) -> None:
    m.verify_preregistration(root)
    sources = source_map(root)
    validate_definitions(sources)
    validate_records(artifact["records"], sources)
    expected = envelope(m.source_snapshot(root, ATTESTED_PATHS), artifact["records"])
    if artifact != expected or artifact["family_status"] != "valid":
        raise m.j.RoundingError("multi-resolution mutation evidence is stale")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.check:
        verify_artifact(m.read_json((m.ROOT / DEFAULT_OUTPUT).read_bytes()))
        print(
            f"Newman multi-resolution mutation evidence verified: "
            f"{len(production_cases())} production kills, valid calibration"
        )
    else:
        artifact = run_mutations()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(m.serialize_artifact(artifact))
        print(
            f"Newman multi-resolution mutations: {len(production_cases())}/"
            f"{len(production_cases())} production killed; calibration correct"
        )


if __name__ == "__main__":
    main()
