from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import unittest

from Discovery import hust_2018_aaf_source_audit as audit


class Hust2018AafSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = audit.load_required_inputs()
        cls.source_capture = audit.load_source_capture()

    def test_preregistration_is_byte_pinned(self) -> None:
        record = audit.verify_preregistration()
        self.assertEqual(record["sha256"], audit.PREREGISTRATION_SHA256)
        self.assertEqual(
            record["path"],
            "Experiments/GMeasurements/hust_2018_aaf_preregistration_v1.md",
        )

    def test_post_audit_clarification_is_byte_pinned(self) -> None:
        record = audit.verify_post_audit_clarification()
        self.assertEqual(
            record["sha256"], audit.POST_AUDIT_CLARIFICATION_SHA256
        )

    def test_semantic_source_review_is_byte_pinned_and_complete(self) -> None:
        record = audit.verify_semantic_review()
        self.assertEqual(record["sha256"], audit.SEMANTIC_REVIEW_SHA256)
        self.assertEqual(
            tuple(record["claim_ids"]),
            audit.EXPECTED_SEMANTIC_REVIEW_CLAIMS,
        )

    def test_reviewed_source_capture_is_fail_closed(self) -> None:
        summary = audit.validate_source_capture(self.source_capture)
        self.assertEqual(
            summary["required_summary_source"],
            "supplementary_information",
        )
        self.assertIn(
            "supplementary_information",
            summary["retrieved_binary_sources"],
        )
        self.assertEqual(
            set(summary["failed_source_data_attempts"]),
            set(audit.EXPECTED_FAILED_SOURCE_DATA),
        )

    def test_source_hash_mutation_is_rejected(self) -> None:
        record = deepcopy(self.source_capture)
        for resource in record["resources"]:
            if resource["source_id"] == "supplementary_information":
                resource["sha256"] = "0" * 64
                break
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_source_capture(record)

    def test_missing_required_source_is_rejected(self) -> None:
        record = deepcopy(self.source_capture)
        record["resources"] = [
            resource
            for resource in record["resources"]
            if resource["source_id"] != "supplementary_information"
        ]
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_source_capture(record)

    def test_html_fallback_cannot_be_promoted_to_retrieved_source(self) -> None:
        record = deepcopy(self.source_capture)
        for resource in record["resources"]:
            if resource["source_id"] == "source_data_fig_2":
                resource["retrieval_status"] = "retrieved_binary"
                break
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_source_capture(record)

    def test_required_input_graph_is_valid(self) -> None:
        audit.validate_required_inputs_graph(self.graph)

    def test_machine_readable_uncertainties_match_printed_notation(self) -> None:
        nodes, _ = audit._flatten_nodes(self.graph)
        expected = {
            "AAF-I:p_sum": Decimal("0.074"),
            "AAF-I:alpha_corrected": Decimal("0.0016"),
            "AAF-I:magnetic_damper_ppm": Decimal("1.95"),
            "AAF-II:p_sum": Decimal("0.075"),
            "AAF-II:alpha_corrected": Decimal("0.0012"),
            "AAF-II:magnetic_damper_ppm": Decimal("1.95"),
            "AAF-III:p_sum": Decimal("0.074"),
            "AAF-III:alpha_corrected": Decimal("0.0006"),
            "AAF-III:magnetic_damper_ppm": Decimal("0.08"),
        }
        for node_id, uncertainty in expected.items():
            node = nodes[node_id]
            value, parsed_uncertainty = audit._parse_printed_measurement(
                node["printed_value"]
            )
            self.assertEqual(value, Decimal(node["value"]))
            self.assertEqual(parsed_uncertainty, uncertainty)
            self.assertEqual(
                parsed_uncertainty,
                Decimal(node["standard_uncertainty"]),
            )

    def test_missing_result_driving_locator_is_rejected(self) -> None:
        graph = deepcopy(self.graph)
        graph["experiments"][0]["nodes"][0]["locator"] = ""
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_required_inputs_graph(graph)

    def test_cross_experiment_parent_is_rejected(self) -> None:
        graph = deepcopy(self.graph)
        for node in graph["experiments"][0]["nodes"]:
            if node["node_id"] == "AAF-I:G_reconstructed":
                node["parents"].append("AAF-II:p_sum")
                break
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_required_inputs_graph(graph)

    def test_numeric_scope_mix_is_rejected_by_transcription_guard(self) -> None:
        graph = deepcopy(self.graph)
        aaf_i = graph["experiments"][0]["nodes"][0]
        aaf_i["value"] = "6926.334"
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_required_inputs_graph(graph)

    def test_source_scope_token_mix_is_rejected(self) -> None:
        graph = deepcopy(self.graph)
        graph["experiments"][0]["nodes"][0]["source_scope_tokens"] = [
            "AAF-II"
        ]
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_required_inputs_graph(graph)

    def test_missing_required_estimator_node_is_rejected(self) -> None:
        graph = deepcopy(self.graph)
        graph["experiments"][0]["nodes"] = [
            node
            for node in graph["experiments"][0]["nodes"]
            if node["node_id"] != "AAF-I:magnetic_damper_ppm"
        ]
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_required_inputs_graph(graph)

    def test_magnetic_damper_sign_and_operator_are_pinned(self) -> None:
        graph = deepcopy(self.graph)
        for experiment in graph["experiments"]:
            for node in experiment["nodes"]:
                if node["node_id"].endswith(":magnetic_damper_ppm"):
                    node["correction_operator"] = "multiply_by_1_minus_delta"
        with self.assertRaises(audit.SourceAuditError):
            audit.validate_required_inputs_graph(graph)

    def test_public_summary_inputs_authorize_go_depth_2a(self) -> None:
        result = audit.classify_graph(self.graph)
        self.assertEqual(result["decision"], "GO")
        self.assertEqual(
            result["maximum_assessed_replication_depth"], "2a"
        )
        self.assertNotIn(
            "maximum_supported_replication_depth",
            result,
        )
        self.assertEqual(result["depth_2a_authorized_count"], 3)
        self.assertEqual(result["depth_2a_candidate_count"], 3)
        self.assertEqual(
            result["decision_summary"],
            "GO / 2a (3 of 3 AAF determinations authorized)",
        )
        self.assertEqual(
            result["depth_2a_authorized_experiments"],
            ["AAF-I", "AAF-II", "AAF-III"],
        )
        self.assertFalse(
            result["combined_aaf_reconstruction_authorized"]
        )
        self.assertEqual(
            result["depth_2b_authorized_experiments"], []
        )

    def test_one_contaminated_experiment_does_not_overstate_global_downgrade(self) -> None:
        graph = deepcopy(self.graph)
        for node in graph["experiments"][0]["nodes"]:
            if node["node_id"] == "AAF-I:p_sum":
                node["evidence_type"] = audit.TARGET_DERIVED
                break
        result = audit.classify_graph(graph)
        self.assertEqual(result["decision"], "GO")
        self.assertEqual(
            result["maximum_assessed_replication_depth"], "2a"
        )
        self.assertEqual(result["depth_2a_authorized_count"], 2)
        self.assertEqual(
            result["depth_2a_authorized_experiments"],
            ["AAF-II", "AAF-III"],
        )

    def test_all_contaminated_experiments_downgrade_to_partial(self) -> None:
        graph = deepcopy(self.graph)
        for experiment in graph["experiments"]:
            for node in experiment["nodes"]:
                if node["node_id"].endswith(":p_sum"):
                    node["evidence_type"] = audit.TARGET_DERIVED
                    break
        result = audit.classify_graph(graph)
        self.assertEqual(result["decision"], "PARTIAL")
        self.assertEqual(
            result["maximum_assessed_replication_depth"], "1"
        )
        self.assertEqual(result["depth_2a_authorized_count"], 0)

    def test_exact_decimal_reconstructions_use_only_upstream_inputs(self) -> None:
        expected = {
            "AAF-I": Decimal(
                "6.6745328035953125108282108677121809575949937283002E-11"
            ),
            "AAF-II": Decimal(
                "6.6743753740743660354813960747489220127126413482226E-11"
            ),
            "AAF-III": Decimal(
                "6.6745350870563487749434592065303623880463414334833E-11"
            ),
        }
        for experiment_id, value in expected.items():
            self.assertEqual(
                audit.reconstruct_experiment(experiment_id, self.graph),
                value,
            )

    def test_published_g_is_terminal_comparison_not_graph_input(self) -> None:
        nodes, _ = audit._flatten_nodes(self.graph)
        for node in nodes.values():
            for parent in node["parents"]:
                self.assertNotIn("published", parent.lower())
        for experiment in self.graph["experiments"]:
            self.assertIn("published_comparison", experiment)
            self.assertNotIn(
                experiment["published_comparison"]["value"],
                [str(node.get("value")) for node in experiment["nodes"]],
            )

    def test_transitive_target_derived_parent_of_parent_refuses_go(self) -> None:
        graph = deepcopy(self.graph)
        for experiment in graph["experiments"]:
            scope = experiment["experiment_id"]
            leak_id = f"{scope}:planted_target_derived_calibration"
            experiment["nodes"].append(
                {
                    "node_id": leak_id,
                    "evidence_type": audit.TARGET_DERIVED,
                    "locator": "planted test mutant",
                    "source_id": "test_mutant",
                    "source_scope_tokens": [scope],
                    "parents": [],
                    "result_driving": True,
                }
            )
            for node in experiment["nodes"]:
                if node["node_id"] == f"{scope}:p_sum":
                    node["parents"] = [leak_id]
                    break
        result = audit.classify_graph(graph)
        self.assertEqual(result["decision"], "PARTIAL")
        self.assertEqual(
            result["maximum_assessed_replication_depth"], "1"
        )
        self.assertEqual(
            result["depth_2a_authorized_experiments"], []
        )

    def test_request_only_result_driving_inputs_refuse_go(self) -> None:
        graph = deepcopy(self.graph)
        for experiment in graph["experiments"]:
            scope = experiment["experiment_id"]
            for node in experiment["nodes"]:
                if node["node_id"] == f"{scope}:alpha_corrected":
                    node["evidence_type"] = audit.REQUEST_ONLY
        result = audit.classify_graph(graph)
        self.assertEqual(result["decision"], "PARTIAL")
        self.assertEqual(
            result["maximum_assessed_replication_depth"], "1"
        )

    def test_depth_2b_is_blocked_by_incomplete_uncertainty_models(self) -> None:
        result = audit.classify_graph(self.graph)
        self.assertEqual(
            set(result["depth_2b_blockers"]),
            {"AAF-I", "AAF-II", "AAF-III"},
        )
        for scope, blockers in result["depth_2b_blockers"].items():
            self.assertEqual(
                blockers,
                [f"{scope}:complete_uncertainty_model"],
            )

    def test_manifest_builder_matches_prose_decision(self) -> None:
        manifest = audit.build_audit_manifest()
        self.assertEqual(manifest["decision"], "GO")
        self.assertEqual(
            manifest["maximum_assessed_replication_depth"], "2a"
        )
        self.assertEqual(
            manifest["depth_2a_authorized_count"], 3
        )
        self.assertEqual(
            manifest["depths_above_assessed"]["status"],
            "not_assessed",
        )
        self.assertEqual(
            set(
                manifest["depths_above_assessed"][
                    "unretrieved_source_ids"
                ]
            ),
            set(audit.EXPECTED_FAILED_SOURCE_DATA),
        )
        self.assertEqual(
            manifest["preregistration"]["sha256"],
            audit.PREREGISTRATION_SHA256,
        )

    def test_serialization_is_deterministic(self) -> None:
        first = audit.serialize_artifact(
            audit.build_audit_manifest()
        )
        second = audit.serialize_artifact(
            audit.build_audit_manifest()
        )
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        self.assertFalse(first.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
