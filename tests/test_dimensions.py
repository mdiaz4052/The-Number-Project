from fractions import Fraction
import unittest

from Discovery.dimensions import (
    ACTION,
    AREA,
    ENERGY,
    FORCE,
    GRAVITATIONAL_CONSTANT,
    LENGTH,
    MASS,
    TIME,
    Dimension,
)


class DimensionTests(unittest.TestCase):
    def test_g_dimension_is_exact(self) -> None:
        self.assertEqual(
            GRAVITATIONAL_CONSTANT,
            Dimension.from_mapping({"M": -1, "L": 3, "T": -2}),
        )
        self.assertEqual(str(GRAVITATIONAL_CONSTANT), "M^-1 L^3 T^-2")

    def test_action_dimension(self) -> None:
        self.assertEqual(ACTION, ENERGY * TIME)
        self.assertEqual(ACTION, MASS * LENGTH**2 / TIME)

    def test_force_and_area_dimensions(self) -> None:
        self.assertEqual(FORCE, Dimension.from_mapping({"M": 1, "L": 1, "T": -2}))
        self.assertEqual(AREA, LENGTH**2)

    def test_rational_powers_remain_exact(self) -> None:
        square_root_area = (LENGTH**2) ** Fraction(1, 2)
        self.assertEqual(square_root_area, LENGTH)

    def test_unknown_base_dimension_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Dimension.from_mapping({"unknown": 1})


if __name__ == "__main__":
    unittest.main()
