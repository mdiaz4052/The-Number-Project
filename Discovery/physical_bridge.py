"""Define a non-circular measurement-model contract for an estimate of ``G``.

This module validates structure, exact dimensions, algebraic target ancestry,
metrological provenance, and uncertainty declarations.  It deliberately does not
ingest observations or calculate a measured value of ``G``.  Decimal measurement
records use :class:`~decimal.Decimal`; binary floating-point values are rejected.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import sys
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from Discovery.dependency_definitions import (
    DEFAULT_DEPENDENCY_CATALOG,
    DependencyCatalog,
    DependencyDefinition,
    build_dependency_catalog,
)
from Discovery.dimensions import (
    DIMENSIONLESS,
    FORCE,
    GRAVITATIONAL_CONSTANT,
    LENGTH,
    MASS,
    Dimension,
)
from Discovery.planck_identities import (
    ExponentSignature,
    normalize_exponent_signature,
)


SCHEMA_VERSION = 1
TARGET_KEY = "G"
DEFAULT_CONTRACT_OUTPUT = Path(
    "Experiments/GMeasurements/physical_bridge_contract.json"
)
DEFAULT_EXAMPLE_OUTPUT = Path(
    "Experiments/GMeasurements/inverse_square_bridge_example.json"
)

SATISFIED = "satisfied"
INCOMPLETE = "incomplete"
UNRESOLVED = "unresolved"
NOT_APPLICABLE = "not_applicable"

TARGET_PATH_DETECTED = "target_path_detected"
NO_REGISTERED_TARGET_PATH = "no_registered_target_path"

DIRECT_OBSERVATION = "direct_observation"
CALIBRATED_MEASUREMENT = "calibrated_measurement"
MODEL_PARAMETER = "model_parameter"
CORRECTION = "correction"
DERIVED_QUANTITY = "derived_quantity"
DEFINITION = "definition"
EXTERNAL_COMPARISON_REFERENCE = "external_comparison_reference"
TARGET_OUTPUT = "target_output"

INPUT_ROLES = (
    DIRECT_OBSERVATION,
    CALIBRATED_MEASUREMENT,
    MODEL_PARAMETER,
    CORRECTION,
    DERIVED_QUANTITY,
    DEFINITION,
    EXTERNAL_COMPARISON_REFERENCE,
    TARGET_OUTPUT,
)

DECLARED_LOCAL_ATOM = "declared_local_atom"
REGISTERED_EXPRESSION = "registered_expression"
UNRESOLVED_ALGEBRAIC_PROVENANCE = "unresolved"
ALGEBRAIC_PROVENANCE_KINDS = (
    DECLARED_LOCAL_ATOM,
    REGISTERED_EXPRESSION,
    UNRESOLVED_ALGEBRAIC_PROVENANCE,
)

DOCUMENTED = "documented"
STRUCTURAL_PLACEHOLDER = "structural_placeholder"
UNRESOLVED_PROVENANCE_EVIDENCE = "unresolved"
PROVENANCE_EVIDENCE_VALUES = (
    DOCUMENTED,
    STRUCTURAL_PLACEHOLDER,
    UNRESOLVED_PROVENANCE_EVIDENCE,
)

STRUCTURAL_EXAMPLE = "structural_example"
EMPIRICAL_RECORD = "empirical_record"
EVIDENCE_LEVELS = (STRUCTURAL_EXAMPLE, EMPIRICAL_RECORD)

DEFINITION_EDGE_KINDS = ("definition",)
METROLOGICAL_EDGE_KINDS = (
    "observation_derivation",
    "calibration",
    "correction",
    "model_input",
    "comparison",
)

REQUIRED_BUT_UNPOPULATED = "required_but_unpopulated"
EXPLICIT_ZERO_ASSUMPTION = "explicit_zero_assumption"
COVARIANCE_MATRIX = "covariance_matrix"
CORRELATION_POLICIES = (
    REQUIRED_BUT_UNPOPULATED,
    EXPLICIT_ZERO_ASSUMPTION,
    COVARIANCE_MATRIX,
)


class BridgeValidationError(ValueError):
    """Raised when a record could be mistaken for a valid physical bridge."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BridgeValidationError(f"{label} must be a nonempty string")
    return value


