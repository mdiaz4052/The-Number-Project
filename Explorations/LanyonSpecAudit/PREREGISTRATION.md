# Preregistration: Lanyon spec-adequacy mutation audit (LSA-1)

Written 2026-10-30, before any Lean compile of any variant. The commit that adds this
file freezes the mutant definitions in `audit.py` and the mathematical content of S1 to S3
below. The Lean text of S1 to S3 in `strengthened/` may change only to make the statements
elaborate, or to make their proofs go through on the two unmutated controls (B0, M0). Any
such change is listed in `README.md`, and the final statement text is committed before
any mutant is compiled.

## Question

Lanyon AI publishes, for each generated solver, a fixed family of Lean theorems. Do
those theorems constrain the physics they are meant to certify? Concretely: when a spec
is changed so that it describes wrong physics, does at least one published theorem stop
being provable?

## Objects

- Pinned upstream (MIT, Lanyon AI Inc): `upstream/BurgersEquation/inviscid_burgers_1d.lean`
  at `lanyonai/BurgersEquation@dd9b081228ea598daa1a097726a84246f94c075d` and
  `upstream/MaxwellEquations/maxwell_1d.lean` at
  `lanyonai/MaxwellEquations@801558f7f5e5f47398f9be0b6365c0193dcb2691`. SHA-256 values are
  checked by `audit.py --check`.
- **Suite L**: the 13 published theorems in each file, unchanged.
- **Suite L+S**: L plus three statements written here, about whatever the (possibly
  mutated) spec declares:
  - **S1 `jacobianIsDerivative`**: every declared Jacobian entry `J_ij` is the derivative
    of declared flux component `i` with respect to state component `j`, at every state.
  - **S2 `realEigenbasis`**: there are matrices `R`, `L` with `L R = I` and
    `J R = R diag(lambda)`, using the declared eigenvalues `lambda`. This is strong
    hyperbolicity with the declared spectrum. For Maxwell it is stated under the spec's own
    parameter assumption `c > 0`, which the published Lean theorems omit.
  - **S3 `dissipationBound`**: the Lax-Friedrichs dissipation speed is at least
    `|lambda_i|` evaluated at both the left and right states.
- Toolchain: Lean `v4.33.1`, Mathlib at this repository's `lake-manifest.json` pin.

## Mutants

All mutants and their exact string edits are in `audit.py`.

- **Curated (12 + 2 controls)**, chosen with knowledge of L's statements:

  | id | change | predicted L | predicted L+S |
  |---|---|---|---|
  | B0 / M0 | none | pass | pass |
  | B1 | Burgers eigenvalue f/2 | pass | fail (S2) |
  | B2 | Burgers eigenvalue -f | pass | fail (S2) |
  | B3 | Burgers Jacobian f^2 | pass | fail (S1, S2) |
  | B4 | flux f^3/3 in flux only | **fail** (positive control) | fail |
  | B5 | flux f^3/3 in flux and waves; Jacobian, eigenvalue, wave speed unchanged | pass | fail (S1) |
  | B6 | wave speed f/2 | **fail** (positive control) | fail |
  | B7 | Lax-Friedrichs speed halved consistently | pass | fail (S3) |
  | M1 | Maxwell spectrum -c,-c,-c,-c,0,0 | pass | fail (S2) |
  | M2 | Jacobian dF_Ey/dBz = c | pass | fail (S1) |
  | M3 | flux_Ey sign flipped in flux, waves and Jacobian: non-hyperbolic (+-ic) system | pass | fail (S2) |
  | M4 | eigenvalue 0 replaced by c | **fail** (positive control) | fail |
  | M5 | Lax-Friedrichs speed halved consistently | pass | fail (S3) |

- **Systematic (20)**: every single-field sign flip of a nonzero right-hand side in the
  flux, Jacobian, eigenvalue and wave-speed definitions of both files. The mechanical
  rule removes our choice of mutants; it still restricts the class to sign flips.
  Predictions by class:
  - flux flips: L fails, because the flux no longer matches the numerical-flux waves.
  - Jacobian and eigenvalue flips: L passes, L+S fails.
  - wave-speed flips: both pass. The published theorems use only `|mu|`, and the
    published C never reads `mu`, so these are expected to be equivalent mutants.

## Measurements and decision rules

- One `lake env lean --json` compile per variant. Each error is attributed to the
  enclosing declaration. A suite **fails** a variant if any of its theorems has an
  error. Errors in non-theorem declarations make the variant invalid; invalid variants
  are reported, not dropped.
- **H1 (gap)**: at least one non-control mutant describing wrong physics passes all of L.
  Supported if any curated wrong-physics mutant passes L.
- **H2 (repair)**: L+S passes B0 and M0 and fails every curated mutant.
- **Kill confirmation**: a proof failure can mean a false statement or only a brittle
  proof script. For each curated mutant, `refutations/<id>.lean` tries to prove in Lean
  that the statement that caught it (an S statement, or a restated L theorem for the
  positive controls) is false. A kill counts as **confirmed** only if its refutation
  compiles. The refutations are written after this preregistration, but they cannot
  change any pass/fail outcome.
- Every prediction mismatch is reported, together with its explanation if found.

## Known limitations

- The curated mutants were chosen with knowledge of L's weak points. The kill rate is
  not an estimate over any natural population of spec errors. The systematic family
  only partly offsets this.
- The audit concerns theorem statements over `Real`. It says nothing about
  floating-point behavior, about the C code (whose published `main` contains no
  simulation driver), or about solvers other than these two 1D files.
- S1 to S3 are necessary conditions for a correct hyperbolic flux spec, not sufficient
  ones. A spec can satisfy all three and still describe the wrong PDE, for example a
  different flux with consistent derivatives.
