"""Mechanical preregistration for Milestone 5B falsification experiments.

The committed JSON freezes the experiment before accepted result artifacts are
generated.  Its hash makes later material changes visible; it is not a claim that
repository history or files cannot be tampered with.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

from Discovery.constants import DEFAULT_SEARCH_CONSTANTS
from Discovery.dependency_analysis import (
    DEFAULT_SEARCH_BOUNDS,
    NO_REGISTERED_TARGET_DEPENDENCY,
    TARGET_DEPENDENT,
    TARGET_RECONSTRUCTION,
    UNRESOLVED_PROVENANCE,
)


PREREGISTRATION_SCHEMA_VERSION = 1
EXPERIMENT_IDENTIFIER = "milestone_5b_core_v1"
IMPLEMENTATION_BASE_SHA = "b9862cb595dde38b5ac3f079c13d641512a73f9d"
DEFAULT_OUTPUT = Path(
    "Experiments/Falsification/milestone_5b_core_v1.preregistration.json"
)


def _dimension_record(constant: object) -> list[str]:
    dimension = getattr(constant, "dimension")
    return [str(value) for value in dimension.exponents]


def build_preregistration() -> dict[str, Any]:
    """Return the immutable version-one experiment definition."""

    return {
        "preregistration_schema_version": PREREGISTRATION_SCHEMA_VERSION,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "repository": {
            "source_commit_sha": IMPLEMENTATION_BASE_SHA,
            "source_commit_semantics": (
                "The clean implementation base on which this preregistration was "
                "authored. Result artifacts separately record the later committed "
                "source state containing this preregistration."
            ),
        },
        "candidate_grammar": {
            "generator_catalog": [
                {
                    "key": constant.key,
                    "symbol": constant.symbol,
                    "value_si_hex": constant.value_si.hex(),
                    "dimension": _dimension_record(constant),
                    "provenance": constant.provenance,
                }
                for constant in DEFAULT_SEARCH_CONSTANTS
            ],
            "generator_order": [
                constant.key for constant in DEFAULT_SEARCH_CONSTANTS
            ],
            "exponent_domain": {
                "kind": "nonzero rational powers in the closed symmetric bound",
                "max_abs_power": DEFAULT_SEARCH_BOUNDS["max_abs_power"],
                "max_denominator": DEFAULT_SEARCH_BOUNDS["max_denominator"],
            },
            "factor_limit": DEFAULT_SEARCH_BOUNDS["max_factors"],
            "canonicalization_rules": [
                "surface factors are distinct and follow generator order",
                "rational exponents are normalized exactly with Fraction",
                "cancelled zero powers are removed",
                "equivalence identifiers derive from canonical expanded signatures",
                "JSON uses sorted keys, two-space indentation, and one final newline",
            ],
            "dimensional_matching_rules": {
                "base_order": [
                    "mass",
                    "length",
                    "time",
                    "electric_current",
                    "temperature",
                    "amount_of_substance",
                    "luminous_intensity",
                ],
                "target_dimension": ["-1", "3", "-2", "0", "0", "0", "0"],
                "comparison": "exact equality of seven Fraction exponents",
            },
        },
        "provenance": {
            "strata": {
                "primary": [NO_REGISTERED_TARGET_DEPENDENCY],
                "circularity_control": [TARGET_RECONSTRUCTION, TARGET_DEPENDENT],
                "ineligible_unresolved": [UNRESOLVED_PROVENANCE],
            },
            "primary_eligibility_rule": (
                "An equivalence class is eligible only when every member has "
                "dependency_status no_registered_target_dependency."
            ),
            "target_dependent_exclusion_rule": (
                "Any class that reconstructs G or retains a nonzero power of G after "
                "registered expansion is excluded from the primary null and reported "
                "only as a circularity control."
            ),
            "equivalence_grouping_rule": (
                "Fully resolved candidates share a class exactly when their canonical "
                "expanded dependency signatures are identical."
            ),
            "scope_nonclaim": (
                "No registered target dependency is catalog-relative and does not "
                "establish physical, experimental, causal, or metaphysical independence."
            ),
        },
        "scoring": {
            "primary": {
                "identifier": "absolute_log10_distance",
                "formula": "abs(log10(candidate_magnitude) - log10(target_magnitude))",
                "direction": "lower_is_closer",
            },
            "class_numeric_position": (
                "Evaluate the class's exact expanded signature from registered atomic "
                "catalog magnitudes, then take log10; surface rounding does not select "
                "the representative."
            ),
            "secondary_exploratory": {
                "identifier": "legacy_composite_rank",
                "reported_in_5b": False,
                "weights": {
                    "absolute_log10_distance": 1.0,
                    "exponent_complexity": 0.02,
                    "additional_factor": 0.05,
                },
            },
            "tie_rule": (
                "Distances equal within 1e-12 are ties; tied class identifiers are "
                "reported in lexical order."
            ),
        },
        "local_null": {
            "role": "primary",
            "distribution": "uniform_in_log10_space",
            "lower": "log10(G)-3",
            "upper": "log10(G)+3",
            "convention_nonclaim": (
                "The plus-or-minus three-decade window is methodological, not physical."
            ),
        },
        "global_null": {
            "role": "contextual",
            "distribution": "uniform_in_log10_space",
            "derivation": (
                "minimum unique eligible class position minus 3 through maximum unique "
                "eligible class position plus 3, enlarged to contain the local interval"
            ),
            "record_derived_interval_in_result": True,
        },
        "randomness": {
            "generator": "python_random.Random_MT19937",
            "sampling_procedure": "a + (b-a) * Random(seed).random()",
            "target_count_per_null": 20000,
            "seeds": {"local_null": 528491, "global_null": 528492},
            "choice_rationale": (
                "Twenty thousand targets per null give useful CDF calibration while "
                "keeping standard-library execution practical in ordinary CI."
            ),
        },
        "analytic_calibration": {
            "statistic": "two_sided_maximum_empirical_analytic_cdf_deviation",
            "tolerance": 0.02,
            "evaluation_points": "both empirical CDF limits at every ordered sample",
            "oracle": (
                "union length of clipped [candidate-d,candidate+d] intervals divided "
                "by the frozen log-interval length"
            ),
            "failure_rule": "mark the null result invalid and do not promote it",
        },
        "planted_controls": {
            "number_of_targets": 3,
            "candidate_selection_rule": (
                "Rank eligible classes by descending distance to their nearest distinct "
                "eligible numerical position, then by class identifier; select the first "
                "three classes whose clearance exceeds the assigned perturbation distance."
            ),
            "epsilon_values": ["-0.01", "0.001", "0.01"],
            "construction": "T_planted = C * (1 + epsilon)",
            "expected_recovery_rule": (
                "The intended class must be the unique winner or a reported tie, and "
                "the measured distance must agree with abs(log10(1+epsilon)) within 1e-12."
            ),
        },
    }


def serialize_artifact(artifact: Mapping[str, Any]) -> str:
    """Serialize deterministic JSON with exactly one final newline."""

    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def preregistration_sha256_bytes(content: bytes) -> str:
    """Hash the exact committed preregistration bytes."""

    return hashlib.sha256(content).hexdigest()


def validate_preregistration_record(record: Mapping[str, Any]) -> None:
    """Reject stale schema/version/base metadata before experiment execution."""

    if record.get("preregistration_schema_version") != PREREGISTRATION_SCHEMA_VERSION:
        raise ValueError("stale preregistration schema version")
    if record.get("experiment_identifier") != EXPERIMENT_IDENTIFIER:
        raise ValueError("stale preregistration experiment identifier")
    repository = record.get("repository")
    if not isinstance(repository, Mapping):
        raise ValueError("preregistration repository metadata is missing")
    source_sha = repository.get("source_commit_sha")
    if source_sha != IMPLEMENTATION_BASE_SHA:
        raise ValueError("preregistration source commit SHA mismatch")
    if not isinstance(source_sha, str) or re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise ValueError("preregistration source commit SHA is invalid")


def load_preregistration(path: Path = DEFAULT_OUTPUT) -> tuple[dict[str, Any], bytes]:
    """Load and validate exact preregistration bytes."""

    content = path.read_bytes()
    try:
        record = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("preregistration is not valid UTF-8 JSON") from error
    if not isinstance(record, dict):
        raise ValueError("preregistration root must be an object")
    validate_preregistration_record(record)
    return record, content


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the committed preregistration is stale",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    rendered = serialize_artifact(build_preregistration())
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"stale or missing preregistration artifact: {args.output}", file=sys.stderr)
            raise SystemExit(1)
        record, content = load_preregistration(args.output)
        del record
        print(
            "Preregistration is current: "
            f"{args.output} (sha256 {preregistration_sha256_bytes(content)})."
        )
        return

    if args.output.exists():
        existing = args.output.read_text(encoding="utf-8")
        if existing != rendered:
            print(
                "refusing to overwrite an existing preregistration; create a new "
                "experiment version",
                file=sys.stderr,
            )
            raise SystemExit(1)
        print(f"Preregistration already exists unchanged: {args.output}.")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote immutable experiment definition to {args.output}.")
    print("Amendments require a new experiment identifier and artifact path.")


if __name__ == "__main__":
    main()
