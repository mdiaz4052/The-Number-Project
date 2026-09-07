"""Pinned HUST component-rounding diagnostic; never an empirical model update."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from Discovery.rounding_consistency import (
    Budget, Interval, RoundingError, calculate, calculation_record, classify,
    decimal_fraction, interval_record, rounding_bin, verify_witness,
)
from Discovery.source_history import (
    SourceStateViolationError, SourceVerificationError, exit_for_source_verification_error,
    verify_preregistration_freeze,
)
from fractions import Fraction


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "hust_2018_aaf_rounding_consistency_preregistration_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "hust_2018_aaf_rounding_consistency_v1.json"
BASELINE = "3fb60ecf64a61db2347bb154cc7e20b02b0f6ca3"
PREREGISTRATION_COMMIT = "8578f20e41476e9490dfbb934342a92bd3ca738e"
PREREGISTRATION_SHA256 = "0c86cfdbe5efa97c6c585db25c1194eb7d798e532ebe8aed03990bde38983233"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/39",
    "created_at": "2026-09-06T20:33:51Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "scope": "Implementation-rule freeze; HUST result and exploratory rounding scenarios already known.",
}
SCOPES = ("AAF-I", "AAF-II", "AAF-III")
UNIT = "m^3 kg^-1 s^-2"
MODELS_NAME = "hust_2018_aaf_depth_2b_measurement_models_v2.json"
GRAPH_NAME = "hust_2018_aaf_required_inputs_depth_2b_v2.json"
SOURCE_PATHS = (
    "Discovery/rounding_consistency.py",
    "Discovery/hust_2018_aaf_rounding_consistency.py",
    "Discovery/source_history.py",
    "Notes/HUST2018AAFRoundingConsistencySpecification.md",
    PREREGISTRATION_PATH.as_posix(),
)


def serialize_artifact(value: dict) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RoundingError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def load_protocol(root: Path = ROOT) -> dict:
    data = (root / PREREGISTRATION_PATH).read_bytes()
    if _hash(data) != PREREGISTRATION_SHA256:
        raise RoundingError("rounding preregistration bytes changed")
    protocol = _json(data)
    spec = protocol["specification"]
    if _hash((root / spec["path"]).read_bytes()) != spec["sha256"]:
        raise RoundingError("bounded specification differs from its preregistered hash")
    return protocol


def verify_preregistration(root: Path = ROOT) -> dict:
    verify_preregistration_freeze(
        root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
        path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256,
    )
    return load_protocol(root)


def _read_pin(root: Path, pin: dict) -> bytes:
    data = (root / pin["path"]).read_bytes()
    if len(data) != pin["byte_length"] or _hash(data) != pin["sha256"]:
        raise RoundingError(f"frozen source bytes changed: {pin['path']}")
    return data


def load_frozen_records(root: Path = ROOT) -> tuple[dict, dict]:
    protocol = load_protocol(root)
    for pin in protocol["source_authority_artifacts"]:
        _read_pin(root, pin)
    records = {Path(pin["path"]).name: _json(_read_pin(root, pin))
               for pin in protocol["allowed_input_artifacts"]}
    return protocol, records


def project_inputs(records: dict, protocol: dict) -> dict:
    """Allowlist calculation inputs; terminal quantities and totals are absent."""
    try:
        models, graph = records[MODELS_NAME]["models"], records[GRAPH_NAME]
        if len(models) != len(SCOPES):
            raise RoundingError("individual run inventory changed")
        central_values = []
        for scope, model in zip(SCOPES, models):
            quantities = model["quantities"]
            if len({q["identifier"] for q in quantities}) != len(quantities):
                raise RoundingError("duplicate source quantity")
            target = next(q for q in quantities if q["identifier"] == scope + ":G_hat")
            reconstruction = model["uncertainty_reconstruction"]
            if (target["role"] != "target_output" or target["unit"] != UNIT
                    or target["dimension"] != ["-1", "3", "-2", "0", "0", "0", "0"]
                    or reconstruction["scope"] != scope
                    or model["target_measurand"]["quantity_id"] != target["identifier"]
                    or target["numerical_record"]["value_decimal"] != reconstruction["G_hat_decimal"]):
                raise RoundingError("central value role, unit, dimension, scope or reconstruction mismatch")
            central_values.append(target["numerical_record"]["value_decimal"])
        components = []
        for row in graph["components"]:
            if row["unit"] != "ppm" or row["evidence_type"] != "PUBLIC_DIRECT":
                raise RoundingError("component unit or source evidence changed")
            if any(not isinstance(row[s], str) or not re.fullmatch(r"[0-9]+\.[0-9]{2}", row[s])
                   for s in SCOPES):
                raise RoundingError("component cells must preserve two printed decimal places")
            components.append({
                "component_id": row["component_id"],
                "correlation": ("independent" if row["component_id"] == "statistical_angular_acceleration"
                                else "shared"),
                "values": [row[s] for s in SCOPES],
            })
        projection = {"scopes": list(SCOPES), "unit": UNIT, "component_unit": "ppm",
                      "central_values": central_values, "components": components}
    except (KeyError, TypeError, StopIteration) as error:
        raise RoundingError("incomplete or malformed source projection") from error
    validate_projection(projection, protocol)
    return projection


def validate_projection(projection: dict, protocol: dict) -> None:
    if (projection != protocol["input_projection"]
            or _hash(serialize_artifact(projection).encode()) != protocol["input_projection_sha256"]):
        raise RoundingError("calculation projection differs from the frozen protocol")


def budget_from_projection(projection: dict, protocol: dict) -> Budget:
    validate_projection(projection, protocol)
    half_width = decimal_fraction(protocol["rounding_policy"]["component_half_width_ppm"])
    return Budget(
        tuple(decimal_fraction(v) for v in projection["central_values"]),
        tuple(tuple(rounding_bin(decimal_fraction(v), half_width) for v in row["values"])
              for row in projection["components"]),
        tuple(row["correlation"] for row in projection["components"]),
    )


def candidate_parameters(protocol: dict) -> tuple[Fraction, ...]:
    return tuple(Fraction(t) for t in protocol["candidate_schedule"]["parameters"])


def build_calculation(root: Path = ROOT):
    """This path never reads a published comparison or combined-result artifact."""
    protocol, records = load_frozen_records(root)
    projection = project_inputs(records, protocol)
    calculation = calculate(budget_from_projection(projection, protocol), candidate_parameters(protocol))
    return protocol, projection, calculation


def run_controls(protocol: dict) -> list[dict]:
    results = []
    for control in protocol["controls"]:
        budget = Budget(
            tuple(decimal_fraction(g) for g in control["g"]),
            ((rounding_bin(decimal_fraction(control["component_ppm"]),
                           decimal_fraction(control["component_half_width_ppm"])),),),
            ("shared",),
        )
        calculation = calculate(budget, candidate_parameters(protocol))
        comparison = rounding_bin(decimal_fraction(control["target_ppm"]),
                                  decimal_fraction(control["target_half_width_ppm"]))
        outcome, witness_index = classify(calculation, comparison)
        if outcome != control["expected"]:
            raise RoundingError(f"synthetic {control['id']} control failed")
        results.append({"id": control["id"], "outcome": outcome, "witness_index": witness_index,
                        "comparison_ppm": interval_record(comparison),
                        "calculation": calculation_record(calculation, places=protocol["calculation"]["output_ppm_decimal_places"])})
    return results


def source_snapshot(root: Path) -> dict:
    result = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", *SOURCE_PATHS],
        capture_output=True, text=True, check=True,
    )
    commit = result.stdout.strip()
    files = []
    for path in SOURCE_PATHS:
        recorded = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True)
        current = (root / path).read_bytes()
        if recorded.returncode or recorded.stdout != current:
            raise SourceStateViolationError("commit result-driving source before emitting a rounding artifact")
        files.append({"path": path, "sha256": _hash(current)})
    return {"source_commit_sha": commit, "files": files}


def build_artifact(root: Path = ROOT, *, comparison: Interval | None = None) -> dict:
    verify_preregistration(root)
    protocol, projection, calculation = build_calculation(root)
    numerical_record = calculation_record(calculation, places=protocol["calculation"]["output_ppm_decimal_places"])
    if comparison is None:
        comparison = rounding_bin(decimal_fraction(protocol["comparison"]["value_ppm"]),
                                  decimal_fraction(protocol["comparison"]["half_width_ppm"]))
    outcome, index = classify(calculation, comparison)
    witness = None
    if index is not None:
        candidate = calculation.candidates[index]
        witness = {"candidate_index": index, "calculation_candidate": numerical_record["candidates"][index],
                   "input_and_comparison_membership_verified": verify_witness(calculation.budget, candidate, comparison)}
    return {
        "schema_version": 1, "artifact_id": "hust_2018_aaf_rounding_consistency_v1",
        "kind": "conditional_rounding_consistency_diagnostic",
        "integrity": {"preregistration_sha256": PREREGISTRATION_SHA256,
                      "preregistration_commit_sha": PREREGISTRATION_COMMIT,
                      "baseline_main_sha": BASELINE, "external_anchor": EXTERNAL_ANCHOR,
                      "source_snapshot": source_snapshot(root)},
        "input_projection": projection, "input_projection_sha256": protocol["input_projection_sha256"],
        "source_pins": protocol["allowed_input_artifacts"] + protocol["source_authority_artifacts"],
        "rounding_policy": protocol["rounding_policy"], "calculation_policy": protocol["calculation"],
        "candidate_schedule": protocol["candidate_schedule"], "calculation": numerical_record,
        "comparison": {"role": "terminal_only", "interval_ppm": interval_record(comparison),
                       "source_reference": protocol["comparison"],
                       "uses_preregistered_interval": comparison == rounding_bin(
                           decimal_fraction(protocol["comparison"]["value_ppm"]),
                           decimal_fraction(protocol["comparison"]["half_width_ppm"]))},
        "decision": {"outcome": outcome, "witness": witness,
                     "scope": "Conditional on the declared component bins, fixed G inputs and correlation model."},
        "synthetic_controls": run_controls(protocol),
        "claim_limits": protocol["claim_limits"],
        "interpretation": {
            "compatible": "A concrete admissible component scenario reaches the comparison bin; actual cause and probability are not established.",
            "incompatible": "The comparison is excluded by a conservative enclosure under the declared model and component domain only.",
            "unresolved": "The enclosure overlaps but the fixed candidate schedule supplies no witness; no exclusion follows.",
        }[outcome],
    }


def verify_preserved_files(root: Path = ROOT) -> None:
    for pin in load_protocol(root)["preserved_baseline_files"]:
        _read_pin(root, pin)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        artifact = build_artifact()
        text = serialize_artifact(artifact)
        if args.check:
            verify_preserved_files()
            if (ROOT / DEFAULT_OUTPUT).read_text() != text:
                raise RoundingError("rounding-consistency artifact is stale")
            print(f"rounding consistency verified: {artifact['decision']['outcome']}")
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
            print(f"wrote {args.output}")
        else:
            print(text, end="")
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except (RoundingError, OSError, ValueError) as error:
        print(f"rounding_consistency_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
