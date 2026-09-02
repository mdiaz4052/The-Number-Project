from __future__ import annotations

import unittest

from Discovery.pysr_leakage_audit import audit_expression
from Discovery.pysr_leakage_probe import (
    DIMENSIONALLY_INVALID,
    NO_REGISTERED_TARGET_PATH,
    NORMALIZED_MONOMIAL,
    TARGET_EXPOSED_CANDIDATE,
)


class PySRLeakageAuditTests(unittest.TestCase):
    def test_constant_only_candidate_has_explicit_preregistered_semantics(self):
        audit = audit_expression("C_hidden_leak", "1.2345")
        self.assertEqual(audit["candidate_origin"], TARGET_EXPOSED_CANDIDATE)
        self.assertFalse(audit["promotion_eligible"])
        self.assertEqual(audit["representation_status"], NORMALIZED_MONOMIAL)
        self.assertEqual(audit["dimensional_status"], DIMENSIONALLY_INVALID)
        self.assertEqual(audit["registered_target_dependency"], NO_REGISTERED_TARGET_PATH)
        self.assertFalse(audit["known_generation_target_leakage"])
        self.assertFalse(audit["hidden_target_leakage_blind_spot"])
        self.assertEqual(audit["referenced_predictors"], [])
        self.assertEqual(audit["normalized_exponents"], [])

    def test_nonconstant_audits_are_unchanged_from_primary_probe_contract(self):
        hidden = audit_expression("C_hidden_leak", "k_hidden / s_hidden")
        self.assertTrue(hidden["known_generation_target_leakage"])
        self.assertTrue(hidden["hidden_target_leakage_blind_spot"])
        self.assertEqual(hidden["registered_target_dependency"], NO_REGISTERED_TARGET_PATH)


if __name__ == "__main__":
    unittest.main()
