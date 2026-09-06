"""Source isolation and an independent exact-rational combined-estimator oracle."""

from copy import deepcopy
from dataclasses import replace
from decimal import Context, Decimal, FloatOperation, ROUND_HALF_EVEN, ROUND_UP, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from Discovery import hust_2018_aaf_combined_measurement_model as combined
from Discovery.physical_bridge import measurement_model_record
from Discovery.physical_bridge_schema import BridgeValidationError, CorrelationDeclaration
from Discovery.physical_bridge_validation import validate_measurement_model


def rational_oracle():
    """Read frozen source strings directly; never call a production calculator."""
    directory = combined.ROOT / "Experiments/GMeasurements"
    models = json.loads((directory / "hust_2018_aaf_depth_2b_measurement_models_v2.json").read_text())["models"]
    graph = json.loads((directory / "hust_2018_aaf_required_inputs_depth_2b_v2.json").read_text())
    scopes = ("AAF-I", "AAF-II", "AAF-III")
    g, u = [], []
    for scope, model in zip(scopes, models):
        target = next(q for q in model["quantities"] if q["identifier"] == scope + ":G_hat")
        g.append(Fraction(target["numerical_record"]["value_decimal"]))
        u.append(Fraction(target["numerical_record"]["standard_uncertainty_decimal"]))
    variances = [x*x for x in u]
    unnormalized = [1 / x for x in variances]
    p = [x / sum(unnormalized) for x in unnormalized]
    components = {row["component_id"]: [g[i] * Fraction(row[scope]) / 1000000
                                      for i, scope in enumerate(scopes)] for row in graph["components"]}
    covariance = [[variances[i] if i == j else sum(values[i]*values[j] for key, values in components.items()
                   if key != "statistical_angular_acceleration") for j in range(3)] for i in range(3)]
    central = sum(p[i] * g[i] for i in range(3))
    variance = sum(p[i] * covariance[i][j] * p[j] for i in range(3) for j in range(3))
    componentwise = sum(sum(p[i]*values[i] for i in range(3))**2 for key, values in components.items()
                        if key != "statistical_angular_acceleration")
    componentwise += sum((p[i] * components["statistical_angular_acceleration"][i])**2 for i in range(3))
    with localcontext(Context(prec=85, rounding=ROUND_HALF_EVEN)):
        standard = (Decimal(variance.numerator) / Decimal(variance.denominator)).sqrt()
    return dict(g=g, variances=variances, weights=p, covariance=covariance, central=central,
                variance=variance, componentwise=componentwise, standard=standard)


class CombinedHUSTModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = combined.load_inputs()
        cls.covariance = combined.construct_covariance(cls.inputs)
        cls.model = combined.build_model()
        cls.result = combined.reconstruct(cls.inputs)
        cls.oracle = rational_oracle()

    def assertRelativeEqual(self, actual, expected):
        actual, expected = Fraction(actual), Fraction(expected)
        self.assertLessEqual(abs(actual-expected) / abs(expected), Fraction("1e-47"))

    def test_canonical_variances_weights_and_covariance_match_independent_oracle(self):
        for i in range(3):
            self.assertRelativeEqual(self.covariance["matrix"][i][i], self.oracle["variances"][i])
            self.assertRelativeEqual(self.result["weights"][i]["coefficient_decimal"], self.oracle["weights"][i])
            for j in range(3):
                self.assertRelativeEqual(self.covariance["matrix"][i][j], self.oracle["covariance"][i][j])
        self.assertTrue(self.covariance["diagnostics"]["positive_definite"])
        self.assertEqual(len(self.covariance["diagnostics"]["principal_minors"]), 7)

    def test_central_estimate_and_standard_uncertainty_match_independent_oracle(self):
        self.assertRelativeEqual(self.result["G_hat_decimal"], self.oracle["central"])
        self.assertRelativeEqual(self.result["variance_decimal"], self.oracle["variance"])
        self.assertRelativeEqual(self.result["standard_uncertainty_decimal"], self.oracle["standard"])

    def test_quadratic_variance_matches_independent_source_component_expression(self):
        self.assertRelativeEqual(self.result["variance_decimal"], self.oracle["componentwise"])

    def test_known_feasibility_numbers_are_only_regression_expectations(self):
        path = combined.ROOT / combined.DIRECTORY / "hust_2018_aaf_combined_feasibility_v1.json"
        historical = json.loads(path.read_text())["reconstructed_combined_result"]
        for name in ("G_hat_decimal", "standard_uncertainty_decimal", "relative_standard_uncertainty_ppm"):
            self.assertRelativeEqual(self.result[name], historical[name])
        for actual, expected in zip(self.result["weights"], historical["weights"]):
            self.assertRelativeEqual(actual["coefficient_decimal"], expected)

    def test_only_authorized_individual_fields_are_projected(self):
        records = combined.load_frozen_records()
        for model in records[combined.MODELS_NAME]["models"]:
            model.pop("external_comparison")
            model["quantities"] = [q for q in model["quantities"] if q["identifier"] not in
                                  (model["uncertainty_reconstruction"]["scope"] + ":comparison_delta",
                                   model["uncertainty_reconstruction"]["scope"] + ":published_G")]
            model["provenance_graphs"]["metrological"]["edges"] = [e for e in model["provenance_graphs"]["metrological"]["edges"] if e["kind"] != "comparison"]
            model["unrelated_output"] = "not an input"
        records[combined.GRAPH_NAME].pop("terminal_comparisons")
        self.assertEqual(combined.project_inputs(records), self.inputs)

    def test_final_published_uncertainty_cannot_replace_individual_total(self):
        records = combined.load_frozen_records()
        model = records[combined.MODELS_NAME]["models"][0]
        model["uncertainty_reconstruction"]["absolute_standard_uncertainty_decimal"] = "7.8e-16"
        target = next(q for q in model["quantities"] if q["identifier"] == "AAF-I:G_hat")
        target["numerical_record"]["standard_uncertainty_decimal"] = "7.8e-16"
        with self.assertRaisesRegex(BridgeValidationError, "differs from authorized individual"):
            combined.project_inputs(records)

    def test_feasibility_output_cannot_replace_an_individual_estimate(self):
        inputs = deepcopy(self.inputs)
        inputs["runs"][0]["G_hat_decimal"] = self.result["G_hat_decimal"]
        with self.assertRaisesRegex(BridgeValidationError, "terminal substitutions forbidden"):
            combined.reconstruct(inputs)

    def test_unrelated_or_terminal_operands_cannot_be_added_to_projection(self):
        for key in ("published_G", "published_standard_uncertainty", "reconstructed_combined_result"):
            inputs = deepcopy(self.inputs)
            inputs[key] = "6.674484e-11"
            with self.subTest(key=key), self.assertRaises(BridgeValidationError):
                combined.reconstruct(inputs)

    def test_feasibility_results_and_comparisons_can_be_changed_or_deleted_without_effect(self):
        expected = combined.serialize_artifact(combined.build_artifact())
        original = Path.read_bytes
        filename = "hust_2018_aaf_combined_feasibility_v1.json"
        for delete in (False, True):
            def substituted(path):
                if path.name == filename:
                    if delete:
                        raise FileNotFoundError(filename)
                    record = json.loads(original(path))
                    record["reconstructed_combined_result"] = {"G_hat_decimal": "999", "standard_uncertainty_decimal": "888"}
                    record.pop("terminal_published_comparison")
                    record["decision"] = "NUMERICAL_AGREEMENT_REMOVED"
                    return json.dumps(record).encode()
                return original(path)
            with self.subTest(delete=delete), patch.object(Path, "read_bytes", substituted):
                self.assertEqual(combined.serialize_artifact(combined.build_artifact()), expected)

    def test_terminal_publication_substitution_leaves_all_production_fields_identical(self):
        original = combined.build_artifact()
        for published in (None, {**combined.DEFAULT_COMPARISON, "G_decimal": "99", "relative_standard_uncertainty_ppm": "123"}):
            actual = combined.build_artifact(published=published)
            before = deepcopy(original)
            before.pop("terminal_published_comparison")
            actual.pop("terminal_published_comparison")
            self.assertEqual(combined.serialize_artifact(actual), combined.serialize_artifact(before))
        self.assertGreater(Decimal(original["terminal_published_comparison"]["relative_uncertainty_delta_ppm"]), 0)

    def test_weight_computation_uses_only_individual_total_uncertainties(self):
        quantities = {q.identifier: q for q in self.model.quantities}
        expected = combined.normalized_inverse_variance_weights({q: quantities[q].standard_uncertainty for q in combined.INPUT_IDS})
        actual = {term.quantity_id: term.coefficient for term in self.model.weighted_estimator_terms}
        self.assertEqual(expected, actual)
        statistical = {run["target_id"]: Decimal(run["components"][-1]["value_ppm"]) for run in self.inputs["runs"]}
        self.assertNotEqual(actual, combined.normalized_inverse_variance_weights(statistical))

    def test_component_order_changes_are_rejected(self):
        records = combined.load_frozen_records()
        records[combined.GRAPH_NAME]["components"].reverse()
        for model in records[combined.MODELS_NAME]["models"]:
            model["uncertainty_reconstruction"]["components_in_source_order"].reverse()
        with self.assertRaisesRegex(BridgeValidationError, "misordered"):
            combined.project_inputs(records)

    def test_missing_duplicate_or_mismatched_component_ids_fail(self):
        for mutation in ("missing", "duplicate", "mismatch"):
            records = combined.load_frozen_records()
            rows = records[combined.GRAPH_NAME]["components"]
            if mutation == "missing": rows.pop()
            elif mutation == "duplicate": rows[-1] = deepcopy(rows[0])
            else: rows[-1]["component_id"] = "invented"
            with self.subTest(mutation=mutation), self.assertRaises(BridgeValidationError):
                combined.project_inputs(records)

    def test_wrong_statistical_and_nonstatistical_correlations_fail(self):
        for index, value in ((20, "1"), (0, "0")):
            correlations = combined.correlation_inventory()
            correlations[index]["off_diagonal_rho"] = value
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "source correlation rule changed"):
                combined.construct_covariance(self.inputs, correlations)

    def test_cross_item_covariance_is_forbidden(self):
        correlations = combined.correlation_inventory()
        correlations[0]["other_component_id"] = correlations[1]["component_id"]
        with self.assertRaisesRegex(ValueError, "undeclared fields"):
            combined.construct_covariance(self.inputs, correlations)

    def test_covariance_matrix_cannot_be_replaced_or_incompletely_serialized(self):
        for mutation in ("off_diagonal", "diagonal", "unknown_input", "cross_item", "missing"):
            covariance = deepcopy(self.covariance)
            if mutation == "off_diagonal": covariance["matrix"][0][1] = covariance["matrix"][1][0] = "0"
            elif mutation == "diagonal": covariance["matrix"][0][0] = "1"
            elif mutation == "unknown_input": covariance["input_ids"][0] = "undeclared"
            elif mutation == "cross_item": covariance["component_terms"][0]["other_component_id"] = "air_density"
            else: covariance["component_terms"].pop()
            with self.subTest(mutation=mutation), self.assertRaisesRegex(BridgeValidationError, "covariance differs"):
                combined.reconstruct(self.inputs, covariance)

    def test_covariance_with_undeclared_model_inputs_is_rejected(self):
        uncertainty = self.model.uncertainty_model
        bad = CorrelationDeclaration("undeclared", combined.INPUT_IDS[0], Decimal("0"), combined.COVARIANCE_UNIT)
        model = replace(self.model, uncertainty_model=replace(uncertainty, correlations=(*uncertainty.correlations, bad)))
        with self.assertRaisesRegex(BridgeValidationError, "unknown uncertainty input"):
            validate_measurement_model(model)

    def test_hust_model_revalidates_covariance_and_output_values(self):
        uncertainty = self.model.uncertainty_model
        for model in (
            replace(self.model, uncertainty_model=replace(uncertainty, correlations=uncertainty.correlations[:-1])),
            replace(self.model, quantities=tuple(replace(q, value=Decimal("1")) if q.identifier == combined.TARGET_ID else q for q in self.model.quantities)),
        ):
            with self.assertRaisesRegex(BridgeValidationError, "combined model differs"):
                combined.validate_hust_combined_model(model, self.inputs, self.covariance)

    def test_authoritative_decimal_float_and_ambient_context_boundary(self):
        inputs = deepcopy(self.inputs)
        inputs["runs"][0]["standard_uncertainty_decimal"] = 8.3e-16
        with self.assertRaises(BridgeValidationError):
            combined.reconstruct(inputs)
        with localcontext() as context:
            context.prec = 7
            context.rounding = ROUND_UP
            context.traps[FloatOperation] = True
            self.assertEqual(combined.reconstruct(self.inputs), self.result)

    def test_model_keeps_complete_individual_central_ancestry(self):
        record = measurement_model_record(self.model)
        identifiers = set(record["target_path_audit"]["estimator_upstream_node_ids"])
        expected = {q["identifier"] for run in self.inputs["runs"] for q in run["quantities"]}
        self.assertEqual(identifiers, expected)
        self.assertEqual(len(identifiers), 18)
        self.assertFalse(any(":published_G" in q or ":comparison_delta" in q or ":u_ppm:" in q for q in identifiers))

    def test_preregistration_ancestry_and_frozen_historical_hashes(self):
        prereg = combined.verify_preregistration()
        for pin in prereg["preserved_baseline_files"]:
            with self.subTest(path=pin["path"]):
                data = (combined.ROOT / pin["path"]).read_bytes()
                self.assertEqual(len(data), pin["byte_length"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), pin["sha256"])
        self.assertEqual(prereg["baseline_main_sha"], combined.BASELINE)
        self.assertIn("already known", combined.EXTERNAL_ANCHOR["scope"])


if __name__ == "__main__":
    unittest.main()
