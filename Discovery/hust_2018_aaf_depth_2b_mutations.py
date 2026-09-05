"""Run narrow behavioral mutations against the HUST AAF depth-2b guards.

The score includes only mutations whose changed runtime behavior is rejected by a
behavioral validator or output oracle.  Artifact freshness, git-tree state, and
historical byte sentinels remain permanent guards but are explicitly not scored.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping

from Discovery.hust_2018_aaf_depth_2b_authorization import (
    CLARIFICATION_PATH,
    OFFICIAL_SOURCE_PATH,
    REQUIRED_INPUTS_PATH,
    validate_clarification_record,
    validate_official_source_record,
    validate_required_inputs_graph,
)
from Discovery.hust_2018_aaf_depth_2b_measurement_models import (
    _build_depth_2b_model_from_records,
    validate_hust_aaf_depth_2b_model,
)
from Discovery.hust_2018_aaf_measurement_models import build_hust_aaf_model
from Discovery.physical_bridge_schema import MODEL_PARAMETER


MUTATION_ARTIFACT_SCHEMA_VERSION = 1
DEFAULT_OUTPUT = Path(
    "Experiments/GMeasurements/hust_2018_aaf_depth_2b_mutation_results_v1.json"
)


class HUSTDepth2BMutationError(ValueError):
    """A mutation survived or the mutation suite could not run."""


class _BehavioralGuardFailure(AssertionError):
    """Internal signal that an output oracle detected mutated behavior."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HUSTDepth2BMutationError(f"mutation input unavailable: {path}") from error
    if not isinstance(value, dict):
        raise HUSTDepth2BMutationError(f"mutation input is not an object: {path}")
    return value


def _quantity_map(model):
    return {quantity.identifier: quantity for quantity in model.quantities}


def _replace_quantity(model, identifier: str, **changes):
    return replace(
        model,
        quantities=tuple(
            replace(quantity, **changes)
            if quantity.identifier == identifier
            else quantity
            for quantity in model.quantities
        ),
    )


def _reject_changed_output(candidate: Decimal, expected: Decimal) -> None:
    if candidate != expected:
        raise _BehavioralGuardFailure("mutated result differs from the authorized output")


def _case(
    identifier: str,
    category: str,
    guard: str,
    action: Callable[[], None],
) -> dict[str, str]:
    try:
        action()
    except (ValueError, AssertionError, TypeError):
        return {
            "mutation_id": identifier,
            "category": category,
            "expected_behavioral_guard": guard,
            "outcome": "KILLED",
        }
    raise HUSTDepth2BMutationError(f"behavioral mutation survived: {identifier}")


