# PR #41 — Target-independent joint representation inference

## Objective and base

Base: `050dde49e733d92a9897706cc7e95e1455edf559`, merged PR #40.
Create one deterministic logical certificate from the established HUST 2018 AAF
combined and Schlamminger 2006 statistical/systematic rounding certificates.
The conjunction is `(exists xH in DH: PH(xH)) and (exists xSstat in DSstat:
PSstat(xSstat)) and (exists xSsys in DSsys: PSsys(xSsys))`. Domains remain
source-specific and uncoupled. No search, optimization or reconstruction occurs.

## Inputs and projection

Only `Experiments/GMeasurements/hust_2018_aaf_rounding_consistency_v1.json`
and `Experiments/GMeasurements/schlamminger_2006_rounding_consistency_v1.json`
may supply scientific inputs. Freeze their exact SHA-256 and artifact IDs, with
generating epochs `2a205adbb9f2edd517d1b37d13633b30eb88ea4a` and
`07fc431dd6cf0953a74cc2d57fea5c867ff8af66`; both must be ancestors of base and
contain those same bytes. Enforce a literal path allowlist before opening inputs.
Do not follow any source or provenance references found inside those artifacts.

Project HUST `decision` and Schlamminger `terminal_decisions` into named required
scopes. Copy only original verdict and witness identity (candidate index, exact
schedule parameter, membership attestation, and JSON pointer). No candidate
component values, central G, weights, uncertainty values, or covariance enter the
projection. For compatible scopes, the established artifacts select the first
successful candidate and their candidate zero is the unshifted midpoint. Derive
`unshifted_midpoint_consistent` from first witness index zero and zero parameter;
label this `unshifted_midpoint`, otherwise `shifted_scheduled`. Check index,
membership flag and selected parameter against the existing candidate and frozen
schedule; do not recompute the historical calculation. Null characterizations
are used for non-compatible scopes. Characterization never affects truth logic.
Missing required scopes or malformed verdict/witness records are errors.

## Exact semantics

`compatible -> representable`; `incompatible -> not_representable`;
`unresolved -> undetermined`, and no other mapping.
A nonempty publication's required scopes yield `not_representable` if any does,
otherwise `representable` if all do, otherwise `undetermined`.
Across a nonempty required publication inventory, any `not_representable` yields
`not_all_representable`; otherwise all `representable` yields
`all_representable_under_separate_declared_models`; otherwise `undetermined`.
Record machine-readable reasoning traces at both levels. Generic synthetic
inputs must exercise all three branches and dominance with unresolved inputs.

## Firewall and nonclaims

The calculator must not read/import the HUST source audit manifest, either
`hust_2018_aaf_depth_2b_authorization_v1.json` or `v2.json`, the combined
MeasurementModel, or disputed `complete_uncertainty_model` classifications.
E-001 remains unresolved and outside the dependency graph. If required, stop as
BLOCKING. No future candidate material (Newman, Rosi, Quinn, others) is consulted.
Do not modify or rerun `Discovery/rounding_consistency.py`, old schedules,
preregistrations, result artifacts or mutation attestations. Do not modify Lean,
shared history infrastructure or deferred-maintenance files.
No numerical G comparison, combined G, absolute uncertainty, covariance matrix,
weighted mean, z-score, chi-square, p-value, CODATA comparison, sampling model,
probability, frequency, confidence level, likelihood, posterior, common-cause
hypothesis, evidence score/count/ranking or universality conclusion is allowed.
The result does not say rounding occurred or caused a discrepancy, nor that
publications measured statistically compatible G values. It says only that each
required subtotal has an admissible realization under its separate declared model.

## Prospective freeze and artifacts

Known prior outcomes: all three compatible; HUST and Schlamminger statistical
shifted, Schlamminger systematic unshifted. This is not a blind prediction.
Freeze allowed inference semantics before implementation, with specification
bytes prepared first and SHA-256 pinned in the preregistration. First commit adds
only the preregistration, with sole parent exactly base. Push it, open a draft PR,
record GitHub's PR-created timestamp, then implement and commit these exact
specification bytes. Use shared strict `Discovery/preregistration_history.py`.
Bind outputs to committed source snapshots; external event anchored in source.

New surfaces: `Discovery/g_measurement_joint_inference.py`,
`Discovery/g_measurement_joint_inference_mutations.py`, corresponding two tests,
this note's specification and scientific-note companions under `Notes/`, and
`g_measurement_joint_representation_inference_{preregistration_v1,v1,mutation_results_v1}.json`
under `Experiments/GMeasurements/` (result name omits the redundant underscore
before v1 as in the user specification). Add only two read-only workflow guards.
Output includes version/ID, base, freeze/hash, external anchor, implementation
snapshot, input hashes/epochs and distinct publication IDs, scope projections,
publication decisions/traces, joint conjunction/trace, uncoupled-domain statement
and nonclaims. Do not duplicate historical numerical records.

## Verification and mutation family

Focused tests cover IDs/hashes/ancestry, malformed or missing/substituted inputs,
determinism, no live retrieval, input allowlist and E-001 isolation, projection
purity and invariance to synthetic numerical context, all 27 three-scope verdict
combinations, incompatible dominance, required-scope enforcement, correct and
non-load-bearing witness character, claim limits and historical preservation.
Use separate behavioral tests for mutation kills, excluding freshness guards.
Bounded production attacks: publication omission, required-scope omission,
unresolved promoted to true/false, broken incompatible dominance, erased midpoint
distinction, E-001 path admission, central-G influence and final-status inversion.
Known-killable calibration must differ in bytes and semantics from every production
mutation and its tuple must be disjoint. Equivalent calibration changes executable
code inertly. Import/collection errors, skips, syntax and infrastructure failures,
source-freshness failures are invalid, never kills. Bind evidence to committed
source, test, runner and definition hashes. Deterministic guards verify new result
and mutation freshness without rerunning mutations or downloading scientific sources.

Final tree: focused tests for both modules, one complete Python suite, new result
and mutation guards, one bounded mutation execution, direct byte-preservation
checks and `git diff --check`. No unrelated mutations or local Lean build.
Inspect workflow diff for accidental permissions/job changes (DM-006–008 watch).
Publish final head, verify exact-head CI. All acceptance requirements must hold;
known current outcome is prior knowledge, not a synthetic test's imposed verdict.

## Scientific note, disposition and handoff

Explain logical existential conjunction, no averaging/comparison/probability/cause/
universality, shifted versus unshifted witnesses (DM-050), and schedule-relative
unresolved -> undetermined (FH-2). Richer search belongs prospectively to the next
new measurement experiment; no FH-3/FH-4 repair or unrelated maintenance here.
Report base/freeze/source/final SHAs, prereg/spec digests, external time, all scope
and joint statuses, tests/guards/mutations/CI, blocking/deferred/future-hardening
separately and any new deferred submission. Provide a concise Claude semantic and
adversarial audit prompt without repeating CI-proven checks. After merge, return
to source feasibility of Newman 2014, later Rosi 2014; do not implement them here.

**Create a merge commit only; never squash, rebase or rewrite freeze history.**
No milestone tag or housekeeping follow-up PR is required.
