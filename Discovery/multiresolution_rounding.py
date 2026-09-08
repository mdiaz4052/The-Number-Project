"""Exact intersection and classification for multi-resolution rounding constraints."""

from __future__ import annotations

from fractions import Fraction

from Discovery.rounding_consistency import (
    Calculation, Candidate, Interval, RoundingError, evaluate_point, rounding_bin,
)


def printed_constraint(center: Fraction, half_width: Fraction) -> Interval:
    """Return a closed conservative rounding-consistency interval."""
    return rounding_bin(center, half_width)


def intersect_closed(intervals: tuple[Interval, ...]) -> Interval | None:
    """Exact closed intersection; None denotes mutually disjoint constraints."""
    if not isinstance(intervals, tuple) or not intervals:
        raise RoundingError("multi-resolution terminal constraints must be a nonempty tuple")
    if any(not isinstance(interval, Interval) for interval in intervals):
        raise RoundingError("terminal constraint is not an Interval")
    low = max(interval.low for interval in intervals)
    high = min(interval.high for interval in intervals)
    return None if high < low else Interval(low, high)


def strict_witness(
    calculation: Calculation, candidate: Candidate, joint_interval: Interval
) -> bool:
    """Verify component interiors and strict interior of a nondegenerate joint target."""
    actual = evaluate_point(calculation.budget, candidate.values)
    if actual != candidate.evaluation:
        raise RoundingError("multi-resolution witness arithmetic differs from component values")
    if joint_interval.low == joint_interval.high:
        return False
    if not all(
        domain.contains(value, interior=True)
        for row, domains in zip(candidate.values, calculation.budget.components)
        for value, domain in zip(row, domains)
    ):
        return False
    target = joint_interval.square()
    value = actual.relative_variance_ppm_squared
    return target.low < value < target.high


def classify_multiresolution(
    calculation: Calculation, constraints: tuple[Interval, ...]
) -> tuple[str, int | None, str, Interval | None]:
    """Classify one calculation against all terminal representations jointly."""
    joint = intersect_closed(constraints)
    if joint is None:
        return "incompatible", None, "terminal_constraints_disjoint", None
    target = joint.square()
    if calculation.enclosure.high < target.low or target.high < calculation.enclosure.low:
        return (
            "incompatible",
            None,
            "component_box_disjoint_from_joint_terminal",
            joint,
        )
    if joint.low == joint.high:
        return "unresolved", None, "degenerate_joint_terminal", joint
    for index, candidate in enumerate(calculation.candidates):
        if strict_witness(calculation, candidate, joint):
            return "compatible", index, "scheduled_strict_interior_witness", joint
    return "unresolved", None, "no_scheduled_strict_interior_witness", joint


def interval_width(interval: Interval) -> Fraction:
    if not isinstance(interval, Interval):
        raise RoundingError("interval width requires an Interval")
    return interval.high - interval.low
