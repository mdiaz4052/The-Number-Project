from __future__ import annotations

import unittest

import Discovery.pysr_leakage_audit_v3 as audit_v3
import Discovery.pysr_leakage_check_v2 as historical_v2
import Discovery.pysr_leakage_hardening as hardening
import Discovery.pysr_leakage_probe as probe


class PySRLeakageFinalCleanupTests(unittest.TestCase):
    def test_exact_cancellation_uses_normalized_structural_ancestry(self) -> None:
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

        cancelled = audit_v3.audit_expression(
            "C_hidden_leak", "k_hidden / k_hidden"
        )
        self.assertEqual(["k_hidden"], cancelled["referenced_predictors"])

    def test_partial_cancellation_preserves_surviving_hidden_factor(self) -> None:
        audit = audit_v3.audit_expression(
            "C_hidden_leak", "(k_hidden * s_hidden) / s_hidden"
        )
        self.assertEqual(
            [{"factor": "k_hidden", "exponent": "1"}],
            audit["normalized_exponents"],
        )
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_DETECTED,
            audit["generation_ancestry_assessment"],
        )
        self.assertTrue(audit["known_generation_target_leakage"])
        self.assertTrue(audit["hidden_target_leakage_blind_spot"])

    def test_single_hidden_factor_still_has_detected_ancestry(self) -> None:
        audit = audit_v3.audit_expression("C_hidden_leak", "k_hidden")
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_DETECTED,
            audit["generation_ancestry_assessment"],
        )
        self.assertTrue(audit["known_generation_target_leakage"])
        self.assertTrue(audit["hidden_target_leakage_blind_spot"])

    def test_overflowing_numeric_literals_are_controlled(self) -> None:
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

    def test_hostile_syntax_remains_a_controlled_v3_failure(self) -> None:
        audit = audit_v3.audit_expression("C_hidden_leak", "k_hidden(1)")
        self.assertEqual(probe.PARSE_FAILURE, audit["representation_status"])
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_UNRESOLVED,
            audit["generation_ancestry_assessment"],
        )

    def test_existing_hardening_guard_pins_final_cleanup_semantics(self) -> None:
        summary = hardening.validate_final_cleanup_semantics()
        self.assertEqual(4, summary["normalized_cancellation_controls"])
        self.assertEqual(2, summary["overflow_controls"])

    def test_historical_v2_result_remains_current(self) -> None:
        result = historical_v2.check_committed_artifacts()
        self.assertEqual("BOUNDARY_CONFIRMED", result["primary_endpoint"]["outcome"])


if __name__ == "__main__":
    unittest.main()