def _unique_text(values: Iterable[str], label: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise BridgeValidationError(f"{label} values must be a sequence, not text")
    result = tuple(values)
    for value in result:
        _require_text(value, label)
    if len(set(result)) != len(result):
        raise BridgeValidationError(f"duplicate {label}")
    return result


def _record_tuple(
    values: Iterable[object],
    record_type: type,
    label: str,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{label} values must be a sequence of records")
    result = tuple(values)
    for value in result:
        if not isinstance(value, record_type):
            raise TypeError(f"{label} values must be {record_type.__name__} records")
    return result


def _strict_fraction(value: object, label: str) -> Fraction:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{label} must be an int or Fraction, not bool or float")
    if not isinstance(value, (int, Fraction)):
        raise TypeError(f"{label} must be an int or Fraction")
    return Fraction(value)


def _strict_signature(
    signature: Iterable[tuple[str, int | Fraction]],
) -> ExponentSignature:
    terms: list[tuple[str, Fraction]] = []
    for term in signature:
        if not isinstance(term, tuple) or len(term) != 2:
            raise TypeError("dependency signature terms must be (key, exponent) tuples")
        key, exponent = term
        _require_text(key, "dependency factor")
        terms.append((key, _strict_fraction(exponent, f"exponent for {key}")))
    return normalize_exponent_signature(terms)


def _validate_decimal(value: object, label: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, (bool, float)) or not isinstance(value, Decimal):
        raise TypeError(f"{label} must be Decimal or None; binary floats are forbidden")
    if not value.is_finite():
        raise BridgeValidationError(f"{label} must be finite")
    return value


def fraction_text(value: Fraction) -> str:
    """Serialize an exact rational without approximation."""

    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def decimal_text(value: Decimal | None) -> str | None:
    """Serialize a base-ten measurement value without converting through float."""

    return None if value is None else str(value)


def dimension_record(dimension: Dimension) -> list[str]:
    return [fraction_text(value) for value in dimension.exponents]


def signature_record(signature: ExponentSignature) -> list[dict[str, str]]:
    return [
        {"factor": factor, "exponent": fraction_text(exponent)}
        for factor, exponent in signature
    ]


def _target_power(signature: ExponentSignature) -> Fraction:
    return next(
        (exponent for key, exponent in signature if key == TARGET_KEY),
        Fraction(0),
    )


@dataclass(frozen=True, slots=True)
class EstimatorTerm:
    """One exact power of an input quantity in a monomial estimator."""

    quantity_id: str
    exponent: Fraction

    def __post_init__(self) -> None:
        _require_text(self.quantity_id, "estimator quantity identifier")
        exponent = _strict_fraction(self.exponent, "estimator exponent")
        if exponent == 0:
            raise BridgeValidationError("estimator terms must have nonzero exponents")
        object.__setattr__(self, "exponent", exponent)


@dataclass(frozen=True, slots=True)
class QuantityRecord:
    """An immutable quantity declaration used by a measurement model."""

    identifier: str
    symbol: str
    role: str
    dimension: Dimension
    unit: str
    algebraic_provenance_kind: str
    registered_dependency_signature: ExponentSignature | None
    provenance_evidence: str
    description: str
    value: Decimal | None = None
    standard_uncertainty: Decimal | None = None
    uncertainty_unit: str | None = None
    exact: bool = False
    source_identifier: str | None = None
    edition: str | None = None
    access_date: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.identifier, "quantity identifier")
        _require_text(self.symbol, f"symbol for {self.identifier}")
        if self.role not in INPUT_ROLES:
            raise BridgeValidationError(
                f"unknown role for {self.identifier}: {self.role}"
            )
        if not isinstance(self.dimension, Dimension):
            raise TypeError(f"dimension for {self.identifier} must be a Dimension")
        _require_text(self.unit, f"unit for {self.identifier}")
        _require_text(self.description, f"description for {self.identifier}")
        if self.algebraic_provenance_kind not in ALGEBRAIC_PROVENANCE_KINDS:
            raise BridgeValidationError(
                f"unknown algebraic provenance kind for {self.identifier}: "
                f"{self.algebraic_provenance_kind}"
            )
        if self.provenance_evidence not in PROVENANCE_EVIDENCE_VALUES:
            raise BridgeValidationError(
                f"unknown provenance evidence for {self.identifier}: "
                f"{self.provenance_evidence}"
            )

        signature = self.registered_dependency_signature
        if self.algebraic_provenance_kind == DECLARED_LOCAL_ATOM:
            expected = ((self.identifier, Fraction(1)),)
            if signature is None:
                signature = expected
            else:
                signature = _strict_signature(signature)
                if signature != expected:
                    raise BridgeValidationError(
                        f"local atom {self.identifier} must use its own unit signature"
                    )
        elif self.algebraic_provenance_kind == REGISTERED_EXPRESSION:
            if signature is None:
                raise BridgeValidationError(
                    f"registered expression {self.identifier} needs a signature"
                )
            signature = _strict_signature(signature)
        else:
            if signature is not None:
                raise BridgeValidationError(
                    f"unresolved quantity {self.identifier} cannot claim a signature"
                )
        object.__setattr__(self, "registered_dependency_signature", signature)

        value = _validate_decimal(self.value, f"value for {self.identifier}")
        uncertainty = _validate_decimal(
            self.standard_uncertainty,
            f"standard uncertainty for {self.identifier}",
        )
        if uncertainty is not None and uncertainty < 0:
            raise BridgeValidationError(
                f"standard uncertainty for {self.identifier} cannot be negative"
            )
        if uncertainty is not None and value is None:
            raise BridgeValidationError(
                f"{self.identifier} cannot have uncertainty without a value"
            )
        if uncertainty is not None:
            _require_text(
                self.uncertainty_unit,
                f"uncertainty unit for {self.identifier}",
            )
        elif self.uncertainty_unit is not None:
            raise BridgeValidationError(
                f"{self.identifier} has an uncertainty unit but no uncertainty"
            )
        if not isinstance(self.exact, bool):
            raise TypeError(f"exact flag for {self.identifier} must be Boolean")
        if uncertainty == 0 and not self.exact:
            raise BridgeValidationError(
                f"zero standard uncertainty for {self.identifier} requires an exact record"
            )
        if self.exact and uncertainty not in (None, Decimal(0)):
            raise BridgeValidationError(
                f"exact quantity {self.identifier} cannot have nonzero uncertainty"
            )
        for value, label in (
            (self.source_identifier, f"source identifier for {self.identifier}"),
            (self.edition, f"edition for {self.identifier}"),
            (self.access_date, f"access date for {self.identifier}"),
        ):
            if value is not None:
                _require_text(value, label)


@dataclass(frozen=True, slots=True)
class ProvenanceEdge:
    """A directed ``child depends on parent`` provenance edge."""

    child: str
    parent: str
    kind: str
    explanation: str

    def __post_init__(self) -> None:
        _require_text(self.child, "provenance child")
        _require_text(self.parent, "provenance parent")
        _require_text(self.kind, "provenance edge kind")
        _require_text(self.explanation, "provenance edge explanation")


@dataclass(frozen=True, slots=True)
class CorrelationDeclaration:
    """One explicit covariance declaration between two uncertainty inputs."""

    left: str
    right: str
    covariance: Decimal
    covariance_unit: str

    def __post_init__(self) -> None:
        _require_text(self.left, "left correlation identifier")
        _require_text(self.right, "right correlation identifier")
        if self.left == self.right:
            raise BridgeValidationError("a covariance pair needs two different inputs")
        covariance = _validate_decimal(self.covariance, "covariance")
        if covariance is None:
            raise BridgeValidationError("covariance cannot be omitted")
        _require_text(self.covariance_unit, "covariance unit")


@dataclass(frozen=True, slots=True)
class UncertaintyModel:
    """The minimum declared uncertainty structure for one measurand."""

    measurand_id: str
    input_ids: tuple[str, ...]
    correction_ids: tuple[str, ...]
    correlation_policy: str
    correlations: tuple[CorrelationDeclaration, ...]
    zero_correlation_justification: str | None
    propagation_method: str
    coverage_factor: Decimal | None
    coverage_probability: Decimal | None
    coverage_basis: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.measurand_id, "uncertainty measurand")
        object.__setattr__(
            self,
            "input_ids",
            _unique_text(self.input_ids, "uncertainty input identifier"),
        )
        object.__setattr__(
            self,
            "correction_ids",
            _unique_text(self.correction_ids, "uncertainty correction identifier"),
        )
        correlations = _record_tuple(
            self.correlations,
            CorrelationDeclaration,
            "correlation declaration",
        )
        object.__setattr__(self, "correlations", correlations)
        if self.correlation_policy not in CORRELATION_POLICIES:
            raise BridgeValidationError(
                "correlation policy must explicitly declare covariance, justify zero "
                "correlations, or remain required_but_unpopulated"
            )
        pair_keys = [
            tuple(sorted((record.left, record.right))) for record in self.correlations
        ]
        if len(set(pair_keys)) != len(pair_keys):
            raise BridgeValidationError("duplicate covariance declaration")
        if self.correlation_policy == EXPLICIT_ZERO_ASSUMPTION:
            _require_text(
                self.zero_correlation_justification,
                "zero-correlation justification",
            )
            if self.correlations:
                raise BridgeValidationError(
                    "explicit_zero_assumption cannot contain covariance declarations"
                )
        elif self.zero_correlation_justification is not None:
            raise BridgeValidationError(
                "zero-correlation justification requires explicit_zero_assumption"
            )
        if self.correlation_policy == COVARIANCE_MATRIX and not self.correlations:
            raise BridgeValidationError(
                "covariance_matrix policy requires covariance declarations"
            )
        if self.correlation_policy == REQUIRED_BUT_UNPOPULATED and self.correlations:
            raise BridgeValidationError(
                "required_but_unpopulated cannot contain partial covariances"
            )
        _require_text(self.propagation_method, "uncertainty propagation method")
        coverage_factor = _validate_decimal(self.coverage_factor, "coverage factor")
        coverage_probability = _validate_decimal(
            self.coverage_probability,
            "coverage probability",
        )
        if (coverage_factor is None) != (coverage_probability is None):
            raise BridgeValidationError(
                "coverage factor and coverage probability must be declared together"
            )
        if coverage_factor is not None and coverage_factor <= 0:
            raise BridgeValidationError("coverage factor must be positive")
        if coverage_probability is not None and not (
            Decimal(0) < coverage_probability < Decimal(1)
        ):
            raise BridgeValidationError("coverage probability must lie between 0 and 1")
        _require_text(self.coverage_basis, "coverage basis")
        object.__setattr__(
            self,
            "limitations",
            _unique_text(self.limitations, "uncertainty limitation"),
        )
        if not self.limitations:
            raise BridgeValidationError(
                "uncertainty model must state at least one limitation"
            )


@dataclass(frozen=True, slots=True)
class LeanTheoremLink:
    """An explicit catalog entry; Python never parses Lean source to discover it."""

    identifier: str
    fully_qualified_name: str
    relation: str
    conditional_scope: str
    estimator_rearrangement_certified: bool

    def __post_init__(self) -> None:
        _require_text(self.identifier, "Lean link identifier")
        _require_text(self.fully_qualified_name, "Lean theorem name")
        _require_text(self.relation, "Lean theorem relation")
        _require_text(self.conditional_scope, "Lean theorem scope")
        if not isinstance(self.estimator_rearrangement_certified, bool):
            raise TypeError("Lean estimator certification flag must be Boolean")


LEAN_THEOREM_CATALOG = (
    LeanTheoremLink(
        identifier="conditional_inverse_square_force_relation",
        fully_qualified_name=(
            "TheNumberProject.EntropicGravity."
            "force_eq_gravitationalConstant_mul_masses_div_radius_sq"
        ),
        relation="F = G * M * m / r^2",
        conditional_scope=(
            "Lean kernel-checks the inverse-square conclusion only if every named "
            "physical equation and nonzero side condition in the theorem holds."
        ),
        estimator_rearrangement_certified=False,
    ),
)
LEAN_THEOREMS_BY_ID: Mapping[str, LeanTheoremLink] = MappingProxyType(
    {record.identifier: record for record in LEAN_THEOREM_CATALOG}
)


