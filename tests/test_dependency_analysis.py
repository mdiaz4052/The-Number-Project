from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from Discovery.dependency_analysis import (
    DEFAULT_OUTPUT,
    EXACT_PYTHON_REDUCTION_ONLY,
    LEAN_CERTIFIED,
    NO_REGISTERED_TARGET_DEPENDENCY,
    NOT_APPLICABLE,
    TARGET_DEPENDENT,
    TARGET_RECONSTRUCTION,
    UNRESOLVED_PROVENANCE,
    _dimensional_system_record,
    analyze_candidates,
    analyze_default_candidates,
    build_artifact,
    candidate_surface_signature,
    serialize_artifact,
    solve_default_dimensional_system,
)
from Discovery.planck_identities import (
    PLANCK_IDENTITIES,
    normalize_exponent_signature,
)


class DependencyAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = analyze_default_candidates()
        cls.by_signature = {
            record.surface_signature: record for record in cls.records
        }

    def test_twenty_one_candidates_collapse_into_ten_exact_groups(self) -> None:
        self.assertEqual(len(self.records), 21)
        group_ids = {record.equivalence_group_identifier for record in self.records}
        self.assertEqual(len(group_ids), 10)

    def test_four_lean_controls_reduce_exactly_to_g(self) -> None:
        for identity in PLANCK_IDENTITIES:
            with self.subTest(identity=identity.identifier):
                record = self.by_signature[identity.signature]
                self.assertEqual(record.dependency_status, TARGET_RECONSTRUCTION)
                self.assertEqual(record.certification_status, LEAN_CERTIFIED)
                self.assertEqual(record.expanded_dependency_signature, (("G", Fraction(1)),))
                self.assertEqual(record.lean_theorem_name, identity.lean_theorem_name)

    def test_two_additional_reconstructions_remain_python_only(self) -> None:
        signatures = (
            normalize_exponent_signature((("l_P", 3), ("m_P", -1), ("t_P", -2))),
            normalize_exponent_signature((("hbar", 2), ("l_P", -1), ("m_P", -3))),
        )
        for signature in signatures:
            with self.subTest(signature=signature):
                record = self.by_signature[signature]
                self.assertEqual(record.dependency_status, TARGET_RECONSTRUCTION)
                self.assertEqual(
                    record.certification_status,
                    EXACT_PYTHON_REDUCTION_ONLY,
                )
                self.assertIsNone(record.lean_theorem_name)

    def test_dependency_and_certification_statuses_are_separate(self) -> None:
        partial = self.by_signature[
            normalize_exponent_signature((("c", 2), ("m_p", -1), ("l_P", 1)))
        ]
        self.assertEqual(partial.dependency_status, TARGET_DEPENDENT)
        self.assertEqual(partial.power_of_g, Fraction(1, 2))
        self.assertEqual(partial.certification_status, NOT_APPLICABLE)

        no_registered_g = self.by_signature[
            normalize_exponent_signature((("c", 1), ("hbar", 1), ("m_p", -2)))
        ]
        self.assertEqual(
            no_registered_g.dependency_status,
            NO_REGISTERED_TARGET_DEPENDENCY,
        )
        self.assertEqual(no_registered_g.power_of_g, 0)
        self.assertIn("does not establish", no_registered_g.explanation)

    def test_proton_electron_and_atomic_mass_triples_are_equivalent(self) -> None:
        for mass in ("m_p", "m_e", "m_u"):
            signatures = (
                normalize_exponent_signature((("c", 2), (mass, -1), ("l_P", 1))),
                normalize_exponent_signature((("c", 3), (mass, -1), ("t_P", 1))),
                normalize_exponent_signature(((mass, -1), ("l_P", 3), ("t_P", -2))),
            )
            records = [self.by_signature[signature] for signature in signatures]
            with self.subTest(mass=mass):
                self.assertEqual(
                    len({record.equivalence_group_identifier for record in records}),
                    1,
                )
                self.assertTrue(all(record.equivalence_group_size == 3 for record in records))

    def test_unresolved_surface_factor_gets_no_equivalence_claim(self) -> None:
        candidate = replace(
            self.records[0].candidate,
            expression="unknown_factor",
            exponents={"unknown_factor": "1"},
        )
        record = analyze_candidates((candidate,))[0]
        self.assertEqual(record.dependency_status, UNRESOLVED_PROVENANCE)
        self.assertEqual(record.unresolved_factors, ("unknown_factor",))
        self.assertEqual(record.certification_status, NOT_APPLICABLE)

    def test_equivalence_group_identifiers_are_deterministic(self) -> None:
        repeated = analyze_candidates(tuple(record.candidate for record in self.records))
        first = {
            record.surface_signature: record.equivalence_group_identifier
            for record in self.records
        }
        second = {
            record.surface_signature: record.equivalence_group_identifier
            for record in repeated
        }
        self.assertEqual(first, second)

    def test_default_dimensional_system_has_rank_four_and_nullity_six(self) -> None:
        solution = solve_default_dimensional_system()
        self.assertEqual(solution.status, "affine")
        self.assertEqual(solution.rank, 4)
        self.assertEqual(solution.nullity, 6)
        rendered = _dimensional_system_record(solution)
        dimensionless_directions = {
            item["dimensionless_monomial"] for item in rendered["nullspace_basis"]
        }
        self.assertIn("m_p / m_e", dimensionless_directions)
        self.assertIn("m_u / m_e", dimensionless_directions)
        self.assertIn("m_P / m_e", dimensionless_directions)

    def test_existing_search_fields_and_classifications_are_preserved(self) -> None:
        artifact = build_artifact()
        candidate_records = artifact["candidates"]
        self.assertEqual(len(candidate_records), len(self.records))
        for analyzed, artifact_record in zip(self.records, candidate_records):
            with self.subTest(expression=analyzed.candidate.expression):
                self.assertEqual(
                    artifact_record["search_record"],
                    analyzed.candidate.as_csv_row(),
                )

    def test_artifact_is_byte_deterministic_and_current(self) -> None:
        first = serialize_artifact(build_artifact())
        second = serialize_artifact(build_artifact())
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertTrue(first.endswith("\n"))
        self.assertEqual(DEFAULT_OUTPUT.read_text(encoding="utf-8"), first)

    def test_check_cli_accepts_current_and_rejects_stale_artifact(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "dependency_analysis.json"
            output.write_text(
                serialize_artifact(build_artifact()),
                encoding="utf-8",
            )
            command = (
                sys.executable,
                "-m",
                "Discovery.dependency_analysis",
                "--check",
                "--output",
                str(output),
            )
            current = subprocess.run(
                command,
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(current.returncode, 0, current.stderr)
            self.assertIn("Dependency artifact is current", current.stdout)

            output.write_text("{}\n", encoding="utf-8")
            stale = subprocess.run(
                command,
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(stale.returncode, 1, stale.stdout)
            self.assertIn("stale or missing dependency artifact", stale.stderr)

    def test_candidate_signature_round_trip_uses_exact_fractions(self) -> None:
        for record in self.records:
            with self.subTest(expression=record.candidate.expression):
                self.assertEqual(
                    candidate_surface_signature(record.candidate),
                    record.surface_signature,
                )


if __name__ == "__main__":
    unittest.main()
