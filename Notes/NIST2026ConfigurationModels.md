# NIST four-configuration restricted-mean diagnostics

**PROVISIONAL — INDEPENDENT AUDIT PENDING.** This is a direct scientific consumer of PR #47's experimental covariance certificate. Review that dependency first. PR #48 supplies a verification-only M0 comparison and shared-data motivation, not independent evidence or a production numerical input.

The four already-seen summaries ask a new, bounded question: which of three specified mean restrictions still leaves a flagged residual? No observations are added. The models are descriptive restrictions, not identified mechanisms, and this analysis selects no winner.

## Frozen model and exact results

Order: copper_servo, copper_free, sapphire_servo, sapphire_free. Coordinates use `U = 10^-11 m^3 kg^-1 s^-2`. Copper/sapphire label source masses, not suspension fibres. Servo/free label electrostatic-servo/free-deflection operation.

For each constraint matrix R, the code computes y = Rx, C = RVRᵀ, Q = yᵀC⁻¹y and A = RᵀC⁻¹R. C is the full **marginal** covariance of the constrained contrasts. The fitted nuisance parameters remain free; conditioning on their observed contrasts would impose a different restriction. Every result is checked against the mean-space GLS profiling formula and independently tested with a cofactor oracle.

| Model | Free mean terms | Residual df | Midpoint Q, decimal rendering | Certified display bound, decimal rendering | Exact cutoff | Disposition over all display values |
|---|---|---:|---:|---|---:|---|
| M0 | Common mean | 3 | 25.0383749520680043 | [24.9984677125400346, 25.0783261791220178] | 7.814728 | FLAGGED_FOR_ALL_DISPLAY_VALUES |
| M_method | Common mean and equal free/servo offset | 2 | 17.7205344138661919 | [17.6843006199167339, 17.7567920228871171] | 5.991465 | FLAGGED_FOR_ALL_DISPLAY_VALUES |
| M_material | Common mean and equal copper/sapphire offset | 2 | 5.45913601272793691 | [5.43745127940459314, 5.48085310524452115] | 5.991465 | NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES |
| M_additive | Common mean, method and material offsets; no interaction | 1 | 1.02699209127435298 | [1.02036633584677651, 1.03362853340423200] | 3.841459 | NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES |

Midpoint classifications agree with the all-display classifications. Exact rational records in `nist_2026_configuration_models_v1.json` control each decision; decimal renderings above are for readability. M0 is exactly equal to the retained PR #48 NIST residual statistic. That check lives in the verification tests, which separately declare their PR #48 file read. Production opens no BIPM or PR #48 result file.

Under the working joint-Gaussian null with fixed, known V, whitening gives a projection of rank equal to the residual df. Algebraically AVA = A and tr(AV) = df; the independently tested allowed mean columns span the nullspace of R. This supplies the chi-square reference under those assumptions, not a guarantee about the source's uncertainty-budget estimation. These are separate nominal 5% diagnostics. Equality at a cutoff is not flagged. The new 2-df cutoff was checked, without measurement data, against 2 ln(20) before freeze. No p-values, joint error-rate or model-selection guarantee is claimed.

## Contrasts and retained covariance

Rows are fixed as material = (1/2,1/2,-1/2,-1/2), method = (-1/2,1/2,-1/2,1/2), and interaction = (-1,1,1,-1). The signed contrast midpoints and exact linear display enclosures are:

| Contrast | Meaning | Midpoint U | Display enclosure U |
|---|---|---:|---|
| material | Copper minus sapphire, averaged over methods | 0.000695 | [0.000694, 0.000696] |
| method | Free minus servo, averaged over materials | 0.000689 | [0.000688, 0.000690] |
| interaction | Copper method gap minus sapphire method gap | -0.000620 | [-0.000622, -0.000618] |

The complete S = LVLᵀ, in U², is retained:

| | material | method | interaction |
|---|---:|---:|---:|
| material | 1.22644250418218713e-7 | -7.82880645345023230e-8 | 1.59078388254830982e-7 |
| method | -7.82880645345023230e-8 | 1.14161495297094613e-7 | -1.69170072900258955e-7 |
| interaction | 1.59078388254830982e-7 | -1.69170072900258955e-7 | 3.74296942757381486e-7 |

These contrasts are correlated. Their marginal standardized squares must not be added, and no unique percentages of M0's Q are assigned to them. The reported central contrasts are descriptive; being nonzero is not the same as being statistically flagged.

## Display certificate and structural controls

V stays fixed at the inherited midpoint absolute covariance throughout. The precise reported uncertainties and correlations cross-check V, but never replace it. Only central-value display ambiguity is propagated; covariance rounding is not.

