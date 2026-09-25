"""Traceable catalogue of the four certified Planck-unit controls.

The catalogue links an exact exponent signature used by Python to the matching
symbolic relation and Lean theorem.  Every entry is a *dependent* identity:
Planck length, mass, and time are themselves defined using ``G``.  Catalogue
membership therefore marks a consistency control, not a discovery or an
independent determination of the gravitational constant.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Iterable, Mapping


RationalExponent = int | Fraction
ExponentSignature = tuple[tuple[str, Fraction], ...]

KNOWN_PLANCK_IDENTITY_CLASSIFICATION = "known Planck-unit identity"
PLANCK_UNIT_KEYS = frozenset({"l_P", "m_P", "t_P", "T_P"})


def normalize_exponent_signature(
    terms: Iterable[tuple[str, RationalExponent]],
) -> ExponentSignature:
    """Return a validated, order-independent exact exponent signature.

    Zero powers and duplicate factor keys are rejected so that two syntactically
    different records cannot silently describe the same expression.
    """

    normalized: list[tuple[str, Fraction]] = []
    seen_keys: set[str] = set()
    for term in terms:
        if not isinstance(term, tuple) or len(term) != 2:
            raise TypeError("signature terms must be (factor key, exponent) pairs")
        key, exponent = term
        if not isinstance(key, str) or not key:
            raise ValueError("signature factor keys must be nonempty strings")
        if key in seen_keys:
            raise ValueError(f"duplicate signature factor key: {key}")
        if isinstance(exponent, bool) or not isinstance(exponent, (int, Fraction)):
            raise TypeError("signature exponents must be exact integers or Fractions")
        exact_exponent = Fraction(exponent)
        if exact_exponent == 0:
            raise ValueError(f"signature exponent for {key} must be nonzero")
        normalized.append((key, exact_exponent))
        seen_keys.add(key)
    if not normalized:
        raise ValueError("an exponent signature must contain at least one factor")
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class PlanckIdentity:
    """One exact Python signature and its formal, epistemic metadata."""

    identifier: str
    signature: ExponentSignature
    symbolic_relation: str
    classification: str
    dependency_explanation: str
    lean_theorem_name: str

    def __post_init__(self) -> None:
        text_fields = {
            "identifier": self.identifier,
            "symbolic_relation": self.symbolic_relation,
            "classification": self.classification,
            "dependency_explanation": self.dependency_explanation,
            "lean_theorem_name": self.lean_theorem_name,
        }
        for field_name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a nonempty string")
        if self.classification != KNOWN_PLANCK_IDENTITY_CLASSIFICATION:
            raise ValueError("certified controls must retain the known-identity classification")
        normalized_signature = normalize_exponent_signature(self.signature)
        if not ({key for key, _ in normalized_signature} & PLANCK_UNIT_KEYS):
            raise ValueError("a Planck identity signature must contain a Planck unit")
        object.__setattr__(self, "signature", normalized_signature)


def build_planck_identity_catalog(
    identities: Iterable[PlanckIdentity],
) -> Mapping[ExponentSignature, PlanckIdentity]:
    """Build a read-only lookup, rejecting duplicate identifiers or signatures."""

    by_signature: dict[ExponentSignature, PlanckIdentity] = {}
    identifiers: set[str] = set()
    for identity in identities:
        if not isinstance(identity, PlanckIdentity):
            raise TypeError("catalogue entries must be PlanckIdentity values")
        if identity.identifier in identifiers:
            raise ValueError(f"duplicate Planck identity identifier: {identity.identifier}")
        if identity.signature in by_signature:
            raise ValueError(f"duplicate Planck identity signature: {identity.signature}")
        identifiers.add(identity.identifier)
        by_signature[identity.signature] = identity
    if not by_signature:
        raise ValueError("the Planck identity catalogue must not be empty")
    return MappingProxyType(by_signature)


PLANCK_IDENTITIES = (
    PlanckIdentity(
        identifier="speed-light-length-mass",
        signature=(("c", Fraction(2)), ("l_P", Fraction(1)), ("m_P", Fraction(-1))),
        symbolic_relation="G = c^2 * l_P / m_P",
        classification=KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
        dependency_explanation=(
            "Planck length and Planck mass are defined from G, c, and hbar; "
            "the relation is an algebraic consistency control."
        ),
        lean_theorem_name=(
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_speedOfLight_sq_mul_planckLength_div_planckMass"
        ),
    ),
    PlanckIdentity(
        identifier="hbar-light-planck-mass",
        signature=(("hbar", Fraction(1)), ("c", Fraction(1)), ("m_P", Fraction(-2))),
        symbolic_relation="G = hbar * c / m_P^2",
        classification=KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
        dependency_explanation=(
            "Planck mass is defined by m_P^2 = hbar*c/G; this is that definition "
            "solved back for G."
        ),
        lean_theorem_name=(
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_reducedPlanckConstant_mul_speedOfLight_div_planckMass_sq"
        ),
    ),
    PlanckIdentity(
        identifier="light-time-planck-mass",
        signature=(("c", Fraction(3)), ("t_P", Fraction(1)), ("m_P", Fraction(-1))),
        symbolic_relation="G = c^3 * t_P / m_P",
        classification=KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
        dependency_explanation=(
            "Planck time and Planck mass are defined from G, c, and hbar; "
            "the relation is an algebraic consistency control."
        ),
        lean_theorem_name=(
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_speedOfLight_cubed_mul_planckTime_div_planckMass"
        ),
    ),
    PlanckIdentity(
        identifier="light-planck-length-hbar",
        signature=(("c", Fraction(3)), ("l_P", Fraction(2)), ("hbar", Fraction(-1))),
        symbolic_relation="G = c^3 * l_P^2 / hbar",
        classification=KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
        dependency_explanation=(
            "Planck length is defined by l_P^2 = hbar*G/c^3; this is that definition "
            "solved back for G."
        ),
        lean_theorem_name=(
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_speedOfLight_cubed_mul_planckLength_sq_div_"
            "reducedPlanckConstant"
        ),
    ),
)

PLANCK_IDENTITIES_BY_SIGNATURE = build_planck_identity_catalog(PLANCK_IDENTITIES)
