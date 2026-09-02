from __future__ import annotations

import unittest

from Discovery.pysr_leakage_probe import audit_expression


class PySRLeakageMutationGuardTests(unittest.TestCase):
    def test_hidden_generation_path_remains_independent_of_registered_graph(self):
        audit = audit_expression("C_hidden_leak", "k_hidden / s_hidden")
        self.assertEqual(audit["registered_target_dependency"], "no_registered_target_path")
        self.assertTrue(audit["known_generation_target_leakage"])
        self.assertTrue(audit["hidden_target_leakage_blind_spot"])


if __name__ == "__main__":
    unittest.main()
