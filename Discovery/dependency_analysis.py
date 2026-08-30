"""Classify G-dimensional candidates by exact definitional provenance.

This module deliberately keeps dimensional matching, registered algebraic
dependency, Lean certification, and numerical magnitude separate.  Exact
``Fraction`` substitution determines dependency and equivalence; floating-point
values remain legacy navigation data and never control those classifications.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from Discovery.constants import DEFAULT_SEARCH_CONSTANTS, GRAVITATIONAL_CONSTANT_G
from Discovery.dependency_definitions import (
    DEFAULT_DEPENDENCY_CATALOG,
    DependencyCatalog,
)
from Discovery.dimensional_search import Candidate, search_candidates
from Discovery.dimensions import BASE_DIMENSIONS, DIMENSIONLESS
from Discovery.monomial_constraints import (
    LinearSystemSolution,
    NamedFactor,
    solve_monomial_constraints,
)
from Discovery.planck_identities import (
    ExponentSignature,
    PLANCK_IDENTITIES,
    PLANCK_IDENTITIES_BY_SIGNATURE,
    normalize_exponent_signature,
)


DEFAULT_OUTPUT = Path("Experiments/GCoincidences/dependency_analysis.json")
DEFAULT_SEARCH_BOUNDS = {
    "max_factors": 3,
    "max_abs_power": 3,
    "max_denominator": 1,
}
TARGET_KEY = "G"

TARGET_RECONSTRUCTION = "target_reconstruction"
TARGET_DEPENDENT = "target_dependent"
NO_REGISTERED_TARGET_DEPENDENCY = "no_registered_target_dependency"
UNRESOLVED_PROVENANCE = "unresolved_provenance"

LEAN_CERTIFIED = "lean_certified"
EXACT_PYTHON_REDUCTION_ONLY = "exact_python_reduction_only"
NOT_APPLICABLE = "not_applicable"

TARGET_SIGNATURE: ExponentSignature = ((TARGET_KEY, Fraction(1)),)


def fraction_text(value: Fraction) -> str:
    """Render an exact rational without decimal approximation."""

    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def signature_record(signature: ExponentSignature) -> list[dict[str, str]]:
    """Return the canonical sorted JSON representation of a signature."""

    return [
        {"factor": factor, "exponent": fraction_text(exponent)}
        for factor, exponent in signature
    ]


def _signature_text(signature: ExponentSignature) -> str:
    if not signature:
        return "1"
    return "|".join(
        f"{factor}:{fraction_text(exponent)}" for factor, exponent in signature
    )


def _signature_power(signature: ExponentSignature, factor: str) -> Fraction:
    return next(
        (exponent for key, exponent in signature if key == factor),
        Fraction(0),
    )


def candidate_surface_signature(candidate: Candidate) -> ExponentSignature:
    """Recover a candidate's exact canonical surface signature."""

    return normalize_exponent_signature(
        (key, Fraction(exponent)) for key, exponent in candidate.exponents.items()
    )


@dataclass(frozen=True, slots=True)
class AnalyzedCandidate:
    """One legacy search candidate with orthogonal provenance metadata."""

    candidate: Candidate
    surface_signature: ExponentSignature
    expanded_dependency_signature: ExponentSignature
    unresolved_factors: tuple[str, ...]
    power_of_g: Fraction
    dependency_status: str
    certification_status: str
    lean_theorem_name: str | None
    equivalence_group_identifier: str = ""
    equivalence_group_size: int = 0
    explanation: str = ""


def _classify_dependency(
    expanded_signature: ExponentSignature,
    unresolved_factors: tuple[str, ...],
) -> tuple[str, Fraction]:
    g_power = _signature_power(expanded_signature, TARGET_KEY)
    if unresolved_factors:
        return UNRESOLVED_PROVENANCE, g_power
    if expanded_signature == TARGET_SIGNATURE:
        return TARGET_RECONSTRUCTION, g_power
    if g_power != 0:
        return TARGET_DEPENDENT, g_power
    return NO_REGISTERED_TARGET_DEPENDENCY, g_power


