from __future__ import annotations

import json
import unittest

from Discovery import bipm_2014_correlated_estimator as b
from Discovery import bipm_2014_correlated_estimator_mutations as mutations


class BIPMCorrelatedEstimatorMutationTests(unittest.TestCase):
    def test_frozen_inventory_and_definitions(self):
        protocol = b.verify_preregistration()
        sources = mutations.source_map(b.ROOT)
        mutations.validate_definitions(sources, protocol)
        self.assertEqual(len(mutations.production_cases()), len(protocol["mutation_requirements"]))
        self.assertEqual(len(mutations.calibration_cases()), 2)
        self.assertEqual(len({case["id"] for case in mutations.CASES}), len(mutations.CASES))

    def test_committed_mutation_artifact(self):
        artifact = json.loads((b.ROOT / mutations.DEFAULT_OUTPUT).read_text())
        sources = mutations.source_map(b.ROOT)
        self.assertEqual(artifact["definitions_sha256"], mutations.definitions_hash())
        self.assertEqual(artifact["source_snapshot"], mutations.source_snapshot(b.ROOT))
        mutations.validate_records(artifact["records"], sources)
        self.assertTrue(artifact["calibration_valid"])
        self.assertEqual(artifact["family_status"], "valid")
        production = [r for r in artifact["records"] if r["category"] == "production"]
        self.assertEqual(len(production), len(mutations.production_cases()))
        self.assertTrue(all(record["outcome"] == "KILLED" for record in production))


if __name__ == "__main__":
    unittest.main()
