# NIST 2026 n=4 experimental-covariance estimator result

## Scope

This note reports The Number Project's project-defined generalized minimum-variance unbiased estimator over the four NIST 2026 experimental determinations and their Table 18 experimental covariance.

It is **not** a reproduction of NIST equation (64). The PR #46 Bayesian-consensus reconstruction boundary remains `NO_GO`; equation (64) remains `NOT_AUTHORIZED` for deterministic reproduction from the primary paper alone.

No BIPM-14 versus NIST-26 common-constant comparison is performed here.

## Frozen inputs

Input order:

1. copper-servo — `6.673642`, `23.2 ppm`;
2. copper-free — `6.674021`, `30.3 ppm`;
3. sapphire-servo — `6.672637`, `37.5 ppm`;
4. sapphire-free — `6.673636`, `93.9 ppm`.

The correlation matrix is the frozen Table 18 matrix with off-diagonal entries `0.42, 0.38, 0.12, 0.23, 0.23, 0.25` in the preregistered order.

The Table 18 precise uncertainty values are now frozen directly in the preregistration. The estimator module derives them from frozen bytes rather than from independent module constants. This is the DM-073 repair.

The primary-source Table 18 transcription used here was directly rechecked against the NIST-served article PDF page 26 before this implementation: the table identifies the diagonal as the relative standard uncertainties and the off-diagonal cells as the correlation coefficients. This prospectively removes the PR #46 external-corroboration limitation for the new estimator surface without rewriting the frozen PR #46 artifact.

## Estimator definition

For each displayed midpoint `x_i` and relative standard uncertainty `s_i` ppm,

`u_i = x_i s_i / 10^6`,

`V_ij = rho_ij u_i u_j`.

The exact system `V z = 1` is solved and normalized as `w = z / sum(z)`. The weights therefore sum exactly to one. The estimator and variance are

`G_hat = w^T x`,

`var(G_hat) = 1 / (1^T V^-1 1) = w^T V w`.

## Exact result

The derived weights, shown decimally only for readability, are approximately:

- copper-servo: `0.617817178931247`;
- copper-free: `0.254323418393757`;
- sapphire-servo: `0.126684517716420`;
- sapphire-free: `0.001174884958577`.

All four weights are positive and nonzero; their exact rational forms in the result artifact sum to exactly one.

The project-defined point estimate is approximately

`G_hat = 6.673611063585956 × 10^-11`.

The combined standard uncertainty is approximately

`0.000141539147833783 × 10^-11`,

corresponding to a relative standard uncertainty of approximately

`21.208779847252525 ppm`.

These numbers are outputs of the frozen experimental-only estimator. Their proximity or distance to NIST equation (64), CODATA, BIPM-14, or any other terminal value is **not evaluated as a scientific comparison in this PR**.

## Finite publication resolution

Each displayed determination has a six-decimal closed cell with half-width `0.0000005` in units of `1e-11`.

The estimator weights are fixed from the displayed midpoint summaries. Mapping the four cells through the fixed linear estimator gives an aggregate enclosure approximately

`[6.673610563585956, 6.673611563585956] × 10^-11`.

Because the four real-data weights happen to be positive and sum to one, the enclosure width is exactly one final printed unit (`0.000001` in the displayed units). The implementation does not assume positivity: a separate synthetic test pins correct sign-aware extrema for negative generalized weights.

This enclosure is exact for the **frozen fixed-weight summary model**. It does not represent a model in which covariance-derived weights are recomputed over unknown hidden values inside the printed cells.

## Load-bearing structure

The result is not equivalent to an independent inverse-variance mean. Zeroing the off-diagonal correlations changes the weights, point estimate, and variance.

Replacing the Table 18 uncertainty values with the rounded Table 16 labels also changes the weights and point estimate. Replacing the absolute covariance construction with a relative-ppm-only covariance likewise changes the weights. Each of the four determinations contributes with a nonzero weight.

These checks make the covariance structure, Table 18 precision, absolute scaling convention, and all four inputs scientifically load-bearing rather than decorative.

## Provenance and isolation

Before this estimator source was added, PR #47 committed and verified a permanent file-read-closure test for the PR #46 NIST feasibility artifact. The n=4 chronology guard requires that read-closure repair to be a strict ancestor of the first estimator-source commit and verifies that the estimator's parent already contains the permanent test. This is the DM-077/DM-070 repair.

The new estimator source inventory is NIST-scoped. It does not consume the HUST AAF E-001 evidence-classification boundary.

## Claim limits

This object is The Number Project's experimental-covariance generalized estimator. It is not the authors' Bayesian consensus, does not recover hidden unrounded measurements, does not validate the apparatus, does not assign a probability that the measurements share one constant, and does not support an apparatus-bias or new-physics claim.

A BIPM-14 versus NIST-26 common-constant comparison remains a separate future experiment requiring its own preregistration and explicit cross-measurement model.