@dataclass(frozen=True, slots=True)
class MeasurementModel:
    """A complete structural declaration for evaluating a physical bridge."""

    identifier: str
    target_measurand_id: str
    target_symbolic_key: str
    theoretical_relation: str
    estimator_relation: str
    domain_and_approximation_regime: tuple[str, ...]
    required_hypotheses: tuple[str, ...]
    quantities: tuple[QuantityRecord, ...]
    estimator_terms: tuple[EstimatorTerm, ...]
    definition_edges: tuple[ProvenanceEdge, ...]
    metrological_edges: tuple[ProvenanceEdge, ...]
    calibration_source_ids: tuple[str, ...]
    correction_ids: tuple[str, ...]
    comparison_reference_ids: tuple[str, ...]
    comparison_node_ids: tuple[str, ...]
    uncertainty_model: UncertaintyModel | None
    lean_link_identifier: str | None
    evidence_level: str
    replication_identifiers: tuple[str, ...]
    limitations: tuple[str, ...]
    nonclaims: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "quantities",
            _record_tuple(self.quantities, QuantityRecord, "quantity"),
        )
        object.__setattr__(
            self,
            "estimator_terms",
            _record_tuple(self.estimator_terms, EstimatorTerm, "estimator term"),
        )
        object.__setattr__(
            self,
            "definition_edges",
            _record_tuple(self.definition_edges, ProvenanceEdge, "definition edge"),
        )
        object.__setattr__(
            self,
            "metrological_edges",
            _record_tuple(
                self.metrological_edges,
                ProvenanceEdge,
                "metrological edge",
            ),
        )
        if self.uncertainty_model is not None and not isinstance(
            self.uncertainty_model,
            UncertaintyModel,
        ):
            raise TypeError("uncertainty model must be UncertaintyModel or None")
        if self.lean_link_identifier is not None:
            _require_text(self.lean_link_identifier, "Lean link identifier")
        _require_text(self.identifier, "model identifier")
        _require_text(self.target_measurand_id, "target measurand identifier")
        _require_text(self.target_symbolic_key, "target symbolic key")
        _require_text(self.theoretical_relation, "theoretical relation")
        _require_text(self.estimator_relation, "estimator relation")
        object.__setattr__(
            self,
            "domain_and_approximation_regime",
            _unique_text(
                self.domain_and_approximation_regime,
                "domain or approximation statement",
            ),
        )
        object.__setattr__(
            self,
            "required_hypotheses",
            _unique_text(self.required_hypotheses, "required hypothesis"),
        )
        object.__setattr__(
            self,
            "calibration_source_ids",
            _unique_text(self.calibration_source_ids, "calibration source identifier"),
        )
        object.__setattr__(
            self,
            "correction_ids",
            _unique_text(self.correction_ids, "correction identifier"),
        )
        object.__setattr__(
            self,
            "comparison_reference_ids",
            _unique_text(
                self.comparison_reference_ids,
                "comparison reference identifier",
            ),
        )
        object.__setattr__(
            self,
            "comparison_node_ids",
            _unique_text(self.comparison_node_ids, "comparison node identifier"),
        )
        if self.evidence_level not in EVIDENCE_LEVELS:
            raise BridgeValidationError(f"unknown evidence level: {self.evidence_level}")
        object.__setattr__(
            self,
            "replication_identifiers",
            _unique_text(self.replication_identifiers, "replication identifier"),
        )
        object.__setattr__(
            self,
            "limitations",
            _unique_text(self.limitations, "model limitation"),
        )
        object.__setattr__(
            self,
            "nonclaims",
            _unique_text(self.nonclaims, "model nonclaim"),
        )
        for values, label in (
            (self.domain_and_approximation_regime, "domain and approximation regime"),
            (self.required_hypotheses, "required hypotheses"),
            (self.limitations, "model limitations"),
            (self.nonclaims, "model nonclaims"),
        ):
            if not values:
                raise BridgeValidationError(f"measurement model must state {label}")


@dataclass(frozen=True, slots=True)
class TargetPathAudit:
    """Catalog-relative result for one algebraic surface signature."""

    identifier: str
    status: str
    surface_signature: ExponentSignature
    expanded_signature: ExponentSignature
    unresolved_factors: tuple[str, ...]
    power_of_target: Fraction
    explanation: str


@dataclass(frozen=True, slots=True)
class BridgeEvaluation:
    """Orthogonal assessments; deliberately not reducible to one score."""

    dimensional_status: str
    algebraic_model_status: str
    registered_target_path_status: str
    metrological_provenance_status: str
    uncertainty_status: str
    empirical_population_status: str
    replication_status: str
    estimator_dimension: Dimension
    estimator_upstream_ids: tuple[str, ...]
    target_path_audits: tuple[TargetPathAudit, ...]
    uncertainty_gaps: tuple[str, ...]


def audit_registered_target_path(
    signature: Iterable[tuple[str, int | Fraction]],
    *,
    identifier: str = "expression",
    catalog: DependencyCatalog = DEFAULT_DEPENDENCY_CATALOG,
) -> TargetPathAudit:
    """Reuse Milestone 3 expansion to classify a target path exactly."""

    surface = _strict_signature(signature)
    expansion = catalog.expand_signature(surface)
    power = _target_power(expansion.signature)
    if expansion.unresolved_factors:
        status = UNRESOLVED
        explanation = (
            "The current catalog cannot expand every factor. Target cleanliness is "
            "therefore unresolved, not established."
        )
    elif power != 0:
        status = TARGET_PATH_DETECTED
        explanation = (
            "Exact registered expansion reaches G with power "
            f"{fraction_text(power)}."
        )
    else:
        status = NO_REGISTERED_TARGET_PATH
        explanation = (
            "No path to G exists under the current registered algebraic records. "
            "This is necessary for the target-clean gate but does not establish "
            "metrological independence."
        )
    return TargetPathAudit(
        identifier=identifier,
        status=status,
        surface_signature=surface,
        expanded_signature=expansion.signature,
        unresolved_factors=expansion.unresolved_factors,
        power_of_target=power,
        explanation=explanation,
    )


def _quantity_map(model: MeasurementModel) -> dict[str, QuantityRecord]:
    identifiers = [record.identifier for record in model.quantities]
    if len(set(identifiers)) != len(identifiers):
        raise BridgeValidationError("duplicate quantity identifiers")
    return {record.identifier: record for record in model.quantities}


def build_model_dependency_catalog(model: MeasurementModel) -> DependencyCatalog:
    """Extend the exact Milestone 3 catalog with explicitly local atomic inputs."""

    definitions = list(DEFAULT_DEPENDENCY_CATALOG.definitions.values())
    dimensions = dict(DEFAULT_DEPENDENCY_CATALOG.dimensions)
    for quantity in sorted(model.quantities, key=lambda item: item.identifier):
        if quantity.algebraic_provenance_kind != DECLARED_LOCAL_ATOM:
            continue
        if quantity.identifier in dimensions:
            raise BridgeValidationError(
                f"local atom shadows registered key: {quantity.identifier}"
            )
        definitions.append(DependencyDefinition(quantity.identifier))
        dimensions[quantity.identifier] = quantity.dimension
    return build_dependency_catalog(
        definitions,
        dimensions,
        required_keys=dimensions,
    )


def _audit_quantity(
    quantity: QuantityRecord,
    catalog: DependencyCatalog,
) -> TargetPathAudit:
    if quantity.algebraic_provenance_kind == UNRESOLVED_ALGEBRAIC_PROVENANCE:
        return TargetPathAudit(
            identifier=quantity.identifier,
            status=UNRESOLVED,
            surface_signature=(),
            expanded_signature=(),
            unresolved_factors=(quantity.identifier,),
            power_of_target=Fraction(0),
            explanation=(
                "No registered algebraic signature was supplied. Target cleanliness "
                "remains unresolved."
            ),
        )
    assert quantity.registered_dependency_signature is not None
    return audit_registered_target_path(
        quantity.registered_dependency_signature,
        identifier=quantity.identifier,
        catalog=catalog,
    )


