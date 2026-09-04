# HUST 2018 AAF depth-2b feasibility audit — provisional finding

Preregistration commit: `d2918e1aaec07b2f9f5728f461441e61d896effe`.

Status: **PROVISIONAL GO for AAF-I, AAF-II, and AAF-III individually, pending primary main-article PDF byte capture/pinning.**

This note does not authorize a depth-2b MeasurementModel and does not change the existing source-audit classifier.

## Why the earlier depth-2b concern changes

The previously pinned Supplementary Information does not itself contain a complete itemized AAF uncertainty table. However, Table 1 of the main Nature article is explicitly titled as the contributions of various experimental parameters to the main error budget and supplies individual AAF-I, AAF-II, and AAF-III relative standard-uncertainty contributions in ppm.

For each AAF scope, Table 1 lists the following 21 components:

1. pendulum dimensions;
2. pendulum attitude;
3. pendulum density inhomogeneity;
4. coating layer;
5. clamp and ferrule;
6. other pendulum effects;
7. source-mass masses;
8. horizontal source-mass distance;
9. vertical source-mass distance;
10. source-mass positions/alignment;
11. fibre anelasticity;
12. thermal effect;
13. time base;
14. rotating gravity gradient;
15. shelf deformation;
16. magnetic damper;
17. air density;
18. magnetic field;
19. angle encoder;
20. residual twist angle;
21. statistical error of angular acceleration alpha_t.

(Fibre nonlinearity, gravitational nonlinearity, and electrostatic-field entries are shown as not applicable for the AAF columns.)

## Direct Table 1 uncertainty contributions (ppm)

| Component | AAF-I | AAF-II | AAF-III |
|---|---:|---:|---:|
| Pendulum dimensions | 0.16 | 0.16 | 0.16 |
| Pendulum attitude | 0.06 | 0.06 | 0.03 |
| Pendulum density inhomogeneity | 0.46 | 0.46 | 0.46 |
| Coating layer | 0.34 | 0.34 | 0.34 |
| Clamp and ferrule | 0.70 | 1.05 | 0.48 |
| Other pendulum effects | 0.29 | 0.29 | 0.29 |
| Source-mass masses | 0.32 | 0.31 | 0.31 |
| Horizontal distance | 8.98 | 8.98 | 8.98 |
| Vertical distance | 5.79 | 5.79 | 5.79 |
| Positions/alignment | 0.57 | 0.62 | 0.35 |
| Fibre anelasticity | 0.01 | 0.01 | 0.01 |
| Thermal effect | 0.91 | 0.91 | 0.91 |
| Time base | 0.01 | 0.01 | 0.01 |
| Rotating gravity gradient | 1.86 | 1.35 | 1.72 |
| Shelf deformation | 1.51 | 1.51 | 1.51 |
| Magnetic damper | 1.95 | 1.95 | 0.08 |
| Air density | 1.00 | 1.51 | 1.13 |
| Magnetic field | 3.98 | 3.98 | 0.90 |
| Angle encoder | 0.72 | 0.72 | 0.72 |
| Residual twist angle | 0.03 | 0.61 | 0.45 |
| Statistical alpha_t | 3.44 | 2.60 | 1.34 |

The article reports total relative standard uncertainties of 12.45, 12.27, and 11.21 ppm for AAF-I, AAF-II, and AAF-III.

## Independent reconstruction of the individual totals

Using the table entries as direct relative standard-uncertainty contributions to G and combining them in quadrature gives:

- AAF-I: `sqrt(155.0861) = 12.453356977136727... ppm` -> displayed total 12.45 ppm;
- AAF-II: `sqrt(150.6924) = 12.275683280371810... ppm` -> displayed total 12.27 ppm;
- AAF-III: `sqrt(125.7279) = 11.212845312408443... ppm` -> displayed total 11.21 ppm.

The small last-digit differences are consistent with recomputing from Table 1 contributions rounded to two decimal places; they are not filled by using the published total as an input.

## Covariance boundary

The Supplementary Information Section 6 states that, across the three AAF experimental results, the statistical angular-acceleration errors are independent while the same non-statistical error item is treated as 100% correlated because the main apparatus is shared.

That cross-run covariance structure is necessary for a future combined AAF estimator. It is not required to reconstruct the standard uncertainty of one individual AAF result: the individual Table 1 totals are reproduced by the quadrature of that result's listed components.

The combined AAF estimator remains unauthorized and out of scope.

## Remaining gate before final GO

The project currently byte-pins the Supplementary Information but not the full main Nature article PDF containing Table 1. Before changing `complete_uncertainty_model` from `UNPUBLISHED_OR_AMBIGUOUS` to a public/derivable depth-2b authorization, capture and pin an authentic copy of the main article and machine-transcribe Table 1 under a second-key exact-content check.

Until then this finding is deliberately `PROVISIONAL GO`, not an implementation authorization.

## Nonclaims

- No published final G uncertainty was used to derive the quadrature totals.
- This does not reconstruct the underlying metrology behind every Table 1 contribution; Table 1 already expresses those contributions directly in ppm of G. Reconstructing their raw metrological derivations would be a deeper replication level.
- This does not authorize the combined AAF value or its 11.61 ppm combined uncertainty.
- This does not validate the experiment or its systematic-error assumptions.
