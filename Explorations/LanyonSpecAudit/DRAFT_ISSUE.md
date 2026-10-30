<!--
DRAFT ONLY. Not posted anywhere. Whether, when, where and under what name to share it
is entirely the repository owner's decision. Nothing in this repository posts it.
-->

# Draft: published `xHyperbolicity` does not constrain the declared eigenvalues

**Suggested target:** `lanyonai/MaxwellEquations` (same pattern in `BurgersEquation`).

Thank you for publishing the generated Lean alongside the solvers; it made this check
possible.

## Observation

In `proofs/maxwell_1d.lean` (commit `801558f`), `xHyperbolicity` states

```lean
(∃ r1 : Real, r1 = (xFluxJacobianEigenExprs C P U).lambda1) ∧ ... ∧
(∃ r6 : Real, r6 = (xFluxJacobianEigenExprs C P U).lambda6)
```

and is proved by `rfl`. This holds for any real-valued expression. `xFluxJacobianExprs` is
defined, but no theorem in the file refers to it, so nothing connects the declared
eigenvalues to the declared Jacobian. Nothing connects the Jacobian to the flux either.
`xWaveStability` compares wave speeds only against the declared eigenvalues.

## Consequence (reproducible)

We compiled your unchanged theorem family against deliberately wrong specs. Lean
v4.33.1, Mathlib at a fixed pin. Your theorems still go through for, among others:

- a Maxwell spec where the `flux_Ey` sign is flipped consistently in the flux, the
  Lax-Friedrichs waves and the Jacobian. The system then has eigenvalues `±i c`, so it is
  not hyperbolic, while the listed eigenvalues stay `±c`;
- a Maxwell spectrum of `-c, -c, -c, -c, 0, 0`;
- a Jacobian entry `c` in place of `c²`;
- a Burgers spec whose flux is `f³/3` while the Jacobian, eigenvalue and wave speed
  still describe `f²/2`.

Every single-field sign flip of a Jacobian entry or declared eigenvalue (10 of 10 across
both files) also passes.
Harness, mutants and per-variant results: `<link to the repository>`.

## Suggested strengthening

Three statements, each proved for your unmutated files, catch all of the above:

1. **Jacobian is the derivative of the flux:** `HasDerivAt` per entry.
2. **Strong hyperbolicity with the declared spectrum:** `∃ R L, L * R = 1 ∧ R * L = 1 ∧
   J * R = R * diagonal λ`, under the spec's `parameters-assumptions` (`c > 0`). The
   current Lean theorems drop that assumption, and at `c = 0` the Maxwell Jacobian is
   not diagonalizable.
3. **Lax-Friedrichs speed dominates `|λ_i|` at both states.**

Because each statement is generated from the same spec, a wrong spec has no proof to
emit. Since proof failure blocks emission in your pipeline, that is enough.

## Smaller notes

- Several theorems fail on true statements because of tactic brittleness. Examples:
  `xFluxConservative` when the dissipation speed is scaled by 1/2, and `xWaveStability`
  when `|mu| = 2|lambda|`. Such false alarms would block correct specs.
- The published C `main` has no time-stepping driver, so the wave-speed estimates are
  not used by any shipped code path.
