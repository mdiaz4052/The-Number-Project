from __future__ import annotations

from decimal import Decimal, localcontext
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FEASIBILITY_PATH = (
    ROOT
    / "Experiments"
    / "GMeasurements"
    / "hust_2018_aaf_depth_2b_feasibility_v1.json"
)
EXTERNAL_SOURCES_PATH = (
    ROOT
    / "Experiments"
    / "GMeasurements"
    / "hust_2018_aaf_external_sources_v1.json"
)

EXPECTED_BASE = "3c4c273871958127e6f3253e7e9495a673993ffe"
EXPECTED_PREREGISTRATION = "d2918e1aaec07b2f9f5728f461441e61d896effe"
EXPECTED_SUPPLEMENT_SHA256 = (
    "5b61d5c831be98c46e47fcc32f1ade0a680b4af6354d2bc34859d94b22279ffb"
)
EXPECTED_SCREENSHOT_SHA256 = (
    "3f47836277c451a0cb0aa466c5bb12f0f813d7a8072856951cf336c04c8d0294"
)
EXPECTED_COMPONENTS = (
    ("pendulum_dimensions", "0.16", "0.16", "0.16"),
    ("pendulum_attitude", "0.06", "0.06", "0.03"),
    ("pendulum_density_inhomogeneity", "0.46", "0.46", "0.46"),
    ("coating_layer", "0.34", "0.34", "0.34"),
    ("clamp_and_ferrule", "0.70", "1.05", "0.48"),
    ("other_pendulum_effects", "0.29", "0.29", "0.29"),
    ("source_mass_masses", "0.32", "0.31", "0.31"),
    ("horizontal_source_mass_distance", "8.98", "8.98", "8.98"),
    ("vertical_source_mass_distance", "5.79", "5.79", "5.79"),
    ("source_mass_positions_alignment", "0.57", "0.62", "0.35"),
    ("fibre_anelasticity", "0.01", "0.01", "0.01"),
    ("thermal_effect", "0.91", "0.91", "0.91"),
    ("time_base", "0.01", "0.01", "0.01"),
    ("rotating_gravity_gradient", "1.86", "1.35", "1.72"),
    ("shelf_deformation", "1.51", "1.51", "1.51"),
    ("magnetic_damper", "1.95", "1.95", "0.08"),
    ("air_density", "1.00", "1.51", "1.13"),
    ("magnetic_field", "3.98", "3.98", "0.90"),
    ("angle_encoder", "0.72", "0.72", "0.72"),
    ("residual_twist_angle", "0.03", "0.61", "0.45"),
    ("statistical_angular_acceleration", "3.44", "2.60", "1.34"),
)
EXPECTED_SUMS = {
    "AAF-I": Decimal("155.0861"),
    "AAF-II": Decimal("150.6924"),
    "AAF-III": Decimal("125.7279"),
}
EXPECTED_REPORTED_TOTALS = {
    "AAF-I": "12.45",
    "AAF-II": "12.27",
    "AAF-III": "11.21",
}
EXPECTED_NOT_APPLICABLE = [
    "fibre_nonlinearity",
    "gravitational_nonlinearity",
    "electrostatic_field",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class HUST2018AAFDepth2BFeasibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = _load(FEASIBILITY_PATH)
        self.external_sources = _load(EXTERNAL_SOURCES_PATH)

    def test_decision_and_scope_match_frozen_feasibility_question(self) -> None:
        self.assertEqual(self.record["schema_version"], 1)
        self.assertEqual(self.record["decision"], "GO")
        self.assertEqual(self.record["scope"], "individual_AAF_depth_2b_feasibility_only")
        self.assertEqual(self.record["base_commit"], EXPECTED_BASE)
        self.assertEqual(self.record["preregistration_commit"], EXPECTED_PREREGISTRATION)
        self.assertEqual(self.record["unit"], "ppm relative standard uncertainty in G")

    def test_table1_component_table_is_exactly_second_keyed(self) -> None:
        actual = tuple(
            (
                row["component_id"],
                row["AAF-I"],
                row["AAF-II"],
                row["AAF-III"],
            )
            for row in self.record["components"]
        )
        self.assertEqual(actual, EXPECTED_COMPONENTS)
        self.assertEqual(self.record["not_applicable_AAF_rows"], EXPECTED_NOT_APPLICABLE)

    def test_main_article_provenance_is_candid(self) -> None:
        article = self.record["sources"]["main_article"]
        self.assertEqual(article["doi"], "10.1038/s41586-018-0431-5")
        self.assertEqual(article["table_locator"], "Table 1, Nature p. 584")
        self.assertIn("third-party-hosted", article["mirror_provenance"])
        self.assertNotIn("byte-identical", article["mirror_provenance"])
        visual = article["nature_visual_confirmation"]
        self.assertEqual(
            visual["status"],
            "confirmed_by_project_owner_from_Nature_accessed_copy",
        )
        self.assertEqual(visual["screenshot_sha256"], EXPECTED_SCREENSHOT_SHA256)
        self.assertEqual(visual["screenshot_byte_length"], 127165)
        self.assertIn("not_stored_in_repository", visual["repository_storage"])

    def test_supplement_source_and_covariance_rule_are_bound_to_existing_capture(self) -> None:
        supplement = self.record["sources"]["supplementary_information"]
        self.assertEqual(supplement["sha256"], EXPECTED_SUPPLEMENT_SHA256)
        resources = {
            resource["source_id"]: resource
            for resource in self.external_sources["resources"]
        }
        self.assertEqual(
            resources["supplementary_information"]["sha256"],
            EXPECTED_SUPPLEMENT_SHA256,
        )
        self.assertIn("root-sum-square", supplement["individual_rule"])
        self.assertIn("independent", supplement["cross_run_rule"])
        self.assertIn("100% correlated", supplement["cross_run_rule"])

    def test_individual_totals_are_reconstructed_without_using_reported_totals(self) -> None:
        rows = self.record["components"]
        reconstructed = self.record["reconstructed_from_rounded_table_entries"]
        for scope in ("AAF-I", "AAF-II", "AAF-III"):
            with localcontext() as ctx:
                ctx.prec = 50
                sum_of_squares = sum(
                    Decimal(row[scope]) ** 2 for row in rows
                )
                rss = sum_of_squares.sqrt()
            self.assertEqual(sum_of_squares, EXPECTED_SUMS[scope])
            self.assertEqual(
                reconstructed[scope]["sum_of_squares"],
                str(EXPECTED_SUMS[scope]),
            )
            self.assertEqual(
                reconstructed[scope]["rss_ppm"],
                str(rss),
            )
        self.assertEqual(
            self.record["reported_individual_totals_ppm"],
            EXPECTED_REPORTED_TOTALS,
        )

    def test_all_preregistered_individual_feasibility_requirements_are_satisfied(self) -> None:
        requirements = self.record["feasibility_requirements"]
        self.assertEqual(
            requirements,
            {
                "complete_component_inventory": "SATISFIED",
                "component_magnitudes_and_units": "SATISFIED",
                "component_to_G_mapping": "SATISFIED_AS_DIRECT_RELATIVE_CONTRIBUTIONS",
                "combination_rule": "SATISFIED",
                "within_result_covariance_needed": "NONE_BEYOND_LISTED_RSS_MODEL_FOR_INDIVIDUAL_RESULTS",
                "statistical_vs_shared_provenance": "SATISFIED",
                "published_individual_uncertainty_reconstructible_without_target_input": "SATISFIED",
            },
        )

    def test_go_does_not_promote_combined_or_deeper_claims(self) -> None:
        boundary = self.record["authorization_boundary"]
        self.assertEqual(
            boundary["depth_2b_implementation"],
            "feasible_but_not_implemented_by_this_audit",
        )
        self.assertEqual(boundary["combined_AAF_estimator"], "NOT_AUTHORIZED")
        self.assertEqual(boundary["raw_or_run_level_replication"], "NOT_ESTABLISHED")
        self.assertEqual(boundary["experiment_validity"], "NOT_ESTABLISHED")
        nonclaims = "\n".join(self.record["nonclaims"])
        self.assertIn("terminal comparison", nonclaims)
        self.assertIn("does not claim byte identity", nonclaims)
        self.assertIn("No combined AAF", nonclaims)
        self.assertIn("No existing depth-2a MeasurementModel is changed", nonclaims)


if __name__ == "__main__":
    unittest.main()
