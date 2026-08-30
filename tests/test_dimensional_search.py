from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from Discovery.constants import (
    GRAVITATIONAL_CONSTANT_G,
    PLANCK_MASS,
    REDUCED_PLANCK_CONSTANT,
    SPEED_OF_LIGHT,
)
from Discovery.dimensional_search import (
    allowed_powers,
    main,
    render_candidates,
    search_candidates,
    write_candidates,
)


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

    def test_default_bounded_search_still_returns_twenty_one_candidates(self) -> None:
        self.assertEqual(len(search_candidates()), 21)

    def test_repeated_csv_rendering_is_byte_deterministic(self) -> None:
        candidates = search_candidates()
        first = render_candidates(candidates)
        second = render_candidates(search_candidates())
        self.assertEqual(first, second)
        self.assertEqual(first.count(b"\r\n"), 22)

    def test_check_accepts_a_current_artifact(self) -> None:
        candidates = search_candidates()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.csv"
            write_candidates(path, candidates)
            with patch("sys.argv", ["dimensional_search", "--check", "--output", str(path)]):
                with redirect_stdout(io.StringIO()) as output:
                    main()
            self.assertIn("artifact is current", output.getvalue())

    def test_check_rejects_a_stale_artifact_without_overwriting_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidates.csv"
            original = b"stale artifact\r\n"
            path.write_bytes(original)
            with patch("sys.argv", ["dimensional_search", "--check", "--output", str(path)]):
                with redirect_stderr(io.StringIO()) as error:
                    with self.assertRaises(SystemExit) as raised:
                        main()
            self.assertEqual(raised.exception.code, 1)
            self.assertEqual(path.read_bytes(), original)
            self.assertIn("regenerate without --check", error.getvalue())

    def test_check_rejects_a_missing_artifact_without_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.csv"
            with patch("sys.argv", ["dimensional_search", "--check", "--output", str(path)]):
                with redirect_stderr(io.StringIO()) as error:
                    with self.assertRaises(SystemExit) as raised:
                        main()
            self.assertEqual(raised.exception.code, 1)
            self.assertFalse(path.exists())
            self.assertIn(str(path), error.getvalue())


if __name__ == "__main__":
    unittest.main()
