# Schlamminger 2006 Table VII rounding-consistency audit

## Objective and base

Base: `7e01334a911ab5bd664b2e32c16149c6739b5f7c` (PR #39 merge).
Evaluate both statistical and systematic Table VII subtotals of Schlamminger et al.
(2006), independently of HUST and regardless of either verdict. This is a
prospective classification freeze with known source data, not a blind physical
prediction. No particular outcome is an acceptance criterion.

## Sources and exact transcription

Publication identity: American Physical Society, *Physical Review D* 74, 082001,
DOI `10.1103/PhysRevD.74.082001`, published 4 October 2006. The publisher title is
“Measurement of Newton's gravitational constant”.

Numerical authority: author manuscript `gr-qc/0609027v1` (7 September 2006),
“A Measurement of Newton's Gravitational Constant”, Table VII and Section V,
printed/PDF page 22. arXiv is the manuscript host, not the publisher.

| Component ID | Statistical ppm | Systematic ppm |
| --- | --- | --- |
| weighings | 11.6 | blank |
| tm_sorption | 7.4 | 7.4 |
| linearity | 6.1 | blank |
| calibration | 4.0 | 0.5 |
| mass_integration | 5.0 | 3.3 |
| terminal subtotal | 16.3 | 8.1 |

Blank cells are omitted, never represented as zeros. “Measured Signal” is a
group heading, not an additional component. The common central value
`6.674252e-11 m^3 kg^-1 s^-2` (Section V) is context required by the generic
positive-G schema; it must have no influence on one-run relative variance.
Section V describes one-sigma uncertainties and RSS combination of statistical
and systematic uncertainties. This audit declares RSS within each printed
subtotal; it does not infer an undocumented cross-component covariance model.
The two scopes have separate terminals; repeated 7.4 values impose no latent
equality constraint between scopes. No joint full-publication consistency is claimed.

Pin the retrieved v1 PDF byte count and SHA-256, its version and locator, and the
exact normalized source-attestation projection. Use hash-only external-document
storage, consistent with existing official source records. APS identity is
verified through its DOI record; an HTTP 403 publisher response is not source
evidence and receives no invented content hash. CI verifies committed metadata,
projection hashes and preserved bytes without downloading live sources. PDF
semantic transcription remains reviewable human/agent source evidence, not a
claim that hashing proves the table's meaning.

## Declared model and exact engine reuse

Use `Discovery/rounding_consistency.py` unchanged. For each scope construct one
`Budget` run, with existing `independent` component correlation tags (the tags
are immaterial for one run). With positive g and S = sum_k x_k^2 > 0,
p_1 = (1/(g^2 S))/(1/(g^2 S)) = 1, combined g = g, and q_1 = p_1 g/g = 1.
Both existing correlation forms therefore reduce exactly to R^2 = sum_k x_k^2.
The interval q_1 endpoints similarly reduce to 1; for positive components the
variance enclosure is [sum_k lower_k^2, sum_k upper_k^2]. This identity holds for
every positive g, so replacing g cannot change enclosure, relative candidate
variances, membership, or classification. Only context central-value fields change.

Declare nearest rounding to 0.1 ppm, without attributing that convention to the
authors. Every printed component has closed domain [c-0.05,c+0.05] ppm.
The terminal domains are [16.25,16.35] and [8.05,8.15] ppm.
Use exact fractions, never floating-point tolerances or formatted decimal verdicts.
Display square-root bounds outward to six decimal places, from the frozen policy.
No alternative rounding model, new correlation class, weighting rule, optimizer,
or engine mutation is authorized.

Evaluate the full PR #39 schedule in its exact order for each scope:
`0, -1/8, +1/8, -2/8, +2/8, ..., -7/8, +7/8`.
Every x_k(t) = midpoint_k + t * half_width_k. Calculate both scope records before
passing either terminal comparison to classification. The numerical API receives
only a component projection, g, rounding policy and schedule. A separate terminal
API validates and uses comparisons. Neither HUST targets nor external G references
are calculator inputs. No adaptive search or post-result candidate additions.

Reuse the three exact outcomes: disjoint closed squared enclosures establish
`incompatible`; the first frozen candidate with interior component membership
and strictly interior squared comparison membership establishes `compatible`;
overlap without a scheduled witness is `unresolved`. Retain generic zero-width
control semantics. Missing or malformed evidence raises, never yields a verdict.
Serialize calculations separately from terminal comparisons and decisions, with
exact exclusion endpoints or the first witness and its membership certificate.

## Chronology

Prepare these exact specification bytes before branching. Create the branch
from the base above and commit only
`Experiments/GMeasurements/schlamminger_2006_rounding_consistency_preregistration_v1.json`.
The freeze's sole parent must be the intended base. Pin this specification's
path/hash, source roles, exact transcription, both scopes, prior knowledge,
rounding and candidate rules, classifications, validation and claim limits.
Publish the freeze and open one draft PR before production code or either result;
record GitHub's PR-created timestamp and freeze head in the implementation.
Commit this specification after the freeze without changing its bytes.
Reuse `Discovery/preregistration_history.py` unchanged for full-history freeze
verification. Any genuine correction needs a versioned amendment. No squash,
rebase, or rewriting preregistration bytes, even temporarily.

## Implementation and checks

New surfaces: this specification; versioned preregistration, source attestation,
result and bounded mutation-attestation JSON under `Experiments/GMeasurements/`;
`Discovery/schlamminger_2006_rounding_consistency.py`;
`Discovery/schlamminger_2006_mutations.py`; and focused tests. Modify only
`verify.yml` to integrate the new read-only artifact/source/mutation guards.
Preserve all pre-existing GMeasurements artifacts and the generic engine bytes.

Source and result guards must validate frozen hashes, both exact ordered scopes,
source roles, input and terminal projections, frozen rounding and schedule,
specification hash, preregistration history, committed calculation source state,
baseline preservation and deterministic artifact freshness. Result-driving
source must be committed before final artifact emission; artifact-only commits
must not change the calculation source anchor.

Focused tests cover every transcribed value/subtotal, blank omission, exact
intervals, omitted/merged/swapped scopes, unconditional two-scope execution,
independent sum-of-squares point/enclosure oracle, q_1=1, positive-g invariance,
all 15 candidates and order, comparison independence, corrupt/deleted sources,
malformed terminals, separated result records, unchanged generic three-outcome
controls, preserved HUST bytes and exclusion of external/HUST calculator inputs.
Use adversarial synthetic targets without requiring either experimental verdict.

Add a self-contained bounded Schlamminger mutation family, without modifying or
rerunning unrelated families. Attack source substitution, radius corruption,
scope omission, target leakage, verdict inversion, and preregistration/source-pin
bypass. Each mutant runs named behavioral or integrity tests in an isolated copy,
with known-killable and equivalent-surviving controls. Import/syntax/infrastructure
failures and dirty-source freshness failures are invalid, not behavioral kills.
Bind results to committed source/test/mutation definitions and require complete
inventory, valid calibration, and all production mutants killed. `--check` verifies
stored evidence and source pins; it need not execute mutations on each CI run.

On the final tree run focused tests, one full Python suite, the new artifact/source
guard, the bounded mutation execution/guard, and `git diff --check`. Use exact-head
protected CI for repository-wide and Lean/proof attestation. No local Lean build.

## Claim limits and handoff

This is a conditional published-table representation audit. It does not reproduce
raw data, the complete beam-balance estimator, or final absolute (109)(54)
uncertainties; infer hidden author values or actual rounding convention; identify
a discrepancy's cause; compare measured G with HUST; test G universality; make a
new physical prediction; upgrade replication depth; or alter HUST evidence status.

Report final and freeze SHAs, PR-created timestamp, PR URL, both exact verdicts and
certificates, local/CI checks, and blocking/deferred/future-hardening findings
separately. Claude's audit should attack source semantics, transcription, chronology,
target isolation, one-run reduction, certificates and claim limits. Required merge
method: merge commit only. No follow-up housekeeping PR. Rosi et al. 2014 is a
future research candidate only, contingent on review of this claim.
