from fractions import Fraction
import unittest

from Discovery.dependency_definitions import (
    DEFAULT_DEPENDENCY_CATALOG,
    DependencyDefinition,
    build_dependency_catalog,
)
from Discovery.dimensions import LENGTH, MASS
from Discovery.planck_identities import normalize_exponent_signature


class DependencyDefinitionTests(unittest.TestCase):
    def test_default_atomic_basis_has_the_declared_model_relative_endpoints(self) -> None:
        self.assertEqual(
            DEFAULT_DEPENDENCY_CATALOG.atomic_basis,
            ("G", "c", "hbar", "k_B", "m_e", "m_p", "m_u"),
        )

    def test_four_planck_definitions_use_exact_fraction_exponents(self) -> None:
        expected = {
            "l_P": (("G", Fraction(1, 2)), ("c", Fraction(-3, 2)), ("hbar", Fraction(1, 2))),
            "m_P": (("G", Fraction(-1, 2)), ("c", Fraction(1, 2)), ("hbar", Fraction(1, 2))),
            "t_P": (("G", Fraction(1, 2)), ("c", Fraction(-5, 2)), ("hbar", Fraction(1, 2))),
            "T_P": (
                ("G", Fraction(-1, 2)),
                ("c", Fraction(5, 2)),
                ("hbar", Fraction(1, 2)),
                ("k_B", Fraction(-1)),
            ),
        }
        for key, signature in expected.items():
            with self.subTest(key=key):
                normalized = normalize_exponent_signature(signature)
                self.assertEqual(
                    DEFAULT_DEPENDENCY_CATALOG.definitions[key].expansion,
                    normalized,
                )
                self.assertEqual(
                    DEFAULT_DEPENDENCY_CATALOG.expanded_definitions[key],
                    normalized,
                )

    def test_recursive_expansion_is_exact_and_normalizes_cancellation(self) -> None:
        catalog = build_dependency_catalog(
            (
                DependencyDefinition("a"),
                DependencyDefinition("b", (("a", 2),)),
                DependencyDefinition("c", (("b", Fraction(1, 2)),)),
            ),
            {"a": MASS, "b": MASS**2, "c": MASS},
            required_keys=("a", "b", "c"),
        )
        self.assertEqual(catalog.expanded_definitions["c"], (("a", Fraction(1)),))
        cancellation = catalog.expand_signature((("a", -1), ("c", 1)))
        self.assertEqual(cancellation.signature, ())
        self.assertTrue(cancellation.is_fully_resolved)

    def test_catalog_is_read_only(self) -> None:
        with self.assertRaises(TypeError):
            DEFAULT_DEPENDENCY_CATALOG.definitions["new"] = DependencyDefinition("new")

    def test_malformed_definition_terms_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DependencyDefinition("x", (("a", 1), ("a", 2)))
        with self.assertRaises(TypeError):
            DependencyDefinition("x", (("a", 0.5),))
        with self.assertRaises(TypeError):
            DependencyDefinition("x", (("a", True),))
        with self.assertRaises(ValueError):
            DependencyDefinition("x", (("a", 0),))

    def test_duplicate_catalog_keys_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_dependency_catalog(
                (DependencyDefinition("x"), DependencyDefinition("x")),
                {"x": MASS},
            )

    def test_unknown_references_and_cycles_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_dependency_catalog(
                (DependencyDefinition("x", (("missing", 1),)),),
                {"x": MASS},
            )
        with self.assertRaises(ValueError):
            build_dependency_catalog(
                (
                    DependencyDefinition("a", (("b", 1),)),
                    DependencyDefinition("b", (("a", 1),)),
                ),
                {"a": MASS, "b": MASS},
            )

    def test_dimensionally_inconsistent_definition_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_dependency_catalog(
                (
                    DependencyDefinition("a"),
                    DependencyDefinition("x", (("a", 1),)),
                ),
                {"a": MASS, "x": LENGTH},
            )

    def test_missing_required_coverage_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_dependency_catalog(
                (DependencyDefinition("a"),),
                {"a": MASS},
                required_keys=("a", "missing"),
            )


if __name__ == "__main__":
    unittest.main()
