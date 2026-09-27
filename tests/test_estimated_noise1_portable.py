"""Engineering checks for the detached exp-provenance verifier correction."""
from decimal import Decimal, localcontext
import math
import unittest
from unittest.mock import patch
from Discovery.estimated_noise1_portable_verifier import exp_binding


class PortableExpBindingTests(unittest.TestCase):
    def test_independent_oracle_and_one_ulp_boundary(self):
        # Engineering arguments, not scientific observed outcomes.
        for x in (-10., -1., 0., 0.25, 1., 10.):
            with localcontext() as ctx:
                ctx.prec = 80
                exact = Decimal.from_float(x).exp()
                nearest = float(exact)
                unit = Decimal.from_float(math.ulp(nearest))
                for direction in (-math.inf, math.inf):
                    v = nearest
                    for _ in range(4):
                        accepted = abs(Decimal.from_float(v)-exact) <= unit
                        # A broken/platform-dependent math.exp is not an oracle.
                        with patch('math.exp', side_effect=AssertionError('libm exp called')):
                            if accepted: exp_binding(v, x)
                            else:
                                with self.assertRaisesRegex(ValueError, 'one ULP'): exp_binding(v, x)
                        v = math.nextafter(v, direction)

    def test_malformed_and_wrong_stream_value_rejected(self):
        for value in (True, 1, 0., -1., float('nan'), float('inf')):
            with self.assertRaises(ValueError): exp_binding(value, 0.)
        with self.assertRaisesRegex(ValueError, 'one ULP'): exp_binding(2., 0.)


if __name__ == '__main__': unittest.main()
