"""Exact algebra for SI dimension vectors.

This module models dimensions only.  It does not attach physical meaning to a
numerical relationship and it does not attempt automatic unit conversion.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping


BASE_DIMENSIONS = ("M", "L", "T", "I", "Theta", "N", "J")
"""Mass, length, time, current, temperature, amount, luminous intensity."""


@dataclass(frozen=True, slots=True)
class Dimension:
    """A product of SI base dimensions with exact rational exponents."""

    exponents: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        normalized = tuple(Fraction(exponent) for exponent in self.exponents)
        if len(normalized) != len(BASE_DIMENSIONS):
            raise ValueError(
                f"expected {len(BASE_DIMENSIONS)} exponents, got {len(normalized)}"
            )
        object.__setattr__(self, "exponents", normalized)

    @classmethod
    def from_mapping(cls, exponents: Mapping[str, int | Fraction]) -> Dimension:
        """Construct a vector by naming only its nonzero base exponents."""

        unknown = set(exponents) - set(BASE_DIMENSIONS)
        if unknown:
            raise ValueError(f"unknown base dimension(s): {sorted(unknown)}")
        return cls(tuple(Fraction(exponents.get(name, 0)) for name in BASE_DIMENSIONS))

    def __mul__(self, other: object) -> Dimension:
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(tuple(a + b for a, b in zip(self.exponents, other.exponents)))

    def __truediv__(self, other: object) -> Dimension:
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(tuple(a - b for a, b in zip(self.exponents, other.exponents)))

    def __pow__(self, exponent: int | Fraction) -> Dimension:
        power = Fraction(exponent)
        return Dimension(tuple(power * component for component in self.exponents))

    @property
    def is_dimensionless(self) -> bool:
        return all(exponent == 0 for exponent in self.exponents)

    def as_mapping(self) -> dict[str, Fraction]:
        return dict(zip(BASE_DIMENSIONS, self.exponents))

    def __str__(self) -> str:
        factors: list[str] = []
        for name, exponent in zip(BASE_DIMENSIONS, self.exponents):
            if exponent == 0:
                continue
            if exponent == 1:
                factors.append(name)
            elif exponent.denominator == 1:
                factors.append(f"{name}^{exponent.numerator}")
            else:
                factors.append(f"{name}^({exponent.numerator}/{exponent.denominator})")
        return " ".join(factors) if factors else "1"


DIMENSIONLESS = Dimension.from_mapping({})
MASS = Dimension.from_mapping({"M": 1})
LENGTH = Dimension.from_mapping({"L": 1})
TIME = Dimension.from_mapping({"T": 1})
ELECTRIC_CURRENT = Dimension.from_mapping({"I": 1})
TEMPERATURE = Dimension.from_mapping({"Theta": 1})
AMOUNT = Dimension.from_mapping({"N": 1})
LUMINOUS_INTENSITY = Dimension.from_mapping({"J": 1})

VELOCITY = LENGTH / TIME
ACCELERATION = LENGTH / TIME**2
AREA = LENGTH**2
FORCE = MASS * ACCELERATION
ENERGY = MASS * LENGTH**2 / TIME**2
ACTION = ENERGY * TIME
GRAVITATIONAL_CONSTANT = LENGTH**3 / (MASS * TIME**2)
