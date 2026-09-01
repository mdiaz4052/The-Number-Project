"""Security-critical graph, target-path, validation, and evaluation logic.

This module is the audit boundary for rejecting circular or structurally ambiguous
measurement models.  It is deliberately separate from artifact construction and
CLI behavior.
"""

from __future__ import annotations

import unicodedata
from fractions import Fraction
from typing import Iterable, Mapping, Sequence

from Discovery.constants import DEFAULT_SEARCH_CONSTANTS, GRAVITATIONAL_CONSTANT_G
from Discovery.dependency_definitions import (
    DEFAULT_DEPENDENCY_CATALOG,
    DependencyCatalog,
    DependencyDefinition,
    build_dependency_catalog,
)
from Discovery.dimensions import (
    DIMENSIONLESS,
    GRAVITATIONAL_CONSTANT,
    Dimension,
)
from Discovery.physical_bridge_schema import (
    CALIBRATED_MEASUREMENT,
    CORRECTION,
    DECLARED_LOCAL_ATOM,
    DEFINITION,
    DEFINITION_EDGE_KINDS,
    DERIVED_QUANTITY,
    DIRECT_OBSERVATION,
    DOCUMENTED,
    EMPIRICAL_RECORD,
    EXTERNAL_COMPARISON_REFERENCE,
    INCOMPLETE,
    LEAN_THEOREMS_BY_ID,
    METROLOGICAL_EDGE_KINDS,
    NO_REGISTERED_TARGET_PATH,
    NOT_APPLICABLE,
    REQUIRED_BUT_UNPOPULATED,
    SATISFIED,
    STRUCTURAL_EXAMPLE,
    TARGET_KEY,
    TARGET_OUTPUT,
    TARGET_PATH_DETECTED,
    UNRESOLVED,
    UNRESOLVED_ALGEBRAIC_PROVENANCE,
    UNRESOLVED_PROVENANCE_EVIDENCE,
    BridgeEvaluation,
    BridgeValidationError,
    MeasurementModel,
    ProvenanceEdge,
    QuantityRecord,
    TargetPathAudit,
    _strict_signature,
    _target_power,
    fraction_text,
)


def _normalized_display_symbol(symbol: str) -> str:
    """Return the exact-match form used by the display namespace guard."""

    without_format_controls = "".join(
        character
        for character in symbol
        if unicodedata.category(character) != "Cf"
    )
    return unicodedata.normalize("NFC", without_format_controls).strip()


_REGISTERED_SYMBOL_TO_KEY = {
    _normalized_display_symbol(constant.symbol): constant.key
    for constant in (GRAVITATIONAL_CONSTANT_G, *DEFAULT_SEARCH_CONSTANTS)
}


def _validate_display_symbol_namespace(model: MeasurementModel) -> None:
    symbol_owners: dict[str, str] = {}
    for quantity in sorted(model.quantities, key=lambda item: item.identifier):
        normalized_symbol = _normalized_display_symbol(quantity.symbol)
        if not normalized_symbol:
            raise BridgeValidationError(
                "display symbol is empty after normalization: "
                f"{quantity.identifier}"
            )
        registered_key = _REGISTERED_SYMBOL_TO_KEY.get(normalized_symbol)
        if registered_key is not None:
            raise BridgeValidationError(
                "display symbol collides with registered catalog symbol after "
                f"normalization: {normalized_symbol} (registered key {registered_key}; "
                f"quantity {quantity.identifier})"
            )
        previous_owner = symbol_owners.get(normalized_symbol)
        if previous_owner is not None:
            raise BridgeValidationError(
                "duplicate display symbol after normalization: "
                f"{normalized_symbol} ({previous_owner}, {quantity.identifier})"
            )
        symbol_owners[normalized_symbol] = quantity.identifier


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
    local_quantities = tuple(
        quantity
        for quantity in sorted(model.quantities, key=lambda item: item.identifier)
        if quantity.algebraic_provenance_kind == DECLARED_LOCAL_ATOM
    )
    for quantity in local_quantities:
        if quantity.identifier in dimensions:
            raise BridgeValidationError(
                f"local atom shadows registered key: {quantity.identifier}"
            )
    _validate_display_symbol_namespace(model)
    for quantity in local_quantities:
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
    # Defense in depth: the general external-reference boundary below already
    # rejects these paths. Keep this earlier check so calibration/correction misuse
    # receives an explicit, auditable diagnostic; it is not an independent barrier.
    for guarded_id in (*model.calibration_source_ids, *model.correction_ids):
        guarded_upstream = set(_upstream_ids((guarded_id,), all_edges))
        leaked = guarded_upstream & references
        if leaked:
            raise BridgeValidationError(
                f"reference G is used in calibration or correction {guarded_id}: "
                f"{sorted(leaked)}"
            )

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
    if model.evidence_level == EMPIRICAL_RECORD:
        source_required_ids = (
            estimator_upstream
            | set(model.calibration_source_ids)
            | set(model.correction_ids)
        )
        for identifier in sorted(source_required_ids):
            quantity = quantities[identifier]
            if quantity.value is None:
                continue
            missing_metadata: list[str] = []
            if quantity.provenance_evidence != DOCUMENTED:
                missing_metadata.append("documented provenance")
            missing_metadata.extend(
                label
                for label, value in (
                    ("source identifier", quantity.source_identifier),
                    ("source edition", quantity.edition),
                    ("source access date", quantity.access_date),
                )
                if value is None
            )
            if missing_metadata:
                raise BridgeValidationError(
                    "populated empirical estimator/calibration ancestry requires "
                    "documented "
                    f"source provenance metadata for {identifier}; missing "
                    f"{', '.join(missing_metadata)}"
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