def _certification(
    surface_signature: ExponentSignature,
    dependency_status: str,
) -> tuple[str, str | None]:
    identity = PLANCK_IDENTITIES_BY_SIGNATURE.get(surface_signature)
    if identity is not None:
        if dependency_status != TARGET_RECONSTRUCTION:
            raise RuntimeError(
                f"Lean-certified signature {identity.identifier} did not reduce to G"
            )
        return LEAN_CERTIFIED, identity.lean_theorem_name
    if dependency_status == TARGET_RECONSTRUCTION:
        return EXACT_PYTHON_REDUCTION_ONLY, None
    return NOT_APPLICABLE, None


def _explanation(
    dependency_status: str,
    certification_status: str,
    power_of_g: Fraction,
    expanded_signature: ExponentSignature,
    unresolved_factors: tuple[str, ...],
    lean_theorem_name: str | None,
) -> str:
    if dependency_status == UNRESOLVED_PROVENANCE:
        factors = ", ".join(unresolved_factors)
        return (
            f"The current catalog cannot fully expand: {factors}. No complete "
            "provenance or equivalence claim is available."
        )
    if dependency_status == TARGET_RECONSTRUCTION:
        if certification_status == LEAN_CERTIFIED:
            return (
                "Exact registered substitution reduces the expression to G^1. "
                f"The linked declaration {lean_theorem_name} kernel-checks the "
                "corresponding symbolic identity, whose Planck-unit premises already "
                "contain G."
            )
        return (
            "Exact registered substitution reduces the expression to G^1 in Python. "
            "No Lean theorem is presently linked to this surface signature, and the "
            "Planck-unit definitions already contain G."
        )
    if dependency_status == TARGET_DEPENDENT:
        return (
            "Registered substitution leaves G with power "
            f"{fraction_text(power_of_g)} and also leaves other atoms "
            f"({_signature_text(expanded_signature)}). The expression therefore "
            "inherits G but is not an exact reconstruction of G."
        )
    return (
        "After every current registered definition is expanded, the power of G is 0. "
        "This means no registered algebraic dependence was found; it does not establish "
        "experimental, causal, or metaphysical independence."
    )


def _group_key(record: AnalyzedCandidate) -> str:
    if record.unresolved_factors:
        return "unresolved-surface|" + _signature_text(record.surface_signature)
    return "resolved-expansion|" + _signature_text(
        record.expanded_dependency_signature
    )


def _group_identifier(group_key: str) -> str:
    digest = hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:16]
    return f"eq-{digest}"


def analyze_candidates(
    candidates: Sequence[Candidate],
    *,
    catalog: DependencyCatalog = DEFAULT_DEPENDENCY_CATALOG,
) -> tuple[AnalyzedCandidate, ...]:
    """Expand, classify, and deterministically group candidate signatures."""

    provisional: list[AnalyzedCandidate] = []
    for candidate in candidates:
        surface = candidate_surface_signature(candidate)
        expansion = catalog.expand_signature(surface)
        dependency_status, power_of_g = _classify_dependency(
            expansion.signature,
            expansion.unresolved_factors,
        )
        certification_status, theorem_name = _certification(
            surface,
            dependency_status,
        )
        provisional.append(
            AnalyzedCandidate(
                candidate=candidate,
                surface_signature=surface,
                expanded_dependency_signature=expansion.signature,
                unresolved_factors=expansion.unresolved_factors,
                power_of_g=power_of_g,
                dependency_status=dependency_status,
                certification_status=certification_status,
                lean_theorem_name=theorem_name,
                explanation=_explanation(
                    dependency_status,
                    certification_status,
                    power_of_g,
                    expansion.signature,
                    expansion.unresolved_factors,
                    theorem_name,
                ),
            )
        )

    group_sizes: dict[str, int] = {}
    group_ids: dict[str, str] = {}
    id_owners: dict[str, str] = {}
    for record in provisional:
        key = _group_key(record)
        group_sizes[key] = group_sizes.get(key, 0) + 1
        identifier = _group_identifier(key)
        other_key = id_owners.get(identifier)
        if other_key is not None and other_key != key:
            raise RuntimeError("equivalence-group identifier collision")
        id_owners[identifier] = key
        group_ids[key] = identifier

    return tuple(
        replace(
            record,
            equivalence_group_identifier=group_ids[_group_key(record)],
            equivalence_group_size=group_sizes[_group_key(record)],
        )
        for record in provisional
    )


