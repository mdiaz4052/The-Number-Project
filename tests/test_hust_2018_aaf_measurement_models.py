from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import unittest

from Discovery.hust_2018_aaf_measurement_models import (
    EXPECTED_ASSESSMENTS,
    HUSTMeasurementModelError,
    PREREGISTRATION_SHA256,
    _build_model_from_records,
    build_artifact,
    build_hust_aaf_model,
    serialize_artifact,
    validate_hust_aaf_model,
    verify_preregistration,
)
from Discovery.hust_2018_aaf_source_audit import (
    DEFAULT_OUTPUT as SOURCE_AUDIT_OUTPUT,
    REQUIRED_INPUTS_PATH,
    load_audit_manifest,
    load_required_inputs,
    reconstruct_experiment,
)
from Discovery.physical_bridge_schema import (
    BridgeValidationError,
    EstimatorTerm,
    ProvenanceEdge,
)
from Discovery.physical_bridge_validation import evaluate_measurement_model


SCOPES = ("AAF-I", "AAF-II", "AAF-III")


class HUST2018AAFMeasurementModelTests(unittest.TestCase):
    def _records(self):
        return (
            load_audit_manifest(SOURCE_AUDIT_OUTPUT),
            load_required_inputs(REQUIRED_INPUTS_PATH),
        )

    def _quantity_map(self, model):
        return {quantity.identifier: quantity for quantity in model.quantities}

    def test_preregistration_is_byte_pinned(self):
        record = verify_preregistration(Path("."))
        self.assertEqual(record["sha256"], PREREGISTRATION_SHA256)

    def test_all_three_scopes_build_as_empirical_depth_2a_models(self):
        graph = load_required_inputs(REQUIRED_INPUTS_PATH)
        for scope in SCOPES:
            with self.subTest(scope=scope):
                model = build_hust_aaf_model(scope)
                quantities = self._quantity_map(model)
                target = quantities[f"{scope}:G_hat"]
                self.assertEqual(target.value, reconstruct_experiment(scope, graph))
                self.assertIsNone(target.standard_uncertainty)
                self.assertIsNone(target.uncertainty_unit)
                self.assertFalse(target.exact)
                self.assertIsNone(model.uncertainty_model)
                self.assertEqual(model.replication_identifiers, ())
                self.assertIsNone(model.lean_link_identifier)
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

    def test_published_G_changes_do_not_change_reconstructed_G(self):
        manifest, graph = self._records()
        baseline = _build_model_from_records("AAF-I", manifest, graph)
        baseline_target = self._quantity_map(baseline)["AAF-I:G_hat"].value

        mutated = deepcopy(graph)
        experiment = next(
            record for record in mutated["experiments"] if record["experiment_id"] == "AAF-I"
        )
        experiment["published_comparison"]["value"] = "9.999999"
        changed = _build_model_from_records("AAF-I", manifest, mutated)
        changed_quantities = self._quantity_map(changed)
        self.assertEqual(changed_quantities["AAF-I:G_hat"].value, baseline_target)
        self.assertNotEqual(
            changed_quantities["AAF-I:published_G"].value,
            self._quantity_map(baseline)["AAF-I:published_G"].value,
        )

    def test_external_published_G_cannot_become_an_estimator_input(self):
        model = build_hust_aaf_model("AAF-I")
        target_id = "AAF-I:G_hat"
        published_id = "AAF-I:published_G"
        alpha_id = "AAF-I:alpha_si"
        correction_id = "AAF-I:correction_factor"
        mutated = replace(
            model,
            estimator_terms=(
                EstimatorTerm(alpha_id, 1),
                EstimatorTerm(correction_id, 1),
                EstimatorTerm(published_id, -1),
            ),
            definition_edges=(
                ProvenanceEdge(target_id, alpha_id, "definition", "hostile test"),
                ProvenanceEdge(target_id, correction_id, "definition", "hostile test"),
                ProvenanceEdge(target_id, published_id, "definition", "hostile test"),
            ),
        )
        with self.assertRaises(BridgeValidationError):
            validate_hust_aaf_model(mutated, "AAF-I")

    def test_cross_scope_estimator_ancestry_is_rejected(self):
        model = build_hust_aaf_model("AAF-I")
        old_id = "AAF-I:alpha_corrected"
        foreign_id = "AAF-II:alpha_corrected"
        quantities = []
        for quantity in model.quantities:
            if quantity.identifier == old_id:
                quantities.append(
                    replace(
                        quantity,
                        identifier=foreign_id,
                        registered_dependency_signature=None,
                    )
                )
            else:
                quantities.append(quantity)
        edges = tuple(
            replace(edge, parent=foreign_id) if edge.parent == old_id else edge
            for edge in model.metrological_edges
        )
        mutated = replace(model, quantities=tuple(quantities), metrological_edges=edges)
        with self.assertRaises(HUSTMeasurementModelError):
            validate_hust_aaf_model(mutated, "AAF-I")

    def test_combined_scope_is_not_constructible(self):
        with self.assertRaises(HUSTMeasurementModelError):
            build_hust_aaf_model("AAF-combined")

    def test_scope_authorization_is_individual_and_fail_closed(self):
        manifest, graph = self._records()
        mutated = deepcopy(manifest)
        mutated["depth_2a_authorized_experiments"].remove("AAF-I")
        with self.assertRaises(HUSTMeasurementModelError):
            _build_model_from_records("AAF-I", mutated, graph)
        self.assertIsNotNone(_build_model_from_records("AAF-II", mutated, graph))

    def test_combined_authorization_boundary_must_remain_false(self):
        manifest, graph = self._records()
        mutated = deepcopy(manifest)
        mutated["combined_aaf_reconstruction_authorized"] = True
        with self.assertRaises(HUSTMeasurementModelError):
            _build_model_from_records("AAF-I", mutated, graph)

    def test_magnetic_damper_operator_and_direction_are_load_bearing(self):
        manifest, graph = self._records()
        for field, bad_value in (
            ("correction_operator", "multiply_by_1_minus_delta"),
            ("correction_direction", "decrease_G"),
        ):
            with self.subTest(field=field):
                mutated = deepcopy(graph)
                experiment = next(
                    record
                    for record in mutated["experiments"]
                    if record["experiment_id"] == "AAF-III"
                )
                node = next(
                    node
                    for node in experiment["nodes"]
                    if node["node_id"] == "AAF-III:magnetic_damper_ppm"
                )
                node[field] = bad_value
                with self.assertRaises(ValueError):
                    _build_model_from_records("AAF-III", manifest, mutated)

    def test_target_uncertainty_and_exactness_are_forbidden_at_depth_2a(self):
        model = build_hust_aaf_model("AAF-II")
        target_id = "AAF-II:G_hat"
        for mutation in (
            {"standard_uncertainty": Decimal("1e-15"), "uncertainty_unit": "m^3 kg^-1 s^-2"},
            {"exact": True},
        ):
            with self.subTest(mutation=mutation):
                quantities = tuple(
                    replace(quantity, **mutation)
                    if quantity.identifier == target_id
                    else quantity
                    for quantity in model.quantities
                )
                mutated = replace(model, quantities=quantities)
                with self.assertRaises(HUSTMeasurementModelError):
                    validate_hust_aaf_model(mutated, "AAF-II")

    def test_preregistered_arithmetic_is_load_bearing(self):
        model = build_hust_aaf_model("AAF-III")
        correction_id = "AAF-III:correction_factor"
        quantities = tuple(
            replace(quantity, value=quantity.value + Decimal("1e-9"))
            if quantity.identifier == correction_id
            else quantity
            for quantity in model.quantities
        )
        mutated = replace(model, quantities=quantities)
        with self.assertRaises(HUSTMeasurementModelError):
            validate_hust_aaf_model(mutated, "AAF-III")

    def test_artifact_is_three_individual_empirical_records_without_combined_output(self):
        artifact = build_artifact()
        self.assertFalse(
            artifact["source_audit_authorization"]["combined_aaf_reconstruction_authorized"]
        )
        self.assertFalse(artifact["global_boundaries"]["combined_estimator_present"])
        self.assertFalse(artifact["global_boundaries"]["replication_claim"])
        self.assertEqual(len(artifact["models"]), 3)
        self.assertEqual(
            [record["central_value_reconstruction"]["scope"] for record in artifact["models"]],
            list(SCOPES),
        )
        for record in artifact["models"]:
            central = record["central_value_reconstruction"]
            scope_record = record["scope_and_evidence_level"]
            assessments = record["assessments"]
            self.assertIsNone(central["G_hat_standard_uncertainty_decimal"])
            self.assertFalse(central["agreement_is_acceptance_criterion"])
            self.assertEqual(
                scope_record["classification"],
                "published_empirical_central_value_reconstruction",
            )
            self.assertTrue(scope_record["empirical_population"])
            self.assertFalse(scope_record["uncertainty_qualified"])
            self.assertFalse(scope_record["replication_claim"])
            self.assertEqual(assessments, EXPECTED_ASSESSMENTS)
            self.assertEqual(record["replication_identifiers"], [])

    def test_artifact_serialization_is_deterministic(self):
        first = serialize_artifact(build_artifact())
        second = serialize_artifact(build_artifact())
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
