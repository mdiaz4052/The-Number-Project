from __future__ import annotations

import unittest

from Discovery.pysr_leakage_probe import (
    CANONICAL_CONTROLS,
    CHANNELS,
    DIMENSIONALLY_INVALID,
    DIMENSIONALLY_VALID,
    EXPERIMENT_IDENTIFIER,
    NO_REGISTERED_TARGET_PATH,
    NORMALIZED_MONOMIAL,
    NOT_APPLICABLE_REPRESENTATION_GAP,
    REPRESENTATIONAL_GAP,
    SCHEMA_VERSION,
    SEEDS,
    TARGET_EXPOSED_CANDIDATE,
    TARGET_PATH_DETECTED,
    LeakageProbeError,
    audit_expression,
    build_datasets_record,
    build_result_record,
    canonical_control_audits,
    canonical_json_bytes,
    candidate_identifier,
    dataset_hashes,
    enforce_candidate_origin,
    sha256_bytes,
)


class PySRLeakageProbeTests(unittest.TestCase):
    def test_datasets_are_byte_deterministic_and_complete(self):
        first = canonical_json_bytes(build_datasets_record())
        second = canonical_json_bytes(build_datasets_record())
        self.assertEqual(first, second)
        record = build_datasets_record()
        self.assertEqual(record["rows_per_channel"], 128)
        self.assertEqual(set(record["channels"]), set(CHANNELS))
        self.assertTrue(all(len(record["channels"][name]) == 128 for name in CHANNELS))
        self.assertEqual(dataset_hashes(record), dataset_hashes(build_datasets_record()))

    def test_canonical_controls_pin_three_distinct_leakage_states(self):
        audits = canonical_control_audits()

        clean = audits["A_clean"]
        self.assertEqual(clean["dimensional_status"], DIMENSIONALLY_VALID)
        self.assertEqual(clean["registered_target_dependency"], NO_REGISTERED_TARGET_PATH)
        self.assertFalse(clean["known_generation_target_leakage"])
        self.assertFalse(clean["hidden_target_leakage_blind_spot"])

        registered = audits["B_registered_leak"]
        self.assertEqual(registered["dimensional_status"], DIMENSIONALLY_VALID)
        self.assertEqual(registered["registered_target_dependency"], TARGET_PATH_DETECTED)
        self.assertTrue(registered["known_generation_target_leakage"])
        self.assertFalse(registered["hidden_target_leakage_blind_spot"])

        hidden = audits["C_hidden_leak"]
        self.assertEqual(hidden["dimensional_status"], DIMENSIONALLY_VALID)
        self.assertEqual(hidden["registered_target_dependency"], NO_REGISTERED_TARGET_PATH)
        self.assertTrue(hidden["known_generation_target_leakage"])
        self.assertTrue(hidden["hidden_target_leakage_blind_spot"])

    def test_all_pysr_candidates_are_target_exposed_and_never_promotable(self):
        audit = audit_expression("A_clean", CANONICAL_CONTROLS["A_clean"])
        self.assertEqual(audit["candidate_origin"], TARGET_EXPOSED_CANDIDATE)
        self.assertFalse(audit["promotion_eligible"])
        with self.assertRaises(LeakageProbeError):
            enforce_candidate_origin(TARGET_EXPOSED_CANDIDATE, True)
        with self.assertRaises(LeakageProbeError):
            enforce_candidate_origin("conjecture", False)

    def test_safe_parser_rejects_code_execution_and_unknown_names(self):
        code = audit_expression("C_hidden_leak", "__import__('os').system('id')")
        self.assertEqual(code["representation_status"], "parse_failure")
        unknown = audit_expression("C_hidden_leak", "G")
        self.assertEqual(unknown["representation_status"], "parse_failure")

    def test_additive_expression_can_be_dimensionally_valid_but_not_monomial(self):
        audit = audit_expression("C_hidden_leak", "k_hidden + k_hidden")
        self.assertEqual(audit["representation_status"], REPRESENTATIONAL_GAP)
        self.assertEqual(audit["dimensional_status"], DIMENSIONALLY_VALID)
        self.assertEqual(
            audit["registered_target_dependency"],
            NOT_APPLICABLE_REPRESENTATION_GAP,
        )
        self.assertTrue(audit["known_generation_target_leakage"])

    def test_incompatible_addition_is_dimensionally_invalid(self):
        audit = audit_expression("C_hidden_leak", "k_hidden + s_hidden")
        self.assertEqual(audit["representation_status"], REPRESENTATIONAL_GAP)
        self.assertEqual(audit["dimensional_status"], DIMENSIONALLY_INVALID)

    def test_multiplicative_candidates_are_normalized_exactly(self):
        audit = audit_expression("B_registered_leak", "2 * hbar * c / m_P**2")
        self.assertEqual(audit["representation_status"], NORMALIZED_MONOMIAL)
        self.assertEqual(audit["normalized_coefficient"], "2")
        self.assertEqual(
            audit["normalized_exponents"],
            [
                {"factor": "c", "exponent": "1"},
                {"factor": "hbar", "exponent": "1"},
                {"factor": "m_P", "exponent": "-2"},
            ],
        )
        self.assertEqual(audit["registered_target_dependency"], TARGET_PATH_DETECTED)

    def test_candidate_identifier_depends_on_raw_identity_not_audit(self):
        a = candidate_identifier("A_clean", 0, 0, "u_clean / r_clean")
        b = candidate_identifier("A_clean", 0, 0, "u_clean / r_clean")
        c = candidate_identifier("A_clean", 1, 0, "u_clean / r_clean")
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_result_builder_audits_every_channel_seed_and_preserves_one_way_valve(self):
        datasets = build_datasets_record()
        runs = []
        for channel in CHANNELS:
            for seed in SEEDS:
                runs.append(
                    {
                        "channel": channel,
                        "seed": seed,
                        "candidates": [
                            {
                                "equation": CANONICAL_CONTROLS[channel],
                                "complexity": 3,
                                "loss": "0.0",
                                "score": "1.0",
                            }
                        ],
                    }
                )
        external = {
            "schema_version": SCHEMA_VERSION,
            "experiment_identifier": EXPERIMENT_IDENTIFIER,
            "dataset_sha256": sha256_bytes(canonical_json_bytes(datasets)),
            "external_source": {
                "pysr_commit": "65b887aeaf97f1c5ae84b0ceffb370551e57ce90"
            },
            "runs": runs,
        }
        result = build_result_record(
            external,
            datasets,
            external_sha256=sha256_bytes(canonical_json_bytes(external)),
            source_commit_sha="0" * 40,
        )
        self.assertTrue(result["primary_endpoint"]["confirmed"])
        self.assertEqual(result["primary_endpoint"]["outcome"], "BOUNDARY_CONFIRMED")
        self.assertEqual(result["candidate_counts"]["total_candidates"], 9)
        self.assertTrue(all(not row["promotion_eligible"] for row in result["candidates"]))
        self.assertEqual(
            sum(row["hidden_target_leakage_blind_spot"] for row in result["candidates"]),
            3,
        )


if __name__ == "__main__":
    unittest.main()
