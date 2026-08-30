# Inverse-square exponent walkthrough

This walkthrough explains exactly what Milestone 2's dimensional calculation does—and
what it cannot do. The goal is not to assume Newton's force law and rediscover it by
notation. The narrower question is:

> Within one selected family of monomials built from `G`, source mass `M`, test mass `m`,
> and radius `R`, which exponents give the dimensions of force?

## 1. What the candidate monomial means

The selected candidate form is

```math
G^\alpha M^\beta m^\gamma R^\delta.
```

A **monomial** here means a product of chosen factors, each raised to one numerical
power. The letters `alpha`, `beta`, `gamma`, and `delta` are those powers:

- `alpha` says how many powers of `G` appear;
- `beta` says how many powers of source mass `M` appear;
- `gamma` says how many powers of test mass `m` appear; and
- `delta` says how many powers of radius `R` appear.

They are not masses, constants, or other physical quantities. Together they form the
**exponent vector** `(alpha, beta, gamma, delta)`. An exponent of `0` removes a factor;
an exponent of `-2` puts its square in the denominator. For example,
`(1, 1, 1, -2)` means `G * M * m / R^2`.

Choosing this monomial and these four generators defines the model class being searched.
Dimensional analysis does not prove that this was the only possible model class.

## 2. Turn dimensions into equations

For this calculation only mass, length, and time slots are nonzero:

```text
[G] = (-1, 3, -2)
[M] = ( 1, 0,  0)
[m] = ( 1, 0,  0)
[R] = ( 0, 1,  0)
[F] = ( 1, 1, -2)
```

Raising a quantity to a power multiplies every component of its dimension vector by that
power. Multiplying quantities adds their dimension vectors. Therefore the candidate has
dimension

```math
\alpha[-1,3,-2]+\beta[1,0,0]+\gamma[1,0,0]+\delta[0,1,0].
```

Matching that vector to force gives one equation per row:

```text
mass:    -alpha + beta + gamma =  1
length:   3alpha + delta       =  1
time:    -2alpha               = -2
```

The time equation immediately gives `alpha = 1`. Substituting that into the length
equation gives `delta = -2`. Substituting it into the mass equation gives only
`beta + gamma = 2`.

Why does dimensional analysis not fix `beta` and `gamma` separately? In the dimension
matrix, the two mass columns are identical:

```text
                 G   M   m   R
mass row        -1   1   1   0
length row       3   0   0   1
time row        -2   0   0   0
```

Units can see that `M` and `m` both contribute one mass power. Units cannot see their
different physical roles as “source body” and “test body.”

## 3. Particular solution plus nullspace direction

One solution is

```text
x_particular = (1, 2, 0, -2).
```

It is called a **particular solution** because it is one concrete point satisfying the
nonzero target equations. It is not yet the only solution.

The vector

```text
x_null = (0, -1, 1, 0)
```

is a **nullspace direction**: adding any multiple of it changes none of the three
dimension totals. Its contributions from `M` and `m` cancel because those columns are
identical.

For a rational parameter `t`, scalar multiplication is componentwise:

```math
t(0,-1,1,0)=(0,-t,t,0).
```

Now add component by component:

```math
\begin{aligned}
(1,2,0,-2)+t(0,-1,1,0)
  &= (1,2,0,-2)+(0,-t,t,0)\\
  &= (1+0,2-t,0+t,-2+0)\\
  &= (1,2-t,t,-2).
\end{aligned}
```

This describes **all** solutions because exact row reduction finds one free variable and
one independent null direction:

```text
x = x_particular + t*x_null.
```

The solution set is an **affine line**: a one-dimensional linear direction translated so
that it passes through `x_particular`. It is not a linear subspace because it does not
pass through the zero vector. The zero exponent vector would be dimensionless, not a
force, and therefore does not satisfy the target equation.

There is also a direct physical reading of the free direction. Starting from the
particular monomial,

```math
\frac{GM^2}{R^2}\left(\frac{m}{M}\right)^t
=\frac{G M^{2-t}m^t}{R^2}.
```

