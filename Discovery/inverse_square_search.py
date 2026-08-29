"""Recover the inverse-square monomial with exact dimensional constraints.

The experiment fixes the candidate form to ``G^alpha M^beta m^gamma R^delta``.
Dimensional analysis determines an affine exponent family.  A separate scaling
assumption—linearity in either mass—then selects the Newtonian exponent tuple.
No measured values or floating-point ranking enter this computation.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

from Discovery.dimensions import (
    BASE_DIMENSIONS,
    FORCE,
    GRAVITATIONAL_CONSTANT,
    LENGTH,
    MASS,
)
from Discovery.monomial_constraints import (
    LinearConstraint,
    LinearSystemSolution,
    NamedFactor,
    solve_monomial_constraints,
)


DEFAULT_OUTPUT = Path("Experiments/InverseSquare/solutions.json")
FACTOR_ROLES = (
    ("G", "area-to-information proportionality constant"),
    ("M", "source mass enclosed by the spherical screen"),
    ("m", "test mass near the screen"),
    ("R", "screen radius"),
)
FACTORS = (
    NamedFactor("G", GRAVITATIONAL_CONSTANT.exponents),
    NamedFactor("M", MASS.exponents),
    NamedFactor("m", MASS.exponents),
    NamedFactor("R", LENGTH.exponents),
)


def fraction_text(value: Fraction) -> str:
    """Serialize a rational without introducing an approximate number."""

    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _vector(values: tuple[Fraction, ...]) -> list[str]:
    return [fraction_text(value) for value in values]


def _matrix(values: tuple[tuple[Fraction, ...], ...]) -> list[list[str]]:
    return [_vector(row) for row in values]


def _solution_record(solution: LinearSystemSolution) -> dict[str, Any]:
    return {
        "status": solution.status,
        "rank": solution.rank,
        "nullity": solution.nullity,
        "pivot_columns_zero_based": list(solution.pivot_columns),
        "free_columns_zero_based": list(solution.free_columns),
        "augmented_rref": _matrix(solution.rref),
        "particular_solution": (
            None
            if solution.particular_solution is None
            else _vector(solution.particular_solution)
        ),
        "nullspace_basis": [_vector(vector) for vector in solution.nullspace_basis],
    }


def solve_inverse_square_systems() -> tuple[
    LinearSystemSolution, LinearSystemSolution, LinearSystemSolution
]:
    """Return the unconstrained, test-linear, and source-linear systems."""

    unconstrained = solve_monomial_constraints(FACTORS, FORCE.exponents)
    test_mass_linear = solve_monomial_constraints(
        FACTORS,
        FORCE.exponents,
        (LinearConstraint({"m": 1}, 1, label="test-mass linearity"),),
    )
    source_mass_linear = solve_monomial_constraints(
        FACTORS,
        FORCE.exponents,
        (LinearConstraint({"M": 1}, 1, label="source-mass linearity"),),
    )
    return unconstrained, test_mass_linear, source_mass_linear


def build_artifact() -> dict[str, Any]:
    """Build the deterministic, machine-readable Milestone 2 result."""

    unconstrained, test_mass_linear, source_mass_linear = solve_inverse_square_systems()
    expected_particular = (Fraction(1), Fraction(2), Fraction(0), Fraction(-2))
    expected_direction = (Fraction(0), Fraction(-1), Fraction(1), Fraction(0))
    expected_unique = (Fraction(1), Fraction(1), Fraction(1), Fraction(-2))
    if (
        unconstrained.status != "affine"
        or unconstrained.particular_solution != expected_particular
        or unconstrained.nullspace_basis != (expected_direction,)
    ):
        raise RuntimeError("unexpected unconstrained inverse-square solution family")
    if (
        test_mass_linear.status != "unique"
        or test_mass_linear.particular_solution != expected_unique
        or source_mass_linear.status != "unique"
        or source_mass_linear.particular_solution != expected_unique
    ):
        raise RuntimeError("a mass-linearity constraint did not select the expected tuple")

    dimension_rows = []
    for row_index, base_dimension in enumerate(BASE_DIMENSIONS):
        dimension_rows.append(
            {
                "base_dimension": base_dimension,
                "coefficients": [
                    fraction_text(factor.dimension[row_index]) for factor in FACTORS
                ],
                "target": fraction_text(FORCE.exponents[row_index]),
            }
        )

    return {
        "schema_version": 1,
        "experiment": "inverse-square monomial dimensional constraints",
        "base_dimension_order": list(BASE_DIMENSIONS),
        "factor_order": [key for key, _ in FACTOR_ROLES],
        "factors": [
            {
                "key": key,
                "role": role,
                "dimension": _vector(factor.dimension),
            }
            for (key, role), factor in zip(FACTOR_ROLES, FACTORS)
        ],
        "target": {"name": "force", "dimension": _vector(FORCE.exponents)},
        "dimension_matrix": {
            "orientation": "rows are SI base dimensions; columns follow factor_order",
            "rows": dimension_rows,
        },
        "model_definition": {
            "candidate_form": "G^alpha * M^beta * m^gamma * R^delta",
            "exponent_domain": "rational numbers",
            "selected_generators": ["G", "M", "m", "R"],
            "overall_dimensionless_coefficient": "not represented and not determined",
        },
        "unconstrained": {
            **_solution_record(unconstrained),
            "implied_relations": [
                "alpha = 1",
                "delta = -2",
                "beta + gamma = 2",
            ],
            "parametric_solution": (
                "(alpha, beta, gamma, delta) = (1, 2, 0, -2) "
                "+ t * (0, -1, 1, 0), t rational"
            ),
            "nullspace_interpretation": (
                "The direction (0, -1, 1, 0) multiplies a candidate by "
                "a rational power of the dimensionless mass ratio m/M."
            ),
        },
        "added_scaling_constraints": {
            "test_mass_linearity": {
                "constraint": "gamma = 1",
                "classification": "additional physical/scaling assumption",
                **_solution_record(test_mass_linear),
                "unique_exponent_tuple": _vector(expected_unique),
            },
            "source_mass_linearity": {
                "constraint": "beta = 1",
                "classification": "additional physical/scaling assumption",
                **_solution_record(source_mass_linear),
                "unique_exponent_tuple": _vector(expected_unique),
            },
        },
        "symbolic_result": {
            "selected_monomial": "G * M * m / R^2",
            "unique_exponent_tuple": _vector(expected_unique),
            "scope": "unique only within the stated four-factor monomial model",
        },
        "epistemic_classification": {
            "dimension_matching": "exact symbolic result",
            "mass_linearity": "assumption",
            "physical_law": "not established by this computation",
            "numerical_observation": "none",
        },
        "limitations": [
            (
                "Dimensional analysis cannot distinguish source mass from test mass "
                "because both carry the same SI dimension."
            ),
            (
                "A dimensionless multiplier or function such as Phi(m/M) remains "
                "dimensionally admissible outside the restricted monomial selection."
            ),
            "Dimensional analysis cannot determine an overall dimensionless coefficient.",
            "The factor set and monomial form define the search space; they are not conclusions.",
            (
                "The result does not empirically validate entropic gravity or prove that "
                "nature must obey the selected relation."
            ),
        ],
    }


def serialize_artifact(artifact: dict[str, Any]) -> str:
    """Serialize with stable ordering, indentation, and a final newline."""

    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the selected artifact is missing or stale",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    rendered = serialize_artifact(build_artifact())
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"stale or missing inverse-square artifact: {args.output}", file=sys.stderr)
            raise SystemExit(1)
        print(f"Inverse-square artifact is current: {args.output}")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote exact inverse-square constraint result to {args.output}.")
    print("Unconstrained: alpha=1, delta=-2, beta+gamma=2.")
    print("With gamma=1 (or beta=1): (alpha,beta,gamma,delta)=(1,1,1,-2).")


if __name__ == "__main__":
    main()
