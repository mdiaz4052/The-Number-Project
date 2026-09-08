# BIPM 2014 correlated two-method estimator reconstruction

This note records the result of the model frozen before implementation in `bipm_2014_correlated_estimator_preregistration_v1.json`. The real-data outcome was already partly exposed during candidate selection, so this is not presented as an outcome-blind discovery.

## Source-bound estimator

The corrected 2014 BIPM source gives servo and Cavendish relative standard uncertainties of 61 ppm and 54 ppm and covariance `κ = -2080 ppm²`. Under the paper's unbiased minimum-variance linear-combination rule, exact arithmetic gives

- servo weight `4996/10797 = 0.462721126...`;
- Cavendish weight `5801/10797 = 0.537278874...`;
- combined relative variance `6524036/10797 ppm²`;
- combined relative standard uncertainty about `24.5814 ppm`.

The source's printed weights 0.46/0.54 and printed combined uncertainty 25 ppm are therefore corroborative outputs, not estimator inputs.

## Finite-resolution central-value reconstruction

The source prints the two method central values as `6.67515` and `6.67586` in units of `10^-11 m^3 kg^-1 s^-2`. Treating each displayed value conservatively as a closed half-last-digit cell and applying the exact covariance-derived weights gives the aggregate enclosure

`[6.67552646800037..., 6.67553646800037...] × 10^-11`.

The weighted midpoint of the two displayed numbers is

`6.67553146800037... × 10^-11`,

which by itself lies below the published combined-value cell. This is why a midpoint-only reconstruction would overstate what the printed summaries can establish.

The paper's combined central value `6.67554 × 10^-11`, printed to the same five decimal places in the displayed mantissa, contributes the closed cell

`[6.675535, 6.675545] × 10^-11`.

The exact aggregate enclosure intersects that cell on

`[6.675535, 6.67553646800037...] × 10^-11`.

Therefore the frozen classification is **compatible**: the published combined central value is representable by at least one pair of underlying method values consistent with the two printed method cells under the covariance-derived minimum-variance weights.

## Interpretation limits

This does not recover the authors' hidden unrounded servo or Cavendish values, and it does not claim that the displayed covariance summaries are unrounded. It establishes a conditional published-summary representation certificate. The negative branch remains meaningful: if the exact weighted image of the two published input cells were disjoint from the published combined-value cell, the result would be `not_representable_under_the_declared_bipm_2014_correlated_weighted_mean_model`.

The scientifically new capability is not simply another rounding check. It is the first real `n = 2` correlated estimator in the repository: covariance changes the weights and the uncertainty, and finite input-resolution propagates through a genuine weighted aggregate before the terminal comparison is exposed.