def analyze_default_candidates() -> tuple[AnalyzedCandidate, ...]:
    """Run the unchanged bounded search and add dependency metadata."""

    return analyze_candidates(search_candidates(**DEFAULT_SEARCH_BOUNDS))


def solve_default_dimensional_system() -> LinearSystemSolution:
    """Solve the complete ten-generator dimensional system against G."""

    factors = tuple(
        NamedFactor(constant.key, constant.dimension.exponents)
        for constant in DEFAULT_SEARCH_CONSTANTS
    )
    return solve_monomial_constraints(
        factors,
        GRAVITATIONAL_CONSTANT_G.dimension.exponents,
    )


def _vector(values: Sequence[Fraction]) -> list[str]:
    return [fraction_text(value) for value in values]


def _matrix(values: Sequence[Sequence[Fraction]]) -> list[list[str]]:
    return [_vector(row) for row in values]


def _factor_text(key: str, power: Fraction) -> str:
    if power == 1:
        return key
    rendered = fraction_text(power)
    return f"{key}^{rendered}" if power.denominator == 1 else f"{key}^({rendered})"


def _monomial_text(keys: Sequence[str], powers: Sequence[Fraction]) -> str:
    numerator = [
        _factor_text(key, power)
        for key, power in zip(keys, powers)
        if power > 0
    ]
    denominator = [
        _factor_text(key, -power)
        for key, power in zip(keys, powers)
        if power < 0
    ]
    numerator_text = " * ".join(numerator) if numerator else "1"
    if not denominator:
        return numerator_text
    denominator_text = " * ".join(denominator)
    if len(denominator) > 1:
        denominator_text = f"({denominator_text})"
    return f"{numerator_text} / {denominator_text}"


def _dimensional_system_record(solution: LinearSystemSolution) -> dict[str, Any]:
    if solution.particular_solution is None:
        raise RuntimeError("the default dimensional system unexpectedly has no solution")

    generator_dimensions = {
        constant.key: constant.dimension for constant in DEFAULT_SEARCH_CONSTANTS
    }
    basis_records = []
    for direction in solution.nullspace_basis:
        dimension = DIMENSIONLESS
        for key, exponent in zip(solution.factor_keys, direction):
            dimension = dimension * generator_dimensions[key] ** exponent
        if not dimension.is_dimensionless:
            raise RuntimeError("reported nullspace direction is not dimensionless")
        basis_records.append(
            {
                "exponent_vector": _vector(direction),
                "dimensionless_monomial": _monomial_text(
                    solution.factor_keys,
                    direction,
                ),
            }
        )

    return {
        "status": solution.status,
        "rank": solution.rank,
        "nullity": solution.nullity,
        "pivot_columns_zero_based": list(solution.pivot_columns),
        "free_columns_zero_based": list(solution.free_columns),
        "augmented_rref": _matrix(solution.rref),
        "particular_solution": _vector(solution.particular_solution),
        "particular_monomial": _monomial_text(
            solution.factor_keys,
            solution.particular_solution,
        ),
        "nullspace_basis": basis_records,
        "interpretation": {
            "rank": (
                "The generator dimensions span four independent SI-dimension "
                "directions."
            ),
            "nullity": (
                "Six independent exponent changes preserve the dimensions; each is a "
                "dimensionless transformation."
            ),
            "basis_nonuniqueness": (
                "This displayed basis is deterministic for the selected ordering, but "
                "other bases can span the same nullspace."
            ),
            "scope": (
                "The formula is underdetermined by the stated dimensional information, "
                "not proven to be underdetermined by nature."
            ),
        },
    }


def _candidate_record(record: AnalyzedCandidate) -> dict[str, Any]:
    return {
        "expression": record.candidate.expression,
        "surface_signature": signature_record(record.surface_signature),
        "expanded_dependency_signature": signature_record(
            record.expanded_dependency_signature
        ),
        "power_of_G": fraction_text(record.power_of_g),
        "dependency_status": record.dependency_status,
        "certification_status": record.certification_status,
        "lean_theorem_name": record.lean_theorem_name,
        "equivalence_group_identifier": record.equivalence_group_identifier,
        "equivalence_group_size": record.equivalence_group_size,
        "unresolved_factors": list(record.unresolved_factors),
        "explanation": record.explanation,
        "search_record": record.candidate.as_csv_row(),
    }


