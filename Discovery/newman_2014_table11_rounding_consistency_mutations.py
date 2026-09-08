"""Bounded behavioral mutations for the Newman 2014 Table 11 rounding audit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import newman_2014_table11_rounding_consistency as j

DEFAULT_OUTPUT = j.DIRECTORY / "newman_2014_table11_rounding_consistency_mutations_v1.json"
MODULE_PATH = "Discovery/newman_2014_table11_rounding_consistency.py"
TEST_PATH = "tests/test_newman_2014_table11_rounding_consistency.py"
TEST_PREFIX = "tests.test_newman_2014_table11_rounding_consistency.NewmanBehaviorTests."
ATTESTED_PATHS = j.SOURCE_PATHS + (
    "Discovery/newman_2014_table11_rounding_consistency_mutations.py",
    TEST_PATH,
    "tests/test_newman_2014_table11_rounding_consistency_mutations.py",
    "Discovery/mutation_test_runner.py",
)
COPY_PATHS = ATTESTED_PATHS + (
    "Discovery/rounding_consistency.py",
    "Discovery/__init__.py",
    "Discovery/preregistration_history.py",
    "Discovery/source_history.py",
)


def case(identifier, category, old, new, test, expected="KILLED"):
    return {
        "id": identifier, "category": category, "path": MODULE_PATH,
        "old": old, "new": new, "tests": [TEST_PREFIX + test], "expected": expected,
    }


CASES = (
    case(
        "calibration_killable_schedule_order", "calibration",
        "return parameters",
        "return tuple(reversed(parameters))",
        "test_schedule_order_freeze",
    ),
    case(
        "calibration_equivalent_tuple_materialization", "calibration",
        'parameters = tuple(Fraction(value) for value in schedule["parameters"])',
        'parameters = tuple(list(Fraction(value) for value in schedule["parameters"]))',
        "test_tensor_schedule_and_independent_coordinates", "SURVIVED",
    ),
    case(
        "collapse_second_tensor_coordinate", "production",
        "for coordinates in product(parameters, repeat=3):",
        "for coordinates in ((a, a, c) for a, b, c in product(parameters, repeat=3)):",
        "test_tensor_schedule_and_independent_coordinates",
    ),
    case(
        "ignore_third_scope", "production",
        "for scope in SCOPES}",
        "for scope in SCOPES[:2]}",
        "test_all_three_published_scopes_are_required",
    ),
    case(
        "terminal_resolution_leaks_into_components", "production",
        'half = decimal_fraction(rounding_policy["component_half_width_ppm"])',
        'half = decimal_fraction(rounding_policy["terminal_half_width_ppm"])',
        "test_terminal_resolution_cannot_drive_candidate_generation",
    ),
    case(
        "widen_component_rounding_bin", "production",
        'rounding_bin(decimal_fraction(row["value_ppm"]), half_width)',
        'rounding_bin(decimal_fraction(row["value_ppm"]), half_width * 10)',
        "test_component_rounding_bin_is_exact",
    ),
    case(
        "unresolved_promoted_true", "production",
        '"unresolved": "undetermined_under_the_frozen_tensor_schedule"',
        '"unresolved": "representable_under_the_declared_table11_rounding_model"',
        "test_synthetic_incompatible_and_unresolved_statuses",
    ),
    case(
        "incompatible_promoted_unresolved", "production",
        "outcome, index = classify(calculation, comparison)",
        'outcome, index = classify(calculation, comparison)\n'
        '        if outcome == "incompatible":\n'
        '            outcome, index = "unresolved", None',
        "test_synthetic_incompatible_and_unresolved_statuses",
    ),
    case(
        "erase_model_relative_negative_qualifier", "production",
        '"incompatible": "not_representable_under_the_declared_table11_rounding_model"',
        '"incompatible": "not_representable"',
        "test_model_relative_negative_label",
    ),
    case(
        "central_G_affects_truth", "production",
        "outcome, index = classify(calculation, comparison)\n        witness = None",
        'outcome, index = classify(calculation, comparison)\n'
        '        if calculation.budget.central_values[0] > Fraction(1, 10**8):\n'
        '            outcome, index = "incompatible", None\n'
        '        witness = None',
        "test_central_value_cannot_affect_variance_or_truth",
    ),
)


def production_cases():
    return tuple(c for c in CASES if c["category"] == "production")


def calibration_cases():
    return tuple(c for c in CASES if c["category"] == "calibration")


def mutation_tuple(definition: dict) -> tuple:
    return definition["path"], definition["old"], definition["new"]


def validate_definitions(source: str) -> None:
    production = production_cases()
    calibration = calibration_cases()
    if (len(calibration) != 2 or not production
            or len({c["id"] for c in CASES}) != len(CASES)):
        raise j.RoundingError("mutation family inventory malformed")
    production_tuples = {mutation_tuple(c) for c in production}
    production_tests = {test for c in production for test in c["tests"]}
    if (mutation_tuple(calibration[0]) in production_tuples
            or calibration[0]["tests"][0] in production_tests):
        raise j.RoundingError("killable calibration must be distinct from production")
    changed_hashes = []
    for definition in CASES:
        if (definition["path"] != MODULE_PATH
                or definition["old"] == definition["new"]
                or source.count(definition["old"]) != 1
                or not definition["tests"]
                or any(not test.startswith(TEST_PREFIX) for test in definition["tests"])):
            raise j.RoundingError("invalid, nonunique, or nonbehavioral mutation definition")
        changed_hashes.append(j.digest(source.replace(
            definition["old"], definition["new"]).encode()))
    if len(set(changed_hashes)) != len(CASES):
        raise j.RoundingError("mutation byte-images are not distinct")


def assess_execution(record: dict, tests: list[str]) -> str:
    """Only named unittest assertion failures count; infrastructure never counts."""
    if (record.get("runner_status") != "completed"
            or record.get("tests_run") != len(tests)
            or record.get("error_tests")
            or record.get("skipped_tests")
            or not isinstance(record.get("failing_tests"), list)
            or not set(record["failing_tests"]).issubset(tests)
            or any(marker in record.get("test_output", "") for marker in (
                "source_state_violated", "commit result-driving source",
                "SyntaxError", "ImportError",
            ))):
        raise j.RoundingError("invalid mutation execution; not a kill")
    module = MODULE_PATH[:-3].replace("/", ".")
    for key in ("validated_imports_before", "validated_imports_after"):
        if record.get(key, {}).get(module) != MODULE_PATH:
            raise j.RoundingError("mutation import binding missing")
    failures = bool(record["failing_tests"])
    if record.get("successful") is not (not failures):
        raise j.RoundingError("mutation success/failure evidence contradicts itself")
    return "KILLED" if failures else "SURVIVED"


def run_case(root: Path, definition: dict, *, mutate=True) -> dict:
    with TemporaryDirectory(prefix="newman-table11-mutant-") as temp:
        target = Path(temp)
        for path in COPY_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        source_path = target / MODULE_PATH
        source = source_path.read_text()
        if mutate:
            if source.count(definition["old"]) != 1:
                raise j.RoundingError("mutation patch is not unique")
            source = source.replace(definition["old"], definition["new"])
            source_path.write_text(source)
        bootstrap = (
            "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
            "runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')"
        )
        command = [
            sys.executable, "-I", "-B", "-c", bootstrap, str(target),
            "--mutation-root", str(target), "--required-module",
            "Discovery.newman_2014_table11_rounding_consistency",
            *definition["tests"],
        ]
        process = subprocess.run(
            command, cwd=target, capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=60,
        )
        if process.returncode:
            raise j.RoundingError("mutation runner process failed")
        evidence = json.loads(process.stdout)
        outcome = assess_execution(evidence, definition["tests"])
        stable = {key: evidence[key] for key in (
            "runner_status", "tests_run", "failing_tests", "error_tests",
            "skipped_tests", "successful", "validated_imports_before",
            "validated_imports_after",
        )}
        return {
            "id": definition["id"], "category": definition["category"],
            "tests": definition["tests"], "expected": definition["expected"],
            "outcome": outcome, "applied_source_sha256": j.digest(source.encode()),
            "evidence": stable,
        }


def baseline_definition() -> dict:
    return {
        "id": "unmutated_baseline", "category": "baseline", "expected": "SURVIVED",
        "tests": sorted({test for definition in CASES for test in definition["tests"]}),
    }


def validate_records(records: list, source: str) -> None:
    definitions = (baseline_definition(),) + CASES
    if not isinstance(records, list) or len(records) != len(definitions):
        raise j.RoundingError("incomplete mutation inventory")
    for definition, record in zip(definitions, records):
        if any(record.get(key) != definition[key]
               for key in ("id", "category", "tests", "expected")):
            raise j.RoundingError("mutation definition/evidence inventory differs")
        expected_source = (
            source if definition["category"] == "baseline"
            else source.replace(definition["old"], definition["new"])
        )
        if record.get("applied_source_sha256") != j.digest(expected_source.encode()):
            raise j.RoundingError("applied mutation source hash differs")
        outcome = assess_execution(record["evidence"], definition["tests"])
        if outcome != record.get("outcome") or outcome != definition["expected"]:
            raise j.RoundingError("mutation survived or calibration invalid")


def definitions_hash() -> str:
    return j.digest(j.serialize_artifact(CASES).encode())


def envelope(snapshot: dict, records: list) -> dict:
    production_count = len(production_cases())
    calibration = [record for record in records if record["category"] == "calibration"]
    production = [record for record in records if record["category"] == "production"]
    calibration_valid = all(record["outcome"] == record["expected"] for record in calibration)
    production_valid = (
        len(production) == production_count
        and all(record["outcome"] == "KILLED" for record in production)
    )
    return {
        "schema_version": 1,
        "artifact_id": "newman_2014_table11_rounding_consistency_mutations_v1",
        "source_snapshot": snapshot,
        "definitions_sha256": definitions_hash(),
        "preregistration_sha256": j.PREREGISTRATION_SHA256,
        "family_status": "valid" if calibration_valid and production_valid else "invalid",
        "calibration_valid": calibration_valid,
        "production_count": production_count,
        "records": records,
        "scope": "Newman Table 11 tensor schedule, rounding boundary, and three-scope classification only.",
        "anti_false_kill_rule": (
            "Named assertion failures only; infrastructure, import, syntax, skip, "
            "and source-freshness failures are invalid."
        ),
    }


def run_mutations(root: Path = j.ROOT) -> dict:
    j.verify_preregistration(root)
    j.verify_preserved_files(root)
    source = (root / MODULE_PATH).read_text()
    validate_definitions(source)
    snapshot = j.source_snapshot(root, ATTESTED_PATHS)
    records = [run_case(root, baseline_definition(), mutate=False)]
    if records[0]["outcome"] != "SURVIVED":
        raise j.RoundingError("unmutated behavioral baseline failed")
    records += [run_case(root, definition) for definition in CASES]
    validate_records(records, source)
    artifact = envelope(snapshot, records)
    if artifact["family_status"] != "valid":
        raise j.RoundingError("mutation family calibration or production status invalid")
    return artifact


def verify_artifact(artifact: dict, root: Path = j.ROOT) -> None:
    j.verify_preregistration(root)
    source = (root / MODULE_PATH).read_text()
    validate_definitions(source)
    validate_records(artifact["records"], source)
    expected = envelope(j.source_snapshot(root, ATTESTED_PATHS), artifact["records"])
    if artifact != expected or artifact["family_status"] != "valid":
        raise j.RoundingError("mutation source or summary evidence is stale")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.check:
        verify_artifact(j.read_json((j.ROOT / DEFAULT_OUTPUT).read_bytes()))
        print(
            f"Newman Table 11 mutation evidence verified: "
            f"{len(production_cases())} production kills, valid calibration"
        )
    else:
        artifact = run_mutations()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(j.serialize_artifact(artifact))
        print(
            f"Newman Table 11 mutations: {len(production_cases())}/"
            f"{len(production_cases())} production killed; calibration correct"
        )


if __name__ == "__main__":
    main()