def _validate_edges(
    edges: Sequence[ProvenanceEdge],
    identifiers: set[str],
    allowed_kinds: tuple[str, ...],
    label: str,
) -> dict[str, tuple[str, ...]]:
    keys: set[tuple[str, str, str]] = set()
    parents: dict[str, list[str]] = {}
    for edge in edges:
        if edge.kind not in allowed_kinds:
            raise BridgeValidationError(f"unknown {label} edge kind: {edge.kind}")
        unknown = {edge.child, edge.parent} - identifiers
        if unknown:
            raise BridgeValidationError(
                f"{label} edge refers to unknown parent or child: {sorted(unknown)}"
            )
        key = (edge.child, edge.parent, edge.kind)
        if key in keys:
            raise BridgeValidationError(f"duplicate {label} edge: {key}")
        keys.add(key)
        parents.setdefault(edge.child, []).append(edge.parent)

    adjacency = {key: tuple(sorted(values)) for key, values in parents.items()}
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visited:
            return
        if identifier in visiting:
            start = visiting.index(identifier)
            cycle = visiting[start:] + [identifier]
            raise BridgeValidationError(
                f"cyclic {label} provenance: {' -> '.join(cycle)}"
            )
        visiting.append(identifier)
        for parent in adjacency.get(identifier, ()):
            visit(parent)
        visiting.pop()
        visited.add(identifier)

    for identifier in sorted(identifiers):
        visit(identifier)
    return adjacency


def _upstream_ids(
    start_ids: Iterable[str],
    edges: Sequence[ProvenanceEdge],
) -> tuple[str, ...]:
    parents: dict[str, list[str]] = {}
    for edge in edges:
        parents.setdefault(edge.child, []).append(edge.parent)
    pending = list(start_ids)
    reached: set[str] = set()
    while pending:
        identifier = pending.pop()
        if identifier in reached:
            continue
        reached.add(identifier)
        pending.extend(parents.get(identifier, ()))
    return tuple(sorted(reached))


def _estimator_dimension(
    model: MeasurementModel,
    quantities: Mapping[str, QuantityRecord],
) -> Dimension:
    result = DIMENSIONLESS
    for term in model.estimator_terms:
        result = result * quantities[term.quantity_id].dimension ** term.exponent
    return result


def _registered_signature_dimension(
    quantity: QuantityRecord,
    catalog: DependencyCatalog,
) -> Dimension | None:
    signature = quantity.registered_dependency_signature
    if signature is None:
        return None
    if any(factor not in catalog.dimensions for factor, _ in signature):
        return None
    result = DIMENSIONLESS
    for factor, exponent in signature:
        result = result * catalog.dimensions[factor] ** exponent
    return result


def validate_measurement_model(model: MeasurementModel) -> None:
    """Reject structural ambiguity, target leakage, and invalid provenance graphs."""

    if not isinstance(model, MeasurementModel):
        raise BridgeValidationError("measurement model is missing or has an invalid type")
    quantities = _quantity_map(model)
    identifiers = set(quantities)
    target = quantities.get(model.target_measurand_id)
    if target is None:
        raise BridgeValidationError("measurement model is missing its target")
    if target.role != TARGET_OUTPUT:
        raise BridgeValidationError("target measurand must have target_output role")
    if target.dimension != GRAVITATIONAL_CONSTANT:
        raise BridgeValidationError("target measurand must have the dimensions of G")
    if model.target_symbolic_key != TARGET_KEY:
        raise BridgeValidationError("this bridge contract targets G")
    if not model.estimator_terms:
        raise BridgeValidationError("measurement model is missing an estimator")

    term_ids = [term.quantity_id for term in model.estimator_terms]
    if len(set(term_ids)) != len(term_ids):
        raise BridgeValidationError("duplicate estimator input identifier")
    unknown_terms = set(term_ids) - identifiers
    if unknown_terms:
        raise BridgeValidationError(
            f"estimator refers to unknown input(s): {sorted(unknown_terms)}"
        )
    forbidden_term_roles = {EXTERNAL_COMPARISON_REFERENCE, TARGET_OUTPUT}
    for identifier in term_ids:
        if quantities[identifier].role in forbidden_term_roles:
            raise BridgeValidationError(
                f"forbidden estimator input role for {identifier}: "
                f"{quantities[identifier].role}"
            )

    definition_parents = _validate_edges(
        model.definition_edges,
        identifiers,
        DEFINITION_EDGE_KINDS,
        "definitional",
    )
    metrological_parents = _validate_edges(
        model.metrological_edges,
        identifiers,
        METROLOGICAL_EDGE_KINDS,
        "metrological",
    )
    _validate_edges(
        (*model.definition_edges, *model.metrological_edges),
        identifiers,
        (*DEFINITION_EDGE_KINDS, *METROLOGICAL_EDGE_KINDS),
        "combined",
    )
    if set(definition_parents.get(model.target_measurand_id, ())) != set(term_ids):
        raise BridgeValidationError(
            "the target definition edges must identify every estimator input exactly"
        )

    for identifier in (
        *model.calibration_source_ids,
        *model.correction_ids,
        *model.comparison_reference_ids,
        *model.comparison_node_ids,
    ):
        if identifier not in identifiers:
            raise BridgeValidationError(f"unknown declared model identifier: {identifier}")
    for identifier in model.calibration_source_ids:
        if quantities[identifier].role not in {DEFINITION, CALIBRATED_MEASUREMENT}:
            raise BridgeValidationError(
                f"calibration source {identifier} has an incompatible role"
            )
    for identifier in model.correction_ids:
        if quantities[identifier].role != CORRECTION:
            raise BridgeValidationError(f"{identifier} is not a correction")

    role_references = {
        identifier
        for identifier, quantity in quantities.items()
        if quantity.role == EXTERNAL_COMPARISON_REFERENCE
    }
    if role_references != set(model.comparison_reference_ids):
        raise BridgeValidationError(
            "every external comparison reference must be explicitly isolated"
        )
    for identifier in model.comparison_reference_ids:
        reference = quantities[identifier]
        if reference.dimension != target.dimension:
            raise BridgeValidationError(
                f"external comparison reference {identifier} must match the target dimension"
            )
        if (
            reference.value is None
            or reference.standard_uncertainty is None
            or reference.source_identifier is None
            or reference.edition is None
            or reference.access_date is None
        ):
            raise BridgeValidationError(
                f"checked-in comparison reference {identifier} needs value, standard "
                "uncertainty, source, edition, and access date"
            )

    comparison_nodes = set(model.comparison_node_ids)
    references = set(model.comparison_reference_ids)
    for identifier in comparison_nodes:
        if quantities[identifier].role != DERIVED_QUANTITY:
            raise BridgeValidationError(
                f"comparison node {identifier} must be a derived quantity"
            )
        if quantities[identifier].dimension != target.dimension:
            raise BridgeValidationError(
                f"comparison node {identifier} must match the target dimension"
            )
        edges = [edge for edge in model.metrological_edges if edge.child == identifier]
        if not edges or any(edge.kind != "comparison" for edge in edges):
            raise BridgeValidationError(
                f"comparison node {identifier} must have comparison-only inputs"
            )
        parent_ids = {edge.parent for edge in edges}
        if model.target_measurand_id not in parent_ids or not (parent_ids & references):
            raise BridgeValidationError(
                f"comparison node {identifier} must consume the estimate and a reference"
            )

    all_edges = (*model.definition_edges, *model.metrological_edges)
    for reference_id in references:
        for edge in all_edges:
            if edge.parent != reference_id:
                continue
            if edge.kind != "comparison" or edge.child not in comparison_nodes:
                raise BridgeValidationError(
                    f"external reference {reference_id} may feed comparison nodes only"
                )
    for comparison_id in comparison_nodes:
        if any(edge.parent == comparison_id for edge in all_edges):
            raise BridgeValidationError(
                f"post-estimation comparison {comparison_id} cannot feed another node"
            )

    for identifier, quantity in quantities.items():
        if quantity.role not in {
            CALIBRATED_MEASUREMENT,
            CORRECTION,
            DERIVED_QUANTITY,
        }:
            continue
        has_parent = bool(
            definition_parents.get(identifier) or metrological_parents.get(identifier)
        )
        if not has_parent and quantity.provenance_evidence != UNRESOLVED_PROVENANCE_EVIDENCE:
            raise BridgeValidationError(
                f"required provenance is missing for {identifier}; fail closed"
            )

    estimator_upstream = set(_upstream_ids(term_ids, all_edges))
    leaked_reference = estimator_upstream & (references | comparison_nodes)
    if leaked_reference:
        raise BridgeValidationError(
            "comparison reference or comparison result flows upstream of the estimator: "
            f"{sorted(leaked_reference)}"
        )
    for guarded_id in (*model.calibration_source_ids, *model.correction_ids):
        guarded_upstream = set(_upstream_ids((guarded_id,), all_edges))
        leaked = guarded_upstream & references
        if leaked:
            raise BridgeValidationError(
                f"reference G is used in calibration or correction {guarded_id}: "
                f"{sorted(leaked)}"
            )

    catalog = build_model_dependency_catalog(model)
    for identifier in sorted(estimator_upstream):
        audit = _audit_quantity(quantities[identifier], catalog)
        if audit.status == TARGET_PATH_DETECTED:
            raise BridgeValidationError(
                f"estimator ancestry reaches G through {identifier} "
                f"(power {fraction_text(audit.power_of_target)})"
            )
    for identifier, quantity in sorted(quantities.items()):
        signature_dimension = _registered_signature_dimension(quantity, catalog)
        if signature_dimension is not None and signature_dimension != quantity.dimension:
            raise BridgeValidationError(
                f"dimensionally inconsistent algebraic provenance for {identifier}: "
                f"declared {quantity.dimension}, signature has {signature_dimension}"
            )

    estimator_dimension = _estimator_dimension(model, quantities)
    if estimator_dimension != target.dimension:
        raise BridgeValidationError(
            "dimensionally inconsistent estimator: expected "
            f"{target.dimension}, obtained {estimator_dimension}"
        )

    if model.lean_link_identifier is not None:
        if model.lean_link_identifier not in LEAN_THEOREMS_BY_ID:
            raise BridgeValidationError(
                f"unknown Lean theorem link: {model.lean_link_identifier}"
            )

    uncertainty = model.uncertainty_model
    if uncertainty is not None:
        if uncertainty.measurand_id != model.target_measurand_id:
            raise BridgeValidationError("uncertainty measurand does not match target")
        if set(uncertainty.input_ids) != set(term_ids):
            raise BridgeValidationError(
                "uncertainty inputs must declare every estimator input exactly"
            )
        if set(uncertainty.correction_ids) != set(model.correction_ids):
            raise BridgeValidationError(
                "uncertainty corrections must match model corrections"
            )
        allowed_uncertainty_ids = set(uncertainty.input_ids) | set(
            uncertainty.correction_ids
        )
        for correlation in uncertainty.correlations:
            unknown = {correlation.left, correlation.right} - allowed_uncertainty_ids
            if unknown:
                raise BridgeValidationError(
                    f"covariance refers to unknown uncertainty input(s): {sorted(unknown)}"
                )


