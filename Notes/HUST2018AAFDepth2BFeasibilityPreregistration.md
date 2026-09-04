# HUST 2018 AAF depth-2b feasibility audit — preregistration

Base: `3c4c273871958127e6f3253e7e9495a673993ffe` (merged PR #31).

## Question

Do the publicly retrievable HUST 2018 materials contain enough information to reconstruct a genuinely uncertainty-qualified individual AAF determination of `G` (depth 2b), without using the published final `G` uncertainty as an input or tuning target?

This is a feasibility audit, not a depth-2b implementation.

## Unit of assessment

Assess AAF-I, AAF-II, and AAF-III separately. A GO for one does not imply GO for the others. The combined AAF estimator remains out of scope and unauthorized.

## What counts as a complete individual uncertainty model

For an individual AAF scope, the public material must supply enough information to identify and machine-reconstruct:

1. every uncertainty component materially included in the authors' stated standard uncertainty for that individual `G` result;
2. the numerical magnitude and unit or relative contribution of each component;
3. the correction/measurement quantity to which each component belongs, or an equivalent direct contribution to `G`;
4. the rule used to combine the components;
5. every within-result correlation/covariance assumption required by that combination rule;
6. enough provenance to distinguish statistical/random terms from shared/systematic terms where that distinction affects the individual uncertainty;
7. enough information to reproduce the published individual standard uncertainty from upstream public information, with the published final uncertainty used only as a terminal comparison.

Cross-run covariance is not required for an individual depth-2b result unless it enters that individual's stated uncertainty. It would be required for any future combined AAF estimator, which is not authorized here.

## GO criterion

An AAF scope is GO for depth 2b only if all seven requirements above are publicly recoverable and the resulting uncertainty can be reconstructed without importing, back-solving from, or tuning to the published final `G` uncertainty.

A numerical agreement check may be reported only after reconstruction. It is diagnostic, not an acceptance threshold and cannot fill a missing uncertainty component or covariance rule.

## NO-GO criterion

An AAF scope is NO-GO if any materially result-driving uncertainty component, component magnitude, combination rule, or required covariance/correlation assumption is unavailable, ambiguous, request-only, or recoverable only by using the published final uncertainty as a constraint.

A partial propagated uncertainty from the three depth-2a inputs (`P_g`, corrected angular acceleration, magnetic-damper correction) does not qualify as depth 2b and must not populate `G_hat.standard_uncertainty`.

## Evidence classes

Use the existing distinctions `PUBLIC_DIRECT`, `PUBLIC_DERIVABLE`, `REQUEST_ONLY`, `TARGET_DERIVED`, and `UNPUBLISHED_OR_AMBIGUOUS`. Do not upgrade request-only or inferred information to public evidence.

## Sources to inspect

At minimum:

- Li et al., Nature 560, 582–588 (2018), DOI `10.1038/s41586-018-0431-5`;
- its Supplementary Information, especially Sections 2, 4, 5, and 6 and Supplementary Tables 1 and 3;
- public Extended Data / Source Data associated with the article, if retrievable;
- later HUST/CODATA discussions may be used only to locate or interpret source categories, not to substitute missing 2018 numerical uncertainty inputs unless those inputs are themselves publicly pinned.

## Frozen nonclaims

This audit does not validate the HUST apparatus, establish raw/run-level replication, authorize the combined AAF estimator, change any existing depth-2a MeasurementModel, or treat the published uncertainty as an upstream datum.

If the result is NO-GO, document the exact missing pieces and move to a qualitatively different empirical benchmark rather than approximating them away.
