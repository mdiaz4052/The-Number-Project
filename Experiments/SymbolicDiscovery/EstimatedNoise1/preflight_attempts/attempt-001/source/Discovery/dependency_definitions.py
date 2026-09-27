"""Exact, validated dependency definitions for the current constant catalog.

The word ``atomic`` is local to this model: it means that this catalog stops
expanding the quantity.  It does not assert metaphysical fundamentality or
experimental independence.  Derived definitions use exact rational exponents
and are checked against the existing SI dimension vectors before publication.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Iterable, Mapping

from Discovery.constants import DEFAULT_SEARCH_CONSTANTS, GRAVITATIONAL_CONSTANT_G
from Discovery.dimensions import DIMENSIONLESS, Dimension
from Discovery.planck_identities import ExponentSignature, normalize_exponent_signature


@dataclass(frozen=True, slots=True)
class DependencyDefinition:
    """One atomic catalog entry or one exact derived exponent definition."""

    key: str
    expansion: ExponentSignature | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key:
            raise ValueError("dependency keys must be nonempty strings")
        if self.expansion is not None:
            object.__setattr__(
                self,
                "expansion",
                normalize_exponent_signature(self.expansion),
            )

    @property
    def kind(self) -> str:
        """Return the stable catalog kind used by the artifact."""

        return "atomic" if self.expansion is None else "derived"


@dataclass(frozen=True, slots=True)
class ExpansionResult:
    """A fully expanded exact signature plus any unresolved surface factors."""

    signature: ExponentSignature
    unresolved_factors: tuple[str, ...]

    @property
    def is_fully_resolved(self) -> bool:
        return not self.unresolved_factors


def _combine_scaled_signatures(
    terms: Iterable[tuple[ExponentSignature, Fraction]],
) -> ExponentSignature:
    """Add scaled signatures and normalize cancelled powers away."""

    totals: dict[str, Fraction] = {}
    for signature, multiplier in terms:
        for key, exponent in signature:
            totals[key] = totals.get(key, Fraction(0)) + multiplier * exponent
    return tuple(sorted((key, exponent) for key, exponent in totals.items() if exponent))


@dataclass(frozen=True, slots=True)
class DependencyCatalog:
    """An immutable set of validated definitions and their atomic expansions."""

    definitions: Mapping[str, DependencyDefinition]
    expanded_definitions: Mapping[str, ExponentSignature]
    dimensions: Mapping[str, Dimension]
    atomic_basis: tuple[str, ...]

    def expand_signature(self, surface: ExponentSignature) -> ExpansionResult:
        """Expand a surface monomial, retaining unknown factors as unresolved terms."""

        normalized_surface = normalize_exponent_signature(surface)
        scaled: list[tuple[ExponentSignature, Fraction]] = []
        unresolved: set[str] = set()
        for key, exponent in normalized_surface:
            expansion = self.expanded_definitions.get(key)
            if expansion is None:
                expansion = ((key, Fraction(1)),)
                unresolved.add(key)
            scaled.append((expansion, exponent))
        return ExpansionResult(
            signature=_combine_scaled_signatures(scaled),
            unresolved_factors=tuple(sorted(unresolved)),
        )


def build_dependency_catalog(
    definitions: Iterable[DependencyDefinition],
    dimensions: Mapping[str, Dimension],
    *,
    required_keys: Iterable[str] = (),
) -> DependencyCatalog:
    """Validate definitions, dimensions, references, cycles, and required coverage."""

    if not isinstance(dimensions, Mapping):
        raise TypeError("dependency dimensions must be a mapping")

    by_key: dict[str, DependencyDefinition] = {}
    for definition in definitions:
        if not isinstance(definition, DependencyDefinition):
            raise TypeError("catalog entries must be DependencyDefinition values")
        if definition.key in by_key:
            raise ValueError(f"duplicate dependency key: {definition.key}")
        by_key[definition.key] = definition
    if not by_key:
        raise ValueError("the dependency catalog must not be empty")

    for key, definition in by_key.items():
        if key not in dimensions:
            raise ValueError(f"missing SI dimension for dependency key: {key}")
        if not isinstance(dimensions[key], Dimension):
            raise TypeError(f"SI dimension for {key} must be a Dimension")
        if definition.expansion is None:
            continue
        unknown = {factor for factor, _ in definition.expansion} - set(by_key)
        if unknown:
            raise ValueError(
                f"definition for {key} refers to unknown factor(s): {sorted(unknown)}"
            )

    required = tuple(required_keys)
    if any(not isinstance(key, str) or not key for key in required):
        raise ValueError("required dependency keys must be nonempty strings")
    missing_required = set(required) - set(by_key)
    if missing_required:
        raise ValueError(
            f"dependency catalog is missing required key(s): {sorted(missing_required)}"
        )

    expanded: dict[str, ExponentSignature] = {}
    visiting: list[str] = []

    def expand_key(key: str) -> ExponentSignature:
        cached = expanded.get(key)
        if cached is not None:
            return cached
        if key in visiting:
            cycle_start = visiting.index(key)
            cycle = visiting[cycle_start:] + [key]
            raise ValueError(f"cyclic dependency definition: {' -> '.join(cycle)}")

        visiting.append(key)
        definition = by_key[key]
        if definition.expansion is None:
            result = ((key, Fraction(1)),)
        else:
            result = _combine_scaled_signatures(
                (expand_key(factor), exponent)
                for factor, exponent in definition.expansion
            )
        visiting.pop()
        expanded[key] = result
        return result

    for key in by_key:
        expand_key(key)

    for key, definition in by_key.items():
        if definition.expansion is None:
            continue
        derived_dimension = DIMENSIONLESS
        for factor, exponent in definition.expansion:
            factor_dimension = dimensions[factor]
            if not isinstance(factor_dimension, Dimension):
                raise TypeError(f"SI dimension for {factor} must be a Dimension")
            derived_dimension = derived_dimension * factor_dimension**exponent
        if derived_dimension != dimensions[key]:
            raise ValueError(
                f"dimensionally inconsistent definition for {key}: "
                f"expected {dimensions[key]}, obtained {derived_dimension}"
            )

    atomic_basis = tuple(
        key for key, definition in by_key.items() if definition.expansion is None
    )
    return DependencyCatalog(
        definitions=MappingProxyType(dict(by_key)),
        expanded_definitions=MappingProxyType(dict(expanded)),
        dimensions=MappingProxyType({key: dimensions[key] for key in by_key}),
        atomic_basis=atomic_basis,
    )


DEFAULT_DEPENDENCY_DEFINITIONS = (
    DependencyDefinition("G"),
    DependencyDefinition("c"),
    DependencyDefinition("hbar"),
    DependencyDefinition("k_B"),
    DependencyDefinition("m_e"),
    DependencyDefinition("m_p"),
    DependencyDefinition("m_u"),
    DependencyDefinition(
        "l_P",
        (
            ("hbar", Fraction(1, 2)),
            ("G", Fraction(1, 2)),
            ("c", Fraction(-3, 2)),
        ),
    ),
    DependencyDefinition(
        "m_P",
        (
            ("hbar", Fraction(1, 2)),
            ("c", Fraction(1, 2)),
            ("G", Fraction(-1, 2)),
        ),
    ),
    DependencyDefinition(
        "t_P",
        (
            ("hbar", Fraction(1, 2)),
            ("G", Fraction(1, 2)),
            ("c", Fraction(-5, 2)),
        ),
    ),
    DependencyDefinition(
        "T_P",
        (
            ("hbar", Fraction(1, 2)),
            ("c", Fraction(5, 2)),
            ("G", Fraction(-1, 2)),
            ("k_B", Fraction(-1)),
        ),
    ),
)

_ALL_CURRENT_CONSTANTS = (GRAVITATIONAL_CONSTANT_G, *DEFAULT_SEARCH_CONSTANTS)
DEFAULT_CONSTANT_DIMENSIONS = MappingProxyType(
    {constant.key: constant.dimension for constant in _ALL_CURRENT_CONSTANTS}
)
DEFAULT_DEPENDENCY_CATALOG = build_dependency_catalog(
    DEFAULT_DEPENDENCY_DEFINITIONS,
    DEFAULT_CONSTANT_DIMENSIONS,
    required_keys=(constant.key for constant in _ALL_CURRENT_CONSTANTS),
)
