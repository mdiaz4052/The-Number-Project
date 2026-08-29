from fractions import Fraction
import unittest

from Discovery.monomial_constraints import (
    LinearConstraint,
    NamedFactor,
    reduced_row_echelon,
    solve_monomial_constraints,
)


class MonomialConstraintTests(unittest.TestCase):
    def test_exact_reduced_row_echelon_form(self) -> None:
        reduction = reduced_row_echelon(
            (
                (1, 2, 1),
                (2, 4, 2),
                (0, 1, 1),
            )
        )
        self.assertEqual(
            reduction.matrix,
            (
                (Fraction(1), Fraction(0), Fraction(-1)),
                (Fraction(0), Fraction(1), Fraction(1)),
                (Fraction(0), Fraction(0), Fraction(0)),
            ),
        )
        self.assertEqual(reduction.pivot_columns, (0, 1))

    def test_duplicate_factor_keys_are_rejected(self) -> None:
        factors = (NamedFactor("x", (1, 0)), NamedFactor("x", (0, 1)))
        with self.assertRaises(ValueError):
            solve_monomial_constraints(factors, (1, 1))

    def test_inconsistent_vector_lengths_are_rejected(self) -> None:
        factors = (NamedFactor("x", (1, 0)), NamedFactor("y", (1,)))
        with self.assertRaises(ValueError):
            solve_monomial_constraints(factors, (1, 1))

    def test_contradictory_constraints_are_reported(self) -> None:
        factors = (NamedFactor("x", (0,)),)
        solution = solve_monomial_constraints(
            factors,
            (0,),
            (
                LinearConstraint({"x": 1}, 0),
                LinearConstraint({"x": 1}, 1),
            ),
        )
        self.assertEqual(solution.status, "inconsistent")
        self.assertIsNone(solution.particular_solution)

    def test_floating_point_coefficients_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            NamedFactor("x", (0.5,))


if __name__ == "__main__":
    unittest.main()
