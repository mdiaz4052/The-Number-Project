from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from Discovery.hust_2018_aaf_depth_2b_authorization import (
    CLARIFICATION_PATH,
    EXPECTED_COMPONENTS,
    EXPECTED_RHO_APPROXIMATIONS,
    EXPECTED_RSS_PPM,
    EXPECTED_SUMS_OF_SQUARES,
    HISTORICAL_ARTIFACT_SHA256,
    HUSTDepth2BAuthorizationError,
    OFFICIAL_SOURCE_PATH,
    OFFICIAL_TABLE_SHA256,
    REQUIRED_INPUTS_PATH,
    SCOPES,
    build_authorization_artifact,
    calculate_scope_diagnostics,
    serialize_artifact,
    sha256_bytes,
    validate_clarification_record,
    validate_official_source_record,
    validate_required_inputs_graph,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class HUST2018AAFDepth2BAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _load(OFFICIAL_SOURCE_PATH)
        self.clarification = _load(CLARIFICATION_PATH)
        self.graph = _load(REQUIRED_INPUTS_PATH)

    def test_official_nature_source_precondition_is_exactly_pinned(self) -> None:
        validate_official_source_record(self.source)
        self.assertEqual(self.source["decision"], "SATISFIED")
        self.assertEqual(
            self.source["source"]["canonical_table_url"],
            "https://www.nature.com/articles/s41586-018-0431-5/tables/1",
        )
        self.assertEqual(self.source["capture"]["sha256"], OFFICIAL_TABLE_SHA256)
        self.assertEqual(self.source["capture"]["byte_length"], 10305)
        self.assertEqual(self.source["capture"]["response_content_type"], "text/html")
        self.assertEqual(
            self.source["capture"]["pdf_magic_validation"],
            "not_applicable_html",
        )
        self.assertIn("not the raw HTTP response", self.source["capture"]["delivery_caveat"])
        self.assertIn("may produce different bytes", self.source["capture"]["delivery_caveat"])

    def test_source_bypass_and_falsified_locator_fail_closed(self) -> None:
        for mutation in (
            ("decision", "NO_GO"),
            ("official_delivery", False),
            ("table_locator", "Table 2"),
            ("capture_hash", "0" * 64),
            ("publisher", "mirror.example"),
        ):
            with self.subTest(mutation=mutation[0]):
                changed = deepcopy(self.source)
                if mutation[0] == "decision":
                    changed["decision"] = mutation[1]
                elif mutation[0] == "official_delivery":
                    changed["validation"]["official_nature_delivery"] = mutation[1]
                elif mutation[0] == "table_locator":
                    changed["source"]["table_locator"] = mutation[1]
                elif mutation[0] == "capture_hash":
                    changed["capture"]["sha256"] = mutation[1]
                else:
                    changed["source"]["publisher_host"] = mutation[1]
                with self.assertRaises(HUSTDepth2BAuthorizationError):
                    validate_official_source_record(changed)

    def test_source_and_clarification_reject_unknown_keys(self) -> None:
        for label, record, validator in (
            ("source", self.source, validate_official_source_record),
            ("clarification", self.clarification, validate_clarification_record),
        ):
            with self.subTest(record=label):
                changed = deepcopy(record)
                changed["target_derived_note"] = "not allowed"
                with self.assertRaisesRegex(
                    HUSTDepth2BAuthorizationError,
                    "unknown=.*target_derived_note",
                ):
                    validator(changed)

    def test_normalized_byte_identity_overclaim_is_rejected(self) -> None:
        changed = deepcopy(self.source)
        changed["nonclaims"].append(
            "The rendered table is byte‑\n   identical to the publisher PDF."
        )
        with self.assertRaisesRegex(
            HUSTDepth2BAuthorizationError,
            "byte-identity overclaim",
        ):
            validate_official_source_record(changed)

    def test_clarification_separates_direct_source_claims_and_derivations(self) -> None:
        validate_clarification_record(self.clarification)
        direct = self.clarification["direct_statements"]
        derivation = self.clarification["project_derivation"]
        correlation = self.clarification["correlation_policy"]
        self.assertEqual(direct["article"]["evidence_type"], "PUBLIC_DIRECT")
        self.assertEqual(direct["supplement"]["evidence_type"], "PUBLIC_DIRECT")
        self.assertEqual(derivation["evidence_type"], "PUBLIC_DERIVABLE")
        self.assertEqual(correlation["evidence_type"], "PUBLIC_DERIVABLE")
        self.assertIn("not a claim", correlation["qualification"])
        self.assertFalse(
            self.clarification["boundaries"][
                "combined_aaf_reconstruction_authorized"
            ]
        )

    def test_component_table_is_an_exact_ordered_second_key(self) -> None:
        validate_required_inputs_graph(self.graph)
        actual = tuple(
            (
                row["component_id"],
                row["row_label"],
                row["AAF-I"],
                row["AAF-II"],
                row["AAF-III"],
            )
            for row in self.graph["components"]
        )
        self.assertEqual(actual, EXPECTED_COMPONENTS)

    def test_component_inventory_and_source_mutations_fail_closed(self) -> None:
        mutations = {}
        changed = deepcopy(self.graph)
        changed["components"].pop()
        mutations["missing"] = changed
        changed = deepcopy(self.graph)
        changed["components"].append(deepcopy(changed["components"][0]))
        mutations["extra_duplicate"] = changed
        changed = deepcopy(self.graph)
        changed["components"][0]["component_id"] = "renamed"
        mutations["renamed"] = changed
        changed = deepcopy(self.graph)
        changed["components"][0], changed["components"][1] = (
            changed["components"][1],
            changed["components"][0],
        )
        mutations["reordered"] = changed
        changed = deepcopy(self.graph)
        changed["components"][0]["unit"] = "percent"
        mutations["wrong_unit"] = changed
        changed = deepcopy(self.graph)
        changed["components"][0]["evidence_type"] = "PUBLIC_DERIVABLE"
        mutations["wrong_role"] = changed
        changed = deepcopy(self.graph)
        changed["components"][0]["source_id"] = "historical_mirror"
        mutations["wrong_source"] = changed
        changed = deepcopy(self.graph)
        changed["components"][4]["AAF-I"], changed["components"][4]["AAF-II"] = (
            changed["components"][4]["AAF-II"],
            changed["components"][4]["AAF-I"],
        )
        mutations["cross_column"] = changed

        for label, mutation in mutations.items():
            with self.subTest(mutation=label):
                with self.assertRaises(HUSTDepth2BAuthorizationError):
                    validate_required_inputs_graph(mutation)

    def test_combined_authorization_must_remain_false(self) -> None:
        changed = deepcopy(self.graph)
        changed["authorizations"]["combined_aaf_reconstruction_authorized"] = True
        with self.assertRaises(HUSTDepth2BAuthorizationError):
            validate_required_inputs_graph(changed)

    def test_derivable_authorizations_depend_on_table_and_clarification(self) -> None:
        authorizations = self.graph["authorizations"]
        self.assertEqual(
            authorizations["component_table"],
            {
                "evidence_type": "PUBLIC_DIRECT",
                "depends_on": ["hust_2018_aaf_depth_2b_official_source_v1"],
            },
        )
        for key in ("individual_rss_rule", "within_result_correlation_policy"):
            self.assertEqual(
                authorizations[key],
                {
                    "evidence_type": "PUBLIC_DERIVABLE",
                    "depends_on": [
                        "component_table",
                        "hust_2018_aaf_depth_2b_clarification_v1",
                    ],
                },
            )
        for scope in SCOPES:
            self.assertEqual(
                authorizations["complete_uncertainty_model"][scope][
                    "evidence_type"
                ],
                "PUBLIC_DERIVABLE",
            )
            self.assertIn(
                "hust_2018_aaf_depth_2b_clarification_v1",
                authorizations["complete_uncertainty_model"][scope]["depends_on"],
            )

        changed = deepcopy(self.graph)
        changed["authorizations"]["complete_uncertainty_model"]["AAF-I"][
            "depends_on"
        ].remove("hust_2018_aaf_depth_2b_clarification_v1")
        with self.assertRaises(HUSTDepth2BAuthorizationError):
            validate_required_inputs_graph(changed)

    def test_rss_and_rho_diagnostics_are_recomputed_at_precision_50(self) -> None:
        for scope in SCOPES:
            with self.subTest(scope=scope):
                diagnostic = calculate_scope_diagnostics(self.graph, scope)
                self.assertEqual(
                    Decimal(diagnostic["sum_of_squares"]),
                    EXPECTED_SUMS_OF_SQUARES[scope],
                )
                self.assertEqual(
                    Decimal(diagnostic["relative_standard_uncertainty_ppm"]),
                    EXPECTED_RSS_PPM[scope],
                )
                self.assertEqual(
                    diagnostic["dominant_component_1"],
                    "horizontal_source_mass_distance",
                )
                self.assertEqual(
                    diagnostic["dominant_component_2"],
                    "vertical_source_mass_distance",
                )
                self.assertEqual(
                    diagnostic["dominant_pair_rho_disclosed_approximation"],
                    EXPECTED_RHO_APPROXIMATIONS[scope],
                )
                self.assertEqual(
                    Decimal(
                        diagnostic["dominant_pair_rho_sensitivity_bound"]
                    ).quantize(Decimal("0.0001")),
                    Decimal(EXPECTED_RHO_APPROXIMATIONS[scope]),
                )

    def test_terminal_comparison_values_do_not_drive_derivations(self) -> None:
        baseline = {
            scope: calculate_scope_diagnostics(self.graph, scope) for scope in SCOPES
        }
        changed = deepcopy(self.graph)
        for scope in SCOPES:
            changed["terminal_comparisons"][scope]["published_g_m3_kg-1_s-2"] = "9e-11"
            changed["terminal_comparisons"][scope][
                "published_standard_uncertainty_m3_kg-1_s-2"
            ] = "9e-15"
            changed["terminal_comparisons"][scope]["displayed_total_ppm"] = "99"
        validate_required_inputs_graph(changed)
        self.assertEqual(
            {scope: calculate_scope_diagnostics(changed, scope) for scope in SCOPES},
            baseline,
        )

    def test_authorization_artifact_is_fresh_and_preserves_historical_bytes(self) -> None:
        artifact = build_authorization_artifact(Path("."))
        committed = Path(
            "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v1.json"
        ).read_text(encoding="utf-8")
        self.assertEqual(committed, serialize_artifact(artifact))
        preserved = {
            row["path"]: row["sha256"]
            for row in artifact["historical_artifact_preservation"]
        }
        self.assertEqual(preserved, HISTORICAL_ARTIFACT_SHA256)
        for path, expected in HISTORICAL_ARTIFACT_SHA256.items():
            with self.subTest(path=path):
                self.assertEqual(sha256_bytes(Path(path).read_bytes()), expected)


if __name__ == "__main__":
    unittest.main()