def _equivalence_group_records(
    candidates: Sequence[AnalyzedCandidate],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[AnalyzedCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.equivalence_group_identifier, []).append(candidate)

    records = []
    for identifier, members in sorted(grouped.items()):
        representative = members[0]
        records.append(
            {
                "identifier": identifier,
                "size": len(members),
                "fully_resolved": not representative.unresolved_factors,
                "expanded_dependency_signature": signature_record(
                    representative.expanded_dependency_signature
                ),
                "candidate_expressions": sorted(
                    member.candidate.expression for member in members
                ),
            }
        )
    return records


def _catalog_record(catalog: DependencyCatalog) -> dict[str, Any]:
    derived = []
    for key, definition in catalog.definitions.items():
        if definition.expansion is None:
            continue
        derived.append(
            {
                "key": key,
                "definition_signature": signature_record(definition.expansion),
                "fully_expanded_signature": signature_record(
                    catalog.expanded_definitions[key]
                ),
                "dimension": _vector(catalog.dimensions[key].exponents),
            }
        )
    return {
        "atomic_basis": list(catalog.atomic_basis),
        "atomic_meaning": (
            "The present catalog stops expansion at these quantities; atomic does not "
            "mean metaphysically fundamental or experimentally independent."
        ),
        "derived_definitions": derived,
    }


def _status_counts(
    candidates: Sequence[AnalyzedCandidate],
    attribute: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        value = getattr(candidate, attribute)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


_EXPECTED_RECONSTRUCTION_SIGNATURES = frozenset(
    {
        normalize_exponent_signature((("c", 2), ("l_P", 1), ("m_P", -1))),
        normalize_exponent_signature((("c", 1), ("hbar", 1), ("m_P", -2))),
        normalize_exponent_signature((("c", 3), ("m_P", -1), ("t_P", 1))),
        normalize_exponent_signature((("c", 3), ("hbar", -1), ("l_P", 2))),
        normalize_exponent_signature((("l_P", 3), ("m_P", -1), ("t_P", -2))),
        normalize_exponent_signature((("hbar", 2), ("l_P", -1), ("m_P", -3))),
    }
)


def build_artifact() -> dict[str, Any]:
    """Build and validate the deterministic Milestone 3 artifact."""

    candidates = analyze_default_candidates()
    groups = _equivalence_group_records(candidates)
    dimensional_system = solve_default_dimensional_system()

    if len(candidates) != 21:
        raise RuntimeError(f"expected 21 default candidates, found {len(candidates)}")
    if len(groups) != 10:
        raise RuntimeError(f"expected 10 equivalence groups, found {len(groups)}")
    reconstructions = {
        candidate.surface_signature
        for candidate in candidates
        if candidate.dependency_status == TARGET_RECONSTRUCTION
    }
    if reconstructions != _EXPECTED_RECONSTRUCTION_SIGNATURES:
        raise RuntimeError("the six expected target reconstructions changed")
    if sum(
        candidate.certification_status == LEAN_CERTIFIED for candidate in candidates
    ) != 4:
        raise RuntimeError("expected exactly four Lean-certified controls")
    if sum(
        candidate.certification_status == EXACT_PYTHON_REDUCTION_ONLY
        for candidate in candidates
    ) != 2:
        raise RuntimeError("expected exactly two Python-only target reconstructions")
    if (
        dimensional_system.status != "affine"
        or dimensional_system.rank != 4
        or dimensional_system.nullity != 6
    ):
        raise RuntimeError("unexpected default dimensional rank/nullity result")

    return {
        "schema_version": 1,
        "analysis": "dependency-aware provenance of G-dimensional candidates",
        "target": {
            "key": TARGET_KEY,
            "dimension": _vector(GRAVITATIONAL_CONSTANT_G.dimension.exponents),
            "expanded_signature": signature_record(TARGET_SIGNATURE),
        },
        "generator_order": [constant.key for constant in DEFAULT_SEARCH_CONSTANTS],
        "search_bounds": dict(DEFAULT_SEARCH_BOUNDS),
        "candidate_count": len(candidates),
        "equivalence_group_count": len(groups),
        "dependency_status_counts": _status_counts(candidates, "dependency_status"),
        "certification_status_counts": _status_counts(
            candidates,
            "certification_status",
        ),
        "dependency_model": _catalog_record(DEFAULT_DEPENDENCY_CATALOG),
        "certification_catalog": [
            {
                "identifier": identity.identifier,
                "surface_signature": signature_record(identity.signature),
                "lean_theorem_name": identity.lean_theorem_name,
            }
            for identity in PLANCK_IDENTITIES
        ],
        "equivalence_rule": (
            "Two fully resolved candidates are grouped exactly when their expanded "
            "dependency signatures are identical. Dimensions, decimal proximity, and "
            "ratios to G do not determine groups."
        ),
        "equivalence_groups": groups,
        "candidates": [_candidate_record(candidate) for candidate in candidates],
        "dimensional_system": {
            "base_dimension_order": list(BASE_DIMENSIONS),
            "generator_order": [constant.key for constant in DEFAULT_SEARCH_CONSTANTS],
            "matrix_orientation": (
                "rows are SI base dimensions; columns follow generator_order; the final "
                "RREF column is the G target"
            ),
            **_dimensional_system_record(dimensional_system),
        },
        "physical_boundary": {
            "established_here": [
                "exact SI-dimensional matches within the declared bounded search",
                "exact algebraic provenance under the registered definitions",
                "exact equivalence classes under those definitions",
                "which four surface identities have linked Lean declarations",
                "rank-4/nullity-6 underdetermination from the stated dimension matrix",
            ],
            "not_established_here": [
                "an experimental value of G",
                "the truth of a gravitational or entropic-gravity model's premises",
                "a noncircular physical origin or explanation of G",
                "experimental independence of any candidate",
                "a unique formula selected by nature",
            ],
            "remaining_empirical_problem": [
                "choose an operational measurement model connecting observables to G",
                "collect independent observations with calibrated SI-traceable apparatus",
                "quantify statistical and systematic uncertainty and model corrections",
                "infer G without using G-derived inputs as independent evidence",
                "test reproducibility across independent apparatus and methods",
            ],
            "remaining_explanatory_problem": [
                "supply a physical theory whose independent premises do not contain G "
                "directly or through registered derived quantities",
                "recover the observed gravitational coupling in the applicable limit",
                "produce falsifiable observable consequences beyond algebraic restatement",
                "compare those consequences with experiment",
            ],
            "formal_methods_role": (
                "Lean can certify deductions from explicit mathematical and empirical "
                "premises, but neither Lean nor exact Python substitution supplies the "
                "premises, calibrates apparatus, or performs a measurement."
            ),
        },
        "limitations_and_nonclaims": [
            "Dimensional equality is compatibility of units, not a physical law.",
            (
                "No registered dependence on G is weaker than independence; the catalog "
                "can be incomplete and its atomic endpoints are model-relative."
            ),
            (
                "Planck-derived target reconstructions inherit G and therefore cannot "
                "serve as independent measurements or noncircular explanations of G."
            ),
            (
                "Exact Python reduction is not automatically a Lean theorem; only the "
                "four linked declarations carry lean_certified status."
            ),
            (
                "Rounded numerical values and proximity to measured G do not determine "
                "dependency, equivalence, or certification."
            ),
            (
                "Rank and nullity describe the selected dimensional system, not all "
                "possible physical information or all of nature."
            ),
            "This milestone makes no new empirical claim or determination of G.",
        ],
    }


def serialize_artifact(artifact: dict[str, Any]) -> str:
    """Serialize with sorted keys, stable indentation, and one final newline."""

    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the dependency artifact is missing or stale",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    artifact = build_artifact()
    rendered = serialize_artifact(artifact)
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"stale or missing dependency artifact: {args.output}", file=sys.stderr)
            raise SystemExit(1)
        print(f"Dependency artifact is current: {args.output}")
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote dependency analysis to {args.output}.")
    print(
        f"{artifact['candidate_count']} candidates collapse into "
        f"{artifact['equivalence_group_count']} exact definitional-equivalence groups."
    )
    print("Six expressions reconstruct G: four Lean-certified, two exact-Python only.")
    print("Rank 4 and nullity 6 leave an affine dimensional family.")
    print("No empirical value, physical law, or independent explanation of G is claimed.")


if __name__ == "__main__":
    main()
