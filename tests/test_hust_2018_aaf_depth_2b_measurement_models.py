from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, localcontext
import json
from pathlib import Path
import unittest

from Discovery.hust_2018_aaf_depth_2b_authorization import (
    CLARIFICATION_PATH,
    EXPECTED_COMPONENTS,
    EXPECTED_RSS_PPM,
    OFFICIAL_SOURCE_PATH,
    REQUIRED_INPUTS_PATH,
    SCOPES,
)
from Discovery.hust_2018_aaf_depth_2b_measurement_models import (
    COMPONENT_DESCRIPTION_PREFIX,
    DEFAULT_OUTPUT,
    EXPECTED_ASSESSMENTS,
    HUSTDepth2BMeasurementModelError,
    SOURCE_ACCESS_DATE,
    SOURCE_EDITION,
    SOURCE_IDENTIFIER,
    ZERO_CORRELATION_JUSTIFICATION,
    _build_depth_2b_model_from_records,
    build_artifact,
    build_hust_aaf_depth_2b_model,
    serialize_artifact,
    validate_hust_aaf_depth_2b_model,
)
from Discovery.hust_2018_aaf_measurement_models import build_hust_aaf_model
from Discovery.physical_bridge_schema import (
    DIRECT_MEASURAND_CONTRIBUTIONS,
    EXPLICIT_ZERO_ASSUMPTION,
    MODEL_PARAMETER,
    UNCERTAINTY_COMPONENT,
)
from Discovery.physical_bridge_validation import evaluate_measurement_model


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


