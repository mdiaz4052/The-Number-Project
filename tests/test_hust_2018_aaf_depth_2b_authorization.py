from __future__ import annotations

from copy import deepcopy
from contextlib import redirect_stderr
from decimal import Decimal
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from Discovery.hust_2018_aaf_depth_2b_authorization import (
    ANCHOR_PATH,
    CLARIFICATION_PATH,
    EXPECTED_ANCHOR_RECORD,
    EXPECTED_COMPONENTS,
    EXPECTED_OFFICIAL_SOURCE_NONCLAIMS,
    EXPECTED_RHO_APPROXIMATIONS,
    EXPECTED_RSS_PPM,
    EXPECTED_SUMS_OF_SQUARES,
    FROZEN_MILESTONE_7_V1_SHA256,
    HISTORICAL_ARTIFACT_SHA256,
    HUSTDepth2BAuthorizationError,
    OFFICIAL_SOURCE_PATH,
    OFFICIAL_TABLE_SHA256,
    PREREGISTRATION_COMMIT,
    PREREGISTRATION_PATH,
    REQUIRED_INPUTS_PATH,
    REMOTE_ANCHOR_COMMIT,
    SCOPES,
    byte_identity_claim_is_forbidden,
    build_authorization_artifact,
    calculate_scope_diagnostics,
    main,
    serialize_artifact,
    sha256_bytes,
    validate_anchor_record,
    validate_clarification_record,
    validate_official_source_record,
    validate_required_inputs_graph,
    verify_depth_2b_source_history,
)
from Discovery.source_history import (
    SourceAncestryViolationError,
    SourceHistoryUnavailableError,
    SourceMetadataError,
    SourceStateViolationError,
    verify_committed_source_state,
)


