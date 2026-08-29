from fractions import Fraction
import unittest

from Discovery.constants import (
    GRAVITATIONAL_CONSTANT_G,
    PLANCK_MASS,
    REDUCED_PLANCK_CONSTANT,
    SPEED_OF_LIGHT,
)
from Discovery.dimensional_search import allowed_powers, search_candidates


class DimensionalSearchTests(unittest.TestCase):
    def test_power_bound_can_include_half_integers(self) -> None:
        powers = allowed_powers(max_abs_power=1, max_denominator=2)
        self.assertIn(Fraction(1, 2), powers)
        self.assertIn(Fraction(-1, 2), powers)
        self.assertNotIn(Fraction(0), powers)

    def test_known_planck_mass_rearrangement_is_found(self) -> None:
        matches = search_candidates(
            (REDUCED_PLANCK_CONSTANT, SPEED_OF_LIGHT, PLANCK_MASS),
            max_factors=3,
            max_abs_power=2,
        )
        candidate = next(
            result
            for result in matches
            if result.exponents == {"hbar": "1", "c": "1", "m_P": "-2"}
        )
        self.assertEqual(candidate.classification, "known Planck-unit identity")
        self.assertAlmostEqual(candidate.ratio_to_g, 1.0, delta=3e-5)

    def test_every_result_matches_target_dimension_and_is_ranked(self) -> None:
        matches = search_candidates(max_factors=3, max_abs_power=2)
        self.assertTrue(matches)
        self.assertTrue(
            all(result.dimension == GRAVITATIONAL_CONSTANT_G.dimension for result in matches)
        )
        self.assertEqual(matches, sorted(matches, key=lambda result: result.rank_key()))

    def test_target_cannot_be_its_own_generator(self) -> None:
        with self.assertRaises(ValueError):
            search_candidates((GRAVITATIONAL_CONSTANT_G,))


if __name__ == "__main__":
    unittest.main()
