# HUST 2018 AAF depth-2b feasibility audit — final finding

Preregistration commit: `d2918e1aaec07b2f9f5728f461441e61d896effe`.

Status: **GO for AAF-I, AAF-II, and AAF-III individually.**

This is a feasibility result. It authorizes a separately preregistered depth-2b implementation to be attempted; it does not itself modify any MeasurementModel, populate `G_hat.standard_uncertainty`, or authorize the combined AAF estimator.

## Evidence that closes the preregistered question

Table 1 of the main Nature article is explicitly the main error budget and gives 21 applicable relative standard-uncertainty contributions for each AAF determination, expressed directly in ppm of `G`. The AAF rows shown as not applicable are fibre nonlinearity, gravitational nonlinearity, and electrostatic field.

The exact 21-by-3 transcription is frozen in:

`Experiments/GMeasurements/hust_2018_aaf_depth_2b_feasibility_v1.json`

and independently second-keyed in:

`tests/test_hust_2018_aaf_depth_2b_feasibility.py`.

The main-article Table 1 was checked through two routes:

1. a publicly retrievable third-party-hosted publisher-formatted copy of the Nature article with DOI `10.1038/s41586-018-0431-5`;
2. a project-owner visual confirmation from a Nature-accessed copy, supplied as a screenshot of Table 1. The screenshot SHA-256 is `3f47836277c451a0cb0aa466c5bb12f0f813d7a8072856951cf336c04c8d0294` (127165 bytes). The screenshot itself is conversation evidence and is not stored in this repository.

This establishes content identity for the feasibility audit but does **not** claim byte identity between the third-party PDF and a Nature-served PDF.

## Individual uncertainty reconstruction

For each AAF scope, Table 1 gives these 21 applicable components:

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
21. statistical angular-acceleration error.

The article identifies the table uncertainties as one standard deviation. The pinned Supplementary Information Section 6 supplies the uncertainty-combination framework: individual uncertainties are formed from the root-sum-square of the uncertainty items, while correlations enter when repeated/run results are combined.

Using only the 21 Table 1 components and **not** the published final uncertainty as an input gives:

- AAF-I: `sqrt(155.0861) = 12.453356977136727047866320298865297714729175627210 ppm`;
- AAF-II: `sqrt(150.6924) = 12.275683280371809918505072305209443766741467830010 ppm`;
- AAF-III: `sqrt(125.7279) = 11.212845312408443280940946155017027106000868654421 ppm`.

The displayed Table 1 totals are `12.45`, `12.27`, and `11.21 ppm`, respectively. The residual last-digit differences are expected when recomputing from contributions displayed only to two decimal places; the published totals are terminal comparisons and do not constrain the reconstruction.

## Covariance boundary

Supplementary Information Section 6 states that for AAF-I/II/III:

- the statistical angular-acceleration errors are independent between the three experiments;
- the same non-statistical error item is treated as 100% correlated because the main parts of the apparatus are shared.

That cross-run covariance structure is needed for a future **combined** AAF estimator. It is not needed to obtain the standard uncertainty of one individual AAF result from its Table 1 components.

The combined AAF estimator remains unauthorized and out of scope.

## Preregistered requirements

All seven individual depth-2b feasibility requirements are satisfied:

1. complete component inventory — **SATISFIED**;
2. component magnitudes and unit/relative contribution — **SATISFIED**;
3. mapping to the measured result — **SATISFIED** as direct relative contributions to `G`;
4. combination rule — **SATISFIED**;
5. within-result covariance assumptions required by that rule — **SATISFIED**; no additional within-result covariance term is needed beyond the stated individual RSS model;
6. statistical/shared provenance — **SATISFIED**;
7. published individual standard uncertainty reconstructible without target input — **SATISFIED**.

## What GO means next

A separate implementation milestone may now construct depth-2b individual AAF MeasurementModels in which `G_hat.standard_uncertainty` is derived from the 21 upstream Table 1 uncertainty contributions rather than copied from the published final `G` uncertainty.

That implementation should remain separate for AAF-I, AAF-II, and AAF-III and should continue to treat the published `G` values and published final uncertainties as terminal comparison references only.

## Nonclaims

- This audit does not itself implement depth 2b.
- It does not reconstruct every Table 1 contribution from raw apparatus metrology; Table 1 already reports those contributions directly in ppm of `G`.
- It does not authorize the combined AAF value or its combined uncertainty.
- It does not establish run-level or raw-data replication.
- It does not validate the HUST apparatus or guarantee that the authors' uncertainty model contains every unknown systematic effect.