The ratio `m/M` is dimensionless. Multiplying by any power of a dimensionless ratio
cannot change units, which is precisely why dimensional analysis leaves `t` free.

## 4. Two different meanings of “linear”

Two uses of the word **linear** must be kept separate.

First, the dimensional equations are linear **in the exponent variables**. For example,
`-alpha + beta + gamma = 1` contains no products such as `alpha*beta` and no squared
unknowns such as `alpha^2`. That is why ordinary row reduction applies.

Second, test-mass linearity is a **physical scaling premise** about the force itself. If
the test mass is rescaled while everything else stays fixed,

```math
m\mapsto\lambda m,
```

then the candidate scales as

```math
F\mapsto\lambda^\gamma F.
```

Physical proportionality to the test mass requires instead

```math
F\mapsto\lambda F.
```

Therefore `gamma = 1`. The already established dimensional condition
`beta + gamma = 2` then gives `beta = 1`, selecting

```text
(alpha, beta, gamma, delta) = (1, 1, 1, -2).
```

The universal-free-fall motivation says the same thing from acceleration. If

```math
a=F/m,
```

then a candidate with test-mass power `gamma` gives acceleration a remaining factor
`m^(gamma-1)`. Requiring the predicted acceleration not to depend on the test body's mass
again selects `gamma = 1`. This is additional physical information; it is not hidden
inside the units.

## 5. What has and has not been established

- **Definition:** the factors `G, M, m, R`, their order, rational exponent domain, and
  monomial form are selected in advance.
- **Symbolic result:** within that selection, dimensions imply `alpha = 1`,
  `delta = -2`, and `beta + gamma = 2` exactly.
- **Assumption:** proportional scaling with test mass supplies `gamma = 1`.
- **Lean theorem:** Lean checks that the stated dimensional equations and scaling premise
  imply the claimed exponent equalities. It proves a conditional implication.
- **Physical interpretation:** the result explains why units alone distinguish the power
  of `G` and `R` but not the roles of two masses.
- **Numerical observation:** none is used in this experiment.

Dimensional analysis still cannot determine an overall dimensionless coefficient. It
also cannot exclude a dimensionless function such as

```math
F=C\,\frac{GMm}{R^2}\,\Phi(m/M),
```

where `C` is dimensionless. More broadly, it cannot prove that nature must use the chosen
monomial or generator set. Physical scaling adds information beyond units, while
experiments are needed to establish whether the premises describe nature.

When VS Code's Lean Infoview says **“Goals accomplished!”**, it means the proof term has
no remaining mathematical goals under the displayed hypotheses. It does not mean Lean
experimentally established those hypotheses or the associated physical model.

## 6. Code map and commands

| Purpose | Location |
|---|---|
| Conditional inverse-square physical-model theorem | `TheNumberProject.EntropicGravity.force_eq_gravitationalConstant_mul_masses_div_radius_sq` in `FormalPhysics/InverseSquare.lean` |
| Dimensional exponent theorem | `force_dimension_exponent_constraints` in `FormalPhysics/InverseSquare.lean` |
| Exponent selection with test-mass linearity | `force_dimension_exponents_unique_of_testMass_linear` in `FormalPhysics/InverseSquare.lean` |
| Reusable exact row-reduction solver | `solve_monomial_constraints` in `Discovery/monomial_constraints.py` |
| Inverse-square experiment and assumptions | `Discovery/inverse_square_search.py` |
| Deterministic result artifact | `Experiments/InverseSquare/solutions.json` |

From the repository root, run:

```bash
lake build --wfail
python3 -m unittest discover -s tests -v
python3 -m Discovery.inverse_square_search --check
python3 -m Discovery.inverse_square_search --output /tmp/inverse-square-solutions.json
```

For an interactive Lean reading, open `FormalPhysics/InverseSquare.lean`. Place the VS
Code cursor immediately after the `:= by` line of `force_dimension_exponent_constraints`
to see its initial hypotheses and goal in Infoview. Move the cursor down one tactic at a
time to watch the goals split and disappear. Repeat this at
`force_dimension_exponents_unique_of_testMass_linear` to see exactly where the separate
premise `hTestMassLinear : gamma = 1` enters.
