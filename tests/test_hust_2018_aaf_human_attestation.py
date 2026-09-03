from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATTESTATION_PATH = ROOT / "Experiments" / "GMeasurements" / "hust_2018_aaf_independent_human_attestation_v1.json"
EXTERNAL_SOURCES_PATH = ROOT / "Experiments" / "GMeasurements" / "hust_2018_aaf_external_sources_v1.json"
REQUIRED_INPUTS_PATH = ROOT / "Experiments" / "GMeasurements" / "hust_2018_aaf_required_inputs_v1.json"
SEMANTIC_REVIEW_PATH = ROOT / "Experiments" / "GMeasurements" / "hust_2018_aaf_semantic_source_review_v1.json"
EXPECTED_ATTESTATION_SHA256 = "560fbef2b08b46a29086e26becbe47701b84ba9e3aa6ecc3ffdda502fbc891b1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_by_id(attestation: dict, claim_id: str) -> dict:
    matches = [item for item in attestation["checks"] if item["claim_id"] == claim_id]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one attestation check for {claim_id!r}")
    return matches[0]


def _semantic_check_by_id(semantic_review: dict, claim_id: str) -> dict:
    matches = [item for item in semantic_review["checks"] if item["claim_id"] == claim_id]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one semantic-review check for {claim_id!r}")
    return matches[0]


