from fractions import Fraction
import unittest

from Discovery.dimensional_search import search_candidates
from Discovery.planck_identities import (
    KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
    PLANCK_IDENTITIES,
    PLANCK_IDENTITIES_BY_SIGNATURE,
    PlanckIdentity,
    build_planck_identity_catalog,
    normalize_exponent_signature,
)


class PlanckIdentityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matches = search_candidates()
        cls.by_signature = {
            normalize_exponent_signature(
                (key, Fraction(exponent)) for key, exponent in candidate.exponents.items()
            ): candidate
            for candidate in cls.matches
        }

    def test_all_four_signatures_are_certified_controls(self) -> None:
        self.assertEqual(len(PLANCK_IDENTITIES), 4)
        for identity in PLANCK_IDENTITIES:
            with self.subTest(identity=identity.identifier):
                self.assertIs(PLANCK_IDENTITIES_BY_SIGNATURE[identity.signature], identity)
                candidate = self.by_signature[identity.signature]
                self.assertEqual(
                    candidate.classification,
                    KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
                )
                self.assertTrue(identity.lean_theorem_name)

    def test_catalog_theorem_names_match_expected_lean_api(self) -> None:
        # The names form the small public API expected by the Lean module. The Lean
        # build imports that module and type-checks the declarations themselves; this
        # test deliberately does not parse Lean source from Python.
        expected_declarations = {
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_speedOfLight_sq_mul_planckLength_div_planckMass",
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_reducedPlanckConstant_mul_speedOfLight_div_planckMass_sq",
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_speedOfLight_cubed_mul_planckTime_div_planckMass",
            "TheNumberProject.FormalPhysics."
            "gravitationalConstant_eq_speedOfLight_cubed_mul_planckLength_sq_div_"
            "reducedPlanckConstant",
        }
        actual_declarations = {identity.lean_theorem_name for identity in PLANCK_IDENTITIES}
        self.assertEqual(actual_declarations, expected_declarations)
        for identity in PLANCK_IDENTITIES:
            with self.subTest(identity=identity.identifier):
                self.assertTrue(identity.lean_theorem_name.startswith("TheNumberProject.FormalPhysics."))

    def test_rounded_numerical_controls_are_approximate_not_exact(self) -> None:
        for identity in PLANCK_IDENTITIES:
            candidate = self.by_signature[identity.signature]
            with self.subTest(identity=identity.identifier):
                self.assertNotEqual(candidate.ratio_to_g, 1.0)
                self.assertAlmostEqual(candidate.ratio_to_g, 1.0, delta=3e-5)

    def test_other_planck_candidate_retains_cautious_classification(self) -> None:
        signature = normalize_exponent_signature(
            (("l_P", 3), ("m_P", -1), ("t_P", -2))
        )
        self.assertNotIn(signature, PLANCK_IDENTITIES_BY_SIGNATURE)
        self.assertEqual(
            self.by_signature[signature].classification,
            "Planck-unit rearrangement",
        )

    def test_baseline_search_still_returns_twenty_one_matches(self) -> None:
        self.assertEqual(len(self.matches), 21)

    def test_malformed_and_duplicate_catalog_entries_are_rejected(self) -> None:
        common_metadata = {
            "identifier": "invalid",
            "symbolic_relation": "G = invalid",
            "classification": KNOWN_PLANCK_IDENTITY_CLASSIFICATION,
            "dependency_explanation": "test-only invalid entry",
            "lean_theorem_name": "Test.invalid",
        }
        with self.assertRaises(ValueError):
            PlanckIdentity(
                signature=(("l_P", Fraction(1)), ("l_P", Fraction(2))),
                **common_metadata,
            )
        with self.assertRaises(TypeError):
            PlanckIdentity(
                signature=(("l_P", 0.5),),
                **common_metadata,
            )
        with self.assertRaises(ValueError):
            build_planck_identity_catalog((PLANCK_IDENTITIES[0], PLANCK_IDENTITIES[0]))


if __name__ == "__main__":
    unittest.main()
