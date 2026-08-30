# The Number Project

The Number Project is a persistent laboratory for formal mathematics, mathematical
physics, symbolic computation, and eventually machine-assisted mathematical discovery.
Milestone 1 established two small, machine-verifiable experiments:

1. a Lean 4 proof that `F = m * a` follows algebraically from explicitly stated
   Verlinde-style assumptions; and
2. a Python search that treats dimensional consistency as a hard constraint while
   looking for expressions with the dimensions of Newton's gravitational constant `G`.

Milestone 2 builds on that foundation with:

1. a Lean-checked conditional derivation of `F = G * M * m / R^2` from the explicit
   spherical-screen equations in §3.2 of Verlinde's paper; and
2. an exact rational constraint solver that explains which monomial exponents follow
   from dimensions alone and which require an added scaling assumption.

Milestone 2.1 hardens and translates those results by:

1. certifying four Planck-unit controls symbolically in Lean, without equating rounded
   CODATA decimals;
2. replacing Python's anonymous signature set with a validated, traceable identity
   catalog;
3. recording paired Lean/Python dimension-vector contracts; and
4. adding a learner-facing inverse-square exponent walkthrough.

The project is exploratory. A compiled implication is not experimental evidence for its
premises, and a dimensionally valid numerical coincidence is not evidence of a physical
law.

## Current machine-verifiable outputs

- `FormalPhysics/Verlinde.lean` contains
  `TheNumberProject.EntropicGravity.force_eq_mass_mul_acceleration`. Lean's kernel checks
  the proof from the stated hypotheses.
- `FormalPhysics/InverseSquare.lean` contains the principal inverse-square theorem, its
  acceleration corollary, and exact rational proofs of the exponent-selection result.
- `FormalPhysics/PlanckUnits.lean` proves four symbolic rearrangements of the conventional
  Planck length, mass, and time definitions as dependent controls.
- `FormalPhysics/Dimensions.lean` checks the dimensions of both milestones' relations.
- `Discovery/dimensional_search.py` enumerates and ranks dimensionally valid candidates.
- `Discovery/planck_identities.py` gives each certified Python control a stable identity,
  dependency explanation, and corresponding Lean theorem name.
- `Discovery/monomial_constraints.py` exposes exact row reduction and affine solutions;
  `Discovery/inverse_square_search.py` applies it to `(G, M, m, R)`.
- `tests/` checks the Python dimension algebra, known Planck-unit rearrangements, and
  both constrained and unconstrained inverse-square systems.
- GitHub Actions builds Lean with the mathlib cache, audits the resulting declarations,
  and runs the Python tests.

## Epistemic labels

These labels are part of the project's design, not merely documentation style.

| Label | Meaning in this repository |
|---|---|
| **Definition** | A chosen mathematical representation or name. It makes no empirical claim. |
| **Assumption / hypothesis** | An input accepted temporarily inside a stated model or theorem. |
| **Theorem** | A proposition whose proof term is accepted by Lean's kernel from its hypotheses. |
| **Conjecture** | A precise proposed relationship for which no proof is currently supplied. |
| **Symbolic result** | Exact output of a declared computational model, including any free parameters. |
| **Numerical observation** | A computational pattern; dimensional validity and numerical proximity alone do not make it a law. |
| **Physical interpretation** | A cautious reading of a result; not an additional proof or measurement. |

## Track A: conditional Lean derivations

### Milestone 1: force and acceleration

