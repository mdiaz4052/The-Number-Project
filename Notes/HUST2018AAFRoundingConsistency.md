# HUST 2018 AAF: conditional rounding consistency

The diagnostic finds a **compatible** component scenario under its preregistered assumptions. Shifting each of the 63 component entries by −0.000625 ppm produces a combined relative standard uncertainty enclosed by **[11.614638, 11.614639] ppm**. This lies strictly inside the comparison bin (11.605, 11.615), so the scenario rounds to the displayed 11.61 ppm under nearest rounding, regardless of the tie convention.

This is a mathematical existence certificate conditional on the stated model and input domain. It does not identify the authors' hidden component values or prove the actual cause of the discrepancy. It supplies no probability, significance level, or new physical prediction. The original combined MeasurementModel, its approximately 11.6161857764 ppm uncertainty, its visible discrepancy, and all evidence classifications remain unchanged.

## Domain and method

The inputs are the three reconstructed individual central estimates and the 63 two-decimal component entries from the pinned v2 records. Each printed component c is assigned [c − 0.005, c + 0.005] ppm. Nearest rounding is a diagnostic assumption; the publisher's actual rounding and tie procedure has not been established.

The declared domain is a product of these intervals, with no additional latent equality constraints or probability distribution. Physical error propagation still uses the adopted source rule: matching non-statistical errors are fully correlated across the three runs, the statistical errors have zero cross-run covariance, and different component rows do not mix. Central-value rounding, apparatus primitives, displayed individual totals, and other publication outputs are outside this diagnostic. Its witness does not establish joint consistency of the whole publication.

The calculator recomputes each marginal total variance, its inverse-variance weight, the combined central estimate, and correlated uncertainty for each scenario. It does not fit or modify the empirical model. Positive fixed central values permit the exact equivalent propagation coefficients q_i = (1/(g_i S_i)) / Σ_j(1/(g_j S_j)), where S_i is the sum of squared ppm components for run i. The relative variance in ppm² is a sum of squares of shared contributions plus squared independent contributions. A separate test oracle constructs the absolute covariance matrix and evaluates pᵀCp.

All authoritative arithmetic uses rational numbers. Monotone positive interval operations give a guaranteed whole-domain uncertainty enclosure of **[11.570884, 11.661636] ppm**, with endpoints rounded outward for display. The enclosure is intentionally conservative because it loses dependencies between repeated quantities. It is not a confidence interval, a tight range, or a claim that its endpoints are attainable. Overlap with this enclosure alone would not establish compatibility.

All 15 candidate tables are computed before consulting the comparison. The fixed common-shift sequence is 0, −1/8, +1/8, …, −7/8, +7/8 of each cell's half-width. The first nonzero candidate supplies the witness. This selection is an existence search over a frozen schedule; it does not estimate a sampling probability.

## Outcomes and controls

| Outcome | Evidence required |
| --- | --- |
| `compatible` | A verified candidate strictly inside the applicable rounding bins reaches the comparison bin. |
| `incompatible` | The exact conservative enclosure excludes the closed comparison interval. |
| `unresolved` | Enclosures overlap but the fixed schedule finds no witness. |

The synthetic controls establish all three branches. In the unresolved control an admissible unscheduled value actually exists, demonstrating why failure to find a witness cannot be treated as exclusion. Boundary tests retain unresolved status when the only apparent support is a rounding tie. Invalid evidence raises an error instead of receiving a numerical verdict.

## Reproduce and inspect

```bash
python -m Discovery.hust_2018_aaf_rounding_consistency --check
python -m Discovery.hust_2018_aaf_rounding_consistency
```

The first command verifies the committed artifact without writing. The second prints the diagnostic. Generation requires an explicit `--output` path and committed result-driving source. Rational bounds, all candidate component values, weights, propagation coefficients, exact variances, the selected witness, controls, source pins, and limitations are in `Experiments/GMeasurements/hust_2018_aaf_rounding_consistency_v1.json`.

The [bounded specification](HUST2018AAFRoundingConsistencySpecification.md) is hash-bound by preregistration commit `8578f20e41476e9490dfbb934342a92bd3ca738e`. Draft [PR #39](https://github.com/mdiaz4052/The-Number-Project/pull/39) was created at `2026-09-06T20:33:51Z`, before implementation. The HUST result and Claude's exploratory rounding draws were already known; this establishes an implementation-rule freeze, not blindness.

The shared chronology verifier checks the sole baseline parent, a preregistration-only addition, frozen/current bytes, ancestry, and all reachable descendants of the freeze, including losing merge parents. The historical PR #37 and PR #38 wrappers retain their pins and output bytes. General source-state attestations retain their separate role.

This capability supports subsequent discrepancy analysis across independent measurements. A second experiment and tests of predeclared physical predictions remain separate work.