def evaluate_measurement_model(model: MeasurementModel) -> BridgeEvaluation:
    """Validate a model and return separate evidence-axis assessments."""

    validate_measurement_model(model)
    quantities = _quantity_map(model)
    term_ids = tuple(term.quantity_id for term in model.estimator_terms)
    all_edges = (*model.definition_edges, *model.metrological_edges)
    upstream_ids = _upstream_ids(term_ids, all_edges)
    catalog = build_model_dependency_catalog(model)
    audits = tuple(
        _audit_quantity(quantities[identifier], catalog) for identifier in upstream_ids
    )
    registered_status = (
        UNRESOLVED
        if any(audit.status == UNRESOLVED for audit in audits)
        else NO_REGISTERED_TARGET_PATH
    )

    evidence = {quantities[identifier].provenance_evidence for identifier in upstream_ids}
    if UNRESOLVED_PROVENANCE_EVIDENCE in evidence:
        metrological_status = UNRESOLVED
    elif evidence - {DOCUMENTED}:
        metrological_status = INCOMPLETE
    else:
        metrological_status = SATISFIED

    uncertainty_gaps: list[str] = []
    uncertainty = model.uncertainty_model
    if uncertainty is None:
        uncertainty_gaps.append("uncertainty model is missing")
    else:
        required_ids = (*uncertainty.input_ids, *uncertainty.correction_ids)
        for identifier in required_ids:
            quantity = quantities[identifier]
            if quantity.value is None:
                uncertainty_gaps.append(f"input estimate is unpopulated: {identifier}")
            elif not quantity.exact and quantity.standard_uncertainty is None:
                uncertainty_gaps.append(
                    f"standard uncertainty is missing: {identifier}"
                )
        if uncertainty.correlation_policy == REQUIRED_BUT_UNPOPULATED:
            uncertainty_gaps.append("correlation or covariance evaluation is unpopulated")
        if uncertainty.propagation_method == REQUIRED_BUT_UNPOPULATED:
            uncertainty_gaps.append("uncertainty propagation method is unpopulated")
        for identifier in upstream_ids:
            quantity = quantities[identifier]
            if (
                quantity.value is not None
                and not quantity.exact
                and quantity.standard_uncertainty is None
            ):
                uncertainty_gaps.append(
                    f"standard uncertainty is missing: {identifier}"
                )
    uncertainty_status = INCOMPLETE if uncertainty_gaps else SATISFIED

    if model.evidence_level == STRUCTURAL_EXAMPLE:
        empirical_status = INCOMPLETE
    elif any(
        quantities[identifier].value is None
        or (
            quantities[identifier].role == DIRECT_OBSERVATION
            and quantities[identifier].provenance_evidence != DOCUMENTED
        )
        for identifier in upstream_ids
    ) or quantities[model.target_measurand_id].value is None:
        empirical_status = INCOMPLETE
    else:
        empirical_status = SATISFIED

    if empirical_status != SATISFIED:
        replication_status = NOT_APPLICABLE
    elif model.replication_identifiers:
        replication_status = SATISFIED
    else:
        replication_status = INCOMPLETE

    return BridgeEvaluation(
        dimensional_status=SATISFIED,
        algebraic_model_status=SATISFIED,
        registered_target_path_status=registered_status,
        metrological_provenance_status=metrological_status,
        uncertainty_status=uncertainty_status,
        empirical_population_status=empirical_status,
        replication_status=replication_status,
        estimator_dimension=_estimator_dimension(model, quantities),
        estimator_upstream_ids=upstream_ids,
        target_path_audits=audits,
        uncertainty_gaps=tuple(sorted(set(uncertainty_gaps))),
    )


def _quantity_record(quantity: QuantityRecord) -> dict[str, Any]:
    return {
        "identifier": quantity.identifier,
        "symbol": quantity.symbol,
        "role": quantity.role,
        "dimension": dimension_record(quantity.dimension),
        "unit": quantity.unit,
        "description": quantity.description,
        "algebraic_provenance": {
            "kind": quantity.algebraic_provenance_kind,
            "surface_signature": (
                None
                if quantity.registered_dependency_signature is None
                else signature_record(quantity.registered_dependency_signature)
            ),
            "caution": (
                "Atomic or target-clean status in this catalog does not establish "
                "metrological independence."
            ),
        },
        "metrological_provenance_evidence": quantity.provenance_evidence,
        "numerical_record": {
            "value_decimal": decimal_text(quantity.value),
            "standard_uncertainty_decimal": decimal_text(
                quantity.standard_uncertainty
            ),
            "uncertainty_unit": quantity.uncertainty_unit,
            "exact": quantity.exact,
        },
        "source": {
            "identifier": quantity.source_identifier,
            "edition": quantity.edition,
            "access_date": quantity.access_date,
        },
    }


def _edge_record(edge: ProvenanceEdge) -> dict[str, str]:
    return {
        "child": edge.child,
        "parent": edge.parent,
        "kind": edge.kind,
        "explanation": edge.explanation,
    }


def _audit_record(audit: TargetPathAudit) -> dict[str, Any]:
    return {
        "identifier": audit.identifier,
        "status": audit.status,
        "surface_signature": signature_record(audit.surface_signature),
        "expanded_signature": signature_record(audit.expanded_signature),
        "unresolved_factors": list(audit.unresolved_factors),
        "power_of_G": fraction_text(audit.power_of_target),
        "explanation": audit.explanation,
    }