class HUST2018AAFDepth2BMeasurementModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _load(OFFICIAL_SOURCE_PATH)
        self.clarification = _load(CLARIFICATION_PATH)
        self.graph = _load(REQUIRED_INPUTS_PATH)

    def _baseline_and_model(self, scope: str):
        baseline = build_hust_aaf_model(scope)
        model = _build_depth_2b_model_from_records(
            scope,
            baseline,
            self.source,
            self.clarification,
            self.graph,
        )
        return baseline, model

    def _validate(self, model, scope: str, baseline) -> None:
        validate_hust_aaf_depth_2b_model(
            model,
            scope,
            self.graph,
            baseline_model=baseline,
        )

    def test_all_three_scopes_are_uncertainty_qualified_depth_2b_models(self) -> None:
        for scope in SCOPES:
            with self.subTest(scope=scope):
                baseline, model = self._baseline_and_model(scope)
                baseline_quantities = _quantity_map(baseline)
                quantities = _quantity_map(model)
                target = quantities[f"{scope}:G_hat"]
                self.assertEqual(
                    target.value,
                    baseline_quantities[f"{scope}:G_hat"].value,
                )
                self.assertIsNotNone(target.standard_uncertainty)
                self.assertEqual(target.uncertainty_unit, target.unit)
                self.assertEqual(len(model.quantities), len(baseline.quantities) + 21)
                self.assertEqual(model.replication_identifiers, ())
                self.assertIsNone(model.lean_link_identifier)
                uncertainty = model.uncertainty_model
                assert uncertainty is not None
                self.assertEqual(
                    uncertainty.uncertainty_basis,
                    DIRECT_MEASURAND_CONTRIBUTIONS,
                )
                self.assertEqual(
                    uncertainty.correlation_policy,
                    EXPLICIT_ZERO_ASSUMPTION,
                )
                self.assertEqual(
                    uncertainty.zero_correlation_justification,
                    ZERO_CORRELATION_JUSTIFICATION,
                )
                self.assertEqual(uncertainty.input_ids, ())
                self.assertEqual(uncertainty.correction_ids, ())
                self.assertIsNone(uncertainty.coverage_factor)
                self.assertIsNone(uncertainty.coverage_probability)
                evaluation = evaluate_measurement_model(model)
                actual = {
                    "dimensional_status": evaluation.dimensional_status,
                    "algebraic_model_status": evaluation.algebraic_model_status,
                    "registered_target_path_status": evaluation.registered_target_path_status,
                    "metrological_provenance_status": evaluation.metrological_provenance_status,
                    "uncertainty_status": evaluation.uncertainty_status,
                    "empirical_population_status": evaluation.empirical_population_status,
                    "replication_status": evaluation.replication_status,
                }
                self.assertEqual(actual, EXPECTED_ASSESSMENTS)

    def test_component_records_are_exactly_source_bound_in_frozen_order(self) -> None:
        for scope in SCOPES:
            with self.subTest(scope=scope):
                baseline, model = self._baseline_and_model(scope)
                del baseline
                components = model.quantities[-21:]
                self.assertEqual(
                    [component.identifier.rpartition(":")[2] for component in components],
                    [row[0] for row in EXPECTED_COMPONENTS],
                )
                column = SCOPES.index(scope) + 2
                for component, expected in zip(components, EXPECTED_COMPONENTS):
                    self.assertEqual(component.value, Decimal(expected[column]))
                    self.assertEqual(component.role, UNCERTAINTY_COMPONENT)
                    self.assertEqual(component.unit, "ppm")
                    self.assertIsNone(component.standard_uncertainty)
                    self.assertIsNone(component.uncertainty_unit)
                    self.assertEqual(component.source_identifier, SOURCE_IDENTIFIER)
                    self.assertEqual(component.edition, SOURCE_EDITION)
                    self.assertEqual(component.access_date, SOURCE_ACCESS_DATE)
                    self.assertIn(COMPONENT_DESCRIPTION_PREFIX, component.description)

    def test_precision_50_rss_and_absolute_uncertainty_are_exact(self) -> None:
        for scope in SCOPES:
            with self.subTest(scope=scope):
                _, model = self._baseline_and_model(scope)
                target = _quantity_map(model)[f"{scope}:G_hat"]
                values = [Decimal(row[scope]) for row in self.graph["components"]]
                with localcontext() as context:
                    context.prec = 50
                    relative = sum(value * value for value in values).sqrt()
                    expected_absolute = abs(target.value) * relative * Decimal("1e-6")
                self.assertEqual(relative, EXPECTED_RSS_PPM[scope])
                self.assertEqual(target.standard_uncertainty, expected_absolute)

    def test_component_inventory_mutations_fail_closed(self) -> None:
        scope = "AAF-II"
        baseline, model = self._baseline_and_model(scope)
        components = list(model.quantities[-21:])
        base_quantities = list(model.quantities[:-21])
        mutations = {}
        mutations["missing"] = replace(
            model,
            quantities=tuple(base_quantities + components[:-1]),
        )
        extra = replace(
            components[0],
            identifier=f"{scope}:u_ppm:extra_component",
            symbol="u_AAF_II_extra_component_ppm",
            registered_dependency_signature=None,
        )
        mutations["extra"] = replace(
            model,
            quantities=tuple(base_quantities + components + [extra]),
        )
        mutations["duplicate"] = replace(
            model,
            quantities=tuple(base_quantities + components + [components[0]]),
        )
        renamed = replace(
            components[0],
            identifier=f"{scope}:u_ppm:renamed_component",
            symbol="u_AAF_II_renamed_component_ppm",
            registered_dependency_signature=None,
        )
        mutations["renamed"] = replace(
            model,
            quantities=tuple(base_quantities + [renamed] + components[1:]),
        )
        reordered = components.copy()
        reordered[0], reordered[1] = reordered[1], reordered[0]
        mutations["reordered"] = replace(
            model,
            quantities=tuple(base_quantities + reordered),
        )
        foreign = replace(
            components[0],
            identifier="AAF-III:u_ppm:pendulum_dimensions",
            symbol="u_AAF_III_foreign_pendulum_dimensions_ppm",
            registered_dependency_signature=None,
        )
        mutations["cross_scope"] = replace(
            model,
            quantities=tuple(base_quantities + [foreign] + components[1:]),
        )
        for label, changed in mutations.items():
            with self.subTest(mutation=label):
                with self.assertRaises(ValueError):
                    self._validate(changed, scope, baseline)

    def test_component_semantic_mutations_fail_closed(self) -> None:
        scope = "AAF-II"
        baseline, model = self._baseline_and_model(scope)
        first_id = f"{scope}:u_ppm:pendulum_dimensions"
        clamp_id = f"{scope}:u_ppm:clamp_and_ferrule"
        mutations = {
            "wrong_unit": _replace_quantity(model, first_id, unit="percent"),
            "wrong_role": _replace_quantity(model, first_id, role=MODEL_PARAMETER),
            "wrong_source": _replace_quantity(
                model,
                first_id,
                source_identifier="url:https://mctoon.net/mirror.pdf",
            ),
            "cross_column": _replace_quantity(
                model,
                clamp_id,
                value=Decimal("0.70"),
            ),
            "uncertainty_on_uncertainty": _replace_quantity(
                model,
                first_id,
                standard_uncertainty=Decimal("0.01"),
                uncertainty_unit="ppm",
            ),
        }
        for label, changed in mutations.items():
            with self.subTest(mutation=label):
                with self.assertRaises(ValueError):
                    self._validate(changed, scope, baseline)

    def test_arithmetic_mutations_fail_closed_for_the_intended_reason(self) -> None:
        scope = "AAF-I"
        baseline, model = self._baseline_and_model(scope)
        target_id = f"{scope}:G_hat"
        target = _quantity_map(model)[target_id]
        assert target.value is not None
        values = [Decimal(row[scope]) for row in self.graph["components"]]
        with localcontext() as context:
            context.prec = 50
            sum_of_squares = sum(value * value for value in values)
            wrong_relative = {
                "sum_instead_of_rss": sum(values),
                "missing_one_square": (
                    sum(value * value for value in values[:-1]) + values[-1]
                ).sqrt(),
                "missing_square_root": sum_of_squares,
            }
        with localcontext() as context:
            context.prec = 28
            wrong_relative["default_precision_28"] = sum_of_squares.sqrt()
        self.assertNotEqual(
            wrong_relative["default_precision_28"],
            EXPECTED_RSS_PPM[scope],
        )
        for label, relative in wrong_relative.items():
            with self.subTest(mutation=label):
                with localcontext() as context:
                    context.prec = 50
                    mutated_absolute = (
                        abs(target.value) * relative * Decimal("1e-6")
                    )
                changed = _replace_quantity(
                    model,
                    target_id,
                    standard_uncertainty=mutated_absolute,
                )
                with self.assertRaisesRegex(
                    HUSTDepth2BMeasurementModelError,
                    "target uncertainty",
                ):
                    self._validate(changed, scope, baseline)
        with localcontext() as context:
            context.prec = 50
            wrong_ppm_absolute = (
                abs(target.value) * EXPECTED_RSS_PPM[scope] * Decimal("1e-5")
            )
        wrong_ppm = _replace_quantity(
            model,
            target_id,
            standard_uncertainty=wrong_ppm_absolute,
        )
        with self.assertRaisesRegex(
            HUSTDepth2BMeasurementModelError,
            "target uncertainty",
        ):
            self._validate(wrong_ppm, scope, baseline)

    def test_terminal_values_cannot_change_reconstructed_outputs(self) -> None:
        scope = "AAF-III"
        baseline, model = self._baseline_and_model(scope)
        baseline_target = _quantity_map(model)[f"{scope}:G_hat"]

        published_id = f"{scope}:published_G"
        mutated_baseline = _replace_quantity(
            baseline,
            published_id,
            value=Decimal("9e-11"),
            standard_uncertainty=Decimal("9e-15"),
        )
        changed_from_published = _build_depth_2b_model_from_records(
            scope,
            mutated_baseline,
            self.source,
            self.clarification,
            self.graph,
        )
        published_target = _quantity_map(changed_from_published)[f"{scope}:G_hat"]
        self.assertEqual(published_target.value, baseline_target.value)
        self.assertEqual(
            published_target.standard_uncertainty,
            baseline_target.standard_uncertainty,
        )

        changed_graph = deepcopy(self.graph)
        terminal = changed_graph["terminal_comparisons"][scope]
        terminal["published_g_m3_kg-1_s-2"] = "8e-11"
        terminal["published_standard_uncertainty_m3_kg-1_s-2"] = "8e-15"
        terminal["displayed_total_ppm"] = "88"
        changed_from_terminal = _build_depth_2b_model_from_records(
            scope,
            baseline,
            self.source,
            self.clarification,
            changed_graph,
        )
        terminal_target = _quantity_map(changed_from_terminal)[f"{scope}:G_hat"]
        self.assertEqual(terminal_target.value, baseline_target.value)
        self.assertEqual(
            terminal_target.standard_uncertainty,
            baseline_target.standard_uncertainty,
        )

    def test_official_source_bypass_and_independence_overclaim_fail_closed(self) -> None:
        scope = "AAF-I"
        baseline = build_hust_aaf_model(scope)
        source = deepcopy(self.source)
        source["capture"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            _build_depth_2b_model_from_records(
                scope,
                baseline,
                source,
                self.clarification,
                self.graph,
            )

        model = _build_depth_2b_model_from_records(
            scope,
            baseline,
            self.source,
            self.clarification,
            self.graph,
        )
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        changed = replace(
            model,
            uncertainty_model=replace(
                uncertainty,
                zero_correlation_justification=(
                    "All physical sources are experimentally independent."
                ),
            ),
        )
        with self.assertRaisesRegex(
            HUSTDepth2BMeasurementModelError,
            "uncertainty-model contract",
        ):
            self._validate(changed, scope, baseline)

    def test_external_comparisons_cannot_become_uncertainty_components(self) -> None:
        scope = "AAF-I"
        baseline, model = self._baseline_and_model(scope)
        uncertainty = model.uncertainty_model
        assert uncertainty is not None
        changed = replace(
            model,
            uncertainty_model=replace(
                uncertainty,
                component_ids=(
                    *uncertainty.component_ids[:-1],
                    f"{scope}:published_G",
                ),
            ),
        )
        with self.assertRaises(ValueError):
            self._validate(changed, scope, baseline)

    def test_combined_scope_is_not_constructible(self) -> None:
        with self.assertRaises(ValueError):
            build_hust_aaf_depth_2b_model("AAF-combined")

    def test_artifact_is_deterministic_and_contains_no_combined_output(self) -> None:
        artifact = build_artifact(Path("."))
        self.assertEqual(
            DEFAULT_OUTPUT.read_text(encoding="utf-8"),
            serialize_artifact(artifact),
        )
        self.assertEqual(len(artifact["models"]), 3)
        self.assertFalse(artifact["global_boundaries"]["combined_estimator_present"])
        self.assertFalse(
            artifact["global_boundaries"][
                "published_final_uncertainties_used_as_inputs"
            ]
        )
        self.assertFalse(
            artifact["global_boundaries"]["displayed_totals_used_as_inputs"]
        )
        for record in artifact["models"]:
            self.assertEqual(record["assessments"], EXPECTED_ASSESSMENTS)


if __name__ == "__main__":
    unittest.main()
