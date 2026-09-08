"""Bounded mutations for the BIPM 2014 correlated two-method estimator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import bipm_2014_correlated_estimator as m


DEFAULT_OUTPUT = m.DIRECTORY / "bipm_2014_correlated_estimator_mutations_v1.json"
PRIMITIVE_PATH = "Discovery/correlated_weighted_mean.py"
MODULE_PATH = "Discovery/bipm_2014_correlated_estimator.py"
TEST_PATH = "tests/test_bipm_2014_correlated_estimator.py"
TEST_PREFIX = "tests.test_bipm_2014_correlated_estimator.BIPMCorrelatedEstimatorBehaviorTests."
ATTESTED_PATHS = m.SOURCE_PATHS + (
    PRIMITIVE_PATH,
    MODULE_PATH,
    "Discovery/bipm_2014_correlated_estimator_mutations.py",
    TEST_PATH,
    "tests/test_bipm_2014_correlated_estimator_mutations.py",
    "Discovery/mutation_test_runner.py",
    "Discovery/preregistration_history.py",
    "Discovery/source_history.py",
)
ATTESTED_PATHS = tuple(dict.fromkeys(ATTESTED_PATHS))
COPY_PATHS = (
    PRIMITIVE_PATH,
    MODULE_PATH,
    TEST_PATH,
    "Discovery/mutation_test_runner.py",
    "Discovery/preregistration_history.py",
    "Discovery/source_history.py",
    "Discovery/__init__.py",
)


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
        "calibration_killable_half_width",
        "calibration",
        PRIMITIVE_PATH,
        "half_width = Fraction(1, 2 * (10 ** places))",
        "half_width = Fraction(1, 4 * (10 ** places))",
        "test_decimal_cells_and_sign_aware_linear_enclosure",
    ),
    case(
        "calibration_equivalent_fraction_wrap",
        "calibration",
        PRIMITIVE_PATH,
        "return Fraction(number)",
        "return Fraction(Fraction(number))",
        "test_exact_minimum_variance_weights_and_sum",
        "SURVIVED",
    ),
    case(
        "erase_covariance_from_combined_variance",
        "production",
        PRIMITIVE_PATH,
        "+ 2 * first * second * covariance",
        "+ 0 * first * second * covariance",
        "test_exact_minimum_variance_weights_and_sum",
    ),
    case(
        "flip_covariance_sign_in_servo_weight",
        "production",
        PRIMITIVE_PATH,
        "first = (variance_second - covariance) / denominator",
        "first = (variance_second + covariance) / denominator",
        "test_exact_minimum_variance_weights_and_sum",
    ),
    case(
        "replace_covariance_with_zero",
        "production",
        MODULE_PATH,
        "covariance = decimal_fraction(source[\"covariance_ppm_squared\"][\"value\"])",
        "covariance = Fraction(0)",
        "test_real_source_midpoint_and_enclosure_are_distinct",
    ),
    case(
        "use_printed_weights_for_enclosure",
        "production",
        MODULE_PATH,
        "(servo_cell, cavendish_cell), (weights.first, weights.second)",
        "(servo_cell, cavendish_cell), (decimal_fraction(protocol[\"source_projection\"][\"comparison_only\"][\"printed_servo_weight\"]), decimal_fraction(protocol[\"source_projection\"][\"comparison_only\"][\"printed_cavendish_weight\"]))",
        "test_target_and_printed_summary_invariance",
    ),
    case(
        "leak_printed_combined_uncertainty_into_covariance",
        "production",
        MODULE_PATH,
        "covariance = decimal_fraction(source[\"covariance_ppm_squared\"][\"value\"])",
        "covariance = decimal_fraction(source[\"covariance_ppm_squared\"][\"value\"]) + decimal_fraction(protocol[\"source_projection\"][\"comparison_only\"][\"printed_combined_relative_uncertainty_ppm\"]) / Fraction(1000)",
        "test_target_and_printed_summary_invariance",
    ),
    case(
        "collapse_input_rounding_cells_to_midpoints",
        "production",
        PRIMITIVE_PATH,
        "half_width = Fraction(1, 2 * (10 ** places))",
        "half_width = Fraction(0)",
        "test_real_source_midpoint_and_enclosure_are_distinct",
    ),
    case(
        "corrupt_positive_weight_lower_enclosure_extremum",
        "production",
        PRIMITIVE_PATH,
        "low += weight * interval.low",
        "low += weight * interval.high",
        "test_real_source_midpoint_and_enclosure_are_distinct",
    ),
    case(
        "erase_model_relative_incompatible_qualifier",
        "production",
        MODULE_PATH,
        "status = \"not_representable_under_the_declared_bipm_2014_correlated_weighted_mean_model\"",
        "status = \"not_representable\"",
        "test_synthetic_compatible_and_incompatible_classification",
    ),
)


def production_cases():
    return tuple(c for c in CASES if c["category"] == "production")


def calibration_cases():
    return tuple(c for c in CASES if c["category"] == "calibration")


def source_map(root: Path) -> dict[str, str]:
    return {path: (root / path).read_text() for path in (PRIMITIVE_PATH, MODULE_PATH)}


def validate_definitions(sources: dict[str, str], protocol: dict | None = None) -> None:
    production = production_cases()
    calibration = calibration_cases()
    if len(calibration) != 2 or len({c["id"] for c in CASES}) != len(CASES):
        raise m.BIPMEstimatorError("BIPM mutation family inventory malformed")
    if protocol is not None and len(production) != len(protocol["mutation_requirements"]):
        raise m.BIPMEstimatorError("BIPM production mutation count differs from frozen requirements")
    images = []
    for definition in CASES:
        source = sources.get(definition["path"])
        if (
            source is None
            or definition["old"] == definition["new"]
            or source.count(definition["old"]) != 1
            or not definition["tests"]
            or any(not test.startswith(TEST_PREFIX) for test in definition["tests"])
        ):
            raise m.BIPMEstimatorError("invalid or nonunique BIPM mutation definition")
        images.append(m.digest(source.replace(definition["old"], definition["new"]).encode()))
    if len(set(images)) != len(CASES):
        raise m.BIPMEstimatorError("BIPM mutation byte-images are not distinct")
    killable = calibration[0]
    if any(
        killable["path"] == p["path"]
        and killable["old"] == p["old"]
        and killable["new"] == p["new"]
        for p in production
    ) or killable["tests"][0] in {t for p in production for t in p["tests"]}:
        raise m.BIPMEstimatorError("killable calibration must be distinct from production")


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
            for marker in ("SyntaxError", "ImportError", "source_state_violated")
        )
    ):
        raise m.BIPMEstimatorError("invalid BIPM mutation execution; not a kill")
    required = {
        "Discovery.correlated_weighted_mean": PRIMITIVE_PATH,
        "Discovery.bipm_2014_correlated_estimator": MODULE_PATH,
    }
    for key in ("validated_imports_before", "validated_imports_after"):
        imports = record.get(key, {})
        if any(imports.get(module) != path for module, path in required.items()):
            raise m.BIPMEstimatorError("BIPM mutation import binding missing")
    failures = bool(record["failing_tests"])
    if record.get("successful") is not (not failures):
        raise m.BIPMEstimatorError("BIPM mutation evidence contradicts itself")
    return "KILLED" if failures else "SURVIVED"


def run_case(root: Path, definition: dict, *, mutate=True) -> dict:
    with TemporaryDirectory(prefix="bipm-correlated-mutant-") as temp:
        target = Path(temp)
        for path in COPY_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        source_path = target / (definition.get("path") or MODULE_PATH)
        source = source_path.read_text()
        if mutate:
            if source.count(definition["old"]) != 1:
                raise m.BIPMEstimatorError("BIPM mutation patch is not unique")
            source = source.replace(definition["old"], definition["new"])
            source_path.write_text(source)
        bootstrap = (
            "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));"
            "runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')"
        )
        command = [
            sys.executable, "-I", "-B", "-c", bootstrap, str(target),
            "--mutation-root", str(target),
            "--required-module", "Discovery.correlated_weighted_mean",
            "--required-module", "Discovery.bipm_2014_correlated_estimator",
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
            raise m.BIPMEstimatorError("BIPM mutation runner process failed")
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
        raise m.BIPMEstimatorError("incomplete BIPM mutation inventory")
    for definition, record in zip(definitions, records):
        if any(record.get(key) != definition[key] for key in ("id", "category", "path", "tests", "expected")):
            raise m.BIPMEstimatorError("BIPM mutation inventory differs")
        if definition["category"] == "baseline":
            expected_hash = m.digest(sources[MODULE_PATH].encode())
        else:
            source = sources[definition["path"]]
            expected_hash = m.digest(source.replace(definition["old"], definition["new"]).encode())
        if record.get("applied_source_sha256") != expected_hash:
            raise m.BIPMEstimatorError("applied BIPM mutation source hash differs")
        outcome = assess_execution(record["evidence"], definition["tests"])
        if outcome != record.get("outcome") or outcome != definition["expected"]:
            raise m.BIPMEstimatorError("BIPM mutation survived or calibration invalid")


def definitions_hash() -> str:
    return m.digest(m.serialize_artifact(CASES).encode())


def source_snapshot(root: Path = m.ROOT) -> dict:
    commit = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", *ATTESTED_PATHS],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    files = []
    for path in ATTESTED_PATHS:
        current = (root / path).read_bytes()
        recorded = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True)
        if recorded.returncode or recorded.stdout != current:
            raise m.BIPMEstimatorError("commit BIPM mutation-driving source before artifact emission")
        files.append({"path": path, "sha256": m.digest(current)})
    return {"source_commit_sha": commit, "files": files}


def envelope(snapshot: dict, records: list) -> dict:
    production = [record for record in records if record["category"] == "production"]
    calibration = [record for record in records if record["category"] == "calibration"]
    return {
        "schema_version": 1,
        "artifact_id": "bipm_2014_correlated_estimator_mutations_v1",
        "scope": "covariance-driven weights, target independence, finite-resolution enclosure, and model-relative classification",
        "preregistration_sha256": m.PREREGISTRATION_SHA256,
        "definitions_sha256": definitions_hash(),
        "source_snapshot": snapshot,
        "anti_false_kill_rule": "Only named assertion failures count; import, syntax, infrastructure, skip, and source-state failures are invalid.",
        "production_count": len(production_cases()),
        "calibration_valid": all(record["outcome"] == record["expected"] for record in calibration),
        "family_status": "valid" if all(record["outcome"] == "KILLED" for record in production) else "invalid",
        "records": records,
    }


def build_artifact(root: Path = m.ROOT) -> dict:
    protocol = m.verify_preregistration(root)
    sources = source_map(root)
    validate_definitions(sources, protocol)
    records = [run_case(root, baseline_definition(), mutate=False)]
    records.extend(run_case(root, definition) for definition in CASES)
    validate_records(records, sources)
    artifact = envelope(source_snapshot(root), records)
    if not artifact["calibration_valid"] or artifact["family_status"] != "valid":
        raise m.BIPMEstimatorError("BIPM mutation family invalid")
    return artifact


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        protocol = m.verify_preregistration()
        sources = source_map(m.ROOT)
        validate_definitions(sources, protocol)
        if args.check:
            artifact = json.loads((m.ROOT / DEFAULT_OUTPUT).read_text())
            if artifact.get("definitions_sha256") != definitions_hash():
                raise m.BIPMEstimatorError("BIPM mutation definitions changed")
            if artifact.get("source_snapshot") != source_snapshot(m.ROOT):
                raise m.BIPMEstimatorError("BIPM mutation source snapshot changed")
            validate_records(artifact.get("records"), sources)
            if not artifact.get("calibration_valid") or artifact.get("family_status") != "valid":
                raise m.BIPMEstimatorError("BIPM mutation artifact invalid")
            print("BIPM 2014 correlated estimator mutation family verified")
        else:
            artifact = build_artifact()
            text = m.serialize_artifact(artifact)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text)
            else:
                print(text, end="")
    except (m.BIPMEstimatorError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as error:
        print(f"bipm_2014_correlated_estimator_mutations_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
