from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch

from Discovery import nist_2026_estimator_feasibility as n


class NIST2026EstimatorFeasibilityBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = n.verify_preregistration()
        cls.attestation = n.load_source_attestation(cls.protocol)

    def test_source_projection_and_precision_roles(self):
        experimental = self.attestation["experimental_layer"]
        self.assertEqual(tuple(experimental["input_order"]), n.INPUT_ORDER)
        self.assertEqual(
            [row["G_decimal_in_1e_minus_11_units"] for row in experimental["table_16"]["measurements"]],
            ["6.673642", "6.674021", "6.672637", "6.673636"],
        )
        self.assertEqual(
            [row["displayed_relative_standard_uncertainty_ppm"] for row in experimental["table_16"]["measurements"]],
            ["23", "30", "38", "94"],
        )
        self.assertEqual(
            experimental["table_18"]["diagonal_relative_standard_uncertainty_ppm"],
            ["23.2", "30.3", "37.5", "93.9"],
        )
        self.assertIn("more precise", experimental["table_18"]["precision_policy"])

    def test_exact_symmetric_correlation_and_covariance(self):
        rho = n.correlation_matrix(self.attestation)
        self.assertEqual(
            rho,
            [
                [Fraction(1), Fraction(21, 50), Fraction(19, 50), Fraction(3, 25)],
                [Fraction(21, 50), Fraction(1), Fraction(23, 100), Fraction(23, 100)],
                [Fraction(19, 50), Fraction(23, 100), Fraction(1), Fraction(1, 4)],
                [Fraction(3, 25), Fraction(23, 100), Fraction(1, 4), Fraction(1)],
            ],
        )
        covariance = n.relative_covariance_matrix(self.attestation)
        self.assertEqual(
            covariance,
            [
                [Fraction(13456, 25), Fraction(184527, 625), Fraction(1653, 5), Fraction(163386, 625)],
                [Fraction(184527, 625), Fraction(91809, 100), Fraction(20907, 80), Fraction(6543891, 10000)],
                [Fraction(1653, 5), Fraction(20907, 80), Fraction(5625, 4), Fraction(14085, 16)],
                [Fraction(163386, 625), Fraction(6543891, 10000), Fraction(14085, 16), Fraction(881721, 100)],
            ],
        )
        for i in range(4):
            for j in range(4):
                self.assertEqual(covariance[i][j], covariance[j][i])

    def test_exact_positive_principal_minors_and_go(self):
        covariance = n.relative_covariance_matrix(self.attestation)
        self.assertEqual(
            n.leading_principal_minors(covariance),
            (
                Fraction(13456, 25),
                Fraction(158978208771, 390625),
                Fraction(121558568110209, 250000),
                Fraction(4846543822981430177733, 1250000000),
            ),
        )
        audit = n.experimental_covariance_audit(self.attestation)
        self.assertEqual(audit["verdict"], "GO")
        self.assertTrue(audit["positive_definite"])

    def test_experimental_go_is_independent_of_consensus_and_terminal_values(self):
        baseline = n.experimental_covariance_audit(self.attestation)
        changed = deepcopy(self.attestation)
        changed["authority_resolution"]["journal_pdf_result"]["G_decimal_in_1e_minus_11_units"] = "9.99999"
        changed["consensus_layer"]["specified"]["mu_prior_center_si"] = "1e-30"
        changed["consensus_layer"]["published_table_19"]["dark_uncertainty_si"]["copper_servo"] = "9e99"
        self.assertEqual(n.experimental_covariance_audit(changed), baseline)

    def test_bayesian_consensus_is_fail_closed_no_go(self):
        audit = n.bayesian_consensus_audit(self.protocol, self.attestation)
        self.assertEqual(audit["verdict"], "NO_GO")
        self.assertEqual(
            tuple(item["id"] for item in audit["missing_result_driving_information"]),
            n.CONSENSUS_MISSING_IDS,
        )
        self.assertIn("GLS", audit["nonclaim"])

    def test_bayesian_missing_inventory_cannot_be_silently_erased(self):
        changed = deepcopy(self.attestation)
        changed["consensus_layer"]["not_uniquely_specified_in_primary_paper"] = []
        with self.assertRaises(n.NISTFeasibilityError):
            n.bayesian_consensus_audit(self.protocol, changed)
        override = _RootOverride(changed)
        try:
            with self.assertRaises(n.NISTFeasibilityError):
                n.load_source_attestation(self.protocol, root=override)
        finally:
            override.close()

    def test_source_authority_resolves_landing_pdf_conflict(self):
        audit = n.source_authority_audit(self.attestation)
        self.assertTrue(audit["numerical_conflict_present"])
        self.assertEqual(audit["journal_pdf_result"]["G_decimal_in_1e_minus_11_units"], "6.67387")
        self.assertEqual(audit["landing_page_displayed_result"]["G_decimal_in_1e_minus_11_units"], "6.67366")
        self.assertEqual(audit["resolution"], "peer_reviewed_article_pdf_controls_scientific_transcription")

    def test_invalid_covariance_geometry_fails(self):
        changed = deepcopy(self.attestation)
        changed["experimental_layer"]["table_18"]["correlation_matrix"][0][1] = "1.2"
        changed["experimental_layer"]["table_18"]["correlation_matrix"][1][0] = "1.2"
        with self.assertRaises(n.NISTFeasibilityError):
            n.experimental_covariance_audit(changed)


class _RootOverride:
    """Minimal root adapter used only to prove source loading fails closed on edited attestation."""

    def __init__(self, attestation):
        import json
        import tempfile
        from pathlib import Path
        self._temp = tempfile.TemporaryDirectory()
        self.path = Path(self._temp.name)
        target = self.path / n.SOURCE_ATTESTATION_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(attestation))

    def __truediv__(self, other):
        return self.path / other

    def close(self):
        self._temp.cleanup()


class NIST2026EstimatorFeasibilityArtifactTests(unittest.TestCase):
    def test_preregistration_and_implementation_chronology(self):
        protocol = n.verify_preregistration()
        self.assertEqual(protocol["intended_base_sha"], n.BASELINE)
        n.verify_implementation_chronology()

    def test_e001_inventory_is_disjoint(self):
        n.verify_e001_isolation()
        self.assertFalse(set(n.E001_FORBIDDEN) & set(n.SOURCE_PATHS))

    def test_build_artifact_read_closure_is_exact(self):
        root = n.ROOT.resolve()
        seen = set()
        original_read_bytes = Path.read_bytes
        original_read_text = Path.read_text

        def record(path):
            try:
                relative = path.resolve().relative_to(root)
            except ValueError:
                return
            if ".git" not in relative.parts:
                seen.add(relative.as_posix())

        def tracked_read_bytes(path):
            record(path)
            return original_read_bytes(path)

        def tracked_read_text(path, *args, **kwargs):
            record(path)
            return original_read_text(path, *args, **kwargs)

        with patch.object(Path, "read_bytes", tracked_read_bytes), patch.object(
            Path, "read_text", tracked_read_text
        ):
            n.build_artifact()

        self.assertEqual(seen, set(n.SOURCE_PATHS))

    def test_committed_artifact_matches_rebuild(self):
        path = n.ROOT / n.DEFAULT_OUTPUT
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(), n.serialize_artifact(n.build_artifact()))


if __name__ == "__main__":
    unittest.main()
