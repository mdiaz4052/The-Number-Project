# NIST 2026 n=4 Experimental-Covariance Estimator — Bounded Specification

## Objective

Construct The Number Project's first genuine four-input correlated estimator from the NIST 2026 BIPM-torsion-balance summary data authorized by PR #46.

The object is a deterministic generalized minimum-variance unbiased linear estimator over the four published determinations and their experimental covariance. It is **not** a reconstruction of the paper's Bayesian hierarchical consensus in equation (64).

## Base, freeze, and prerequisite

Base: `30227abeb3f6ab009b70c429e491bb015e798542`, the true merge of PR #46.

Freeze: `504200ae817a60b211decec4432b43be9087e9e3`.

The freeze is the sole first branch commit and pins all four displayed determinations, all four Table 18 precise relative standard uncertainties, all six correlations, the fixed input order, the estimator equations, the finite-resolution convention, and the five Bayesian reconstruction blockers inherited from PR #46.

Draft PR #47 was created at `2026-09-09T00:26:16Z` before implementation.

Before this estimator module was introduced, commit `36f8323dfea425b84f41021ababeedd1a2683572` added the permanent PR #46 build read-closure test and its Python verification job passed. The estimator chronology guard must prove that this prerequisite commit is a strict ancestor of the first estimator-source commit. This is the preregistered DM-077/DM-070 repair.

## Source and upstream authorization

Primary publication: Stephan Schlamminger et al., *Redetermination of the gravitational constant with the BIPM torsion balance at NIST*, Metrologia 63 025012 (2026), DOI `10.1088/1681-7575/ae570f`.

PR #46 established:

- `experimental_covariance = GO`;
- `published_bayesian_consensus = NO_GO` for unique deterministic reproduction;
- `equation_64_reproduction = NOT_AUTHORIZED`;
- `common_constant_comparison = NOT_EVALUATED`.

This PR must preserve that boundary.

The primary article's Table 16 supplies the four displayed determinations. Table 18 supplies the more precise combined relative standard uncertainties and the full correlation matrix. For this PR the Table 18 numerical inputs are frozen directly, rather than residing in post-freeze module constants. This is the DM-073 repair.

## Frozen input order

1. `copper_servo`: 6.673642, 23.2 ppm;
2. `copper_free`: 6.674021, 30.3 ppm;
3. `sapphire_servo`: 6.672637, 37.5 ppm;
4. `sapphire_free`: 6.673636, 93.9 ppm.

All central values are in units of `1e-11`. Each is printed to six decimal places.

Frozen correlation matrix:

```text
        cuS    cuF    saS    saF
cuS     1      .42    .38    .12
cuF     .42    1      .23    .23
saS     .38    .23    1      .25
saF     .12    .23    .25    1
```

## Estimator

For displayed midpoint `x_i` and Table 18 relative standard uncertainty `s_i` ppm,

`u_i = x_i s_i / 10^6`.

The absolute covariance matrix is

`V_ij = rho_ij u_i u_j`.

The estimator solves exactly

`V z = 1`,

then normalizes

`w = z / sum(z)`.

Thus `sum_i w_i = 1` exactly and

`G_hat = sum_i w_i x_i`.

The combined variance must satisfy both exact forms

`var(G_hat) = 1 / (1^T V^-1 1)`

and

`var(G_hat) = w^T V w`.

All result-driving matrix arithmetic uses exact rational Gaussian elimination. Binary floating point is not an authoritative decision path. Weight signs are not constrained in advance.

## Finite publication resolution

Each six-decimal displayed value denotes the closed interval

`[x_i - 0.5e-6, x_i + 0.5e-6]`

in the displayed `1e-11` units.

The estimator weights are fixed from the displayed midpoint summaries and Table 18 covariance summary. They are **not** recomputed as hidden values move inside their display cells. The four cells are mapped through the fixed linear estimator using sign-aware exact extrema.

This is therefore a conditional summary-level representation enclosure. It does not recover the authors' hidden unrounded values and does not model uncertainty in the published covariance summary itself.

## Claim boundary

This PR must not:

- call this object NIST's equation (64) estimator;
- use the published Bayesian final value as an estimator input or terminal acceptance target;
- use Table 19 dark uncertainty/configuration effects in the estimator;
- use CODATA or BIPM values in estimator construction;
- perform a BIPM-14 versus NIST-26 common-constant test;
- assign a p-value or a probabilistic compatibility interpretation;
- infer apparatus bias or new physics;
- cross the HUST AAF E-001 evidence-classification boundary.

## Required tests

Tests must independently pin the frozen projection, source cross-checks, absolute covariance construction, positive definiteness, exact four weights and normalization, exact point estimate and variance identities, and finite-resolution enclosure. Adversarial tests must show that removing correlations, substituting rounded Table 16 uncertainty labels, replacing absolute covariance with relative covariance, omitting any input, or collapsing display cells changes or invalidates the protected behavior. A synthetic signed-weight case must exercise sign-aware enclosure logic even if all four real-data weights are positive.

The permanent PR #46 read-closure test must remain in place, and this estimator's own result-driving filesystem inventory must remain NIST-scoped.

## Validation and merge semantics

Run focused tests during development. On the final tree run one complete Python suite, relevant `--check` guards, and `git diff --check`; exact-head GitHub CI provides the final repository-wide automated gate. No Lean source changes are planned.

Merge only with a **true merge commit**. Never squash or rebase the freeze/anchor/prerequisite ancestry.