def _uncertainty_record(uncertainty: UncertaintyModel | None) -> dict[str, Any] | None:
    if uncertainty is None:
        return None
    return {
        "measurand_id": uncertainty.measurand_id,
        "input_ids": sorted(uncertainty.input_ids),
        "correction_ids": sorted(uncertainty.correction_ids),
        "correlation_policy": uncertainty.correlation_policy,
        "correlations": [
            {
                "left": record.left,
                "right": record.right,
                "covariance_decimal": decimal_text(record.covariance),
                "covariance_unit": record.covariance_unit,
            }
            for record in sorted(
                uncertainty.correlations,
                key=lambda item: (min(item.left, item.right), max(item.left, item.right)),
            )
        ],
        "zero_correlation_justification": (
            uncertainty.zero_correlation_justification
        ),
        "propagation_method": uncertainty.propagation_method,
        "coverage": {
            "factor_decimal": decimal_text(uncertainty.coverage_factor),
            "probability_decimal": decimal_text(uncertainty.coverage_probability),
            "basis": uncertainty.coverage_basis,
        },
        "limitations": list(uncertainty.limitations),
    }


def _lean_record(identifier: str | None) -> dict[str, Any] | None:
    if identifier is None:
        return None
    theorem = LEAN_THEOREMS_BY_ID[identifier]
    return {
        "catalog_identifier": theorem.identifier,
        "fully_qualified_name": theorem.fully_qualified_name,
        "relation": theorem.relation,
        "conditional_scope": theorem.conditional_scope,
        "estimator_rearrangement_certified": (
            theorem.estimator_rearrangement_certified
        ),
        "nonclaim": (
            "The link does not certify that observations occurred, an apparatus obeyed "
            "the model, calibrations were correct, or uncertainties are complete."
        ),
    }


def measurement_model_record(model: MeasurementModel) -> dict[str, Any]:
    """Return a deterministic machine-readable model and its assessments."""

    evaluation = evaluate_measurement_model(model)
    quantities = _quantity_map(model)
    comparison_audits = []
    catalog = build_model_dependency_catalog(model)
    for identifier in sorted(model.comparison_reference_ids):
        comparison_audits.append(_audit_record(_audit_quantity(quantities[identifier], catalog)))

    assessments = {
        "dimensional_status": evaluation.dimensional_status,
        "algebraic_model_status": evaluation.algebraic_model_status,
        "registered_target_path_status": evaluation.registered_target_path_status,
        "metrological_provenance_status": (
            evaluation.metrological_provenance_status
        ),
        "uncertainty_status": evaluation.uncertainty_status,
        "empirical_population_status": evaluation.empirical_population_status,
        "replication_status": evaluation.replication_status,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": "inverse-square physical bridge structural example",
        "model_identifier": model.identifier,
        "scope_and_evidence_level": {
            "evidence_level": model.evidence_level,
            "classification": "structural_measurement_model_skeleton",
            "empirical_determination": False,
            "statement": (
                "This record validates a contract shape. It contains no experimental "
                "dataset and reports no measured value of G."
            ),
        },
        "target_measurand": {
            "quantity_id": model.target_measurand_id,
            "symbolic_key": model.target_symbolic_key,
            "dimension": dimension_record(
                quantities[model.target_measurand_id].dimension
            ),
            "unit": quantities[model.target_measurand_id].unit,
        },
        "measurement_model": {
            "theoretical_relation": model.theoretical_relation,
            "estimator_relation": model.estimator_relation,
            "domain_and_approximation_regime": list(
                model.domain_and_approximation_regime
            ),
            "required_hypotheses": list(model.required_hypotheses),
            "estimator_terms": [
                {
                    "quantity_id": term.quantity_id,
                    "exponent": fraction_text(term.exponent),
                }
                for term in sorted(
                    model.estimator_terms,
                    key=lambda item: item.quantity_id,
                )
            ],
            "estimator_dimension": dimension_record(
                evaluation.estimator_dimension
            ),
        },
        "quantities": [
            _quantity_record(quantities[identifier])
            for identifier in sorted(quantities)
        ],
        "provenance_graphs": {
            "edge_direction": "child depends on parent",
            "combined_cycle_status": "acyclic",
            "definitional": {
                "cycle_status": "acyclic",
                "edges": [
                    _edge_record(edge)
                    for edge in sorted(
                        model.definition_edges,
                        key=lambda item: (item.child, item.parent, item.kind),
                    )
                ],
            },
            "metrological": {
                "cycle_status": "acyclic",
                "edges": [
                    _edge_record(edge)
                    for edge in sorted(
                        model.metrological_edges,
                        key=lambda item: (item.child, item.parent, item.kind),
                    )
                ],
                "calibration_source_ids": sorted(model.calibration_source_ids),
                "correction_ids": sorted(model.correction_ids),
            },
        },
        "target_path_audit": {
            "gate_result": evaluation.registered_target_path_status,
            "estimator_upstream_node_ids": list(
                evaluation.estimator_upstream_ids
            ),
            "estimator_upstream_assessments": [
                _audit_record(audit) for audit in evaluation.target_path_audits
            ],
            "isolated_comparison_reference_assessments": comparison_audits,
            "required_caution": (
                "No registered algebraic path to G is necessary for a target-clean "
                "input, but it is not sufficient to establish experimental independence."
            ),
        },
        "external_comparison": {
            "reference_ids": sorted(model.comparison_reference_ids),
            "comparison_node_ids": sorted(model.comparison_node_ids),
            "isolation_rule": (
                "External G references may be consumed only by terminal "
                "post-estimation comparison nodes. They cannot calibrate, correct, "
                "tune, accept, or reject an estimate."
            ),
        },
        "uncertainty_model": _uncertainty_record(model.uncertainty_model),
        "uncertainty_gaps": list(evaluation.uncertainty_gaps),
        "lean_linkage": _lean_record(model.lean_link_identifier),
        "assessments": assessments,
        "replication_identifiers": list(model.replication_identifiers),
        "limitations": list(model.limitations),
        "nonclaims": list(model.nonclaims),
    }


LITERATURE_IDENTIFIERS = (
    {
        "identifier": "rothleitner_schlamminger_2017_review",
        "document_type": "peer_reviewed_review",
        "doi": "10.1063/1.4994619",
    },
    {
        "identifier": "gundlach_merkowitz_2000",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1103/PhysRevLett.85.2869",
    },
    {
        "identifier": "schlamminger_et_al_2006",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1103/PhysRevD.74.082001",
    },
    {
        "identifier": "rosi_et_al_2014",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1038/nature13433",
    },
    {
        "identifier": "li_et_al_2018",
        "document_type": "peer_reviewed_experiment",
        "doi": "10.1038/s41586-018-0431-5",
    },
    {
        "identifier": "codata_2022_adjustment",
        "document_type": "adjusted_external_comparison_reference",
        "doi": "10.1063/5.0279860",
    },
    {
        "identifier": "jcgm_100_2008",
        "document_type": "authoritative_metrology_standard",
        "url": "https://www.bipm.org/en/committees/jc/jcgm/publications",
    },
    {
        "identifier": "jcgm_200_2012",
        "document_type": "authoritative_metrology_vocabulary",
        "doi": "10.59161/JCGM200-2012",
    },
    {
        "identifier": "bipm_si_brochure_2026",
        "document_type": "authoritative_si_reference",
        "doi": "10.59161/AUEZ1291",
    },
)