def run_mutations(root: Path = Path(".")) -> dict[str, Any]:
    source = _read_json(root / OFFICIAL_SOURCE_PATH)
    clarification = _read_json(root / CLARIFICATION_PATH)
    graph = _read_json(root / REQUIRED_INPUTS_PATH)
    baseline = build_hust_aaf_model("AAF-I", root=root)
    model = _build_depth_2b_model_from_records(
        "AAF-I", baseline, source, clarification, graph
    )
    target_id = "AAF-I:G_hat"
    target = _quantity_map(model)[target_id]
    if target.value is None or target.standard_uncertainty is None:
        raise HUSTDepth2BMutationError("authorized target is unexpectedly unpopulated")
    values = [Decimal(row["AAF-I"]) for row in graph["components"]]
    with localcontext() as context:
        context.prec = 50
        sum_of_squares = sum(value * value for value in values)
        rss = sum_of_squares.sqrt()
        expected_absolute = abs(target.value) * rss * Decimal("1e-6")
        missing_square_relative = (
            sum(value * value for value in values[:-1]) + values[-1]
        ).sqrt()

    def absolute_from_relative(
        relative: Decimal, conversion: Decimal = Decimal("1e-6")
    ) -> Decimal:
        with localcontext() as context:
            context.prec = 50
            return abs(target.value) * relative * conversion

    cases: list[dict[str, str]] = []

    def graph_mutation(mutator: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        def action() -> None:
            changed = deepcopy(graph)
            mutator(changed)
            validate_required_inputs_graph(changed)

        return action

    cases.append(
        _case(
            "missing_component",
            "component_inventory",
            "exact ordered component second key",
            graph_mutation(lambda changed: changed["components"].pop()),
        )
    )
    cases.append(
        _case(
            "duplicate_component",
            "component_inventory",
            "exact ordered component second key",
            graph_mutation(
                lambda changed: changed["components"].append(
                    deepcopy(changed["components"][0])
                )
            ),
        )
    )

    def add_extra(changed: dict[str, Any]) -> None:
        extra = deepcopy(changed["components"][0])
        extra["component_id"] = "extra_component"
        changed["components"].append(extra)

    cases.append(
        _case(
            "extra_component",
            "component_inventory",
            "exact ordered component second key",
            graph_mutation(add_extra),
        )
    )
    cases.append(
        _case(
            "renamed_component",
            "component_inventory",
            "exact ordered component second key",
            graph_mutation(
                lambda changed: changed["components"][0].__setitem__(
                    "component_id", "renamed"
                )
            ),
        )
    )

    def reorder(changed: dict[str, Any]) -> None:
        changed["components"][0], changed["components"][1] = (
            changed["components"][1],
            changed["components"][0],
        )

    cases.append(
        _case(
            "reordered_components",
            "component_inventory",
            "exact ordered component second key",
            graph_mutation(reorder),
        )
    )
    cases.append(
        _case(
            "wrong_component_unit",
            "component_semantics",
            "component unit validator",
            graph_mutation(
                lambda changed: changed["components"][0].__setitem__(
                    "unit", "percent"
                )
            ),
        )
    )
    cases.append(
        _case(
            "wrong_component_source",
            "component_semantics",
            "official source binding",
            graph_mutation(
                lambda changed: changed["components"][0].__setitem__(
                    "source_id", "historical_mirror"
                )
            ),
        )
    )

    def cross_column(changed: dict[str, Any]) -> None:
        changed["components"][4]["AAF-I"], changed["components"][4]["AAF-II"] = (
            changed["components"][4]["AAF-II"],
            changed["components"][4]["AAF-I"],
        )

    cases.append(
        _case(
            "cross_column_component",
            "component_semantics",
            "component cross-column second key",
            graph_mutation(cross_column),
        )
    )
    cases.append(
        _case(
            "combined_authorization_flag",
            "scope_isolation",
            "combined authorization must remain false",
            graph_mutation(
                lambda changed: changed["authorizations"].__setitem__(
                    "combined_aaf_reconstruction_authorized", True
                )
            ),
        )
    )

    def source_hash_bypass() -> None:
        changed = deepcopy(source)
        changed["capture"]["sha256"] = "0" * 64
        validate_official_source_record(changed)

    cases.append(
        _case(
            "official_source_hash_bypass",
            "source_authorization",
            "official Nature capture second key",
            source_hash_bypass,
        )
    )

    def source_locator_falsification() -> None:
        changed = deepcopy(source)
        changed["source"]["table_locator"] = "Table 2"
        validate_official_source_record(changed)

    cases.append(
        _case(
            "falsified_table_locator",
            "source_authorization",
            "official Table 1 locator second key",
            source_locator_falsification,
        )
    )

    def unknown_clarification_key() -> None:
        changed = deepcopy(clarification)
        changed["target_derived_note"] = "hostile extension"
        validate_clarification_record(changed)

    cases.append(
        _case(
            "unknown_target_derived_note",
            "strict_schema",
            "unknown clarification key rejection",
            unknown_clarification_key,
        )
    )

    def byte_identity_overclaim() -> None:
        changed = deepcopy(source)
        changed["nonclaims"].append(
            "The rendered table is byte‑\n identical to the publisher PDF."
        )
        validate_official_source_record(changed)

    cases.append(
        _case(
            "normalized_byte_identity_overclaim",
            "source_authorization",
            "normalized byte-identity overclaim rejection",
            byte_identity_overclaim,
        )
    )

    def validate_changed_model(changed) -> None:
        validate_hust_aaf_depth_2b_model(
            changed,
            "AAF-I",
            graph,
            baseline_model=baseline,
        )

    cases.append(
        _case(
            "wrong_component_role",
            "component_semantics",
            "apparatus-specific component role validator",
            lambda: validate_changed_model(
                _replace_quantity(
                    model,
                    "AAF-I:u_ppm:pendulum_dimensions",
                    role=MODEL_PARAMETER,
                )
            ),
        )
    )

    def cross_scope_component() -> None:
        old = _quantity_map(model)["AAF-I:u_ppm:pendulum_dimensions"]
        foreign = replace(
            old,
            identifier="AAF-II:u_ppm:pendulum_dimensions",
            symbol="u_AAF_II_foreign_pendulum_dimensions_ppm",
            registered_dependency_signature=None,
        )
        changed = replace(
            model,
            quantities=tuple(
                foreign if quantity.identifier == old.identifier else quantity
                for quantity in model.quantities
            ),
        )
        validate_changed_model(changed)

    cases.append(
        _case(
            "cross_scope_component_ancestry",
            "scope_isolation",
            "individual-scope ancestry validator",
            cross_scope_component,
        )
    )

    def independence_overclaim() -> None:
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        validate_changed_model(
            replace(
                model,
                uncertainty_model=replace(
                    uncertainty,
                    zero_correlation_justification=(
                        "All physical sources are experimentally independent."
                    ),
                ),
            )
        )

    cases.append(
        _case(
            "physical_independence_overclaim",
            "correlation_semantics",
            "qualified zero-correlation policy",
            independence_overclaim,
        )
    )

    for identifier, relative in (
        ("sum_instead_of_rss", sum(values)),
        ("missing_component_square", missing_square_relative),
        ("missing_square_root", sum_of_squares),
    ):
        candidate = absolute_from_relative(relative)
        cases.append(
            _case(
                identifier,
                "uncertainty_arithmetic",
                "precision-50 absolute uncertainty oracle",
                lambda candidate=candidate: _reject_changed_output(
                    candidate, expected_absolute
                ),
            )
        )
    cases.append(
        _case(
            "incorrect_ppm_conversion",
            "uncertainty_arithmetic",
            "precision-50 absolute uncertainty oracle",
            lambda: _reject_changed_output(
                absolute_from_relative(rss, Decimal("1e-5")), expected_absolute
            ),
        )
    )
    with localcontext() as context:
        context.prec = 28
        precision_28_rss = sum_of_squares.sqrt()
        precision_28_absolute = abs(target.value) * precision_28_rss * Decimal("1e-6")
    cases.append(
        _case(
            "default_decimal_precision_28",
            "uncertainty_arithmetic",
            "serialized precision-50 output oracle",
            lambda: _reject_changed_output(precision_28_absolute, expected_absolute),
        )
    )
    cases.append(
        _case(
            "displayed_total_as_input",
            "terminal_leakage",
            "reconstructed uncertainty output oracle",
            lambda: _reject_changed_output(
                absolute_from_relative(
                    Decimal(
                        graph["terminal_comparisons"]["AAF-I"]["displayed_total_ppm"]
                    )
                ),
                expected_absolute,
            ),
        )
    )
    published = _quantity_map(baseline)["AAF-I:published_G"]
    assert published.standard_uncertainty is not None
    cases.append(
        _case(
            "published_final_uncertainty_as_input",
            "terminal_leakage",
            "reconstructed uncertainty output oracle",
            lambda: _reject_changed_output(
                published.standard_uncertainty,
                expected_absolute,
            ),
        )
    )
    cases.append(
        _case(
            "combined_scope_authorization",
            "scope_isolation",
            "individual-scope constructor boundary",
            lambda: _build_depth_2b_model_from_records(
                "AAF-combined",
                baseline,
                source,
                clarification,
                graph,
            ),
        )
    )

    killed = sum(case["outcome"] == "KILLED" for case in cases)
    return {
        "artifact_schema_version": MUTATION_ARTIFACT_SCHEMA_VERSION,
        "artifact": "HUST 2018 AAF depth-2b behavioral mutation results",
        "mutation_scope": "narrow in-memory behavioral mutations",
        "scoring_rule": (
            "Only behavioral validator failures and changed-output oracle failures "
            "count as kills."
        ),
        "excluded_non_behavioral_guards": [
            "git tree-state sentinels",
            "artifact source-state --check comparisons",
            "historical byte-preservation sentinels",
        ],
        "cases": cases,
        "score": {
            "killed": killed,
            "total": len(cases),
            "survived": len(cases) - killed,
            "ratio_decimal": str(Decimal(killed) / Decimal(len(cases))),
        },
        "decision": "PASS" if killed == len(cases) else "FAIL",
    }


def serialize_artifact(record: Mapping[str, Any]) -> str:
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="rerun behavioral mutations and verify the committed result bytes",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        rendered = serialize_artifact(run_mutations(Path(".")))
        if args.check:
            try:
                existing = args.output.read_text(encoding="utf-8")
            except OSError as error:
                raise HUSTDepth2BMutationError(
                    f"mutation artifact is unavailable: {args.output}"
                ) from error
            if existing != rendered:
                raise HUSTDepth2BMutationError(
                    f"mutation artifact is stale: {args.output}"
                )
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    except HUSTDepth2BMutationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
