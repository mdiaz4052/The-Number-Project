"""Immutable physical-bridge constants, strict scalars, and record types.

The schema layer contains no graph traversal, target-leakage decisions, artifact
construction, or command-line behavior. Validation lives in
``Discovery.physical_bridge_validation``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping
import unicodedata
from urllib.parse import urlsplit

from Discovery.dimensions import Dimension
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
UNCERTAINTY_COMPONENT = "uncertainty_component"

INPUT_ROLES = (
    DIRECT_OBSERVATION,
    CALIBRATED_MEASUREMENT,
    MODEL_PARAMETER,
    CORRECTION,
    DERIVED_QUANTITY,
    DEFINITION,
    EXTERNAL_COMPARISON_REFERENCE,
    TARGET_OUTPUT,
    UNCERTAINTY_COMPONENT,
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

ESTIMATOR_INPUT_PROPAGATION = "estimator_input_propagation"
DIRECT_MEASURAND_CONTRIBUTIONS = "direct_measurand_contributions"
UNCERTAINTY_BASES = (
    ESTIMATOR_INPUT_PROPAGATION,
    DIRECT_MEASURAND_CONTRIBUTIONS,
)


class BridgeValidationError(ValueError):
    """Raised when a record could be mistaken for a valid physical bridge."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BridgeValidationError(f"{label} must be a nonempty string")
    return value


_ACCESS_DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", re.ASCII)
_DOI_RE = re.compile(r"^10\.[0-9]{4,9}/\S+$", re.ASCII)
_CERTIFICATE_ISSUER_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._+\-]{0,63}$",
    re.ASCII,
)
_CERTIFICATE_RECORD_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._+\-]{0,127}$",
    re.ASCII,
)
_SOURCE_IDENTIFIER_PREFIXES = ("doi", "url", "certificate")
_BLANK_LIKE_SOURCE_CODEPOINTS = frozenset(
    {0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0}
)


def _validate_access_date(value: object, label: str) -> str:
    text = _require_text(value, label)
    if text != text.strip() or _ACCESS_DATE_RE.fullmatch(text) is None:
        raise BridgeValidationError(
            f"{label} must be a strict ISO calendar date in YYYY-MM-DD form"
        )
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise BridgeValidationError(
            f"{label} must be a valid calendar date in YYYY-MM-DD form"
        ) from error
    return text


def _validate_source_identifier(value: object, label: str) -> str:
    text = _require_text(value, label)
    if unicodedata.normalize("NFC", text) != text:
        raise BridgeValidationError(
            f"{label} must be NFC-normalized; automatic rewriting is forbidden"
        )
    if text != text.strip() or any(
        character.isspace()
        or not character.isprintable()
        or unicodedata.category(character) in {"Mn", "Me"}
        or ord(character) in _BLANK_LIKE_SOURCE_CODEPOINTS
        for character in text
    ):
        raise BridgeValidationError(
            f"{label} cannot contain whitespace, control, or invisible characters"
        )
    prefix, separator, payload = text.partition(":")
    if not separator or prefix not in _SOURCE_IDENTIFIER_PREFIXES:
        raise BridgeValidationError(
            f"{label} must use one of the explicit prefixes: "
            "doi:, url:, certificate:"
        )
    if prefix == "doi":
        if _DOI_RE.fullmatch(payload) is None:
            raise BridgeValidationError(
                f"{label} has a malformed DOI; expected doi:10.<registrant>/<suffix>"
            )
    elif prefix == "url":
        try:
            parsed = urlsplit(payload)
            hostname = parsed.hostname
            _ = parsed.port
        except ValueError as error:
            raise BridgeValidationError(f"{label} URL is unparseable") from error
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or hostname is None
            or not any(character.isalnum() for character in hostname)
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise BridgeValidationError(
                f"{label} URL must be an absolute credential-free https URL"
            )
    else:
        if payload.count("/") != 1:
            raise BridgeValidationError(
                f"{label} certificate must use issuer/record form"
            )
        issuer, record_id = payload.split("/", 1)
        if (
            _CERTIFICATE_ISSUER_RE.fullmatch(issuer) is None
            or _CERTIFICATE_RECORD_RE.fullmatch(record_id) is None
        ):
            raise BridgeValidationError(
                f"{label} certificate must use issuer/record form"
            )
    return text


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
        source_identifier = self.source_identifier
        if source_identifier is not None:
            _validate_source_identifier(
                source_identifier,
                f"source identifier for {self.identifier}",
            )
        if self.edition is not None:
            _require_text(self.edition, f"edition for {self.identifier}")
        if self.access_date is not None:
            _validate_access_date(
                self.access_date,
                f"access date for {self.identifier}",
            )


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
    uncertainty_basis: str = ESTIMATOR_INPUT_PROPAGATION
    component_ids: tuple[str, ...] = ()

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
        if self.uncertainty_basis not in UNCERTAINTY_BASES:
            raise BridgeValidationError(
                f"unknown uncertainty basis: {self.uncertainty_basis}"
            )
        object.__setattr__(
            self,
            "component_ids",
            _unique_text(self.component_ids, "uncertainty component identifier"),
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
    LeanTheoremLink(
        identifier="conditional_inverse_square_estimator_correctness",
        fully_qualified_name=(
            "TheNumberProject.FormalPhysics."
            "inverseSquareEstimator_eq_gravitationalConstant"
        ),
        relation=(
            "F_hat = G * m_1 * m_2 / r^2 and "
            "G_hat = F_hat * r^2 / (m_1 * m_2) imply G_hat = G"
        ),
        conditional_scope=(
            "Lean kernel-checks the estimator equality only from the named "
            "inverse-square relation, estimator definition, and nonzero mass and "
            "separation hypotheses; it does not certify apparatus inputs or evidence."
        ),
        estimator_rearrangement_certified=True,
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
    uncertainty_component_upstream_ids: tuple[str, ...]
    uncertainty_component_target_path_audits: tuple[TargetPathAudit, ...]
    uncertainty_gaps: tuple[str, ...]
