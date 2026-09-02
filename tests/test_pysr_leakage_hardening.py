from __future__ import annotations

import copy
import json
import unittest

import Discovery.pysr_leakage_audit_v3 as audit_v3
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

    def test_nonconstant_hidden_leak_retains_detected_ancestry(self) -> None:
        audit = audit_v3.audit_expression("C_hidden_leak", "k_hidden / s_hidden")
        self.assertEqual(
            audit_v3.GENERATION_ANCESTRY_DETECTED,
            audit["generation_ancestry_assessment"],
        )
        self.assertTrue(audit["known_generation_target_leakage"])
        self.assertTrue(audit["hidden_target_leakage_blind_spot"])

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


if __name__ == "__main__":
    unittest.main()
