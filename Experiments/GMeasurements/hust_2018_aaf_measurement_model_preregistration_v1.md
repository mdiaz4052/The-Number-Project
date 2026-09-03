# HUST 2018 AAF MeasurementModel preregistration v1

## Frozen scope

Base repository state: `672950469bb965b5eb673234b3337ed8a9006e2e` (merge of PR #28).

Target publication: Q. Li et al., *Measurements of the gravitational constant using two independent methods*, Nature 560 (2018), DOI `10.1038/s41586-018-0431-5`.

Target method: angular-acceleration feedback (AAF).

This milestone may construct exactly three empirical central-value reconstruction models:

- `AAF-I`
- `AAF-II`
- `AAF-III`

It must not construct a combined AAF estimator.

## Authorization gate

A scope may be modeled only if the checked-in HUST source-audit artifact remains current and classifies that exact scope as depth-2a authorized.

The builder must fail closed if:

- the source audit is stale or invalid;
- the global decision is not `GO`;
- assessed depth is below `2a`;
- the requested scope is absent from `depth_2a_authorized_experiments`;
- `combined_aaf_reconstruction_authorized` is anything other than `false`.

No model may mix result-driving ancestry from more than one AAF scope.

## Frozen central-value estimator

For one authorized scope, use only the already audited public summary inputs:

- `p_sum = |Σ_l P_g,l,2|`, in `kg m^-3`;
- `alpha_table = <alpha_t(2omega_d)>`, in `nrad s^-2`, already stated by Supplementary Table 3 to be air-density corrected;
- `delta_MD_ppm = ΔG_MD/G`, in ppm, with the audited correction operator `multiply_by_1_plus_delta`.

The numerical derivation is frozen as:

`delta_MD = delta_MD_ppm * 1e-6`

`c_MD = 1 + delta_MD`

`alpha_SI = alpha_table * 1e-9 s^-2`

`G_hat = alpha_SI * c_MD / p_sum`

The `1e-6` ppm conversion and `1e-9` nrad-to-rad conversion are exact decimal unit conversions, not fitted parameters.

The published HUST value of `G` is a terminal external comparison reference only. It may not calibrate, tune, authorize, correct, or otherwise influence `G_hat`.

Numerical agreement with the published value is never an acceptance criterion.

## Uncertainty rule

This milestone is depth 2a, not depth 2b.

For every reconstructed target quantity:

`G_hat.standard_uncertainty = None`

`G_hat.uncertainty_unit = None`

`G_hat.exact = False`

The published input uncertainties may remain attached to their source quantities as documented evidence.

The milestone must not:

- copy the published HUST final uncertainty onto `G_hat`;
- propagate the available subset of input uncertainties and label the result a combined standard uncertainty;
- set target uncertainty to zero;
- claim uncertainty-qualified agreement.

A partial propagated uncertainty may be studied only in a later, separately labeled diagnostic milestone; it is not part of this record.

## MeasurementModel boundaries

Each AAF scope receives its own `EMPIRICAL_RECORD` `MeasurementModel`.

The estimator ancestry must contain only that scope's public inputs and their deterministic derived quantities.

The published HUST `G` value must be isolated as an `EXTERNAL_COMPARISON_REFERENCE` consumed only by a terminal comparison node.

`replication_identifiers` must remain empty. This milestone is a central-value reconstruction, not a replication claim.

No Lean theorem link is required or claimed for the apparatus-specific AAF estimator.

The existing physical-bridge schema and validator should be reused without modification unless implementation proves that an honest representation is impossible. A schema change, if genuinely required, must be separated from the empirical population work rather than silently mixed into it.

## Artifact semantics

The new deterministic HUST artifact must describe itself as a published empirical central-value reconstruction.

It must not reuse the existing structural-example statements that say no experimental dataset/value is present.

The existing structural physical-bridge artifacts must remain byte-for-byte unchanged.

The HUST artifact must preserve separate assessment axes. Expected by design:

- dimensional status: satisfied;
- algebraic model status: satisfied;
- registered target-path status: no registered target path;
- metrological provenance status: satisfied;
- empirical population status: satisfied;
- uncertainty status: incomplete;
- replication status: incomplete.

Those statuses are acceptance expectations of the representation, not evidence that the HUST experiment itself is correct.

## Required tests and fail-closed controls

At minimum, tests must establish that:

1. all three authorized scopes construct independently;
2. their central values are computed from the frozen formula and audited inputs;
3. target `standard_uncertainty` is `None`, target `exact` is false, and no combined uncertainty is emitted;
4. published `G` is terminal and changing it cannot change reconstructed `G_hat`;
5. injecting published `G` into estimator ancestry is rejected;
6. cross-scope ancestry is rejected;
7. a combined AAF model is rejected while combined authorization is false;
8. removing one scope from the source-audit authorization prevents construction of that scope without affecting still-authorized scopes;
9. changing the magnetic-damper correction operator or direction fails closed;
10. the model leaves `replication_identifiers` empty and replication status incomplete;
11. the deterministic HUST artifact is byte-stable and has a permanent `--check` guard;
12. the existing structural physical-bridge artifacts remain unchanged.

## Nonclaims

This milestone does not establish that the HUST value of `G` is correct.

It does not constitute a new laboratory measurement.

It does not reconstruct the complete HUST uncertainty budget.

It does not authorize the combined AAF value.

It does not establish independent replication.

It does not turn agreement with the publication into an empirical acceptance test.

The Supplementary Information remains supported by the existing single human semantic attestation; a second independent human reader remains desirable before strong empirical promotion, but is not a code prerequisite for this central-value reconstruction milestone.
