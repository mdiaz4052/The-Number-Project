from __future__ import annotations

import copy
import json
import unittest

import Discovery.pysr_leakage_audit_v3 as audit_v3
import Discovery.pysr_leakage_check_v2 as historical_v2
import Discovery.pysr_leakage_hardening as hardening
import Discovery.pysr_leakage_probe as probe


class PySRLeakageHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.preregistration = probe.load_json(probe.PREREGISTRATION_PATH)
        self.external = json.loads(probe.EXTERNAL_PATH.read_text(encoding="utf-8"))

    def test_committed_external_search_matches_preregistration_exactly(self) -> None:
        summary = hardening.validate_search_contract(
            self.preregistration,
            self.external,
        )
        self.assertTrue(summary["search_configuration_match"])
        self.assertEqual([0, 1, 2], summary["observed_seeds"])
        self.assertEqual(9, summary["observed_run_count"])
        self.assertTrue(summary["external_source_pin_match"])

    def test_search_configuration_mismatch_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.external)
        mutated["search_configuration"]["niterations"] += 1
        with self.assertRaisesRegex(
            hardening.PySRHardeningError,
            "search_configuration does not match preregistration",
        ):
            hardening.validate_search_contract(self.preregistration, mutated)

    def test_seed_coverage_mismatch_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.external)
        mutated["runs"][0]["seed"] = 99
        with self.assertRaisesRegex(
            hardening.PySRHardeningError,
            "channel/seed coverage does not match preregistration",
        ):
            hardening.validate_search_contract(self.preregistration, mutated)

    def test_external_source_pin_mismatch_fails_closed(self) -> None:
        mutated = copy.deepcopy(self.external)
        mutated["external_source"]["pysr_commit"] = "0" * 40
        with self.assertRaisesRegex(
            hardening.PySRHardeningError,
            "source pin does not match preregistration",
        ):
            hardening.validate_search_contract(self.preregistration, mutated)

    def test_constant_only_target_exposed_candidate_is_structurally_not_applicable(self) -> None:
        audit = audit_v3.audit_expression("C_hidden_leak", "1.25")
        self.assertEqual(probe.TARGET_EXPOSED_CANDIDATE, audit["candidate_origin"])
        self.assertFalse(audit["promotion_eligible"])
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_NOT_APPLICABLE,
            audit["generation_ancestry_assessment"],
        )
        self.assertIsNone(audit["known_generation_target_leakage"])
        self.assertIsNone(audit["hidden_target_leakage_blind_spot"])
        self.assertEqual([], audit["referenced_predictors"])

    def test_exactly_cancelled_predictors_use_normalized_structural_ancestry(self) -> None:
        expressions = (
            "17.64",
            "k_hidden / k_hidden",
            "s_hidden / s_hidden",
            "(k_hidden * s_hidden) / (k_hidden * s_hidden)",
        )
        for expression in expressions:
            with self.subTest(expression=expression):
                audit = audit_v3.audit_expression("C_hidden_leak", expression)
                self.assertEqual(probe.NORMALIZED_MONOMIAL, audit["representation_status"])
                self.assertEqual([], audit["normalized_exponents"])
                self.assertEqual(
                    audit_v3.GENERATION_ANCESTRY_NOT_APPLICABLE,
                    audit["generation_ancestry_assessment"],
                )
                self.assertIsNone(audit["known_generation_target_leakage"])
                self.assertIsNone(audit["hidden_target_leakage_blind_spot"])
                self.assertEqual(probe.TARGET_EXPOSED_CANDIDATE, audit["candidate_origin"])
                self.assertFalse(audit["promotion_eligible"])

    def test_raw_predictor_names_remain_diagnostic_after_exact_cancellation(self) -> None:
        audit = audit_v3.audit_expression("C_hidden_leak", "k_hidden / k_hidden")
        self.assertEqual(["k_hidden"], audit["referenced_predictors"])
        self.assertEqual([], audit["normalized_exponents"])
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_NOT_APPLICABLE,
            audit["generation_ancestry_assessment"],
        )

    def test_nonconstant_hidden_leak_retains_detected_ancestry(self) -> None:
        for expression in ("k_hidden", "k_hidden / s_hidden"):
            with self.subTest(expression=expression):
                audit = audit_v3.audit_expression("C_hidden_leak", expression)
                self.assertEqual(
                    audit_v3.GENERATION_ANCESTRY_DETECTED,
                    audit["generation_ancestry_assessment"],
                )
                self.assertTrue(audit["known_generation_target_leakage"])
                self.assertTrue(audit["hidden_target_leakage_blind_spot"])

    def test_overflowing_numeric_literals_are_controlled_parse_failures(self) -> None:
        for expression in ("1e400", "-1e400"):
            with self.subTest(expression=expression):
                audit = audit_v3.audit_expression("C_hidden_leak", expression)
                self.assertEqual(probe.PARSE_FAILURE, audit["representation_status"])
                self.assertEqual(probe.DIMENSION_UNRESOLVED, audit["dimensional_status"])
                self.assertEqual(
                    probe.NOT_APPLICABLE_REPRESENTATION_GAP,
                    audit["registered_target_dependency"],
                )
                self.assertEqual(
                    audit_v3.GENERATION_ANCESTRY_UNRESOLVED,
                    audit["generation_ancestry_assessment"],
                )
                self.assertIsNone(audit["known_generation_target_leakage"])
                self.assertIsNone(audit["hidden_target_leakage_blind_spot"])
                self.assertIn("unrepresentable", audit["parse_diagnostic"])

    def test_hostile_syntax_remains_controlled_under_v3(self) -> None:
        audit = audit_v3.audit_expression("C_hidden_leak", "k_hidden(1)")
        self.assertEqual(probe.PARSE_FAILURE, audit["representation_status"])
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_UNRESOLVED,
            audit["generation_ancestry_assessment"],
        )

    def test_parser_rejects_call_syntax_even_when_function_name_is_allowed(self) -> None:
        with self.assertRaisesRegex(probe.LeakageProbeError, "unsupported expression syntax"):
            probe.parse_expression("k_hidden(1)", probe.CHANNEL_PREDICTORS["C_hidden_leak"])

    def test_frozen_evidence_contains_explicit_constant_semantics_controls(self) -> None:
        summary = hardening.validate_future_constant_semantics(self.external)
        self.assertEqual(6, summary["constant_only_candidates"])
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_NOT_APPLICABLE,
            summary["future_generation_ancestry_semantics"],
        )

    def test_final_cleanup_semantics_are_pinned_by_existing_hardening_guard(self) -> None:
        summary = hardening.validate_final_cleanup_semantics()
        self.assertEqual(4, summary["normalized_cancellation_controls"])
        self.assertEqual(2, summary["overflow_controls"])

    def test_historical_v2_result_still_verifies_under_frozen_semantics(self) -> None:
        result = historical_v2.check_committed_artifacts()
        self.assertEqual("BOUNDARY_CONFIRMED", result["primary_endpoint"]["outcome"])


if __name__ == "__main__":
    unittest.main()
