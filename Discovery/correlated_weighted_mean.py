"""Exact two-input correlated minimum-variance weighted-mean primitives."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction


class CorrelatedMeanError(ValueError):
    """Invalid covariance geometry or finite-resolution representation."""


@dataclass(frozen=True)
class Interval:
    low: Fraction
    high: Fraction

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise CorrelatedMeanError("interval low exceeds high")


@dataclass(frozen=True)
class TwoInputWeights:
    first: Fraction
    second: Fraction
    denominator: Fraction
    determinant: Fraction
    variance: Fraction


def decimal_fraction(value: str) -> Fraction:
    if not isinstance(value, str):
        raise CorrelatedMeanError("authoritative decimal must be a string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise CorrelatedMeanError("malformed decimal") from error
    if not number.is_finite():
        raise CorrelatedMeanError("decimal must be finite")
    return Fraction(number)


def decimal_cell(value: str, places: int) -> Interval:
    if not isinstance(places, int) or isinstance(places, bool) or places < 0:
        raise CorrelatedMeanError("printed decimal places must be a nonnegative integer")
    midpoint = decimal_fraction(value)
    half_width = Fraction(1, 2 * (10 ** places))
    return Interval(midpoint - half_width, midpoint + half_width)


def minimum_variance_unbiased_weights(
    sigma_first: Fraction,
    sigma_second: Fraction,
    covariance: Fraction,
) -> TwoInputWeights:
    if sigma_first <= 0 or sigma_second <= 0:
        raise CorrelatedMeanError("standard uncertainties must be positive")
    variance_first = sigma_first * sigma_first
    variance_second = sigma_second * sigma_second
    determinant = variance_first * variance_second - covariance * covariance
    if determinant <= 0:
        raise CorrelatedMeanError("covariance matrix must be positive definite")
    denominator = variance_first + variance_second - 2 * covariance
    if denominator <= 0:
        raise CorrelatedMeanError("minimum-variance denominator must be positive")
    first = (variance_second - covariance) / denominator
    second = 1 - first
    if first + second != 1:
        raise CorrelatedMeanError("weights do not satisfy unbiased normalization")
    variance = (
        first * first * variance_first
        + 2 * first * second * covariance
        + second * second * variance_second
    )
    if variance <= 0:
        raise CorrelatedMeanError("combined variance must be positive")
    return TwoInputWeights(first, second, denominator, determinant, variance)


def linear_enclosure(intervals: tuple[Interval, ...], weights: tuple[Fraction, ...]) -> Interval:
    if not intervals or len(intervals) != len(weights):
        raise CorrelatedMeanError("interval/weight arity mismatch")
    low = Fraction(0)
    high = Fraction(0)
    for interval, weight in zip(intervals, weights):
        if weight >= 0:
            low += weight * interval.low
            high += weight * interval.high
        else:
            low += weight * interval.high
            high += weight * interval.low
    return Interval(low, high)


def closed_intersection(first: Interval, second: Interval) -> Interval | None:
    low = max(first.low, second.low)
    high = min(first.high, second.high)
    return None if high < low else Interval(low, high)


def fraction_record(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
