# HUST 2018 AAF source-availability preregistration v1

Status: FROZEN BEFORE SOURCE-AVAILABILITY CLASSIFICATION

Baseline: `ef74bd1a6a8abbfc631c326fab2cbc61a9d0fc45` (merged PR #24)

Target publication: Q. Li et al., “Measurements of the gravitational constant using two independent methods,” Nature 560, 582–588 (2018), DOI `10.1038/s41586-018-0431-5`.

Target method: angular-acceleration feedback (AAF) only. Time-of-swing is out of scope.

## Purpose

Determine the deepest HUST-2018 AAF result that can be reconstructed from the public record without requesting unpublished data and without using a published G value, or any target-derived surrogate, upstream.

This milestone is a source audit. It must not create a `MeasurementModel`, change the physical-bridge schema, or claim an independent laboratory measurement.

## Frozen comparison targets

The following are terminal comparison values only and are forbidden as estimator inputs:

- AAF-I: `6.674534(83) × 10^-11 m^3 kg^-1 s^-2`.
- AAF-II: `6.674375(82) × 10^-11 m^3 kg^-1 s^-2`.
- AAF-III: `6.674535(75) × 10^-11 m^3 kg^-1 s^-2`.
- Combined AAF: `6.674484(78) × 10^-11 m^3 kg^-1 s^-2`.
- Combined AAF relative standard uncertainty: `11.61 ppm`.

The printed AAF values are taken from Supplementary Table 3. The combined method pairing is cross-checked against the Nature abstract.

## Public-source inventory to inspect

1. Nature version-of-record landing page.
2. Supplementary Information PDF.
3. Supplementary Data XLSX.
4. Source Data Fig. 2 XLSX.
5. Source Data Fig. 3 XLSX.
6. Source Data Extended Data Fig. 2 XLSX.
7. Source Data Extended Data Fig. 4 XLSX.
8. Source Data Extended Data Fig. 5 XLSX.

The retrieved Nature listing itself is evidence: its bytes, offered resource labels, and resolved resource URLs must be recorded. Retrieval dates are recorded inputs and are never recomputed by `--check`.

## Evidence classes

- `PUBLIC_DIRECT`: value appears directly in a retrieved public source.
- `PUBLIC_DERIVABLE`: every parent and exact derivation rule needed for the value are publicly pinned.
- `REQUEST_ONLY`: source states the information is obtainable by request but it is not in the retrieved public set.
- `UNPUBLISHED_OR_AMBIGUOUS`: no unique checkable public value/procedure is established.
- `TARGET_DERIVED`: value or procedure depends on published G or another downstream target quantity.

Figure digitization is not allowed in this milestone. If plotted numerical source data are supplied in XLSX, reading those cells is `PUBLIC_DIRECT`.

`TARGET_DERIVED` is disqualifying for an independent central-value reconstruction.

## Required-input graph rules

Construct a directed acyclic dependency graph from public observables/apparatus quantities to one named AAF determination. Graph ancestry, not string matching, decides target leakage.

A node is result-driving if the paper explicitly applies it to the central estimate, or if it participates in the uncertainty/correlation calculation required for the claimed replication depth. A quantity the paper explicitly declares negligible and does not apply is not required.

At minimum inspect the paper's own treatment of:

- the gravity-coupling coefficients `P_g,l,2`;
- their summed magnitude;
- the average measured angular acceleration `<alpha_t(2 omega_d)>`;
- magnetic-damper correction;
- data-averaging and numerical-differentiation attenuation corrections;
- air-density correction;
- co-moving and lab-fixed background gravitational-gradient treatment;
- AAF-I / AAF-II / AAF-III partitioning;
- any other correction explicitly applied to a central estimate;
- the uncertainty and correlation structure needed for depth 2b or deeper.

Do not preregister an apparatus-specific correction merely because it appeared in UW-2000. It is required only if the HUST source itself applies it under the rule above.

## Replication-depth ladder

- Depth 0: provenance-complete headline result only.
- Depth 1: published component values and combination statements can be independently checked, but no individual G can be recomputed from upstream public quantities.
- Depth 2a: at least one specifically named AAF-I/II/III central G value can be computed from `PUBLIC_DIRECT`/`PUBLIC_DERIVABLE` ancestors without target-derived inputs.
- Depth 2b: depth 2a plus enough public uncertainty/correlation information to reconstruct a meaningful standard uncertainty for that same determination.
- Depth 3: run/set-level public data support recomputation and combination.
- Depth 4: public raw time-series data support substantial recreation of the reduction pipeline.

A depth-2a GO authorizes a later implementation only for the specific determination(s) that reach 2a. It does not authorize the combined AAF value. Depth 2b is required before calling that later implementation an uncertainty-qualified empirical reproduction. The combined AAF result requires its own publicly reconstructible weighting/correlation structure.

## Decision classifier

- `GO`: maximum supported depth is at least 2a.
- `PARTIAL`: an honest public record is supportable, but maximum supported depth is only 0 or 1.
- `NO_GO`: even a provenance-complete intended record cannot be supported from the retrieved public evidence.

The audit must record both the decision and `maximum_supported_replication_depth`.

No expected decision or expected depth is preregistered.

## Fail-closed conditions

Downgrade rather than fill a gap when:

- a required source cannot be retrieved;
- a result-driving node is `REQUEST_ONLY`, `UNPUBLISHED_OR_AMBIGUOUS`, or `TARGET_DERIVED`;
- a claimed table/cell/page locator does not support the asserted input;
- AAF experiment scopes are mixed;
- a prior paper is used without proof that the 2018 experiment imports that value/procedure;
- a quantity is inferred by tuning or back-solving from a published G value;
- a required graph node or dependency edge is missing;
- a transitive ancestor, including a parent-of-a-parent, is target-derived.

## Determinism and source pinning

The committed source-capture artifact records immutable retrieval metadata: retrieval date, resolved URL, byte length, and SHA-256 of every successfully retrieved external source. The source listing is pinned the same way.

Artifact generation must use stable ordering and deterministic JSON (`sort_keys=True`, fixed indentation, one trailing newline). `--check` never re-fetches a URL or recomputes an access date.

The governing preregistration is byte-pinned by a literal SHA-256 in source code. A later outcome may not silently bless altered preregistration bytes.

## NFC metadata boundary

External identifiers are recorded verbatim in evidence metadata. A non-NFC identifier is recorded as a metadata finding and excluded from schema-bound `source_identifier` fields until deliberately resolved. No silent Unicode normalization is permitted.

## Nonclaims

This source audit does not establish that HUST's G value is correct, that the apparatus is free of systematic error, that a future estimator implementation is correct, or that laboratory G measurements validate emergent gravity.

Do not make HUST simultaneously provide the scientific data and define the representation required to accept those data.
