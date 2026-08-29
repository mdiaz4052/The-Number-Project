# Exact inverse-square constraints

This experiment asks a deliberately narrow question: within the monomial search space

```text
G^alpha * M^beta * m^gamma * R^delta,
```

which rational exponents give the dimensions of force?

`solutions.json` is generated deterministically with exact `Fraction` arithmetic by:

```bash
python -m Discovery.inverse_square_search
```

Check that the committed artifact is current without rewriting it:

```bash
python -m Discovery.inverse_square_search --check
```

## Result

Matching mass, length, and time exponents gives

```text
-alpha + beta + gamma = 1
3*alpha + delta = 1
-2*alpha = -2
```

The exact row reduction therefore yields

```text
alpha = 1
delta = -2
beta + gamma = 2
```

or, parametrically,

```text
(alpha, beta, gamma, delta) = (1, 2, 0, -2) + t*(0, -1, 1, 0).
```

The remaining direction transfers a power between the two masses. Algebraically, it
multiplies a candidate by a power of the dimensionless ratio `m/M`. Setting `gamma = 1`
(linearity in the test mass) removes that freedom and gives the unique tuple
`(1, 1, 1, -2)`. Setting `beta = 1` (source-mass linearity) gives the same tuple.

## Epistemic status

- **Definition:** the four selected factors, the monomial form, rational exponent domain,
  factor ordering, and exact solver conventions.
- **Assumption:** test-mass or source-mass linearity when imposed.
- **Symbolic result:** exact dimensional constraints, rank, nullity, affine family, and
  constrained tuple recorded in `solutions.json`.
- **Numerical observation:** none; no measured values or numerical ranking are used.
- **Physical interpretation:** dimensional equations act like a filter. They force the
  power of `G` and the inverse-square power of `R`, but initially see `M` and `m` only as
  two quantities with the same mass dimension. A separate scaling principle is needed to
  say how force depends on each mass.

This is uniqueness only inside the chosen generator set and monomial model. Dimensional
analysis cannot determine an overall dimensionless coefficient and permits more general
dimensionless dependence such as `Phi(m/M)`. The computation does not prove that nature
must obey Newtonian gravity or empirically validate entropic gravity.

The related conditional physical-model derivation uses equations (3.6), (3.7), and
(3.10)--(3.12), plus spherical area, to derive (3.13) in §3.2 of Erik Verlinde's
original paper,
[*On the Origin of Gravity and the Laws of Newton*](https://arxiv.org/html/1001.0785v1#S3.SS2).