For every perturbation |δᵢ| ≤ hᵢ, PSD of A gives δᵀAδ ≥ 0. The cross term obeys |2δᵀAx| ≤ B = 2Σhᵢ|(Ax)ᵢ|, while δᵀAδ ≤ E = Σhᵢhⱼ|Aᵢⱼ|. Therefore max(0,Q−B) ≤ Q(x+δ) ≤ Q+B+E globally. These are conservative outer bounds, not necessarily attained extrema. Nuisance fits may move with x. Corner/interior examples supplement this algebraic proof; corners alone cannot establish a quadratic minimum.

The lower bound must strictly exceed the cutoff to flag every display value. The upper bound must be at most the cutoff to leave every value non-flagged. Otherwise the result is `UNRESOLVED_FROM_CERTIFIED_BOUNDS`; a straddling conservative interval does not establish attainable classifications on both sides. Contract and computational failures are errors, never non-rejections.

Since L1 = 0, L(x+a1) = Lx and L(V+t11ᵀ)Lᵀ = LVLᵀ for t ≥ 0. Every restricted diagnostic is invariant to an identical additive shift in all four G coordinates and to added uncertainty with exactly that common loading. Unequal sensitivities, multiplicative changes and time-varying apparatus effects remain possible. Exact synthetic tests enforce both this invariance and an unequal-loading counterexample.

A four-parameter saturated model has zero residual df. It appears only as a synthetic identity control, `NOT_TESTABLE_ZERO_RESIDUAL_DF`, with scientific_acceptance=false. Its exact fit is no evidence of adequacy. Nonincreasing raw Q under nested model enlargements is a mathematical identity, not an improvement claim.

## Interpretation limits

An equal method offset in G units alone does not remove the flagged residual in these summaries under this covariance. The material-only and additive restrictions are not flagged by these diagnostics. Neither is proved correct, and no preference is inferred between them. Labels are not randomized causal interventions. These results establish neither composition-dependent gravity nor a specific instrumental bias.

The paper already discusses a servo/free offset and unresolved origin. Equal G-unit offsets are not equal parasitic torques when gravitational sensitivities differ. A torque-domain extension requires a separate source-supported mapping through the published configuration aggregation; preliminary torque entries alone do not authorize that mapping.

No new measurement, independent confirmation, winning model, corrected or pooled G, p-value, universality probability, variance inflation, configuration removal, Bayesian consensus reproduction, or newly discovered author-missed effect is supplied. The earlier Bayesian `NO_GO` / `NOT_AUTHORIZED` dispositions are preserved. E-001 lies outside this numerical and provenance read closure.

## Chronology, source access and verification

Base: `61b7b2a0b0136b4859c52a56a8ab8a501284f244`. Sole-file freeze: `9b15de44f1fef889ae8744e4e7e4e4c4b60a12b0`; SHA-256 `e19a32c3f6c6ed190a7c6593b77a37b1d44b1b6f586734489e9c30c742fa6a2d`. GitHub draft PR #49 creation anchor: `2026-09-09T14:29:55Z`. **outcome_blind=false**: summaries, M0 and source offset discussion were already known. Candidate implementation and computation followed the anchor. The result-driving source snapshot is committed before artifact emission and identified in each artifact.

The September 9 planning review recorded in the supplied specification and rolling handoff visually inspected NIST PDF indices 25 and 26, including Tables 16 and 18. This implementation attributes that prior inspection; it does not claim another visual review, Claude's audit, retrospective validation of earlier screenshot access, or raw-PDF custody/hash verification. Older freeze and correction records remain unchanged. Primary source: Schlamminger et al., Metrologia 63 (2026) 025012, DOI [10.1088/1681-7575/ae570f](https://doi.org/10.1088/1681-7575/ae570f), [NIST-hosted PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075), printed pp.25–26 and §4.4. This source supports inputs, labels and interpretation limits; the restricted tests are project-defined.

The focused suite checks independent GLS/cofactor results; rank/nullspaces and PSD; full covariance; scaling/permutations; M0 equality; nested models; synthetic effects; global bounds and signed linear enclosures; exact cutoff equality; saturated non-test; frozen-field consumption; terminal/dark-field invariance beyond digest rejection; actual filesystem/Git closure and static imports. The new bounded mutation family has separate assertion-specific controls and read-only evidence validation. No historical mutation family is rerun by the new guard.

Eleven new files and exactly two read-only workflow entries implement the specification. Lean, shared scientific engines and upstream certificates are unchanged. True merge commit required; no squash or rebase. Independent review timing follows the accepted provisional workflow. Leave this PR unmerged for Miguel.
