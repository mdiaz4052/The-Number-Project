"""Enumerate small expressions whose dimensions exactly match those of G.

Dimensional equality is a hard filter.  Ranking is a navigation aid for an
experiment, not statistical evidence and not a claim of a physical law.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import csv
from fractions import Fraction
from itertools import combinations, product
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

from Discovery.constants import (
    DEFAULT_SEARCH_CONSTANTS,
    GRAVITATIONAL_CONSTANT_G,
    PhysicalConstant,
)
from Discovery.dimensions import DIMENSIONLESS, Dimension
from Discovery.planck_identities import (
    PLANCK_IDENTITIES_BY_SIGNATURE,
    PLANCK_UNIT_KEYS,
    normalize_exponent_signature,
)


def _format_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _expression(constants: Sequence[PhysicalConstant], powers: Sequence[Fraction]) -> str:
    factors: list[str] = []
    for constant, power in zip(constants, powers):
        if power == 1:
            factors.append(constant.symbol)
        elif power.denominator == 1:
            factors.append(f"{constant.symbol}^{power.numerator}")
        else:
            factors.append(f"{constant.symbol}^({_format_fraction(power)})")
    return " * ".join(factors)


def _exponent_complexity(powers: Iterable[Fraction]) -> int:
    """Small integers are simpler; denominators incur an additional cost."""

    return sum(abs(power.numerator) + power.denominator - 1 for power in powers)


def _classification(
    constants: Sequence[PhysicalConstant], powers: Sequence[Fraction]
) -> tuple[str, str]:
    signature = normalize_exponent_signature(
        (constant.key, power) for constant, power in zip(constants, powers)
    )
    keys = {constant.key for constant in constants}
    identity = PLANCK_IDENTITIES_BY_SIGNATURE.get(signature)
    if identity is not None:
        return (
            identity.classification,
            f"control ({identity.identifier}): {identity.dependency_explanation}",
        )
    if keys & PLANCK_UNIT_KEYS:
        return (
            "Planck-unit rearrangement",
            "not independent of G; inspect algebraically before interpreting the ratio",
        )
    return (
        "exploratory dimensional match",
        "no identity assigned; dimensional validity and numerical proximity are not evidence",
    )


@dataclass(frozen=True, slots=True)
class Candidate:
    expression: str
    exponents: dict[str, str]
    dimension: Dimension
    value_si: float
    ratio_to_g: float
    log10_ratio: float
    abs_log10_ratio: float
    exponent_complexity: int
    constant_count: int
    rank_score: float
    classification: str
    assessment: str

    def rank_key(self) -> tuple[float, int, int, str]:
        return (
            self.rank_score,
            self.exponent_complexity,
            self.constant_count,
            self.expression,
        )

    def as_csv_row(self) -> dict[str, str | int | float]:
        return {
            "expression": self.expression,
            "exponents": json.dumps(self.exponents, sort_keys=True),
            "dimension": str(self.dimension),
            "value_si": f"{self.value_si:.12e}",
            "ratio_to_G": f"{self.ratio_to_g:.12e}",
            "log10_ratio": f"{self.log10_ratio:.12f}",
            "abs_log10_ratio": f"{self.abs_log10_ratio:.12f}",
            "exponent_complexity": self.exponent_complexity,
            "constant_count": self.constant_count,
            "rank_score": f"{self.rank_score:.12f}",
            "classification": self.classification,
            "assessment": self.assessment,
        }


def allowed_powers(max_abs_power: int, max_denominator: int) -> tuple[Fraction, ...]:
    """Return distinct nonzero rationals p with |p| <= max_abs_power."""

    if max_abs_power < 1:
        raise ValueError("max_abs_power must be at least 1")
    if max_denominator < 1:
        raise ValueError("max_denominator must be at least 1")
    powers = {
        Fraction(numerator, denominator)
        for denominator in range(1, max_denominator + 1)
        for numerator in range(-max_abs_power * denominator, max_abs_power * denominator + 1)
        if numerator != 0
    }
    return tuple(sorted(powers))


def search_candidates(
    generators: Sequence[PhysicalConstant] = DEFAULT_SEARCH_CONSTANTS,
    *,
    target: PhysicalConstant = GRAVITATIONAL_CONSTANT_G,
    max_factors: int = 3,
    max_abs_power: int = 3,
    max_denominator: int = 1,
) -> list[Candidate]:
    """Search bounded products and return exact dimensional matches ranked by score."""

    if max_factors < 1:
        raise ValueError("max_factors must be at least 1")
    keys = [constant.key for constant in generators]
    if len(keys) != len(set(keys)):
        raise ValueError("generator keys must be unique")
    if target.key in keys:
        raise ValueError("the measured target must not be one of its own generators")

    powers_to_try = allowed_powers(max_abs_power, max_denominator)
    target_log10 = math.log10(target.value_si)
    matches: list[Candidate] = []

    for factor_count in range(1, min(max_factors, len(generators)) + 1):
        for selected in combinations(generators, factor_count):
            for powers in product(powers_to_try, repeat=factor_count):
                dimension = DIMENSIONLESS
                value_log10 = 0.0
                for constant, power in zip(selected, powers):
                    dimension = dimension * constant.dimension**power
                    value_log10 += float(power) * math.log10(constant.value_si)
                if dimension != target.dimension:
                    continue

                log10_ratio = value_log10 - target_log10
                ratio = 10.0**log10_ratio
                complexity = _exponent_complexity(powers)
                rank_score = abs(log10_ratio) + 0.02 * complexity + 0.05 * (factor_count - 1)
                classification, assessment = _classification(selected, powers)
                matches.append(
                    Candidate(
                        expression=_expression(selected, powers),
                        exponents={
                            constant.key: _format_fraction(power)
                            for constant, power in zip(selected, powers)
                        },
                        dimension=dimension,
                        value_si=10.0**value_log10,
                        ratio_to_g=ratio,
                        log10_ratio=log10_ratio,
                        abs_log10_ratio=abs(log10_ratio),
                        exponent_complexity=complexity,
                        constant_count=factor_count,
                        rank_score=rank_score,
                        classification=classification,
                        assessment=assessment,
                    )
                )

    return sorted(matches, key=Candidate.rank_key)


CSV_FIELDS = (
    "expression",
    "exponents",
    "dimension",
    "value_si",
    "ratio_to_G",
    "log10_ratio",
    "abs_log10_ratio",
    "exponent_complexity",
    "constant_count",
    "rank_score",
    "classification",
    "assessment",
)


def write_candidates(path: Path, candidates: Sequence[Candidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(candidate.as_csv_row() for candidate in candidates)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-factors", type=int, default=3)
    parser.add_argument("--max-abs-power", type=int, default=3)
    parser.add_argument(
        "--max-denominator",
        type=int,
        default=1,
        help="1 searches integer exponents; 2 also permits half-integers, and so on",
    )
    parser.add_argument("--limit", type=int, default=50, help="rows to print and save")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Experiments/GCoincidences/candidates.csv"),
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    candidates = search_candidates(
        max_factors=args.max_factors,
        max_abs_power=args.max_abs_power,
        max_denominator=args.max_denominator,
    )
    selected = candidates[: max(args.limit, 0)]
    write_candidates(args.output, selected)

    print(
        f"Found {len(candidates)} exact dimensional matches; "
        f"wrote {len(selected)} to {args.output}."
    )
    print("Dimensional matches are exploratory observations, not physical laws.\n")
    print(f"{'expression':<32} {'ratio/G':>13} {'|log10|':>10}  classification")
    for candidate in selected[:15]:
        print(
            f"{candidate.expression:<32} {candidate.ratio_to_g:>13.6g} "
            f"{candidate.abs_log10_ratio:>10.6f}  {candidate.classification}"
        )


if __name__ == "__main__":
    main()
