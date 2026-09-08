# BIPM 2014 correlated two-method estimator — bounded implementation specification

## Objective

Implement the project's first genuine correlated `n = 2` published estimator reconstruction from Quinn, Speake, Parks & Davis (2014), *The BIPM measurements of the Newtonian constant of gravitation, G*, DOI `10.1098/rsta.2014.0032`.

The scientific question is narrowly:

> Given the corrected published servo and Cavendish determinations, their reported standard uncertainties, and their reported covariance, what minimum-variance unbiased linear estimator follows without using the paper's reported combined value or printed weights to determine the estimator?

The reported combined central value, printed 0.46/0.54 weights, and printed 25 ppm combined uncertainty are comparison-only.

## Intended base and chronology

Base: `fe9b6ee4301612530143ae13e814a16cc5fef2cb` (true merge of PR #43).

Frozen preregistration commit: `1d71e27e1655f3cef7f674e507c03a1a14e2a340`, which must remain the sole first branch commit and introduce only the preregistration. Draft PR #44 is the external implementation anchor. This work is explicitly **not outcome-blind** because the candidate-selection discussion exposed the paper's final aggregate before the freeze; the protected claim is target-independent implementation.

## Authorized source projection

Primary source: DOI `10.1098/rsta.2014.0032`.

Estimator inputs, frozen before implementation:

- servo: `6.67515 × 10^-11 m^3 kg^-1 s^-2`, relative standard uncertainty `61 ppm`;
- Cavendish: `6.67586 × 10^-11 m^3 kg^-1 s^-2`, relative standard uncertainty `54 ppm`;
- covariance `κ = -2080 ppm^2`.

Source locations: §11(d), eqs. (11.13a)–(11.15b), Table 1, and §12 eqs. (12.1a)–(12.2). The 2014 PRL erratum DOI `10.1103/PhysRevLett.113.039901` corroborates correction provenance relative to the 2013 PRL.

Comparison-only source fields: published weights `0.46`, `0.54`; combined uncertainty `25 ppm`; combined central value `6.67554 × 10^-11`.

## Mathematical contract

For covariance matrix

`V = [[σ_s², κ], [κ, σ_c²]]`,

require `σ_s > 0`, `σ_c > 0`, positive determinant, and `D = σ_s² + σ_c² - 2κ > 0`.

Under `λ_s + λ_c = 1`, minimize

`Var = λ_s² σ_s² + 2 λ_s λ_c κ + λ_c² σ_c²`.

The unique weights are

- `λ_s = (σ_c² - κ) / D`;
- `λ_c = (σ_s² - κ) / D`.

Use exact rational arithmetic.

The two printed method central values are finite-resolution decimal representations. Each contributes a closed half-last-digit cell. Apply the derived weights to the Cartesian product of those two cells and compute the exact sign-aware linear image. Only after that enclosure exists may the comparison-only combined central-value cell be constructed.

Classification:

- `compatible`: aggregate enclosure intersects the published combined-value cell;
- `incompatible`: the two closed intervals are disjoint, labeled `not_representable_under_the_declared_bipm_2014_correlated_weighted_mean_model`;
- `unresolved`: reserved for invalid/degenerate future extensions, not for a valid positive-definite two-input source summary.

## Claim boundaries

No raw-run reconstruction; no apparatus validation; no hidden unrounded-value claim; no use of published combined value or printed weights to fit the estimator; no cross-publication common-constant inference; no HUST artifact or E-001 boundary; no Lean change; no rewrite of frozen HUST, Schlamminger, Newman, or joint artifacts.

## Implementation surfaces

Add a reusable exact two-input correlated weighted-mean primitive, a BIPM source-bound wrapper, source attestation, result note, focused behavior/artifact tests, and a bounded mutation family. Modify `verify.yml` only to add read-only checks for the final BIPM result and mutation evidence.

## Focused verification

Tests must prove exact weights and unity sum, positive-definite/denominator rejection, covariance sensitivity, input-swap symmetry, exact decimal cells, sign-aware aggregate enclosure, target/printed-weight/printed-uncertainty invariance, synthetic compatible/incompatible classifications, model-qualified negative label, preregistration/source chronology, artifact rebuild, and E-001 isolation.

Because the new protected boundary is covariance-driven estimation plus target independence, run a bounded mutation family covering at minimum: erased covariance, flipped covariance sign, diagonal-only inverse variance, printed-weight substitution, target leakage into weights, input-cell collapse, enclosure-extremum corruption, and negative-label dequalification.

## Acceptance and merge

On the final tree: focused tests, one complete Python suite, relevant `--check` guards, bounded mutation evidence, and `git diff --check` where locally available. Exact-head GitHub CI is the repository-wide final gate. No Lean-specific local rerun is required because no Lean-linked surface changes.

Merge only by a true merge commit. Never squash or rebase the freeze/anchor ancestry.
