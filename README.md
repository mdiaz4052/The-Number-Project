# The Number Project

The Number Project is a persistent laboratory for formal mathematics, mathematical
physics, symbolic computation, and eventually machine-assisted mathematical discovery.
Milestone 1 establishes two small, machine-verifiable experiments:

1. a Lean 4 proof that `F = m * a` follows algebraically from explicitly stated
   Verlinde-style assumptions; and
2. a Python search that treats dimensional consistency as a hard constraint while
   looking for expressions with the dimensions of Newton's gravitational constant `G`.

The project is exploratory. A compiled implication is not experimental evidence for its
premises, and a dimensionally valid numerical coincidence is not evidence of a physical
law.

## Current machine-verifiable outputs

- `FormalPhysics/Verlinde.lean` contains
  `TheNumberProject.EntropicGravity.force_eq_mass_mul_acceleration`. Lean's kernel checks
  the proof from the stated hypotheses.
- `FormalPhysics/Dimensions.lean` checks the dimensions of the three input relations.
- `Discovery/dimensional_search.py` enumerates and ranks dimensionally valid candidates.
- `tests/` checks the Python dimension algebra, known Planck-unit rearrangements, and
  search invariants.
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
| **Numerical observation** | A computational pattern; dimensional validity and numerical proximity alone do not make it a law. |

## Track A: the algebraic core

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

## Track B: dimensional search

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
of the tabulated values. The program labels these as known Planck-unit rearrangements,
not discoveries. Expressions such as `hbar * c * m_e^-2` are dimensionally valid
comparisons but are not thereby physical identities.

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
Notes/                         Research decisions, literature, and tooling notes
tests/                         Python unit tests
.github/workflows/verify.yml   Lean, proof-audit, and Python CI
.devcontainer/                Reproducible Codespaces setup
```

The next formal-physics extension may study the additional assumptions behind the inverse
square law, but those assumptions are intentionally outside Milestone 1.
