from __future__ import annotations

from decimal import Decimal, localcontext
import unittest

from Discovery.hust_2018_aaf_measurement_models import build_hust_aaf_model


SCOPES = ("AAF-I", "AAF-II", "AAF-III")


class HUSTDecimalHygieneTests(unittest.TestCase):
    def test_terminal_comparison_delta_uses_declared_precision_50(self):
        for scope in SCOPES:
            with self.subTest(scope=scope):
                model = build_hust_aaf_model(scope)
                quantities = {quantity.identifier: quantity for quantity in model.quantities}
                g_hat = quantities[f"{scope}:G_hat"].value
                published_g = quantities[f"{scope}:published_G"].value
                comparison_delta = quantities[f"{scope}:comparison_delta"].value
                self.assertIsNotNone(g_hat)
                self.assertIsNotNone(published_g)
                self.assertIsNotNone(comparison_delta)
                assert g_hat is not None
                assert published_g is not None
                assert comparison_delta is not None
                with localcontext() as context:
                    context.prec = 50
                    expected = g_hat - published_g
                self.assertEqual(comparison_delta, expected)

    def test_default_precision_28_is_not_the_comparison_contract(self):
        model = build_hust_aaf_model("AAF-I")
        quantities = {quantity.identifier: quantity for quantity in model.quantities}
        g_hat = quantities["AAF-I:G_hat"].value
        published_g = quantities["AAF-I:published_G"].value
        comparison_delta = quantities["AAF-I:comparison_delta"].value
        assert g_hat is not None
        assert published_g is not None
        assert comparison_delta is not None
        with localcontext() as context:
            context.prec = 28
            default_precision_delta = g_hat - published_g
        self.assertNotEqual(comparison_delta, default_precision_delta)


if __name__ == "__main__":
    unittest.main()
