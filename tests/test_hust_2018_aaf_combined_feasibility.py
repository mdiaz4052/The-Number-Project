from __future__ import annotations

import ast
from copy import deepcopy
from decimal import Decimal, ROUND_DOWN, localcontext
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from Discovery import hust_2018_aaf_combined_feasibility as audit


class CombinedFeasibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prereg, cls.records = audit.load_frozen_records()
        cls.inputs = audit.project_inputs(cls.records)
        cls.covariance = audit.construct_covariance(cls.inputs, audit.correlation_inventory())

    def test_source_prescription_supports_go_and_complete_evidence(self):
        result = audit.audit(self.inputs)
        self.assertEqual(result["decision"], "GO")
        self.assertEqual(result["reason_codes"], [])
        self.assertEqual(set(result["required_source_claims"]), set(self.prereg["required_evidence"]))
        for claim in result["required_source_claims"].values():
            self.assertEqual(claim["status"], "supported")
            self.assertTrue(claim["locator"])
            self.assertTrue(claim["quote_ids"])
            self.assertTrue(all(key in audit.QUOTES for key in claim["quote_ids"]))

    def test_independent_exact_rational_calculation_matches_decimal(self):
        # Independent oracle: no production covariance/weight helper, no terminal target.
        runs = self.inputs["runs"]
        g = [Fraction(run["G_hat_decimal"]) for run in runs]
        u = [[g[i] * Fraction(c["value_ppm"]) / 10**6 for c in run["components"]]
             for i, run in enumerate(runs)]
        v = [sum(x*x for x in row) for row in u]
        # Product-of-other-variances normalization, algebraically equivalent to 1/v.
        raw = [v[1]*v[2], v[0]*v[2], v[0]*v[1]]
        weights = [x/sum(raw) for x in raw]
        estimate = sum(w*x for w, x in zip(weights, g))
        variance = sum(sum(weights[i]*u[i][k] for i in range(3))**2 for k in range(20))
        variance += sum((weights[i]*u[i][20])**2 for i in range(3))
        result = audit.audit(self.inputs)["reconstructed_combined_result"]
        with localcontext() as context:
            context.prec = 90
            def decimal(f):
                return Decimal(f.numerator) / Decimal(f.denominator)
            comparisons = [(result["G_hat_decimal"], decimal(estimate)),
                           (result["variance_decimal"], decimal(variance)),
                           (result["standard_uncertainty_decimal"], decimal(variance).sqrt())]
            comparisons += list(zip(result["weights"], map(decimal, weights)))
            for actual, expected in comparisons:
                self.assertLess(abs(Decimal(actual)-expected)/abs(expected), Decimal("1e-47"))

    def test_all_seven_exact_principal_minors_are_positive(self):
        diagnostics = self.covariance["diagnostics"]
        self.assertEqual(len(diagnostics["principal_minors"]), 7)
        self.assertTrue(all(Fraction(x["exact_fraction"]) > 0 for x in diagnostics["principal_minors"]))
        self.assertTrue(diagnostics["positive_definite"])
        self.assertTrue(diagnostics["invertible"])
        self.assertFalse(diagnostics["inverse_required"])
        self.assertFalse(diagnostics["inverse_or_regularization_used"])

    def test_diagonals_reproduce_independent_rss_and_preserved_models(self):
        individuals = audit.individual_diagnostics(self.inputs, self.records)
        for i, individual in enumerate(individuals):
            self.assertEqual(individual["diagonal_variance"], self.covariance["matrix"][i][i])
            self.assertTrue(individual["historical_reconstruction_preserved"])
            self.assertEqual(individual["component_count"], 21)

    def test_every_scope_has_distinct_complete_inventory(self):
        self.assertEqual([run["scope"] for run in self.inputs["runs"]], list(audit.SCOPES))
        identities = [c["quantity_id"] for r in self.inputs["runs"] for c in r["components"]]
        self.assertEqual(len(identities), 63)
        self.assertEqual(len(set(identities)), 63)
        self.assertNotEqual(self.inputs["runs"][0]["components"], self.inputs["runs"][1]["components"])

    def test_forbidden_upstream_targets_and_weights_fail(self):
        for key in self.prereg["forbidden_inputs"] + ["weights", "coefficient", "terminal_comparison"]:
            for layer in ("root", "run", "component"):
                with self.subTest(key=key, layer=layer):
                    inputs = deepcopy(self.inputs)
                    target = inputs if layer == "root" else inputs["runs"][0]
                    if layer == "component":
                        target = target["components"][0]
                    target[key] = "6.674484e-11"
                    with self.assertRaises(audit.FeasibilityError):
                        audit.audit(inputs)

    def test_terminal_change_or_deletion_cannot_change_computation(self):
        baseline = audit.audit(self.inputs)
        for terminal in (None, {"published_G": "1e90", "published_u": "1e-99"}, {"weights": ["1", "0", "0"]}):
            actual = audit.audit(self.inputs, terminal_comparison=terminal)
            actual["terminal_published_comparison"] = None
            self.assertEqual(actual, baseline)

    def test_terminal_objects_inside_historical_artifacts_are_not_projected(self):
        records = deepcopy(self.records)
        records[audit.GRAPH_NAME]["terminal_comparisons"] = {"G": "1e90"}
        for model in records[audit.MODELS_NAME]["models"]:
            model["external_comparison"] = {"published_G": "1e-90"}
            model["uncertainty_reconstruction"].pop("terminal_comparisons_not_used_as_inputs")
        self.assertEqual(audit.project_inputs(records), self.inputs)

    def test_authoritative_builder_is_independent_of_terminal_function(self):
        original = audit.build_artifact()
        with patch.object(audit, "terminal_comparison", return_value={"changed": "1"}):
            changed = audit.build_artifact()
        original.pop("terminal_published_comparison")
        changed.pop("terminal_published_comparison")
        self.assertEqual(original, changed)

    def test_missing_duplicated_renamed_or_misscoped_component_fails(self):
        for mode in ("missing", "duplicate", "renamed", "scope"):
            with self.subTest(mode=mode):
                inputs = deepcopy(self.inputs)
                components = inputs["runs"][1]["components"]
                if mode == "missing":
                    components.pop()
                elif mode == "duplicate":
                    components[1] = deepcopy(components[0])
                elif mode == "renamed":
                    components[0]["component_id"] = "apparatus_dimensions"
                else:
                    components[0]["quantity_id"] = "AAF-I:u_ppm:pendulum_dimensions"
                with self.assertRaises(audit.FeasibilityError):
                    audit.audit(inputs)

    def test_perturbed_source_transcription_fails_even_if_graph_and_model_agree(self):
        records = deepcopy(self.records)
        records[audit.GRAPH_NAME]["components"][0]["AAF-I"] = "0.17"
        records[audit.MODELS_NAME]["models"][0]["uncertainty_reconstruction"]["components_in_source_order"][0]["value_ppm"] = "0.17"
        with self.assertRaisesRegex(audit.FeasibilityError, "transcription"):
            audit.project_inputs(records)

    def test_substituted_central_value_and_nonstring_or_nonfinite_numbers_fail(self):
        for value in ("6.674484e-11", "NaN", "Infinity", "-1", 1.5, None):
            inputs = deepcopy(self.inputs)
            inputs["runs"][0]["G_hat_decimal"] = value
            with self.subTest(value=value), self.assertRaises(audit.FeasibilityError):
                audit.audit(inputs)

    def test_duplicated_or_extra_run_fails(self):
        inputs = deepcopy(self.inputs)
        inputs["runs"][1] = deepcopy(inputs["runs"][0])
        with self.assertRaises(audit.FeasibilityError):
            audit.audit(inputs)
        inputs["runs"].append(deepcopy(inputs["runs"][0]))
        with self.assertRaises(audit.FeasibilityError):
            audit.audit(inputs)

    def test_asymmetric_matrix_fails(self):
        matrix = deepcopy(self.covariance["matrix"])
        matrix[0][1] = "0"
        with self.assertRaisesRegex(audit.FeasibilityError, "asymmetric"):
            audit.validate_covariance(matrix, self.inputs, audit.correlation_inventory())

    def test_invalid_correlation_coefficient_fails(self):
        for rho in ("1.01", "-1.01", "NaN", "Infinity", 0):
            correlations = audit.correlation_inventory()
            correlations[0]["off_diagonal_rho"] = rho
            with self.subTest(rho=rho), self.assertRaises(audit.FeasibilityError):
                audit.construct_covariance(self.inputs, correlations)

    def test_statistical_term_made_correlated_fails(self):
        correlations = audit.correlation_inventory()
        correlations[-1]["off_diagonal_rho"] = "1"
        with self.assertRaisesRegex(audit.FeasibilityError, "source correlation"):
            audit.construct_covariance(self.inputs, correlations)

    def test_shared_nonstatistical_term_made_independent_fails(self):
        correlations = audit.correlation_inventory()
        correlations[0]["off_diagonal_rho"] = "0"
        with self.assertRaisesRegex(audit.FeasibilityError, "source correlation"):
            audit.construct_covariance(self.inputs, correlations)

    def test_missing_duplicate_and_undeclared_covariance_terms_fail(self):
        for mode in ("missing", "duplicate", "extra", "renamed"):
            terms = audit.correlation_inventory()
            if mode == "missing":
                terms.pop()
            elif mode == "duplicate":
                terms[0] = terms[1]
            elif mode == "extra":
                terms.append({"component_id": "hidden_covariance", "off_diagonal_rho": "1"})
            else:
                terms[0]["component_id"] = "hidden_covariance"
            with self.subTest(mode=mode), self.assertRaises(audit.FeasibilityError):
                audit.construct_covariance(self.inputs, terms)

    def test_incorrect_diagonal_variance_fails(self):
        matrix = deepcopy(self.covariance["matrix"])
        matrix[0][0] = "1"
        with self.assertRaisesRegex(audit.FeasibilityError, "diagonal variance"):
            audit.validate_covariance(matrix, self.inputs, audit.correlation_inventory())

    def test_symmetric_psd_but_unauthorized_covariance_fails(self):
        matrix = [[self.covariance["matrix"][i][j] if i == j else "0" for j in range(3)] for i in range(3)]
        with self.assertRaisesRegex(audit.FeasibilityError, "declared component"):
            audit.validate_covariance(matrix, self.inputs, audit.correlation_inventory())

    def test_negative_nonpsd_and_malformed_matrices_fail(self):
        for matrix in ([['-1','0','0'],['0','1','0'],['0','0','1']],
                       [['1','2','0'],['2','1','0'],['0','0','1']],
                       [['1','0','0'],['0','1','2'],['0','2','1']],
                       [['1','0.9','0.9'],['0.9','1','-0.9'],['0.9','-0.9','1']],
                       [['1','0'],['0','1']]):
            with self.subTest(matrix=matrix), self.assertRaises(audit.FeasibilityError):
                audit.matrix_diagnostics(matrix)

    def test_exact_singular_psd_diagnostic_without_pseudoinverse(self):
        diagnostics = audit.matrix_diagnostics([["1"]*3 for _ in range(3)])
        self.assertTrue(diagnostics["positive_semidefinite"])
        self.assertFalse(diagnostics["invertible"])
        self.assertFalse(diagnostics["inverse_or_regularization_used"])

    def test_covariance_component_trace_or_target_injection_fails(self):
        for mode in ("contribution", "target", "weights"):
            covariance = deepcopy(self.covariance)
            if mode == "contribution":
                covariance["component_terms"][0]["absolute_standard_contributions"][0] = "1"
            elif mode == "target":
                covariance["component_terms"][0]["published_combined_G"] = "6.674484e-11"
            else:
                covariance["weights"] = ["1", "0", "0"]
            with self.subTest(mode=mode), self.assertRaises(audit.FeasibilityError):
                audit.combine_by_source_rule(self.inputs, covariance)

    def test_missing_combination_rule_produces_no_go_with_covariance_retained(self):
        evidence = audit.source_evidence()
        del evidence["combination_rule"]
        result = audit.audit(self.inputs, evidence)
        self.assertEqual(result["decision"], "NO-GO")
        self.assertIn("MISSING_COMBINATION_RULE", result["reason_codes"])
        self.assertIsNotNone(result["covariance"])
        self.assertIsNone(result["reconstructed_combined_result"])

    def test_ambiguous_rule_or_normalization_produces_no_go(self):
        for key in ("combination_rule", "normalization_or_weighting"):
            evidence = audit.source_evidence()
            evidence[key]["status"] = "ambiguous"
            result = audit.audit(self.inputs, evidence)
            self.assertEqual(result["decision"], "NO-GO")
            self.assertIn("AMBIGUOUS_COMBINATION_RULE", result["reason_codes"])
            self.assertIsNone(result["reconstructed_combined_result"])

    def test_each_missing_indispensable_claim_blocks_go(self):
        for key in audit.REQUIRED_CLAIMS:
            evidence = audit.source_evidence()
            del evidence[key]
            with self.subTest(key=key):
                result = audit.audit(self.inputs, evidence)
                self.assertEqual(result["decision"], "NO-GO")
                self.assertIsNone(result["reconstructed_combined_result"])

    def test_unverified_source_blocks_covariance_and_combination(self):
        evidence = audit.source_evidence()
        evidence["cross_run_correlations"]["status"] = "unverified"
        result = audit.audit(self.inputs, evidence)
        self.assertEqual(result["reason_codes"], ["SOURCE_UNVERIFIED"])
        self.assertIsNone(result["covariance"])
        self.assertIsNone(result["reconstructed_combined_result"])

    def test_weight_tuning_or_guessed_formula_cannot_be_accepted_as_source_evidence(self):
        evidence = audit.source_evidence()
        evidence["normalization_or_weighting"]["interpretation"] = "Tune weights to published combined G"
        with self.assertRaisesRegex(audit.FeasibilityError, "weight tuning"):
            audit.audit(self.inputs, evidence)
        for rule in ("GLS", "statistical_only_inverse_variance", "pseudoinverse", "target_fit"):
            with self.subTest(rule=rule), self.assertRaises(audit.FeasibilityError):
                audit.combine_by_source_rule(self.inputs, self.covariance, rule_id=rule)

    def test_arithmetic_is_independent_of_ambient_decimal_context(self):
        expected = audit.serialize_artifact(audit.audit(self.inputs))
        with localcontext() as context:
            context.prec = 6
            context.rounding = ROUND_DOWN
            actual = audit.serialize_artifact(audit.audit(self.inputs))
        self.assertEqual(actual, expected)

    def test_no_model_replication_or_lean_promotion(self):
        result = audit.build_artifact()
        self.assertFalse(result["authorization_boundary"]["combined_measurement_model_emitted"])
        self.assertFalse(result["authorization_boundary"]["combined_measurement_model_authorized"])
        self.assertNotIn("models", result)
        self.assertIn("No Lean certification of the apparatus or combination procedure.", result["nonclaims"])
        for model in self.records[audit.MODELS_NAME]["models"]:
            self.assertEqual(model["assessments"]["replication_status"], "incomplete")
        tree = ast.parse(Path(audit.__file__).read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any("physical_bridge" in str(name) for name in imports))
        self.assertFalse(any(isinstance(node, ast.Constant) and isinstance(node.value, float) for node in ast.walk(tree)))

    def test_undeclared_file_and_duplicate_json_key_fail(self):
        with self.assertRaisesRegex(audit.FeasibilityError, "undeclared"):
            audit.load_frozen_records(input_paths=["Experiments/target.json"])
        with self.assertRaisesRegex(audit.FeasibilityError, "duplicate JSON"):
            audit._json(b'{"runs": [], "runs": []}')

    def test_generated_bytes_and_cli_freshness_guard(self):
        expected = audit.serialize_artifact(audit.build_artifact()).encode()
        self.assertEqual((audit.ROOT / audit.DEFAULT_OUTPUT).read_bytes(), expected)
        self.assertEqual(audit.main(["--check"]), 0)
        with patch.object(Path, "read_bytes", autospec=True) as read:
            original = expected + b" "
            actual_read = self._actual_read_bytes
            read.side_effect = lambda path: original if path == audit.ROOT/audit.DEFAULT_OUTPUT else actual_read(path)
            self.assertEqual(audit.main(["--check"]), 1)

    _actual_read_bytes = staticmethod(Path.read_bytes)


class PreregistrationHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        subprocess.run(["git", "clone", "--quiet", "--shared", str(audit.ROOT), str(self.root)], check=True)
        self.git("checkout", "--quiet", "--detach", audit.PREREGISTRATION_COMMIT)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", *args],
                              check=True, capture_output=True).stdout

    def test_first_commit_freeze_and_descendant_verified(self):
        self.assertEqual(audit.verify_preregistration(self.root)["baseline_main_sha"], audit.BASELINE)
        self.git("commit", "--quiet", "--allow-empty", "-m", "descendant")
        audit.verify_preregistration(self.root)

    def test_original_local_freeze_object_matches_its_git_identity(self):
        actual = subprocess.run(
            ["git", "hash-object", "-t", "commit", "--stdin"],
            input=audit.LOCAL_FREEZE_OBJECT.encode(), capture_output=True, check=True,
        ).stdout.decode().strip()
        self.assertEqual(actual, audit.LOCAL_FREEZE_COMMIT)
        with patch.object(audit, "LOCAL_FREEZE_OBJECT", audit.LOCAL_FREEZE_OBJECT + " "):
            with self.assertRaisesRegex(audit.FeasibilityError, "local freeze object"):
                audit.verify_preregistration(self.root)

    def test_current_preregistration_bytes_changed_fails(self):
        path = self.root / audit.PREREGISTRATION_PATH
        path.write_bytes(path.read_bytes()+b" ")
        with self.assertRaisesRegex(audit.FeasibilityError, "bytes changed"):
            audit.verify_preregistration(self.root)

    def test_modify_then_restore_preregistration_history_fails(self):
        path = self.root / audit.PREREGISTRATION_PATH
        original = path.read_bytes()
        path.write_bytes(original+b" ")
        self.git("add", str(audit.PREREGISTRATION_PATH))
        self.git("commit", "--quiet", "-m", "tamper")
        path.write_bytes(original)
        self.git("add", str(audit.PREREGISTRATION_PATH))
        self.git("commit", "--quiet", "-m", "restore")
        with self.assertRaisesRegex(audit.FeasibilityError, "intervening history"):
            audit.verify_preregistration(self.root)

    def test_head_without_preregistration_ancestry_fails(self):
        self.git("checkout", "--quiet", "--detach", audit.BASELINE)
        self.git("checkout", audit.PREREGISTRATION_COMMIT, "--", str(audit.PREREGISTRATION_PATH))
        with self.assertRaisesRegex(audit.FeasibilityError, "ancestry"):
            audit.verify_preregistration(self.root)

    def test_changed_or_missing_pinned_input_fails(self):
        path = self.root / audit.DIRECTORY / audit.GRAPH_NAME
        path.write_bytes(path.read_bytes()+b" ")
        with self.assertRaisesRegex(audit.FeasibilityError, "frozen input/history"):
            audit.load_frozen_records(self.root)
        path.unlink()
        with self.assertRaises(OSError):
            audit.load_frozen_records(self.root)

    def test_frozen_lean_and_mutation_history_are_preserved(self):
        for path in ("FormalPhysics/Estimator.lean", "Experiments/GMeasurements/hust_2018_aaf_depth_2b_mutation_results_v3.json"):
            target = self.root / path
            original = target.read_bytes()
            target.write_bytes(original+b" ")
            with self.subTest(path=path), self.assertRaisesRegex(audit.FeasibilityError, "frozen input/history"):
                audit.load_frozen_records(self.root)
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