V1_GRAPH_PATH = Path(
    "Experiments/GMeasurements/hust_2018_aaf_required_inputs_depth_2b_v1.json"
)
README_PATH = Path("Experiments/GMeasurements/README.md")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _copy_current_tree(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "venv",
            ".lake",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".mypy_cache",
        ),
    )


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

    def test_official_source_nonclaims_are_an_exact_ordered_second_key(self) -> None:
        self.assertEqual(self.source["nonclaims"], EXPECTED_OFFICIAL_SOURCE_NONCLAIMS)
        changed = deepcopy(self.source)
        changed["nonclaims"].append("An unauthorized extra nonclaim.")
        with self.assertRaisesRegex(
            HUSTDepth2BAuthorizationError,
            "exact ordered second key",
        ):
            validate_official_source_record(changed)

        changed = deepcopy(self.source)
        changed["nonclaims"][0] += " altered"
        with self.assertRaisesRegex(
            HUSTDepth2BAuthorizationError,
            "exact ordered second key",
        ):
            validate_official_source_record(changed)

    def test_byte_identity_detector_rejects_bounded_evasions(self) -> None:
        forbidden = (
            "The capture is byte identical to the raw HTTP response, though this "
            "record does not claim byte identity.",
            "These bytes are exactly the same as the publisher's raw HTTP response body.",
            "The capture is byte‑identical to the publisher response.",
            "The capture is bit-for-bit equivalent to the publisher response.",
            "The capture is bit‑for‑bit equivalent to the publisher response.",
        )
        for text in forbidden:
            with self.subTest(text=text):
                self.assertTrue(byte_identity_claim_is_forbidden(text))
        self.assertFalse(
            byte_identity_claim_is_forbidden(EXPECTED_OFFICIAL_SOURCE_NONCLAIMS[0])
        )

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
                row["printed_row_label"],
                row["AAF-I"],
                row["AAF-II"],
                row["AAF-III"],
            )
            for row in self.graph["components"]
        )
        self.assertEqual(actual, EXPECTED_COMPONENTS)

    def test_printed_labels_are_exact_and_v1_field_name_fails(self) -> None:
        labels = {
            row["component_id"]: row["printed_row_label"]
            for row in self.graph["components"]
        }
        self.assertEqual(
            labels["source_mass_positions_alignment"],
            "Positions, alignment",
        )
        self.assertEqual(
            labels["statistical_angular_acceleration"],
            "Statistical error of Δω² or αₜ",
        )

        changed = deepcopy(self.graph)
        changed["components"][0]["row_label"] = changed["components"][0].pop(
            "printed_row_label"
        )
        with self.assertRaisesRegex(HUSTDepth2BAuthorizationError, "keys differ"):
            validate_required_inputs_graph(changed)

        changed = deepcopy(self.graph)
        changed["components"][9]["printed_row_label"] = "Positions alignment"
        with self.assertRaisesRegex(HUSTDepth2BAuthorizationError, "labels"):
            validate_required_inputs_graph(changed)

    def test_v1_to_v2_numerical_projection_is_identical(self) -> None:
        v1 = _load(V1_GRAPH_PATH)
        self.assertEqual(v1["not_applicable_aaf_rows"], self.graph["not_applicable_aaf_rows"])
        self.assertEqual(v1["terminal_comparisons"], self.graph["terminal_comparisons"])
        self.assertEqual(v1["authorizations"], self.graph["authorizations"])
        for old, new in zip(v1["components"], self.graph["components"], strict=True):
            self.assertEqual(old["component_id"], new["component_id"])
            for key in (
                "unit",
                "evidence_type",
                "source_id",
                "AAF-I",
                "AAF-II",
                "AAF-III",
            ):
                self.assertEqual(old[key], new[key])

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

    def test_anchor_metadata_is_strictly_validated(self) -> None:
        anchor = _load(ANCHOR_PATH)
        self.assertEqual(anchor, EXPECTED_ANCHOR_RECORD)
        validate_anchor_record(anchor)

        mutations = {}
        changed = deepcopy(anchor)
        changed["unknown"] = True
        mutations["unknown"] = changed
        changed = deepcopy(anchor)
        changed.pop("workflow_id")
        mutations["missing"] = changed
        changed = deepcopy(anchor)
        changed["workflow_id"] = "345072294"
        mutations["wrong_type"] = changed
        changed = deepcopy(anchor)
        changed["preregistration_commit_sha"] = PREREGISTRATION_COMMIT[:12]
        mutations["short_sha"] = changed
        changed = deepcopy(anchor)
        changed["preregistration_path"] = "Experiments/GMeasurements/drifted.md"
        mutations["path_drift"] = changed

        for label, changed in mutations.items():
            with self.subTest(mutation=label):
                with self.assertRaises(SourceMetadataError) as caught:
                    validate_anchor_record(changed)
                self.assertEqual(caught.exception.status, "source_metadata_invalid")

    def test_real_preregistration_and_anchor_history_are_verified(self) -> None:
        result = verify_depth_2b_source_history(Path("."))
        self.assertEqual(result["preregistration"]["status"], "verified")
        self.assertEqual(result["preregistration"]["commit"], PREREGISTRATION_COMMIT)
        self.assertEqual(result["remote_anchor"]["status"], "verified")
        self.assertEqual(result["remote_anchor"]["commit"], REMOTE_ANCHOR_COMMIT)

    def test_synthetic_squash_fails_specifically_for_ancestry(self) -> None:
        root = Path(".").resolve()
        with tempfile.TemporaryDirectory() as temporary:
            synthetic_root = Path(temporary) / "repository"
            subprocess.run(
                ["git", "clone", "--quiet", "--no-hardlinks", str(root), str(synthetic_root)],
                check=True,
            )
            _copy_current_tree(root, synthetic_root)
            _git(synthetic_root, "config", "user.name", "Synthetic Squash Test")
            _git(
                synthetic_root,
                "config",
                "user.email",
                "synthetic-squash@example.invalid",
            )
            _git(synthetic_root, "add", "-A")
            tree = _git(synthetic_root, "write-tree")
            completed = subprocess.run(
                [
                    "git",
                    "commit-tree",
                    tree,
                    "-p",
                    "715c189818dea258f3c6d447d7854226c1f2a575",
                ],
                cwd=synthetic_root,
                input="synthetic squash\n",
                check=True,
                capture_output=True,
                text=True,
            )
            synthetic = completed.stdout.strip()
            _git(synthetic_root, "cat-file", "-e", f"{synthetic}^{{commit}}")
            _git(synthetic_root, "checkout", "--quiet", "--detach", synthetic)
            with self.assertRaises(SourceAncestryViolationError) as caught:
                verify_depth_2b_source_history(synthetic_root)
            self.assertEqual(caught.exception.status, "ancestry_violated")

    def test_changed_preregistration_fails_specifically_for_source_state(self) -> None:
        root = Path(".").resolve()
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repository"
            subprocess.run(
                ["git", "clone", "--quiet", "--no-hardlinks", str(root), str(clone)],
                check=True,
            )
            path = clone / PREREGISTRATION_PATH
            path.rename(path.with_name("drifted_preregistration.md"))
            with self.assertRaises(SourceStateViolationError) as caught:
                verify_committed_source_state(
                    clone,
                    PREREGISTRATION_COMMIT,
                    source_paths=(PREREGISTRATION_PATH.as_posix(),),
                    artifact_label="depth-2b preregistration",
                )
            self.assertEqual(caught.exception.status, "source_state_violated")

    def test_shallow_history_remains_unavailable(self) -> None:
        root = Path(".").resolve()
        with tempfile.TemporaryDirectory() as temporary:
            shallow = Path(temporary) / "shallow"
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--depth",
                    "1",
                    f"file://{root}",
                    str(shallow),
                ],
                check=True,
            )
            with self.assertRaises(SourceHistoryUnavailableError) as caught:
                verify_depth_2b_source_history(shallow)
            self.assertEqual(caught.exception.status, "history_unavailable")

    def test_authorization_cli_preserves_history_exit_taxonomy(self) -> None:
        stderr = io.StringIO()
        with patch(
            "Discovery.hust_2018_aaf_depth_2b_authorization.build_authorization_artifact",
            side_effect=SourceHistoryUnavailableError("fixture unavailable"),
        ), patch("sys.argv", ["authorization", "--check"]), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("history_unavailable:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_readme_reports_current_v2_artifacts_and_exact_assessment_boundary(self) -> None:
        text = README_PATH.read_text(encoding="utf-8")
        self.assertIn("hust_2018_aaf_required_inputs_depth_2b_v2.json", text)
        self.assertIn("hust_2018_aaf_depth_2b_authorization_v2.json", text)
        self.assertIn("hust_2018_aaf_depth_2b_measurement_models_v2.json", text)
        self.assertIn("hust_2018_aaf_depth_2b_mutation_results_v2.json", text)
        self.assertIn(
            "the target-path axis reports `no_registered_target_path`, and\n"
            "replication remains `incomplete`",
            text,
        )
        self.assertNotIn(
            "satisfied dimensional, algebraic, target-path, metrological",
            text,
        )

    def test_authorization_artifact_is_fresh_and_preserves_historical_bytes(self) -> None:
        artifact = build_authorization_artifact(Path("."))
        committed = Path(
            "Experiments/GMeasurements/hust_2018_aaf_depth_2b_authorization_v2.json"
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
        frozen = {
            row["path"]: row["sha256"]
            for row in artifact["frozen_milestone_7_v1_preservation"]
        }
        self.assertEqual(frozen, FROZEN_MILESTONE_7_V1_SHA256)
        for path, expected in FROZEN_MILESTONE_7_V1_SHA256.items():
            with self.subTest(path=path):
                self.assertEqual(sha256_bytes(Path(path).read_bytes()), expected)
        self.assertEqual(artifact["artifact_schema_version"], 2)
        self.assertTrue(
            all(
                record["status"] == "verified"
                for record in artifact["source_history_verification"].values()
            )
        )
        limitation = artifact["official_source_precondition"]
        self.assertFalse(limitation["publisher_bytes_committed"])
        self.assertFalse(
            limitation["independently_reproducible_from_repository_contents"]
        )
        self.assertFalse(limitation["secondary_source_authorized_as_official"])


if __name__ == "__main__":
    unittest.main()
    FROZEN_MILESTONE_7_V1_SHA256,
    byte_identity_claim_is_forbidden,
    main,
    validate_anchor_record,
    main,