def build_inverse_square_model() -> MeasurementModel:
    """Build the unpopulated educational inverse-square bridge skeleton."""

    local = DECLARED_LOCAL_ATOM
    placeholder = STRUCTURAL_PLACEHOLDER
    quantities = (
        QuantityRecord(
            "alignment_correction",
            "delta_F_align",
            CORRECTION,
            FORCE,
            "N",
            local,
            None,
            placeholder,
            (
                "Structural placeholder for an alignment correction. A real value "
                "would carry its own standard uncertainty."
            ),
        ),
        QuantityRecord(
            "angle_observation",
            "theta_obs",
            DIRECT_OBSERVATION,
            DIMENSIONLESS,
            "rad",
            local,
            None,
            placeholder,
            (
                "Example lower-level observable showing that force must not be "
                "treated as an unexplained number."
            ),
        ),
        QuantityRecord(
            "codata_2022_G",
            "G_CODATA_2022",
            EXTERNAL_COMPARISON_REFERENCE,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            REGISTERED_EXPRESSION,
            (("G", Fraction(1)),),
            DOCUMENTED,
            (
                "CODATA 2022 adjusted value, isolated for post-estimation comparison "
                "only; it is not an estimator input or acceptance threshold."
            ),
            value=Decimal("6.67430e-11"),
            standard_uncertainty=Decimal("1.5e-15"),
            uncertainty_unit="m^3 kg^-1 s^-2",
            source_identifier="doi:10.1063/5.0279860",
            edition="2022 CODATA adjustment, published 2025",
            access_date="2026-08-30",
        ),
        QuantityRecord(
            "force_estimate",
            "F_hat",
            DERIVED_QUANTITY,
            FORCE,
            "N",
            local,
            None,
            placeholder,
            (
                "Force inferred from lower-level observations, calibration, and a "
                "correction; not a direct or populated force reading."
            ),
        ),
        QuantityRecord(
            "force_reference",
            "F_ref",
            DEFINITION,
            FORCE,
            "N",
            local,
            None,
            placeholder,
            "Placeholder force-scale realization or calibration reference.",
        ),
        QuantityRecord(
            "G_hat",
            "G_hat",
            TARGET_OUTPUT,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            local,
            None,
            placeholder,
            "Unpopulated target output of the estimator.",
        ),
        QuantityRecord(
            "length_reference",
            "L_ref",
            DEFINITION,
            LENGTH,
            "m",
            local,
            None,
            placeholder,
            "Placeholder realization of the metre used by a calibration chain.",
        ),
        QuantityRecord(
            "mass_1",
            "m_1",
            CALIBRATED_MEASUREMENT,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Unpopulated calibrated estimate of the first mass.",
        ),
        QuantityRecord(
            "mass_1_observation",
            "m_1_obs",
            DIRECT_OBSERVATION,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Structural balance or comparator observation for the first mass.",
        ),
        QuantityRecord(
            "mass_2",
            "m_2",
            CALIBRATED_MEASUREMENT,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Unpopulated calibrated estimate of the second mass.",
        ),
        QuantityRecord(
            "mass_2_observation",
            "m_2_obs",
            DIRECT_OBSERVATION,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Structural balance or comparator observation for the second mass.",
        ),
        QuantityRecord(
            "mass_reference",
            "M_ref",
            DEFINITION,
            MASS,
            "kg",
            local,
            None,
            placeholder,
            "Placeholder realization or calibrated standard of the kilogram.",
        ),
        QuantityRecord(
            "post_estimation_comparison",
            "G_hat_minus_G_ref",
            DERIVED_QUANTITY,
            GRAVITATIONAL_CONSTANT,
            "m^3 kg^-1 s^-2",
            local,
            None,
            placeholder,
            (
                "Terminal comparison node. It cannot feed the estimator, calibration, "
                "corrections, or an acceptance decision."
            ),
        ),
        QuantityRecord(
            "separation",
            "r",
            CALIBRATED_MEASUREMENT,
            LENGTH,
            "m",
            local,
            None,
            placeholder,
            "Unpopulated calibrated centre-to-centre separation estimate.",
        ),
        QuantityRecord(
            "separation_observation",
            "r_obs",
            DIRECT_OBSERVATION,
            LENGTH,
            "m",
            local,
            None,
            placeholder,
            "Structural position or distance observation.",
        ),
    )

    definition_edges = (
        ProvenanceEdge(
            "G_hat",
            "force_estimate",
            "definition",
            "The estimator numerator contains the inferred force.",
        ),
        ProvenanceEdge(
            "G_hat",
            "separation",
            "definition",
            "The estimator contains the squared separation.",
        ),
        ProvenanceEdge(
            "G_hat",
            "mass_1",
            "definition",
            "The first mass appears in the estimator denominator.",
        ),
        ProvenanceEdge(
            "G_hat",
            "mass_2",
            "definition",
            "The second mass appears in the estimator denominator.",
        ),
    )
    metrological_edges = (
        ProvenanceEdge(
            "alignment_correction",
            "angle_observation",
            "correction",
            "The alignment correction depends on the observed angular geometry.",
        ),
        ProvenanceEdge(
            "alignment_correction",
            "separation_observation",
            "correction",
            "The alignment correction also depends on measured geometry.",
        ),
        ProvenanceEdge(
            "force_estimate",
            "alignment_correction",
            "correction",
            "The inferred force includes the declared correction and its uncertainty.",
        ),
        ProvenanceEdge(
            "force_estimate",
            "angle_observation",
            "observation_derivation",
            "A real apparatus can infer force from angle, torque, or acceleration data.",
        ),
        ProvenanceEdge(
            "force_estimate",
            "force_reference",
            "calibration",
            "The force inference requires a documented scale realization.",
        ),
        ProvenanceEdge(
            "mass_1",
            "mass_1_observation",
            "observation_derivation",
            "The calibrated mass estimate derives from an instrument observation.",
        ),
        ProvenanceEdge(
            "mass_1",
            "mass_reference",
            "calibration",
            "The first mass is related to a mass reference through calibration.",
        ),
        ProvenanceEdge(
            "mass_2",
            "mass_2_observation",
            "observation_derivation",
            "The calibrated mass estimate derives from an instrument observation.",
        ),
        ProvenanceEdge(
            "mass_2",
            "mass_reference",
            "calibration",
            "The second mass is related to a mass reference through calibration.",
        ),
        ProvenanceEdge(
            "post_estimation_comparison",
            "G_hat",
            "comparison",
            "Comparison occurs only after an estimate has been produced.",
        ),
        ProvenanceEdge(
            "post_estimation_comparison",
            "codata_2022_G",
            "comparison",
            "The adjusted reference is isolated in the terminal comparison node.",
        ),
        ProvenanceEdge(
            "separation",
            "length_reference",
            "calibration",
            "The separation estimate is traceable through a length calibration.",
        ),
        ProvenanceEdge(
            "separation",
            "separation_observation",
            "observation_derivation",
            "The calibrated separation derives from an instrument observation.",
        ),
    )

    uncertainty = UncertaintyModel(
        measurand_id="G_hat",
        input_ids=("force_estimate", "mass_1", "mass_2", "separation"),
        correction_ids=("alignment_correction",),
        correlation_policy=REQUIRED_BUT_UNPOPULATED,
        correlations=(),
        zero_correlation_justification=None,
        propagation_method=REQUIRED_BUT_UNPOPULATED,
        coverage_factor=None,
        coverage_probability=None,
        coverage_basis="not applicable until an empirical estimate exists",
        limitations=(
            "The record validates required uncertainty fields but does not propagate uncertainty.",
            "A correction never implies that the corrected systematic effect has zero uncertainty.",
        ),
    )

    return MeasurementModel(
        identifier="educational_inverse_square_bridge_v1",
        target_measurand_id="G_hat",
        target_symbolic_key="G",
        theoretical_relation="F = G * m_1 * m_2 / r^2",
        estimator_relation="G_hat = F_hat * r^2 / (m_1 * m_2)",
        domain_and_approximation_regime=(
            "Newtonian weak-field, low-velocity educational scalar model",
            "masses represented by an explicitly documented geometry and separation",
            "apparatus-specific force inference and corrections must be supplied recursively",
        ),
        required_hypotheses=(
            "the stated inverse-square measurement model is adequate in the declared regime",
            "mass_1, mass_2, and separation are nonzero",
            "the force inference, geometry model, calibrations, and corrections are documented",
            "all material uncertainty contributions and correlations are evaluated",
        ),
        quantities=quantities,
        estimator_terms=(
            EstimatorTerm("force_estimate", Fraction(1)),
            EstimatorTerm("separation", Fraction(2)),
            EstimatorTerm("mass_1", Fraction(-1)),
            EstimatorTerm("mass_2", Fraction(-1)),
        ),
        definition_edges=definition_edges,
        metrological_edges=metrological_edges,
        calibration_source_ids=(
            "force_reference",
            "length_reference",
            "mass_reference",
        ),
        correction_ids=("alignment_correction",),
        comparison_reference_ids=("codata_2022_G",),
        comparison_node_ids=("post_estimation_comparison",),
        uncertainty_model=uncertainty,
        lean_link_identifier="conditional_inverse_square_force_relation",
        evidence_level=STRUCTURAL_EXAMPLE,
        replication_identifiers=(),
        limitations=(
            "This is not a complete torsion-balance, beam-balance, or atom-interferometer model.",
            (
                "The force-estimation submodel is represented by provenance edges, "
                "not an apparatus equation."
            ),
            "No instrument serial number, calibration certificate, observation, or dataset is present.",
            "No acceptance threshold is defined by comparison with CODATA or any other reference G.",
        ),
        nonclaims=(
            "No value of G is measured or inferred by this artifact.",
            "No apparatus is validated.",
            "No target-clean algebraic status is called experimental independence.",
            "No Lean theorem is treated as evidence that an observation occurred.",
            "No uncertainty is fabricated as zero when information is missing.",
        ),
    )


