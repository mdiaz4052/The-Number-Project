"""Exact, conditional rounding consistency for positive weighted budgets.

No experiment, target constant, random sampling or physical evidence status lives
here. Interval endpoints are conservative enclosures, not attainable extrema.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from math import isqrt
import re


class RoundingError(ValueError):
    """Malformed evidence or an invalid calculation certificate."""


def decimal_fraction(value: str) -> Fraction:
    if not isinstance(value, str) or not re.fullmatch(
        r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value
    ):
        raise RoundingError("authoritative scalar must be a finite base-ten string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise RoundingError("malformed decimal") from error
    if not number.is_finite():
        raise RoundingError("non-finite decimal")
    return Fraction(number)


@dataclass(frozen=True)
class Interval:
    low: Fraction
    high: Fraction

    def __post_init__(self):
        if not all(isinstance(x, Fraction) for x in (self.low, self.high)):
            raise RoundingError("interval endpoints must be exact Fractions")
        if self.low < 0 or self.high < self.low:
            raise RoundingError("interval must be nonnegative and ordered")

    @classmethod
    def point(cls, value: Fraction) -> Interval:
        return cls(value, value)

    def __add__(self, other: Interval) -> Interval:
        return Interval(self.low + other.low, self.high + other.high)

    def __mul__(self, other: Interval) -> Interval:
        return Interval(self.low * other.low, self.high * other.high)

    def square(self) -> Interval:
        return Interval(self.low**2, self.high**2)

    def reciprocal(self) -> Interval:
        if self.low <= 0:
            raise RoundingError("reciprocal interval must be strictly positive")
        return Interval(1 / self.high, 1 / self.low)

    def contains(self, value: Fraction, *, interior: bool = False) -> bool:
        if interior and self.low != self.high:
            return self.low < value < self.high
        return self.low <= value <= self.high


ZERO = Interval.point(Fraction(0))


def interval_sum(values) -> Interval:
    return sum(values, ZERO)


def rounding_bin(center: Fraction, half_width: Fraction) -> Interval:
    if not isinstance(center, Fraction) or not isinstance(half_width, Fraction):
        raise RoundingError("rounding bin requires exact Fractions")
    if half_width < 0:
        raise RoundingError("negative rounding half-width")
    return Interval(center - half_width, center + half_width)


@dataclass(frozen=True)
class Budget:
    central_values: tuple[Fraction, ...]
    # Component-major layout: each row contains one value per run.
    components: tuple[tuple[Interval, ...], ...]
    correlations: tuple[str, ...]

    def __post_init__(self):
        if (not isinstance(self.central_values, tuple) or not self.central_values
                or any(not isinstance(g, Fraction) or g <= 0 for g in self.central_values)):
            raise RoundingError("central values must be a nonempty positive Fraction tuple")
        if not isinstance(self.components, tuple) or not self.components:
            raise RoundingError("missing component inventory")
        if (not isinstance(self.correlations, tuple)
                or len(self.correlations) != len(self.components)
                or any(c not in ("shared", "independent") for c in self.correlations)):
            raise RoundingError("unsupported or missing correlation class")
        for row in self.components:
            if (not isinstance(row, tuple) or len(row) != len(self.central_values)
                    or any(not isinstance(x, Interval) or x.low <= 0 for x in row)):
                raise RoundingError("component inventory must be positive and match all runs")


@dataclass(frozen=True)
class PointEvaluation:
    weights: tuple[Fraction, ...]
    propagation_coefficients: tuple[Fraction, ...]
    combined_central_value: Fraction
    relative_variance_ppm_squared: Fraction


def evaluate_point(budget: Budget, values: tuple[tuple[Fraction, ...], ...]) -> PointEvaluation:
    if (not isinstance(values, tuple) or len(values) != len(budget.components)
            or any(not isinstance(row, tuple) or len(row) != len(budget.central_values)
                   for row in values)):
        raise RoundingError("point shape differs from component inventory")
    for row, intervals in zip(values, budget.components):
        for value, domain in zip(row, intervals):
            if not isinstance(value, Fraction) or not domain.contains(value):
                raise RoundingError("candidate outside declared component domain")
    sums = tuple(sum(row[i]**2 for row in values) for i in range(len(budget.central_values)))
    inverse_variances = tuple(1 / (g*g*s) for g, s in zip(budget.central_values, sums))
    weights = tuple(v / sum(inverse_variances) for v in inverse_variances)
    central = sum(p*g for p, g in zip(weights, budget.central_values))
    q = tuple(p*g / central for p, g in zip(weights, budget.central_values))
    variance = Fraction(0)
    for row, correlation in zip(values, budget.correlations):
        terms = tuple(qi*xi for qi, xi in zip(q, row))
        variance += sum(terms)**2 if correlation == "shared" else sum(t*t for t in terms)
    return PointEvaluation(weights, q, central, variance)


def enclose_relative_variance(budget: Budget) -> Interval:
    n = len(budget.central_values)
    sums = tuple(interval_sum(row[i].square() for row in budget.components) for i in range(n))
    a = tuple((Interval.point(g)*s).reciprocal() for g, s in zip(budget.central_values, sums))
    q = tuple(Interval(
        a[i].low / (a[i].low + sum(a[j].high for j in range(n) if j != i)),
        a[i].high / (a[i].high + sum(a[j].low for j in range(n) if j != i)),
    ) for i in range(n))
    variance = ZERO
    for row, correlation in zip(budget.components, budget.correlations):
        terms = tuple(qi*xi for qi, xi in zip(q, row))
        variance += (interval_sum(terms).square() if correlation == "shared"
                     else interval_sum(t.square() for t in terms))
    return variance


@dataclass(frozen=True)
class Candidate:
    parameter: Fraction
    values: tuple[tuple[Fraction, ...], ...]
    evaluation: PointEvaluation


@dataclass(frozen=True)
class Calculation:
    budget: Budget
    enclosure: Interval
    candidates: tuple[Candidate, ...]


def calculate(budget: Budget, parameters: tuple[Fraction, ...]) -> Calculation:
    """Evaluate the full predetermined schedule; there is no comparison argument."""
    if (not isinstance(parameters, tuple) or not parameters
            or any(not isinstance(t, Fraction) or not -1 < t < 1 for t in parameters)
            or len(set(parameters)) != len(parameters)):
        raise RoundingError("candidate schedule must contain distinct exact interior parameters")
    enclosure = enclose_relative_variance(budget)
    candidates = []
    for parameter in parameters:
        values = tuple(tuple((x.low+x.high)/2 + parameter*(x.high-x.low)/2 for x in row)
                       for row in budget.components)
        evaluation = evaluate_point(budget, values)
        if not enclosure.contains(evaluation.relative_variance_ppm_squared):
            raise RoundingError("candidate escapes guaranteed enclosure")
        candidates.append(Candidate(parameter, values, evaluation))
    return Calculation(budget, enclosure, tuple(candidates))


def verify_witness(budget: Budget, candidate: Candidate, comparison: Interval) -> bool:
    actual = evaluate_point(budget, candidate.values)
    if actual != candidate.evaluation:
        raise RoundingError("witness arithmetic certificate differs from its component values")
    return (all(domain.contains(value, interior=True)
                for row, domains in zip(candidate.values, budget.components)
                for value, domain in zip(row, domains))
            and comparison.square().contains(actual.relative_variance_ppm_squared, interior=True))


def classify(calculation: Calculation, comparison: Interval) -> tuple[str, int | None]:
    target = comparison.square()
    if calculation.enclosure.high < target.low or target.high < calculation.enclosure.low:
        return "incompatible", None
    for index, candidate in enumerate(calculation.candidates):
        if verify_witness(calculation.budget, candidate, comparison):
            return "compatible", index
    return "unresolved", None


def rational_record(value: Fraction) -> dict:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def interval_record(value: Interval) -> dict:
    return {"low": rational_record(value.low), "high": rational_record(value.high)}


def sqrt_display_bounds(value: Interval, places: int) -> dict:
    """Exact outward square-root rounding, independent of Decimal context."""
    if type(places) is not int or not 0 <= places <= 30:
        raise RoundingError("display places must be an integer from 0 to 30")
    scale = 10**places
    low = isqrt(value.low.numerator*scale*scale // value.low.denominator)
    high = isqrt(value.high.numerator*scale*scale // value.high.denominator)
    if Fraction(high*high, scale*scale) < value.high:
        high += 1
    def formatted(integer):
        if not places:
            return str(integer)
        return f"{integer // scale}.{integer % scale:0{places}d}"
    return {"low": formatted(low), "high": formatted(high), "decimal_places": places,
            "interpretation": "outward-rounded conservative enclosure, not attainable extrema"}


def calculation_record(calculation: Calculation, *, places: int) -> dict:
    return {
        "relative_variance_enclosure_ppm_squared": interval_record(calculation.enclosure),
        "relative_uncertainty_enclosure_ppm": sqrt_display_bounds(calculation.enclosure, places),
        "candidates": [{
            "parameter": rational_record(c.parameter),
            "component_values_ppm": [[rational_record(v) for v in row] for row in c.values],
            "weights": [rational_record(p) for p in c.evaluation.weights],
            "propagation_coefficients": [rational_record(q) for q in c.evaluation.propagation_coefficients],
            "combined_central_value": rational_record(c.evaluation.combined_central_value),
            "relative_variance_ppm_squared": rational_record(c.evaluation.relative_variance_ppm_squared),
            "relative_uncertainty_ppm": sqrt_display_bounds(
                Interval.point(c.evaluation.relative_variance_ppm_squared), places),
        } for c in calculation.candidates],
    }
