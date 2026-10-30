# Lanyon AI: overlap and opportunity scan

Scan date: 2026-10-30. Sources: the public `lanyonai` GitHub organization (shallow
clones of `MaxwellEquations` and `BurgersEquation` were read, not executed) and press
coverage of the company. `lanyon.ai` itself was unreachable from this session's network
policy, so the linked "technical deep dive" was not read.

## What Lanyon does

Tagline: "Formal Verification for a Computable Universe." Co-founded by Jonathan Gorard,
Ammar Hakim, and James Juno (Princeton / PPPL lineage; Gkeyll plasma code).

Reported pipeline: an LLM writes a specification in a Racket DSL (state, parameters,
fluxes, wave speeds, diffusive fluxes, numerical-flux "waves"). Deterministic generators
expand that one spec into (a) C solver code over `double` and (b) Lean 4 + Mathlib
theorems over `Real`. If the Lean proofs fail, no implementation is emitted. The stated
target failure mode is "misformalization": a proof that type-checks but describes
something other than the implementation.

Public repos: Maxwell (incl. perfectly hyperbolic), GR-Maxwell, advection-diffusion,
Burgers, electrostatic Vlasov, compressible Euler, ideal MHD; finite-volume and
p=1/p=2 discontinuous Galerkin; 1D-3D.

## What the published Lean theorems actually state (observed)

Per solver, a fixed family of `x*` theorems: `Hyperbolicity`, `WaveStability`,
`DiffusiveFluxConsistency`, `WaveConsistency`, `WaveJumpCondition`,
`Left/RightFluctuationsConsistent`, `FluxConservative`, reconstruction consistency,
linearity preservation and symmetry (DG adds modal/volume-integral analogues).
No `sorry`. All quantities are `Real`.

Observations from `MaxwellEquations/proofs/maxwell_1d.lean`:

1. **`xHyperbolicity` is vacuous as stated.** It proves `∃ r : Real, r = lambda_i` for
   each listed eigenvalue expression, discharged by `rfl`. Any real expression satisfies
   this. The flux Jacobian (`xFluxJacobianExprs`) is defined but is never referenced by
   any theorem, so nothing ties the listed `lambda_i` to the Jacobian's actual spectrum,
   and nothing asserts a complete real eigenbasis.
2. **`xWaveStability` inherits that gap.** It shows `|mu_i| ≥ |lambda_i|` (wave-speed
   estimate dominates the listed eigenvalues). If the spec listed wrong eigenvalues, both
   theorems could still pass.
3. **No floating-point semantics.** Lean reasons over `Real`; the C uses `double`. The
   Lean-to-C link is the shared generator, not a refinement proof. Round-off, overflow
   and CFL/time-step choice are outside the theorems. The published C `main` contains
   only the comment `// Insert simulation drivers here.`, so no time integrator ships.
4. **No units.** Specs carry no physical dimensions; e.g. Maxwell's `c*c*Bz` flux is
   unit-correct only by convention.

These are claims about the theorem statements as published, not about the C code's
numerical quality, which was not run.

## Overlap with The Number Project

| Theme | Lanyon | This repository |
|---|---|---|
| Lean 4 + Mathlib over `Real` for physics | yes (scheme properties) | yes (conditional derivations, estimator) |
| Explicit hypotheses vs. claims | implicit in DSL | central (epistemic labels) |
| Misformalization concern | headline problem | same concern as target leakage / vacuity |
| Mutation / adversarial testing of the checker | not visible | core practice (planted mutants must be killed) |
| Dimensional analysis | absent | exact rational dimension algebra |
| Empirical / numerical validation | screencaps only | preregistered numerical studies |
| Float-level guarantees | absent | absent |

Follow-up: [`Explorations/LanyonSpecAudit`](../Explorations/LanyonSpecAudit/README.md) tests
these observations with preregistered mutants.

## Candidate enhancements and expansions

- **Spec-adequacy mutation audit**: plant wrong physics (wrong eigenvalue, sign-flipped
  flux, wrong wave speed) into a Lanyon-shaped spec and count which mutants the theorem
  family kills. Directly measures "misformalization" exposure.
- **Strengthened theorem**: replace the vacuous hyperbolicity statement with
  `det(A - lambda_i I) = 0` plus eigenvector completeness for one small system.
- **Units layer**: type-check DSL flux and wave-speed expressions with
  `Discovery/dimensions.py`.
- **Preregistered convergence study**: compile a solver and test the claimed order
  (2nd for FV/p=1, 3rd for p=2) against exact solutions.
- **Float bridge**: a bounded round-off or invariant check for one update step.
