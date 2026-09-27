"""Exact linear constraints for dimensional monomial exponents.

For a monomial ``x_1^p_1 * ... * x_n^p_n``, dimensional matching is a
linear system in the unknown rational exponents ``p_i``.  This module solves
that system with transparent Fraction-based row reduction.  It deliberately
returns an affine family when free variables remain instead of choosing an
arbitrary member of that family.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, Mapping, Sequence


RationalInput = int | Fraction


def _as_fraction(value: RationalInput) -> Fraction:
    """Accept only inputs that are exact before conversion."""

    if isinstance(value, bool):
        raise TypeError("boolean values are not rational coefficients")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    raise TypeError(f"expected int or Fraction, got {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class NamedFactor:
    """A named monomial factor and its exact dimension vector."""

    key: str
    dimension: tuple[Fraction, ...]

    def __init__(self, key: str, dimension: Sequence[RationalInput]) -> None:
        if not isinstance(key, str) or not key:
            raise ValueError("factor keys must be nonempty strings")
        normalized = tuple(_as_fraction(component) for component in dimension)
        if not normalized:
            raise ValueError("factor dimension vectors must not be empty")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "dimension", normalized)


@dataclass(frozen=True, slots=True)
class LinearConstraint:
    """An exact equation ``sum(coeff[key] * exponent[key]) = rhs``."""

    coefficients: tuple[tuple[str, Fraction], ...]
    rhs: Fraction
    label: str

    def __init__(
        self,
        coefficients: Mapping[str, RationalInput],
        rhs: RationalInput,
        *,
        label: str = "",
    ) -> None:
        if not isinstance(coefficients, Mapping):
            raise TypeError("constraint coefficients must be a mapping")
        normalized: list[tuple[str, Fraction]] = []
        for key, value in coefficients.items():
            if not isinstance(key, str) or not key:
                raise ValueError("constraint keys must be nonempty strings")
            coefficient = _as_fraction(value)
            if coefficient != 0:
                normalized.append((key, coefficient))
        if not isinstance(label, str):
            raise TypeError("constraint labels must be strings")
        object.__setattr__(self, "coefficients", tuple(normalized))
        object.__setattr__(self, "rhs", _as_fraction(rhs))
        object.__setattr__(self, "label", label)


@dataclass(frozen=True, slots=True)
class RREFResult:
    """The exact reduced row-echelon form and its pivot columns."""

    matrix: tuple[tuple[Fraction, ...], ...]
    pivot_columns: tuple[int, ...]


def reduced_row_echelon(matrix: Sequence[Sequence[RationalInput]]) -> RREFResult:
    """Compute exact RREF by Gauss-Jordan elimination over ``Fraction``."""

    if not matrix:
        raise ValueError("a matrix must contain at least one row")
    rows = [list(_as_fraction(value) for value in row) for row in matrix]
    width = len(rows[0])
    if width == 0:
        raise ValueError("matrix rows must not be empty")
    if any(len(row) != width for row in rows):
        raise ValueError("matrix rows must all have the same length")

    pivot_row = 0
    pivot_columns: list[int] = []
    for column in range(width):
        pivot = next(
            (row for row in range(pivot_row, len(rows)) if rows[row][column] != 0),
            None,
        )
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]

        pivot_value = rows[pivot_row][column]
        rows[pivot_row] = [value / pivot_value for value in rows[pivot_row]]
        for row_index, row in enumerate(rows):
            if row_index == pivot_row:
                continue
            multiplier = row[column]
            if multiplier != 0:
                rows[row_index] = [
                    value - multiplier * pivot_value
                    for value, pivot_value in zip(row, rows[pivot_row])
                ]

        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(rows):
            break

    return RREFResult(
        matrix=tuple(tuple(row) for row in rows),
        pivot_columns=tuple(pivot_columns),
    )


@dataclass(frozen=True, slots=True)
class LinearSystemSolution:
    """A unique solution, affine family, or proof of inconsistency."""

    status: Literal["unique", "affine", "inconsistent"]
    factor_keys: tuple[str, ...]
    rref: tuple[tuple[Fraction, ...], ...]
    pivot_columns: tuple[int, ...]
    free_columns: tuple[int, ...]
    rank: int
    nullity: int
    particular_solution: tuple[Fraction, ...] | None
    nullspace_basis: tuple[tuple[Fraction, ...], ...]


def solve_monomial_constraints(
    factors: Sequence[NamedFactor],
    target_dimension: Sequence[RationalInput],
    constraints: Sequence[LinearConstraint] = (),
) -> LinearSystemSolution:
    """Solve dimensional matching plus optional exact exponent constraints.

    Dimension components supply the rows of the coefficient matrix and factors
    supply its columns.  Contradictory equations are reported as an
    ``inconsistent`` result; malformed shapes or unknown names raise errors.
    """

    if not factors:
        raise ValueError("at least one factor is required")
    keys = tuple(factor.key for factor in factors)
    if len(keys) != len(set(keys)):
        raise ValueError("factor keys must be unique")

    target = tuple(_as_fraction(component) for component in target_dimension)
    if not target:
        raise ValueError("the target dimension vector must not be empty")
    for factor in factors:
        if len(factor.dimension) != len(target):
            raise ValueError(
                f"factor {factor.key!r} has dimension length {len(factor.dimension)}; "
                f"expected {len(target)}"
            )

    augmented: list[list[Fraction]] = [
        [factor.dimension[row] for factor in factors] + [target[row]]
        for row in range(len(target))
    ]
    key_to_column = {key: column for column, key in enumerate(keys)}
    for constraint in constraints:
        row = [Fraction(0) for _ in factors]
        for key, coefficient in constraint.coefficients:
            if key not in key_to_column:
                raise ValueError(f"constraint refers to unknown factor {key!r}")
            row[key_to_column[key]] = coefficient
        augmented.append(row + [constraint.rhs])

    reduction = reduced_row_echelon(augmented)
    variable_count = len(factors)
    pivot_columns = tuple(
        column for column in reduction.pivot_columns if column < variable_count
    )
    free_columns = tuple(
        column for column in range(variable_count) if column not in pivot_columns
    )
    rank = len(pivot_columns)
    nullity = variable_count - rank
    inconsistent = any(
        all(row[column] == 0 for column in range(variable_count))
        and row[variable_count] != 0
        for row in reduction.matrix
    )
    if inconsistent:
        return LinearSystemSolution(
            status="inconsistent",
            factor_keys=keys,
            rref=reduction.matrix,
            pivot_columns=pivot_columns,
            free_columns=free_columns,
            rank=rank,
            nullity=nullity,
            particular_solution=None,
            nullspace_basis=(),
        )

    pivot_rows = {
        column: row_index
        for row_index, column in enumerate(reduction.pivot_columns)
        if column < variable_count
    }
    particular = [Fraction(0) for _ in factors]
    for column, row_index in pivot_rows.items():
        particular[column] = reduction.matrix[row_index][variable_count]

    basis: list[tuple[Fraction, ...]] = []
    for free_column in free_columns:
        direction = [Fraction(0) for _ in factors]
        direction[free_column] = Fraction(1)
        for pivot_column, row_index in pivot_rows.items():
            direction[pivot_column] = -reduction.matrix[row_index][free_column]
        basis.append(tuple(direction))

    return LinearSystemSolution(
        status="unique" if nullity == 0 else "affine",
        factor_keys=keys,
        rref=reduction.matrix,
        pivot_columns=pivot_columns,
        free_columns=free_columns,
        rank=rank,
        nullity=nullity,
        particular_solution=tuple(particular),
        nullspace_basis=tuple(basis),
    )
