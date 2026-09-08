"""Target-independent reconstruction of the BIPM 2014 correlated two-method estimator."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, localcontext, Context
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from Discovery.correlated_weighted_mean import (
    CorrelatedMeanError,
    closed_intersection,
    decimal_cell,
    decimal_fraction,
    fraction_record,
    linear_enclosure,
    minimum_variance_unbiased_weights,
)
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import SourceVerificationError


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("Experiments/GMeasurements")
PREREGISTRATION_PATH = DIRECTORY / "bipm_2014_correlated_estimator_preregistration_v1.json"
SOURCE_ATTESTATION_PATH = DIRECTORY / "bipm_2014_correlated_estimator_source_attestation_v1.json"
DEFAULT_OUTPUT = DIRECTORY / "bipm_2014_correlated_estimator_v1.json"

BASELINE = "fe9b6ee4301612530143ae13e814a16cc5fef2cb"
PREREGISTRATION_COMMIT = "1d71e27e1655f3cef7f674e507c03a1a14e2a340"
PREREGISTRATION_SHA256 = "e5516661e79a222a5fca6f8de61e7c461575129a34a3e1e41359491fa42076a9"
EXTERNAL_ANCHOR = {
    "event": "draft_pull_request_created",
    "url": "https://github.com/mdiaz4052/The-Number-Project/pull/44",
    "created_at": "2026-09-08T20:29:13Z",
    "preregistration_commit_sha": PREREGISTRATION_COMMIT,
    "outcome_blind": False,
}
SOURCE_PATHS = (
    "Discovery/correlated_weighted_mean.py",
    "Discovery/bipm_2014_correlated_estimator.py",
    "Notes/BIPM2014CorrelatedEstimatorSpecification.md",
    "Notes/BIPM2014CorrelatedEstimator.md",
    PREREGISTRATION_PATH.as_posix(),
    SOURCE_ATTESTATION_PATH.as_posix(),
)
E001_FORBIDDEN = (
    "Experiments/GMeasurements/hust_2018_aaf_source_audit_v1.manifest.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v1.json",
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v2.json",
)
DECIMAL_CONTEXT = Context(prec=50)


class BIPMEstimatorError(CorrelatedMeanError):
    """Invalid source, target-independence boundary, or result artifact."""


def serialize_artifact(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BIPMEstimatorError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def verify_preregistration(root: Path = ROOT) -> dict:
    try:
        data = verify_preregistration_freeze(
            root,
            baseline=BASELINE,
            commit=PREREGISTRATION_COMMIT,
            path=PREREGISTRATION_PATH.as_posix(),
            sha256=PREREGISTRATION_SHA256,
        )
    except SourceVerificationError as error:
        raise BIPMEstimatorError(str(error)) from error
    protocol = _json(data)
    if protocol["known_prior_information"]["outcome_blind"] is not False:
        raise BIPMEstimatorError("BIPM capability PR must not claim outcome blindness")
    return protocol


def load_source_attestation(protocol: dict, root: Path = ROOT) -> dict:
    data = _json((root / SOURCE_ATTESTATION_PATH).read_bytes())
    if data.get("primary_source", {}).get("doi") != protocol["primary_source"]["doi"]:
        raise BIPMEstimatorError("BIPM source DOI differs from frozen protocol")
    source = data.get("transcription", {}).get("estimator_inputs", {})
    frozen = protocol["source_projection"]["estimator_inputs"]
    expected = {
        "servo": {
            "value_decimal_in_1e_minus_11_units": frozen["servo"]["G_decimal_in_1e_minus_11_units"],
            "printed_decimal_places": frozen["servo"]["printed_decimal_places"],
            "relative_standard_uncertainty_ppm": frozen["servo"]["standard_uncertainty_ppm"],
        },
        "cavendish": {
            "value_decimal_in_1e_minus_11_units": frozen["cavendish"]["G_decimal_in_1e_minus_11_units"],
            "printed_decimal_places": frozen["cavendish"]["printed_decimal_places"],
            "relative_standard_uncertainty_ppm": frozen["cavendish"]["standard_uncertainty_ppm"],
        },
        "covariance_ppm_squared": {"value": frozen["covariance_ppm_squared"]},
    }
    for method in ("servo", "cavendish"):
        for key, value in expected[method].items():
            if source.get(method, {}).get(key) != value:
                raise BIPMEstimatorError("BIPM source transcription differs from freeze")
    if source.get("covariance_ppm_squared", {}).get("value") != frozen["covariance_ppm_squared"]:
        raise BIPMEstimatorError("BIPM covariance transcription differs from freeze")
    return data


def estimator_state(protocol: dict, attestation: dict) -> dict:
    """Build all estimator-driving state without accepting comparison-only fields."""
    source = attestation["transcription"]["estimator_inputs"]
    servo = source["servo"]
    cavendish = source["cavendish"]
    sigma_servo = decimal_fraction(servo["relative_standard_uncertainty_ppm"])
    sigma_cavendish = decimal_fraction(cavendish["relative_standard_uncertainty_ppm"])
    covariance = decimal_fraction(source["covariance_ppm_squared"]["value"])
    weights = minimum_variance_unbiased_weights(sigma_servo, sigma_cavendish, covariance)
    servo_cell = decimal_cell(
        servo["value_decimal_in_1e_minus_11_units"], servo["printed_decimal_places"]
    )
    cavendish_cell = decimal_cell(
        cavendish["value_decimal_in_1e_minus_11_units"], cavendish["printed_decimal_places"]
    )
    enclosure = linear_enclosure(
        (servo_cell, cavendish_cell), (weights.first, weights.second)
    )
    midpoint = (
        weights.first * decimal_fraction(servo["value_decimal_in_1e_minus_11_units"])
        + weights.second * decimal_fraction(cavendish["value_decimal_in_1e_minus_11_units"])
    )
    return {
        "weights": weights,
        "input_cells": {"servo": servo_cell, "cavendish": cavendish_cell},
        "aggregate_enclosure": enclosure,
        "midpoint_aggregate": midpoint,
        "sigma_servo": sigma_servo,
        "sigma_cavendish": sigma_cavendish,
        "covariance": covariance,
    }


def classify(state: dict, comparison_only: dict) -> dict:
    """Expose the frozen terminal comparison only after estimator state exists."""
    target = decimal_cell(
        comparison_only["published_combined_G_decimal_in_1e_minus_11_units"],
        comparison_only["published_combined_printed_decimal_places"],
    )
    overlap = closed_intersection(state["aggregate_enclosure"], target)
    if overlap is None:
        outcome = "incompatible"
        status = "not_representable_under_the_declared_bipm_2014_correlated_weighted_mean_model"
        reason = "aggregate_enclosure_disjoint_from_published_combined_cell"
    else:
        outcome = "compatible"
        status = "representable_under_the_declared_bipm_2014_correlated_weighted_mean_model"
        reason = "aggregate_enclosure_intersects_published_combined_cell"
    return {
        "outcome": outcome,
        "status": status,
        "reason": reason,
        "target_cell": target,
        "intersection": overlap,
    }


def _fraction_interval(interval) -> dict:
    return {"low": fraction_record(interval.low), "high": fraction_record(interval.high)}


def _decimal_text(value: Fraction, places: int = 12) -> str:
    with localcontext(DECIMAL_CONTEXT):
        number = Decimal(value.numerator) / Decimal(value.denominator)
        return f"{number:.{places}f}"


def _sqrt_decimal(value: Fraction, places: int = 12) -> str:
    with localcontext(DECIMAL_CONTEXT):
        number = (Decimal(value.numerator) / Decimal(value.denominator)).sqrt()
        return f"{number:.{places}f}"


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def verify_implementation_chronology(root: Path = ROOT) -> None:
    anchor = _timestamp(EXTERNAL_ANCHOR["created_at"])
    freeze = subprocess.run(
        ["git", "-C", str(root), "show", "-s", "--format=%aI%x00%cI", PREREGISTRATION_COMMIT],
        capture_output=True, text=True, check=True,
    ).stdout.strip().split("\x00")
    if len(freeze) != 2 or any(_timestamp(value) >= anchor for value in freeze):
        raise BIPMEstimatorError("BIPM freeze does not precede GitHub anchor")
    added = subprocess.run(
        [
            "git", "-C", str(root), "log", "--diff-filter=A", "--reverse",
            "--format=%H%x00%aI%x00%cI", "--",
            "Discovery/bipm_2014_correlated_estimator.py",
        ],
        capture_output=True, text=True, check=True,
    ).stdout.strip().splitlines()
    if not added:
        raise BIPMEstimatorError("BIPM implementation source has no committed introduction")
    fields = added[0].split("\x00")
    if len(fields) != 3 or any(_timestamp(value) <= anchor for value in fields[1:]):
        raise BIPMEstimatorError("BIPM implementation does not postdate GitHub anchor")
    ancestry = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", PREREGISTRATION_COMMIT, fields[0]],
        capture_output=True,
    )
    if ancestry.returncode:
        raise BIPMEstimatorError("BIPM implementation does not descend from freeze")


def source_snapshot(root: Path = ROOT) -> dict:
    commit = subprocess.run(
        ["git", "-C", str(root), "log", "-1", "--format=%H", "--", *SOURCE_PATHS],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    files = []
    for path in SOURCE_PATHS:
        current = (root / path).read_bytes()
        recorded = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True,
        )
        if recorded.returncode or recorded.stdout != current:
            raise BIPMEstimatorError("commit BIPM result-driving source before artifact emission")
        files.append({"path": path, "sha256": digest(current)})
    return {"source_commit_sha": commit, "files": files}


def verify_e001_isolation() -> None:
    if set(E001_FORBIDDEN) & set(SOURCE_PATHS):
        raise BIPMEstimatorError("E-001 artifact entered BIPM source inventory")


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    verify_implementation_chronology(root)
    attestation = load_source_attestation(protocol, root)

    state = estimator_state(protocol, attestation)
    comparison = deepcopy(protocol["source_projection"]["comparison_only"])
    decision = classify(state, comparison)

    weights = state["weights"]
    printed_servo = decimal_fraction(comparison["printed_servo_weight"])
    printed_cavendish = decimal_fraction(comparison["printed_cavendish_weight"])
    return {
        "schema_version": 1,
        "artifact_id": "bipm_2014_correlated_estimator_v1",
        "kind": "conditional_correlated_two_input_weighted_estimator_reconstruction",
        "integrity": {
            "baseline_main_sha": BASELINE,
            "preregistration_commit_sha": PREREGISTRATION_COMMIT,
            "preregistration_sha256": PREREGISTRATION_SHA256,
            "external_anchor": EXTERNAL_ANCHOR,
            "source_snapshot": source_snapshot(root),
        },
        "known_prior_information": protocol["known_prior_information"],
        "source": {
            "doi": protocol["primary_source"]["doi"],
            "locators": protocol["primary_source"]["locators"],
            "source_attestation_path": SOURCE_ATTESTATION_PATH.as_posix(),
        },
        "estimator": {
            "input_order": ["servo", "cavendish"],
            "covariance_matrix_ppm_squared": [
                [fraction_record(state["sigma_servo"] ** 2), fraction_record(state["covariance"])],
                [fraction_record(state["covariance"]), fraction_record(state["sigma_cavendish"] ** 2)],
            ],
            "determinant_ppm_fourth": fraction_record(weights.determinant),
            "denominator_ppm_squared": fraction_record(weights.denominator),
            "derived_weights": {
                "servo": fraction_record(weights.first),
                "cavendish": fraction_record(weights.second),
                "sum": fraction_record(weights.first + weights.second),
                "servo_decimal": _decimal_text(weights.first),
                "cavendish_decimal": _decimal_text(weights.second),
            },
            "combined_relative_variance_ppm_squared": fraction_record(weights.variance),
            "combined_relative_standard_uncertainty_ppm_decimal": _sqrt_decimal(weights.variance),
            "printed_weight_corroboration": {
                "servo_printed": comparison["printed_servo_weight"],
                "cavendish_printed": comparison["printed_cavendish_weight"],
                "servo_difference": fraction_record(weights.first - printed_servo),
                "cavendish_difference": fraction_record(weights.second - printed_cavendish),
                "role": "comparison_only_not_estimator_input",
            },
        },
        "representation": {
            "input_cells_in_1e_minus_11_units": {
                key: _fraction_interval(value) for key, value in state["input_cells"].items()
            },
            "midpoint_aggregate_in_1e_minus_11_units": fraction_record(state["midpoint_aggregate"]),
            "midpoint_aggregate_decimal": _decimal_text(state["midpoint_aggregate"], 12),
            "aggregate_enclosure_in_1e_minus_11_units": _fraction_interval(state["aggregate_enclosure"]),
            "published_combined_cell_in_1e_minus_11_units": _fraction_interval(decision["target_cell"]),
            "intersection_in_1e_minus_11_units": (
                None if decision["intersection"] is None else _fraction_interval(decision["intersection"])
            ),
        },
        "decision": {
            "outcome": decision["outcome"],
            "status": decision["status"],
            "reason": decision["reason"],
        },
        "comparison_only": {
            "published_combined_G_decimal_in_1e_minus_11_units": comparison[
                "published_combined_G_decimal_in_1e_minus_11_units"
            ],
            "published_combined_printed_decimal_places": comparison[
                "published_combined_printed_decimal_places"
            ],
            "printed_combined_relative_uncertainty_ppm": comparison[
                "printed_combined_relative_uncertainty_ppm"
            ],
        },
        "claim_limits": protocol["nonclaims"] + [
            "Compatible means the exact weighted image of the two printed method cells intersects the printed combined-value cell; it does not recover unique hidden author values.",
            "The exact derived weights condition on the displayed 61 ppm, 54 ppm, and -2080 ppm^2 summaries as declared source inputs.",
            "The printed 0.46/0.54 weights and 25 ppm combined uncertainty are corroboration only.",
        ],
    }


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
            verify_e001_isolation()
            if (ROOT / DEFAULT_OUTPUT).read_text() != text:
                raise BIPMEstimatorError("BIPM correlated-estimator artifact is stale")
            print("BIPM 2014 correlated estimator source, chronology, target independence and result verified")
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        else:
            print(text, end="")
    except (BIPMEstimatorError, CorrelatedMeanError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as error:
        print(f"bipm_2014_correlated_estimator_invalid: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