def _theorem_catalog_record() -> list[dict[str, Any]]:
    return [
        {
            "identifier": theorem.identifier,
            "fully_qualified_name": theorem.fully_qualified_name,
            "relation": theorem.relation,
            "conditional_scope": theorem.conditional_scope,
            "estimator_rearrangement_certified": (
                theorem.estimator_rearrangement_certified
            ),
        }
        for theorem in LEAN_THEOREM_CATALOG
    ]


def build_contract_artifact() -> dict[str, Any]:
    """Build the deterministic Milestone 4 physical-bridge contract."""

    target_controls = []
    for key in ("G", "l_P", "m_P", "t_P", "T_P"):
        target_controls.append(
            _audit_record(
                audit_registered_target_path(
                    ((key, Fraction(1)),),
                    identifier=key,
                )
            )
        )
    if any(record["status"] != TARGET_PATH_DETECTED for record in target_controls):
        raise RuntimeError("a required direct or Planck target-path control changed")

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": "physical bridge contract for G",
        "scope_and_evidence_level": {
            "milestone": 4,
            "evidence_level": "contract_definition",
            "operational_definition": (
                "Produce a non-circular, traceable, uncertainty-qualified estimate of "
                "G from documented observations under an explicitly stated physical "
                "measurement model, followed by reproducibility and preferably "
                "comparison across methods with materially different systematic effects."
            ),
            "supplied_here": (
                "validated schema, graph rules, target-leakage gate, exact dimensional "
                "check, uncertainty requirements, and an unpopulated structural example"
            ),
            "not_supplied_here": (
                "observations, apparatus validation, a propagated uncertainty, an "
                "empirical estimate, or replication"
            ),
        },
        "evidence_layers": [
            {
                "layer": "dimensional_compatibility",
                "meaning": "same units as G; necessary but neither a law nor a value",
            },
            {
                "layer": "definitional_identity",
                "meaning": "exact reduction under registered definitions; may be circular",
            },
            {
                "layer": "theoretical_measurement_model",
                "meaning": "conditional relation between the measurand and operational inputs",
            },
            {
                "layer": "empirical_observation",
                "meaning": "external instrument or procedure readings; not proven by Lean",
            },
            {
                "layer": "metrological_traceability",
                "meaning": "documented calibration chain to a reference or unit realization",
            },
            {
                "layer": "uncertainty",
                "meaning": "input, correction, covariance, propagation, and coverage model",
            },
            {
                "layer": "independent_comparison",
                "meaning": "post-estimation comparison across results or methods only",
            },
        ],
        "separate_assessment_axes": {
            "dimensional_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "algebraic_model_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "registered_target_path_status": [
                TARGET_PATH_DETECTED,
                NO_REGISTERED_TARGET_PATH,
                UNRESOLVED,
                NOT_APPLICABLE,
            ],
            "metrological_provenance_status": [
                SATISFIED,
                INCOMPLETE,
                UNRESOLVED,
                NOT_APPLICABLE,
            ],
            "uncertainty_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "empirical_population_status": [
                SATISFIED,
                INCOMPLETE,
                UNRESOLVED,
                NOT_APPLICABLE,
            ],
            "replication_status": [SATISFIED, INCOMPLETE, UNRESOLVED, NOT_APPLICABLE],
            "single_score": "forbidden",
            "bare_independent_status": "forbidden",
        },
        "measurement_model_required_fields": [
            "model identifier",
            "target measurand",
            "theoretical relation",
            "estimator relation",
            "domain and approximation regime",
            "required hypotheses",
            "input quantities and roles",
            "units and exact dimensions",
            "definitional and metrological provenance edges",
            "calibration sources",
            "corrections and their uncertainties",
            "uncertainty and correlation policy",
            "external comparison references",
            "Lean theorem linkage when available",
            "limitations and nonclaims",
        ],
        "input_roles": list(INPUT_ROLES),
        "provenance_graph_contract": {
            "edge_direction": "child depends on parent",
            "definitional_cycles": "rejected",
            "metrological_cycles": "rejected",
            "cross_layer_cycles": "rejected",
            "unknown_parents": "rejected",
            "missing_required_provenance": "unresolved or rejected; never clean",
            "graph_order": "deterministically sorted by child, parent, and edge kind",
        },
        "target_clean_gate": {
            "rules": [
                "reject a direct G estimator input",
                "reject any registered input expansion with nonzero power of G",
                "reject any estimator ancestor whose registered expansion reaches G",
                "reject a calibration or correction chain that consumes reference G",
                "treat unresolved provenance as unresolved",
                "permit reference G only in isolated terminal comparison nodes",
                "fail closed when required provenance is absent",
            ],
            "required_caution": (
                "No registered algebraic path to G is necessary for a target-clean "
                "input, but it is not sufficient to establish experimental independence."
            ),
            "atomic_catalog_caution": (
                "Atomic means only that the current algebraic catalog stops expanding. "
                "It does not establish metrological independence."
            ),
            "required_target_dependent_controls": target_controls,
        },
        "uncertainty_requirements": {
            "required": [
                "measurand",
                "input estimates",
                "standard uncertainties",
                "units",
                "correlations or a documented zero-correlation justification",
                "corrections",
                "uncertainties associated with corrections",
                "propagation method",
                "coverage information when applicable",
            ],
            "missing_model_status": INCOMPLETE,
            "missing_uncertainty_is_zero": False,
            "binary_floating_point_measurement_values": "rejected",
            "exact_exponent_domain": "int or Fraction; bool and float rejected",
        },
        "external_reference_boundary": {
            "allowed_role": EXTERNAL_COMPARISON_REFERENCE,
            "allowed_use": "isolated post-estimation comparison",
            "forbidden_uses": [
                "estimator input",
                "calibration",
                "correction",
                "candidate tuning",
                "acceptance threshold",
            ],
            "checked_in_metadata": [
                "edition",
                "source",
                "units",
                "standard uncertainty",
                "access date",
            ],
        },
        "lean_boundary": {
            "explicit_catalog": _theorem_catalog_record(),
            "source_parsing": "forbidden",
            "can_establish": (
                "conditional algebraic implications from explicit hypotheses and "
                "nonzero side conditions"
            ),
            "cannot_establish": [
                "that the physical model is complete",
                "that an instrument behaved as modeled",
                "that a reading occurred",
                "that calibrations are correct",
                "that every systematic effect is covered",
                "that nature selected a dimensional candidate",
            ],
        },
        "literature_identifiers": list(LITERATURE_IDENTIFIERS),
        "limitations_and_nonclaims": [
            "The contract does not contain a real experimental dataset.",
            "The contract does not report a new or recommended value of G.",
            "The structural example is not an empirical determination.",
            "Passing the algebraic target gate is weaker than experimental independence.",
            "Cross-method agreement is evidence beyond repeated algebra, not logical proof.",
        ],
    }


def build_example_artifact() -> dict[str, Any]:
    return measurement_model_record(build_inverse_square_model())


def serialize_artifact(artifact: dict[str, Any]) -> str:
    """Serialize with deterministic key order and exactly one final newline."""

    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract-output",
        type=Path,
        default=DEFAULT_CONTRACT_OUTPUT,
    )
    parser.add_argument(
        "--example-output",
        type=Path,
        default=DEFAULT_EXAMPLE_OUTPUT,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when either committed artifact is stale",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    outputs = (
        (args.contract_output, serialize_artifact(build_contract_artifact())),
        (args.example_output, serialize_artifact(build_example_artifact())),
    )
    if args.check:
        stale = [
            path
            for path, rendered in outputs
            if not path.exists() or path.read_text(encoding="utf-8") != rendered
        ]
        if stale:
            for path in stale:
                print(f"stale or missing physical bridge artifact: {path}", file=sys.stderr)
            raise SystemExit(1)
        print("Physical bridge artifacts are current and byte-stable.")
        return

    for path, rendered in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        print(f"Wrote physical bridge artifact to {path}.")
    print("The inverse-square example is structural and contains no measured value of G.")


if __name__ == "__main__":
    main()