def _node_by_id(required_inputs: dict, node_id: str) -> dict:
    matches = [
        node
        for experiment in required_inputs["experiments"]
        for node in experiment["nodes"]
        if node["node_id"] == node_id
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one required-input node for {node_id!r}")
    return matches[0]


class HUST2018AAFHumanAttestationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.attestation = _load(ATTESTATION_PATH)
        self.external_sources = _load(EXTERNAL_SOURCES_PATH)
        self.required_inputs = _load(REQUIRED_INPUTS_PATH)
        self.semantic_review = _load(SEMANTIC_REVIEW_PATH)

    def test_attestation_bytes_are_pinned(self) -> None:
        digest = hashlib.sha256(ATTESTATION_PATH.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_ATTESTATION_SHA256)

    def test_attestation_records_prior_disclosure_and_no_blind_claim(self) -> None:
        self.assertEqual(
            self.attestation["attestation_scope"],
            "depth_2a_result_driving_primary_source_facts",
        )
        self.assertEqual(self.attestation["reviewer_role"], "project_owner_human_reader")
        independence = self.attestation["review_independence"]
        self.assertFalse(independence["blind_confirmation"])
        self.assertIn("project conversation", independence["prior_disclosure"])
        self.assertIn("Claude audit materials", independence["prior_disclosure"])
        self.assertTrue(independence["same_turn_repository_comparison_withheld_until_after_report"])
        self.assertIn("expected units", independence["unit_confirmation_phase"])
        self.assertIn("not a blind confirmation", self.attestation["boundary"])

        for claim_id in (
            "p_g_definition_excludes_G",
            "magnetic_damper_direction_and_magnitude",
            "table3_air_density_statement",
            "table3_result_driving_values",
        ):
            self.assertEqual(
                _check_by_id(self.attestation, claim_id)["status"],
                "confirmed_by_independent_human_reader_after_prior_disclosure",
            )
        for claim_id in ("table1_damper_unit", "table3_result_driving_units"):
            self.assertEqual(
                _check_by_id(self.attestation, claim_id)["status"],
                "confirmed_after_expected_unit_disclosed",
            )

    def test_attestation_is_explicitly_nonpromotional(self) -> None:
        boundary = self.attestation["boundary"]
        self.assertIn("not an independent experiment", boundary)
        self.assertIn("does not establish depth 2b", boundary)
        self.assertIn("does not authorize a combined AAF estimator", boundary)
        self.assertIn(
            "This attestation is not blind; prior project materials had already disclosed the checked values and semantic expectations.",
            self.attestation["nonclaims"],
        )
        self.assertIn(
            "No claim is made that the HUST experiment itself has been independently replicated.",
            self.attestation["nonclaims"],
        )

    def test_attestation_is_bound_to_captured_pdf_without_claiming_portable_hash_identity(self) -> None:
        resources = {
            resource["source_id"]: resource for resource in self.external_sources["resources"]
        }
        source = resources[self.attestation["source_id"]]
        self.assertEqual(source["retrieval_status"], "retrieved_binary")
        self.assertEqual(source["content_type"], "application/pdf")
        self.assertEqual(self.attestation["source_sha256"], source["sha256"])
        self.assertEqual(
            self.attestation["source_sha256"],
            "5b61d5c831be98c46e47fcc32f1ade0a680b4af6354d2bc34859d94b22279ffb",
        )
        hash_scope = self.attestation["source_hash_scope"]
        self.assertIn("GitHub-runner-captured PDF bytes", hash_scope)
        self.assertIn("different hash alone is not evidence of semantic disagreement", hash_scope)

    def test_semantic_boundary_and_damper_operator_match_frozen_source_graph(self) -> None:
        pg_check = _check_by_id(self.attestation, "p_g_definition_excludes_G")
        self.assertEqual(
            self.required_inputs["source_definition_check"]["target_dependency_status"],
            "no_G_in_registered_source_definition",
        )
        self.assertIn("does not contain G", pg_check["finding"])

        damper_check = _check_by_id(
            self.attestation, "magnetic_damper_direction_and_magnitude"
        )
        self.assertIn("(1 + (K/K_m)(I_m/I))", damper_check["finding"])
        self.assertIn("455.40(1.95)", damper_check["finding"])
        self.assertIn("25.74(8)", damper_check["finding"])
        for scope in ("AAF-I", "AAF-II", "AAF-III"):
            node = _node_by_id(self.required_inputs, f"{scope}:magnetic_damper_ppm")
            self.assertEqual(node["correction_operator"], "multiply_by_1_plus_delta")
            self.assertEqual(node["correction_direction"], "increase_G")
        self.assertEqual(
            _node_by_id(self.required_inputs, "AAF-I:magnetic_damper_ppm")["printed_value"],
            "455.40(1.95)",
        )
        self.assertEqual(
            _node_by_id(self.required_inputs, "AAF-II:magnetic_damper_ppm")["printed_value"],
            "455.40(1.95)",
        )
        self.assertEqual(
            _node_by_id(self.required_inputs, "AAF-III:magnetic_damper_ppm")["printed_value"],
            "25.74(8)",
        )
        unit_check = _check_by_id(self.attestation, "table1_damper_unit")
        self.assertIn("ppm", unit_check["finding"])
        self.assertTrue(
            all(
                _node_by_id(
                    self.required_inputs, f"{scope}:magnetic_damper_ppm"
                )["unit"]
                == "ppm"
                for scope in ("AAF-I", "AAF-II", "AAF-III")
            )
        )

    def test_table3_values_and_prompted_units_match_frozen_source_graph(self) -> None:
        values = _check_by_id(
            self.attestation, "table3_result_driving_values"
        )["finding"]
        units = _check_by_id(
            self.attestation, "table3_result_driving_units"
        )["finding"]
        for scope in ("AAF-I", "AAF-II", "AAF-III"):
            p_sum = _node_by_id(self.required_inputs, f"{scope}:p_sum")
            alpha = _node_by_id(self.required_inputs, f"{scope}:alpha_corrected")
            self.assertEqual(values[scope]["p_g_sum"], p_sum["printed_value"])
            self.assertEqual(values[scope]["alpha_t_2omega_d"], alpha["printed_value"])
            self.assertEqual(units["p_g_sum_unit"], p_sum["unit"])
            self.assertEqual(units["alpha_t_unit"], alpha["unit"])

        air_density = _check_by_id(
            self.attestation, "table3_air_density_statement"
        )["finding"]
        self.assertIn("corrected for the air density effect", air_density)
        for scope in ("AAF-I", "AAF-II", "AAF-III"):
            self.assertIn(
                "air-density corrected",
                _node_by_id(self.required_inputs, f"{scope}:alpha_corrected")["locator"],
            )

    def test_overlapping_semantic_review_claims_remain_consistent(self) -> None:
        self.assertEqual(
            self.attestation["source_sha256"],
            self.semantic_review["source_sha256"],
        )
        pg = _check_by_id(self.attestation, "p_g_definition_excludes_G")["finding"]
        pg_prior = _semantic_check_by_id(
            self.semantic_review, "p_g_definition_excludes_G"
        )["finding"]
        self.assertIn("does not contain G", pg)
        self.assertIn("G remains a separate", pg_prior)

        damper = _check_by_id(
            self.attestation, "magnetic_damper_direction_and_magnitude"
        )["finding"]
        damper_prior = _semantic_check_by_id(
            self.semantic_review, "magnetic_damper_direction"
        )["finding"]
        self.assertIn("(1 +", damper)
        self.assertIn("multiplicative 1-plus correction", damper_prior)
        for printed in ("455.40(1.95)", "25.74(8)"):
            self.assertIn(printed, damper)
            self.assertIn(printed, damper_prior)

        air = _check_by_id(
            self.attestation, "table3_air_density_statement"
        )["finding"]
        air_prior = _semantic_check_by_id(
            self.semantic_review, "table3_scope_and_air_density"
        )["finding"]
        self.assertIn("air density", air)
        self.assertIn("air density", air_prior)

    def test_attestation_does_not_promote_uncertainty_or_combined_estimator(self) -> None:
        self.assertIn(
            "No complete uncertainty or covariance budget was independently reconstructed.",
            self.attestation["nonclaims"],
        )
        self.assertIn(
            "No combined AAF estimator is authorized by this attestation.",
            self.attestation["nonclaims"],
        )
        self.assertIn(
            "No published G value or published G uncertainty was needed for this source attestation.",
            self.attestation["nonclaims"],
        )


if __name__ == "__main__":
    unittest.main()
