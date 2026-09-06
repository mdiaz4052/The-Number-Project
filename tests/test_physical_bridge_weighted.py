"""Behavioral boundaries for the narrow normalized weighted estimator variant."""

from dataclasses import replace
from decimal import Decimal, localcontext, ROUND_UP
from fractions import Fraction
import unittest

from Discovery import hust_2018_aaf_combined_measurement_model as combined
from Discovery.dimensions import FORCE
from Discovery.physical_bridge import (
    build_example_artifact, build_inverse_square_model, serialize_artifact,
    measurement_model_record,
)
from Discovery.physical_bridge_schema import (
    BridgeValidationError, EstimatorTerm, WeightedEstimatorTerm, ProvenanceEdge,
    EXTERNAL_COMPARISON_REFERENCE, REGISTERED_EXPRESSION, UNCERTAINTY_COMPONENT,
)
from Discovery.physical_bridge_validation import (
    evaluate_measurement_model, normalized_inverse_variance_weights, validate_measurement_model,
)


def change_quantity(model, identifier, **changes):
    return replace(model, quantities=tuple(
        replace(q, **changes) if q.identifier == identifier else q for q in model.quantities
    ))


class WeightedEstimatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = combined.build_model()

    def test_valid_normalized_estimator_is_structural_and_uncertainty_qualified(self):
        result = evaluate_measurement_model(self.model)
        self.assertEqual(result.estimator_dimension, self.model.quantities[-1].dimension)
        self.assertEqual(result.uncertainty_status, "satisfied")
        self.assertEqual(result.replication_status, "incomplete")
        record = measurement_model_record(self.model)["measurement_model"]
        self.assertIn("weighted_estimator_terms", record)
        self.assertNotIn("estimator_terms", record)

    def test_missing_weighted_term_is_rejected(self):
        with self.assertRaises(BridgeValidationError):
            validate_measurement_model(replace(self.model, weighted_estimator_terms=self.model.weighted_estimator_terms[:-1]))

    def test_duplicate_empirical_input_is_rejected(self):
        with self.assertRaisesRegex(BridgeValidationError, "duplicate estimator"):
            validate_measurement_model(replace(self.model, weighted_estimator_terms=(*self.model.weighted_estimator_terms, self.model.weighted_estimator_terms[0])))

    def test_coefficients_must_be_finite_positive_decimals(self):
        for value in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), Decimal("0"), Decimal("-1"), None):
            with self.subTest(value=value), self.assertRaises(BridgeValidationError):
                WeightedEstimatorTerm("run", value)
        for value in (0.3, True, "0.3"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                WeightedEstimatorTerm("run", value)

    def test_mixed_input_dimensions_are_rejected(self):
        with self.assertRaisesRegex(BridgeValidationError, "common dimension"):
            validate_measurement_model(change_quantity(self.model, combined.INPUT_IDS[0], dimension=FORCE))

    def test_different_numerical_units_are_rejected(self):
        with self.assertRaisesRegex(BridgeValidationError, "units"):
            validate_measurement_model(change_quantity(self.model, combined.INPUT_IDS[0], unit="cm^3 kg^-1 s^-2"))

    def test_non_normalized_weights_are_rejected(self):
        terms = tuple(WeightedEstimatorTerm(q, Decimal("0.2")) for q in combined.INPUT_IDS)
        with self.assertRaisesRegex(BridgeValidationError, "not normalized"):
            validate_measurement_model(replace(self.model, weighted_estimator_terms=terms))

    def test_normalization_does_not_replace_inverse_variance_recomputation(self):
        terms = tuple(WeightedEstimatorTerm(q, Decimal(w)) for q, w in zip(combined.INPUT_IDS, ("0.3", "0.3", "0.4")))
        with self.assertRaisesRegex(BridgeValidationError, "recomputed inverse total variances"):
            validate_measurement_model(replace(self.model, weighted_estimator_terms=terms))

    def test_both_estimator_representations_are_rejected(self):
        with self.assertRaisesRegex(BridgeValidationError, "mutually exclusive"):
            validate_measurement_model(replace(self.model, estimator_terms=(EstimatorTerm(combined.INPUT_IDS[0], Fraction(1)),)))

    def test_empty_estimator_is_rejected(self):
        with self.assertRaisesRegex(BridgeValidationError, "missing an estimator"):
            validate_measurement_model(replace(self.model, weighted_estimator_terms=(), weighting_rule=None))

    def test_weighting_rule_cannot_be_attached_to_a_monomial(self):
        with self.assertRaisesRegex(BridgeValidationError, "requires a weighted"):
            validate_measurement_model(replace(build_inverse_square_model(), weighting_rule=self.model.weighting_rule))

    def test_unknown_weight_rule_is_rejected(self):
        with self.assertRaisesRegex(BridgeValidationError, "unrecognized"):
            validate_measurement_model(replace(self.model, weighting_rule="GLS"))

    def test_definition_must_name_every_weighted_input(self):
        edges = tuple(e for e in self.model.definition_edges if not (e.child == combined.TARGET_ID and e.parent == combined.INPUT_IDS[0]))
        with self.assertRaisesRegex(BridgeValidationError, "definition edges"):
            validate_measurement_model(replace(self.model, definition_edges=edges))

    def test_registered_target_path_in_weighted_input_is_rejected(self):
        model = change_quantity(self.model, combined.INPUT_IDS[0], algebraic_provenance_kind=REGISTERED_EXPRESSION,
                                registered_dependency_signature=(("G", Fraction(1)),))
        with self.assertRaisesRegex(BridgeValidationError, "estimator ancestry reaches G"):
            validate_measurement_model(model)

    def test_registered_target_path_in_deep_weighted_ancestry_is_rejected(self):
        model = change_quantity(self.model, "AAF-I:alpha_corrected", algebraic_provenance_kind=REGISTERED_EXPRESSION,
                                registered_dependency_signature=(("G", Fraction(1)),))
        with self.assertRaisesRegex(BridgeValidationError, "estimator ancestry reaches G"):
            validate_measurement_model(model)

    def test_external_comparison_cannot_be_a_weighted_input(self):
        with self.assertRaisesRegex(BridgeValidationError, "forbidden estimator input role"):
            validate_measurement_model(change_quantity(self.model, combined.INPUT_IDS[0], role=EXTERNAL_COMPARISON_REFERENCE))

    def test_external_comparison_cannot_feed_weighted_ancestry(self):
        original = next(q for q in self.model.quantities if q.identifier == combined.INPUT_IDS[0])
        reference = replace(original, identifier="published_reference", symbol="G_published_reference",
                            registered_dependency_signature=None, role=EXTERNAL_COMPARISON_REFERENCE)
        model = replace(self.model, quantities=(*self.model.quantities, reference),
                        comparison_reference_ids=(reference.identifier,),
                        metrological_edges=(*self.model.metrological_edges, ProvenanceEdge(
                            "AAF-I:alpha_corrected", reference.identifier, "model_input", "Attempt terminal calibration.")))
        with self.assertRaisesRegex(BridgeValidationError, "may feed comparison nodes only"):
            validate_measurement_model(model)

    def test_dm011_component_role_is_rejected_under_estimator_input_propagation(self):
        # This is a deep ancestor, not a weighted term or declared direct component.
        model = change_quantity(self.model, "AAF-I:alpha_corrected", role=UNCERTAINTY_COMPONENT)
        with self.assertRaisesRegex(BridgeValidationError, "uncertainty component or component ancestor enters central"):
            validate_measurement_model(model)

    def test_inverse_variance_arithmetic_rejects_invalid_uncertainties(self):
        for value in (Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), None):
            with self.subTest(value=value), self.assertRaises(BridgeValidationError):
                normalized_inverse_variance_weights({"a": value})
        with self.assertRaises(TypeError):
            normalized_inverse_variance_weights({"a": 0.2})
        with self.assertRaises(BridgeValidationError):
            normalized_inverse_variance_weights({})

    def test_weight_calculation_is_independent_of_ambient_context_and_mapping_order(self):
        inputs = {"c": Decimal("3"), "a": Decimal("1"), "b": Decimal("2")}
        canonical = normalized_inverse_variance_weights(inputs)
        with localcontext() as context:
            context.prec = 7
            context.rounding = ROUND_UP
            self.assertEqual(canonical, normalized_inverse_variance_weights(dict(reversed(list(inputs.items())))))

    def test_legacy_example_serializes_byte_identically(self):
        path = combined.ROOT / combined.DIRECTORY / "inverse_square_bridge_example.json"
        self.assertEqual(serialize_artifact(build_example_artifact()), path.read_text())


if __name__ == "__main__":
    unittest.main()
