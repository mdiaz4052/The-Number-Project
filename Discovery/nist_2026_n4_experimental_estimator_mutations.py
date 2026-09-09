"""Bounded production-source mutations for the frozen NIST n=4 estimator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import nist_2026_n4_experimental_estimator as n
from Discovery.source_history import verify_committed_source_state

MODULE = "Discovery/nist_2026_n4_experimental_estimator.py"
SELF = "Discovery/nist_2026_n4_experimental_estimator_mutations.py"
TEST = "tests/test_nist_2026_n4_experimental_estimator_mutations.py"
NOTE = "Notes/NIST2026N4MutationValidation.md"
PREFIX = "tests.test_nist_2026_n4_experimental_estimator_mutations.N4MutationBehaviorTests."
OUTPUT = n.DIRECTORY / "nist_2026_n4_experimental_estimator_mutations_v1.json"
COPY_PATHS = (
    MODULE, SELF, TEST, n.PREREGISTRATION_PATH.as_posix(),
    "Discovery/__init__.py", "Discovery/mutation_test_runner.py",
    "Discovery/preregistration_history.py", "Discovery/source_history.py",
)
SOURCE_PATHS = tuple(dict.fromkeys((*n.SOURCE_PATHS, *COPY_PATHS, NOTE)))
IMPORTS = {
    "Discovery.nist_2026_n4_experimental_estimator": MODULE,
    "Discovery.nist_2026_n4_experimental_estimator_mutations": SELF,
    "tests.test_nist_2026_n4_experimental_estimator_mutations": TEST,
}


class MutationEvidenceError(ValueError):
    """Invalid execution or evidence is never a scientific mutation kill."""


def case(ident, old, new, test, requirement=None, expected="KILLED"):
    return {
        "id": ident, "category": "calibration" if requirement is None else "production",
        "requirement_index": requirement, "path": MODULE, "old": old, "new": new,
        "tests": [PREFIX + test], "expected": expected,
    }


CASES = (
    case("calibration_asymmetric_cell", "return midpoint - half_width, midpoint + half_width",
         "return midpoint - half_width, midpoint + 2 * half_width", "test_cell_calibration"),
    case("calibration_equivalent_fraction", "return Fraction(number)",
         "return Fraction(Fraction(number))", "test_equivalent_decimal_calibration", expected="SURVIVED"),
    case("erase_off_diagonal_correlations",
         "correlation[i][j] * absolute_uncertainties[i] * absolute_uncertainties[j]",
         "Fraction(i == j) * absolute_uncertainties[i] * absolute_uncertainties[j]",
         "test_correlated_weights", 0),
    case("substitute_table16_uncertainty_labels", 'relative = inputs["relative_uncertainties_ppm"]',
         'relative = tuple(Fraction(round(value)) for value in inputs["relative_uncertainties_ppm"])',
         "test_precise_uncertainties", 1),
    case("omit_absolute_covariance_scaling",
         "values[index] * relative[index] / 1_000_000 for index in range(4)",
         "relative[index] / 1_000_000 for index in range(4)", "test_absolute_scaling", 2),
    case("omit_fourth_determination", "estimate = sum(weight * value for weight, value in zip(weights, values))",
         "estimate = sum(weight * value for weight, value in zip(weights[:3], values[:3]))",
         "test_four_input_aggregate", 3),
    case("read_bayesian_target_into_estimate", "estimate = sum(weight * value for weight, value in zip(weights, values))",
         'estimate = sum(weight * value for weight, value in zip(weights, values)) + decimal_fraction(_json((ROOT / UPSTREAM_ATTESTATION_PATH).read_bytes())["authority_resolution"]["journal_pdf_result"]["G_decimal_in_1e_minus_11_units"]) / 1_000_000',
         "test_terminal_free_execution", 4),
    case("collapse_display_cells", "half_width = Fraction(1, 2 * (10 ** places))",
         "half_width = Fraction(0)", "test_resolution_box", 5),
    case("ignore_negative_weight_sign", "if weight >= 0:", "if True:", "test_signed_extrema", 6),
    case("omit_unbiased_normalization", "weights = tuple(value / normalization for value in solution)",
         "weights = tuple(solution)", "test_unbiased_normalization", 7),
)


def baseline():
    return {
        "id": "unmutated_baseline", "category": "baseline", "requirement_index": None,
        "path": MODULE, "tests": sorted({t for c in CASES for t in c["tests"]}),
        "expected": "SURVIVED",
    }


def validate_definitions(source: str, protocol: dict) -> None:
    production = [c for c in CASES if c["category"] == "production"]
    controls = [c for c in CASES if c["category"] == "calibration"]
    if [c["requirement_index"] for c in production] != list(range(len(protocol["mutation_requirements"]))):
        raise MutationEvidenceError("one production case must cover each frozen requirement in order")
    if len(controls) != 2 or [c["expected"] for c in controls] != ["KILLED", "SURVIVED"]:
        raise MutationEvidenceError("two distinct calibration controls required")
    images = set()
    for c in CASES:
        if c["path"] != MODULE or source.count(c["old"]) != 1 or c["new"] == c["old"]:
            raise MutationEvidenceError("mutation patch missing, ambiguous, or unchanged")
        if len(c["tests"]) != 1 or not c["tests"][0].startswith(PREFIX):
            raise MutationEvidenceError("only designated behavioral assertions may score")
        images.add(n.digest(source.replace(c["old"], c["new"]).encode()))
    if len(images) != len(CASES) or len({c["id"] for c in CASES}) != len(CASES):
        raise MutationEvidenceError("mutation identities and byte images must be distinct")
    if set(controls[0]["tests"]) & {t for c in production for t in c["tests"]}:
        raise MutationEvidenceError("killable calibration oracle must be separate")


def assess_execution(evidence: dict, tests: list[str]) -> str:
    required = {
        "runner_status", "tests_run", "failing_tests", "error_tests", "skipped_tests",
        "successful", "validated_imports_before", "validated_imports_after",
    }
    if not isinstance(evidence, dict) or not required <= evidence.keys():
        raise MutationEvidenceError("incomplete runner evidence")
    failures = evidence["failing_tests"]
    if (evidence["runner_status"] != "completed"
            or type(evidence["tests_run"]) is not int or evidence["tests_run"] != len(tests)
            or evidence["error_tests"] != [] or evidence["skipped_tests"] != []
            or not isinstance(failures, list) or any(t not in tests for t in failures)
            or len(set(failures)) != len(failures)
            or evidence["successful"] is not (not failures)
            or any(marker in evidence.get("test_output", "") for marker in (
                "SyntaxError", "ImportError", "ModuleNotFoundError", "source_state_violated",
                "history_unavailable", "ancestry_violated", "source_metadata_invalid"))):
        raise MutationEvidenceError("infrastructure, skip, source-state, or contradictory execution is invalid")
    for phase in ("validated_imports_before", "validated_imports_after"):
        imports = evidence[phase]
        if not isinstance(imports, dict) or any(imports.get(k) != v for k, v in IMPORTS.items()):
            raise MutationEvidenceError("isolated import bindings are missing or wrong")
    return "KILLED" if failures else "SURVIVED"


def run_case(root: Path, definition: dict) -> dict:
    """Execute one actual changed module in a disposable, import-isolated copy."""
    with TemporaryDirectory(prefix="nist-n4-mutant-") as temp:
        target = Path(temp)
        for path in COPY_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        # Prevent an installed package named tests from shadowing the isolated tests.
        (target / "tests/__init__.py").write_bytes(b"")
        source = (target / MODULE).read_text()
        if definition["category"] != "baseline":
            if source.count(definition["old"]) != 1:
                raise MutationEvidenceError("mutation patch is not unique")
            source = source.replace(definition["old"], definition["new"])
            (target / MODULE).write_text(source)
        bootstrap = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')"
        command = [sys.executable, "-I", "-B", "-c", bootstrap, str(target), "--mutation-root", str(target)]
        for module in IMPORTS:
            command.extend(["--required-module", module])
        command.extend(definition["tests"])
        execution = subprocess.run(command, cwd=target, capture_output=True, text=True,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=60)
        if execution.returncode:
            raise MutationEvidenceError("mutation subprocess failed; no kill credit")
        evidence = json.loads(execution.stdout)
        outcome = assess_execution(evidence, definition["tests"])
        stable = {key: value for key, value in evidence.items() if key != "test_output"}
        return {**{key: definition[key] for key in (
            "id", "category", "requirement_index", "path", "tests", "expected")},
            "applied_source_sha256": n.digest(source.encode()), "outcome": outcome, "evidence": stable}


def validate_records(records: list, source: str) -> None:
    definitions = (baseline(), *CASES)
    if not isinstance(records, list) or len(records) != len(definitions):
        raise MutationEvidenceError("incomplete mutation records")
    for definition, record in zip(definitions, records):
        if not isinstance(record, dict) or any(record.get(k) != definition[k] for k in (
                "id", "category", "requirement_index", "path", "tests", "expected")):
            raise MutationEvidenceError("record inventory differs from definitions")
        applied = source if definition["category"] == "baseline" else source.replace(definition["old"], definition["new"])
        if record.get("applied_source_sha256") != n.digest(applied.encode()):
            raise MutationEvidenceError("applied mutation bytes differ")
        outcome = assess_execution(record.get("evidence"), definition["tests"])
        if outcome != definition["expected"] or record.get("outcome") != outcome:
            raise MutationEvidenceError("production survivor or invalid calibration")


def source_snapshot(root: Path) -> dict:
    commit = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%H", "--", *SOURCE_PATHS],
                            capture_output=True, text=True, check=True).stdout.strip()
    verify_committed_source_state(root, commit, source_paths=SOURCE_PATHS, artifact_label="NIST n4 mutations")
    files = []
    for path in SOURCE_PATHS:
        data = (root / path).read_bytes()
        committed = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True, check=True).stdout
        if committed != data:
            raise MutationEvidenceError("commit all mutation-driving sources before emission")
        files.append({"path": path, "sha256": n.digest(data)})
    return {"source_commit_sha": commit, "files": files}


def envelope(snapshot: dict, records: list, protocol: dict) -> dict:
    production = [r for r in records if r["category"] == "production"]
    controls = [r for r in records if r["category"] == "calibration"]
    calibration_valid = len(controls) == 2 and [r["outcome"] for r in controls] == ["KILLED", "SURVIVED"]
    production_valid = len(production) == len(protocol["mutation_requirements"]) and all(r["outcome"] == "KILLED" for r in production)
    baseline_valid = len(records) > 0 and records[0]["category"] == "baseline" and records[0]["outcome"] == "SURVIVED"
    return {
        "schema_version": 1, "artifact_id": "nist_2026_n4_experimental_estimator_mutations_v1",
        "scope": "Eight frozen n4 estimator requirements; no Bayesian or cross-measurement inference.",
        "preregistration_sha256": n.PREREGISTRATION_SHA256,
        "definitions_sha256": n.digest(n.serialize_artifact(CASES).encode()),
        "source_snapshot": snapshot, "requirements": protocol["mutation_requirements"],
        "anti_false_kill_rule": "Named behavioral assertion failures only; errors, skips, missing history, source-state, syntax and import failures receive no credit.",
        "isolation": {"python_flags": ["-I", "-B"], "temporary_tests_init_sha256": n.digest(b"")},
        "production_count": len(production), "production_killed": sum(r["outcome"] == "KILLED" for r in production),
        "calibration_valid": calibration_valid,
        "family_status": "valid" if production_valid and calibration_valid and baseline_valid else "invalid",
        "records": records,
    }


def prepare(root: Path):
    protocol = n.verify_preregistration(root)
    n.verify_implementation_chronology(root)
    source = (root / MODULE).read_text()
    validate_definitions(source, protocol)
    return protocol, source, source_snapshot(root)


def build_artifact(root: Path = n.ROOT) -> dict:
    protocol, source, snapshot = prepare(root)
    records = [run_case(root, definition) for definition in (baseline(), *CASES)]
    validate_records(records, source)
    return envelope(snapshot, records, protocol)


def check_artifact(root: Path = n.ROOT) -> dict:
    """Read-only attestation: verify committed records, never rerun a mutation family."""
    protocol, source, snapshot = prepare(root)
    text = (root / OUTPUT).read_text()
    artifact = n._json(text.encode())
    records = artifact.get("records")
    validate_records(records, source)
    expected = envelope(snapshot, records, protocol)
    if artifact != expected or text != n.serialize_artifact(expected):
        raise MutationEvidenceError("mutation artifact is stale, altered, or noncanonical")
    return artifact


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.check:
            check_artifact()
            print("NIST n4 mutation evidence verified: 8 production kills; valid controls")
        else:
            result = build_artifact()
            output = args.output or (n.ROOT / OUTPUT)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(n.serialize_artifact(result))
    except (MutationEvidenceError, n.NISTN4EstimatorError, n.SourceVerificationError,
            OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as error:
        print(f"nist_n4_mutation_evidence_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
