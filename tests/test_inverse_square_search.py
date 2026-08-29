from fractions import Fraction
import unittest

from Discovery.inverse_square_search import (
    build_artifact,
    serialize_artifact,
    solve_inverse_square_systems,
)


class InverseSquareSearchTests(unittest.TestCase):
    def test_unconstrained_family_has_one_mass_ratio_direction(self) -> None:
        unconstrained, _, _ = solve_inverse_square_systems()
        self.assertEqual(unconstrained.status, "affine")
        self.assertEqual(unconstrained.rank, 3)
        self.assertEqual(unconstrained.nullity, 1)
        self.assertEqual(
            unconstrained.particular_solution,
            (Fraction(1), Fraction(2), Fraction(0), Fraction(-2)),
        )
        self.assertEqual(
            unconstrained.nullspace_basis,
            ((Fraction(0), Fraction(-1), Fraction(1), Fraction(0)),),
        )

    def test_every_member_has_beta_plus_gamma_two(self) -> None:
        unconstrained, _, _ = solve_inverse_square_systems()
        particular = unconstrained.particular_solution
        self.assertIsNotNone(particular)
        assert particular is not None
        self.assertEqual(particular[1] + particular[2], 2)
        for direction in unconstrained.nullspace_basis:
            self.assertEqual(direction[1] + direction[2], 0)

    def test_test_mass_linearity_selects_unique_newtonian_tuple(self) -> None:
        _, test_mass_linear, _ = solve_inverse_square_systems()
        self.assertEqual(test_mass_linear.status, "unique")
        self.assertEqual(
            test_mass_linear.particular_solution,
            (Fraction(1), Fraction(1), Fraction(1), Fraction(-2)),
        )

    def test_source_mass_linearity_selects_same_tuple(self) -> None:
        _, _, source_mass_linear = solve_inverse_square_systems()
        self.assertEqual(source_mass_linear.status, "unique")
        self.assertEqual(
            source_mass_linear.particular_solution,
            (Fraction(1), Fraction(1), Fraction(1), Fraction(-2)),
        )

    def test_serialization_is_byte_deterministic_and_exact(self) -> None:
        first = serialize_artifact(build_artifact())
        second = serialize_artifact(build_artifact())
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))
        self.assertTrue(first.endswith("\n"))
        self.assertIn('"unique_exponent_tuple": [\n        "1",', first)


if __name__ == "__main__":
    unittest.main()