The formal target follows equations (3.6)--(3.8) of Erik Verlinde's 2010 paper,
[On the Origin of Gravity and the Laws of Newton](https://arxiv.org/abs/1001.0785):

```text
F * delta_x = T * delta_S
delta_S = (2 * pi * k_B * m * c / hbar) * delta_x
T = hbar * a / (2 * pi * k_B * c)
```

The Lean theorem treats those equations as named hypotheses. It also requires the
displacement and the three cancelling constants to be nonzero. Nothing in the theorem
claims that the entropy-displacement postulate, the entropic-force interpretation, or the
application of the Unruh relation is physically correct. Lean proves the conditional
statement: **if these equations and side conditions hold over the real numbers, then
`F = m * a`.**

`FormalPhysics/Constants.lean` defines only a container for the three scalar constants.
It deliberately places no model equation inside the definition. `Dimensions.lean` uses
the seven SI base dimensions as an integer-exponent vector and separately checks that the
relations are dimensionally homogeneous.

### Milestone 2: the inverse-square relation

The new formal target uses equations (3.6), (3.7), and (3.10)--(3.12), plus the spherical
area relation, to derive equation (3.13) of
[§3.2 in the original paper](https://arxiv.org/html/1001.0785v1#S3.SS2):

```text
delta_S = (2 * pi * k_B * m * c / hbar) * delta_x
F * delta_x = T * delta_S
N = A * c^3 / (G * hbar)
E = (1/2) * N * k_B * T
E = M * c^2
A = 4 * pi * R^2
```

`TheNumberProject.EntropicGravity.force_eq_gravitationalConstant_mul_masses_div_radius_sq`
treats every displayed equation as a named hypothesis and concludes
`F = G * M * m / R^2`. Its only nonzero premises are `delta_x`, `c`, `hbar`, `G`, and
`R`: those are the quantities used as denominators or genuinely cancelled by the proof.
The masses, temperature, bit count, area, energy, entropy change, force, and even `k_B`
need no nonzero premise.

The Unruh-temperature relation from Milestone 1 is intentionally absent. Verlinde says
at the start of §3.2 that it is not needed for this argument. Equation (3.10) introduces
`G` as the proportionality constant connecting area and information count; only after the
algebra is completed is it identified with Newton's gravitational constant.

The theorem is therefore conditional. **Assumptions** include the spherical screen,
holographic bit count, equipartition, the adopted mass-energy relation, the entropy-
displacement postulate, and entropic work. The **theorem** is the real-number implication
from those assumptions. Lean does not prove that the model's premises are physically
correct or that the result empirically supports entropic gravity.

The file also composes an assumed `F = m * a` equality with the inverse-square equality:
for a nonzero test mass it obtains `a = G * M / R^2`. This corollary does not independently
validate either input relation.

### Milestone 2.1: symbolic Planck-unit controls

`FormalPhysics/PlanckUnits.lean` takes the conventional squared definitions

```text
l_P^2 = hbar * G / c^3
m_P^2 = hbar * c / G
t_P^2 = hbar * G / c^5
```

as explicit theorem hypotheses. Positivity selects the conventional positive-root branch
where two squared expressions must be compared and supplies the nonzero denominators used
by the algebra. Lean then certifies:

```text
G = c^2 * l_P / m_P
G = hbar * c / m_P^2
G = c^3 * t_P / m_P
G = c^3 * l_P^2 / hbar
```

These are **dependent controls**, not new determinations of `G`: Planck length, mass, and
time were defined using `G` in the first place. Lean proves the symbolic rearrangements;
it does not assert equality among rounded measured decimals. The Python ratios are close
to one rather than exactly one because the checked-in Planck-unit values have finite
precision and inherit uncertainty from measured `G`.

The exact cross-language base ordering and literal shared vectors are recorded in
[`Notes/DimensionContract.md`](Notes/DimensionContract.md).

## Track B: exact dimensional computation

### Milestone 1: bounded search for the dimensions of G

The search represents a dimension as an exact seven-component vector over rational
exponents, ordered as mass, length, time, electric current, temperature, amount of
substance, and luminous intensity. Thus:

```text
[G] = M^-1 L^3 T^-2
```

The default search:

- excludes `G` itself from the generating constants;
- uses products of at most three distinct constants;
- uses nonzero integer powers from `-3` through `3`;
- rejects every expression whose dimension vector differs from `[G]` exactly; and
- records expression, exponents, SI magnitude, ratio to measured `G`, logarithmic
  magnitude difference, complexity, number of constants, and a cautious classification.

Planck length, mass, and time are included intentionally as controls. Expressions such as
`hbar * c * m_P^-2` should reconstruct `G` up to the rounding and measurement uncertainty
of the tabulated values. The structured catalog certifies exactly four selected controls
as `known Planck-unit identity`; other Planck-containing candidates retain the more
cautious `Planck-unit rearrangement` label. Neither label is a discovery claim.
Expressions such as `hbar * c * m_e^-2` are dimensionally valid comparisons but are not
thereby physical identities.

The constants are from the
[NIST 2022 CODATA complete listing](https://physics.nist.gov/cuu/Constants/Table/allascii.txt).
The exact SI defining constants are cross-checked against the
[BIPM SI defining constants](https://www.bipm.org/en/measurement-units/si-defining-constants).

Run the search from the repository root:

```bash
python -m Discovery.dimensional_search
```

It prints the leading candidates and regenerates
`Experiments/GCoincidences/candidates.csv`. Use `--help` to see bounded rational-power,
factor-count, and output options. The implementation uses only Python's standard library.

### Milestone 2: exact monomial constraints

For the explicitly chosen candidate form

```text
G^alpha * M^beta * m^gamma * R^delta,
```

matching the dimensions of force gives three independent equations:

```text
-alpha + beta + gamma = 1
3*alpha + delta = 1
-2*alpha = -2
```

Exact row reduction yields

```text
alpha = 1,  delta = -2,  beta + gamma = 2.
```

The particular solution `(1, 2, 0, -2)` plus nullspace direction `(0, -1, 1, 0)`
describes the whole family. That direction shifts a power between `M` and `m`, or
equivalently multiplies by a power of the dimensionless ratio `m/M`. Dimensional analysis
cannot distinguish the two masses because they have the same SI dimension.

The extra **assumption** `gamma = 1`—linearity in the test mass—selects the unique tuple
`(1, 1, 1, -2)` within this four-factor monomial model. Source-mass linearity selects the
same tuple. This uniqueness is not global: a dimensionless coefficient or function such
as `Phi(m/M)` remains possible, and the factor set and monomial form define the search
space rather than follow from dimensional analysis.

Regenerate or check the exact artifact with:

```bash
python -m Discovery.inverse_square_search
python -m Discovery.inverse_square_search --check
```

The machine-readable rank, nullity, RREF, affine family, constraints, exact tuple, and
limitations are recorded in `Experiments/InverseSquare/solutions.json`. There is no
numerical fitting or candidate ranking in this experiment. The same exponent implications
are separately proved over `ℚ` in Lean.

For a step-by-step explanation of monomials, exponent vectors, the affine solution line,
the nullspace direction, and the separate test-mass scaling premise, read
[`Notes/InverseSquareWalkthrough.md`](Notes/InverseSquareWalkthrough.md).

## Lean and mathlib setup

The repository pins the matching stable releases Lean `v4.33.1` and mathlib `v4.33.1`.
`lake-manifest.json` additionally fixes mathlib and its transitive dependencies to exact
commits. Mathlib's cache command downloads precompiled artifacts, avoiding a local rebuild
of the full library.

The repository's development-container configuration installs Elan and the official Lean
extension. Its first-run hook also runs `lake update`, which synchronizes the pinned
dependencies and invokes mathlib's precompiled-cache download.

To repeat that step manually, open the menu at the upper left, choose **Terminal -> New
Terminal**, and run:

```bash
lake update
```

Successful output normally shows repositories being cloned or updated, followed by a
cache download summary. Then verify the project with `lake build`.

Run the Python checks with:

```bash
python -m unittest discover -s tests -v
```

## Repository map

```text
FormalPhysics/                 Lean definitions and proofs
Discovery/                     Reusable Python search components
Experiments/GCoincidences/     Reproducible search output and interpretation
Experiments/InverseSquare/     Exact constraint artifact and interpretation
Notes/                         Research decisions, literature, and tooling notes
tests/                         Python unit tests
.github/workflows/verify.yml   Lean, proof-audit, and Python CI
.devcontainer/                Reproducible Codespaces setup
```

Promising extensions belong in `Notes/ToolingRoadmap.md`; this milestone intentionally
stops before general relativity, empirical fitting, modified gravity, neural symbolic
regression, LeanDojo integration, or a general physical-units library.
