# Implementation record for the supplied specification

The specification below was prepared before the external freeze. Its pre-freeze obligations were completed with the source-access limits recorded in the frozen JSON. GitHub main remained at its intended base. PR #48 was created at 2026-09-09T02:59:14Z with sole freeze commit bf310acdbbef61100efa50fe411ae7873593db4c. The JSON protocol is the result-driving freeze; this copied specification is explanatory. No independent acceptance of PR #47 is inferred.

# The Number Project — BIPM–NIST Common-Constant Diagnostic
## Bounded implementation specification, v1

Prepared: 2026-09-09 UTC. Status: specification only; not a frozen preregistration, implementation, or scientific result. No new real-data diagnostic has been evaluated in preparing this document.

## 1. Objective and nonclaims

Implement one scientific PR answering:

> Under an explicitly declared fixed-covariance Gaussian summary model, do the NIST four-configuration results show internal lack of fit, and is the difference between the existing project-defined BIPM and NIST aggregates flagged across the full admissible range of cross-campaign correlation?

Deliver two separately interpreted diagnostics, not a pooled hypothesis test. The within-NIST diagnostic tests the four-input experimental-only common-mean model. The cross-campaign diagnostic compares two existing aggregates under their declared marginal uncertainty models.

This is a new, conditional statistical interpretation of published summaries. It is not a new measurement, an outcome-blind discovery, reproduction of NIST equation (64), validation of either apparatus, determination of the actual cross-campaign covariance, or evidence identifying a physical cause. Neither non-rejection nor rejection establishes whether G is universal. Do not produce a combined BIPM–NIST estimate of G, fit additional variance, remove configurations, or introduce a Bayesian/random-effects model.

## 2. Intended base and acceptance state

Repository: `mdiaz4052/The-Number-Project`.

Intended base, verified through GitHub during preparation:

`4e8acdebc5b03d03d5039c24a73bcc37e44711e2`

This is the true merge commit of PR #47. Its implementation verification head is `621f5ddc938bc62273eac42004e56d940ef376fa`. The last independently audited and merged checkpoint established by the current handoff is PR #46, merge `30227abeb3f6ab009b70c429e491bb015e798542`. PR #47 is provisionally integrated and independently unaudited in the retrieved handoff; GitHub supersedes that handoff's stale open/unmerged integration status. [S1, S2]

Any result consuming PR #47 inherits **PROVISIONAL — INDEPENDENT AUDIT PENDING** until the relevant dependency chain is accepted. Store the status at freeze as provenance, not as a mutable scientific input or a claim of subsequent approval.

At implementation start, verify the intended base once. If main has advanced, identify the change and explicitly re-pin the specification before freezing; do not silently change the base. No PR number is reserved by this document. Suggested branch: `codex/bipm-nist-common-constant-diagnostic`.

## 3. Frozen input and source contracts

### 3.1 Existing records to consume, not rewrite

Use the following records at the intended base, with full SHA-256 digests and exact authorized field projections recorded in the new preregistration:

```text
Experiments/GMeasurements/bipm_2014_correlated_estimator_preregistration_v1.json
Experiments/GMeasurements/bipm_2014_correlated_estimator_source_attestation_v1.json
Experiments/GMeasurements/bipm_2014_correlated_estimator_v1.json
Experiments/GMeasurements/nist_2026_n4_experimental_estimator_preregistration_v1.json
Experiments/GMeasurements/nist_2026_n4_experimental_estimator_v1.json
Experiments/GMeasurements/nist_2026_estimator_feasibility_v1.json
Experiments/GMeasurements/nist_2026_estimator_source_attestation_v1.json
```

Consume rational records, not rendered decimal approximations. Pin artifact identities, source identities, input order, units, estimator model identities, relevant authorization decisions, and the exact field paths used. Validate covariance dimensions, symmetry and positive definiteness, positive variances, normalized weights, and consistency of the consumed central values and variance identities with their projections. This is validation of the new consumer, not a request to regenerate historical certificates.

Preserve every existing `NOT_EVALUATED` and Bayesian `NO_GO`/`NOT_AUTHORIZED` field. The new protocol authorizes its own comparison; it does not retroactively expand earlier claims. [S3–S5]

### 3.2 BIPM convention

Let all numerical G coordinates be expressed in the shared unit

`U = 10^-11 m^3 kg^-1 s^-2`.

Set `b` to the exact reconstructed midpoint in the PR #44 artifact, `I_B` to its full fixed-weight aggregate enclosure, and `r_B` to its exact combined relative variance in ppm squared.

The existing summaries are the servo/Cavendish values `6.67515` and `6.67586`, uncertainties `61` and `54` ppm, and covariance `-2080 ppm²`. Their derived weights and relative variance are inherited, not independently selected. [S3]

Define the new consumer's absolute variance by

`v_B = b² r_B / 10^12`.

This is an explicit **project-defined common-reference scaling convention**, with reference `b` held fixed. Equivalently, apply the common factor `b² / 10^12` to the existing relative covariance matrix. It preserves PR #44's weights. It is not a claim to recover hidden author covariance values.

Do not rescale the two BIPM component errors by their separate midpoints and recompute weights. Do not substitute the published final central value, rounded final uncertainty, printed weights, or the intersection with the published final-value cell. Those fields remain comparison-only upstream. In particular, `I_B` is the full reconstructed enclosure, not a target-conditioned subset. [S3, S4]

### 3.3 NIST convention

Consume `x`, the four displayed values in their frozen order; `V`, the exact absolute experimental covariance; `w`, the fixed weights; `n = w^T x`; `v_N = w^T V w`; and the fixed-weight aggregate enclosure `I_N`.

Keep PR #47's `u_i = x_i s_i / 10^6` and `V_ij = rho_ij u_i u_j` conventions. Table 18's precise uncertainties, not Table 16's rounded uncertainty labels, control the covariance. [S5]

Do not import NIST's Bayesian consensus, configuration corrections, dark-uncertainty estimates, CODATA, or other measurements into either diagnostic. Do not recalculate weights or covariance over the publication cells.

### 3.4 Bounded cross-campaign source review

Before the new freeze, inspect only the relevant source passages: the corrected BIPM paper's covariance/combination treatment; NIST's apparatus lineage, experimental uncertainty treatment and concluding discussion; and directly linked clarification or correction material if necessary. Record DOI, version/access information, section/page locators, and the closest relevant positive statements.

The NIST paper describes reuse of the BIPM apparatus, so a new team and location do not establish statistical independence. Its Table 18 correlations are within NIST, not estimates of BIPM–NIST correlation. [S6]

The review must distinguish a numerically identified cross-campaign covariance from a covariance not identified in the reviewed material, inaccessible evidence, or conflicting evidence. Do not claim exhaustive absence. No metadata-derived value, midpoint-difference fit, or guessed zero is permitted.

For v1, retain the full `rho in [-1,1]` envelope even if a source suggests a narrower scenario. This is a mathematically admissible aggregate-covariance class, not a measured uncertainty interval or prior distribution for rho. A narrower, source-authorized model would be separate work. Missing cross-campaign covariance alone does not prevent this envelope diagnostic.

## 4. Statistical model and operational cutoffs

Assume, for calibration only, zero-mean jointly Gaussian summary errors and covariance matrices treated as fixed and known. Under the within-NIST null, `E[x] = mu 1`. Under the aggregate-comparison null, `E[b] = E[n] = mu`, with marginal variances `v_B`, `v_N` and covariance `rho sqrt(v_B v_N)`.

These are declared working assumptions. Published standard uncertainties and rounded covariance entries are not independently proven population parameters. The calibration is nominal under this fixed-summary model, not an exact experimental error guarantee. Publication-cell ambiguity is a separate deterministic sensitivity calculation, not an additional random error term.

Use upper-tail chi-square reference distributions: three degrees of freedom for NIST's four observations with one fitted mean; one degree of freedom for the standardized aggregate contrast. The rank/whitening derivation shall be included in the result note. [S7]

Freeze these **operational rational cutoffs**:

- within-NIST: `c_3 = 7.814728`;
- aggregate contrast: `c_1 = 3.841459`.

They are upward-rounded approximations to the respective 95th percentiles. Call the calibration **nominal 5%**, and disclose that the actual implemented cutoffs are those exact rationals. Flag only for a statistic strictly greater than its cutoff; equality is not flagged. Verify the reference-percentile approximations independently of real data before the freeze.

Do not compute p-values in v1. Do not claim a joint 5% error rate, multiply tail probabilities, add the two statistics, or treat the two diagnostics as independent evidence. Prior selection and outcome exposure preclude an outcome-blind confirmatory-discovery claim regardless of nominal calibration.

## 5. Required diagnostics

### 5.1 Within-NIST lack of fit

At the displayed midpoints, compute exactly:

`Q_N = (x - n 1)^T V^-1 (x - n 1)`.

Also establish the equivalent form

`A = V^-1 - (V^-1 1)(V^-1 1)^T / (1^T V^-1 1)`,

`Q_N = x^T A x`.

Use exact rational linear algebra. Check `A 1 = 0` and the rank-three residual interpretation. The midpoint status is `FLAGGED_UNDER_DECLARED_MODEL` or `NOT_FLAGGED_UNDER_DECLARED_MODEL`.

For publication-resolution sensitivity let `h_i` be each input cell half-width, and define

`L = 2 sum_i h_i |(A x)_i|`,

`E = sum_ij h_i h_j |A_ij|`.

The required conservative enclosure is

`Q_N(display cells) in [max(0, Q_N - L), Q_N + L + E]`.

Its lower bound uses positive semidefiniteness of `A`; document that derivation. This is a certified outer bound, not necessarily the exact minimum/maximum. Fixed weights are applied to each possible cell value; the fitted mean may move with those values, but the covariance and weights stay fixed.

Report `FLAGGED_FOR_ALL_DISPLAY_VALUES` if the lower bound exceeds `c_3`; `NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES` if the upper bound is at most `c_3`; otherwise `UNRESOLVED_BY_DISPLAY_BOUND`. Do not add a general optimizer to sharpen an inconclusive bound in this PR.

### 5.2 Aggregate difference and correlation sensitivity

Compute the signed difference `D_0 = b - n` and its exact display enclosure:

`I_D = [low(I_B) - high(I_N), high(I_B) - low(I_N)]`.

For a fixed rho with positive contrast variance,

`v_D(rho) = v_B + v_N - 2 rho sqrt(v_B v_N)`,

`T(rho,D) = D² / v_D(rho)`.

Report `rho = 0` as an explicitly hypothetical, uncorrelated reference scenario, never as an established independence finding or the default empirical result.

Let `a_min` be the minimum absolute value in `I_D` (zero if it contains zero), and `a_max` its maximum absolute value. With `u_B = sqrt(v_B)` and `u_N = sqrt(v_N)`, the full covariance-class endpoints are

`v_D,min = (u_B - u_N)²`,

`v_D,max = (u_B + u_N)²`.

When `v_D,min > 0`, the exact all-rho, all-display statistic range is

`T_min = a_min² / v_D,max`,

`T_max = a_max² / v_D,min`.

Report:

- `FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES` when `T_min > c_1`;
- `NOT_FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES` when `T_max <= c_1`;
- `RHO_OR_DISPLAY_DEPENDENT` otherwise.

The last classification indicates that admissible choices produce different threshold dispositions, not that rho has been estimated. Preserve separate midpoint, display, and rho diagnostics so the source of dependence is visible.

Do not replace the continuous envelope with a finite rho grid. For equal marginal variances, rho = 1 has zero contrast variance; emit `UNRESOLVED_SINGULAR_ENDPOINT` for the closed-family classification and a separately labeled valid rho-zero reference. Do not divide by zero, output NaN, regularize, or silently discard the endpoint. Invalid marginal variances or covariance geometry fail validation rather than become a scientific non-rejection.

### 5.3 Numerical representation and interpretation

Rational statistics, units, cell bounds and cutoffs remain exact. Endpoint comparisons involve at most rational expressions and `sqrt(v_B v_N)`; use an exact sign-aware algebraic comparison, or an independently certified outward enclosure with an explicit unresolved outcome. A fixed floating-point precision alone is not a certification. Do not square inequalities without first checking signs. Serialize the algebraic operands and supply decimal approximations only for readability.

Report both diagnostics regardless of their outcomes. If NIST is internally flagged, state that the experimental-only model is already challenged internally and that the cross-campaign statistic remains a conditional sensitivity result under that same model. Do not suppress it, inflate the variance, or treat it as independent confirmation.

Allowed conclusion: “The declared model is flagged by this diagnostic under the stated uncertainty/dependence assumptions.” Non-rejection means only that this diagnostic did not flag the model. Never translate either outcome into a probability that G is constant, a proof of model truth/falsity, or identification of apparatus bias or new physics.

## 6. Preregistration and chronology

Before branch publication, complete the bounded source review, validate the selected upstream projections, and resolve any genuine source/contract blocker. The new preregistration must contain actual SHA-256 pins—not placeholders—and the complete result-driving model, cutoffs, decision vocabulary, numerical boundary policy, prior-knowledge disclosure, source-review projection and planned file inventory.

The first branch commit must introduce **only**:

`Experiments/GMeasurements/bipm_nist_common_constant_preregistration_v1.json`.

Validate JSON syntax, duplicate-key rejection and schema locally before committing. Push the freeze, open a draft PR, and record the real GitHub-controlled creation timestamp. Only afterward add new diagnostic source, numerical results or result-bearing notes. Record source-review/specification preparation as pre-freeze work; do not backdate or misdescribe it.

Set `outcome_blind: false`. Explicitly disclose that the source numbers, published discrepancy, previous estimator outputs and source discussion were already known. This document does not constitute the external freeze.

The validator must actually consume or validate each frozen result-driving field; matching hardcoded prose is insufficient. Before new artifact emission, commit the final result-driving source snapshot and bind its paths/digests. Keep the result artifact outside its own source-digest closure. Preserve the freeze and chronology through a true merge commit; no squash or rebase.

## 7. Bounded implementation surfaces

New files:

```text
Discovery/bipm_nist_common_constant.py
Discovery/bipm_nist_common_constant_mutations.py
Experiments/GMeasurements/bipm_nist_common_constant_preregistration_v1.json
Experiments/GMeasurements/bipm_nist_common_constant_source_attestation_v1.json
Experiments/GMeasurements/bipm_nist_common_constant_v1.json
Experiments/GMeasurements/bipm_nist_common_constant_mutations_v1.json
Notes/BIPMNISTCommonConstantDiagnosticSpecification.md
Notes/BIPMNISTCommonConstantDiagnostic.md
Notes/BIPMNISTCommonConstantMutationValidation.md
tests/test_bipm_nist_common_constant.py
tests/test_bipm_nist_common_constant_mutations.py
```

Modify `.github/workflows/verify.yml` only to add the two new read-only `--check` guards. [S8]

Prefer a small new consumer with narrow pure numerical functions and typed/validated projections. Reuse suitable existing exact helpers without modifying upstream scientific modules or shared provenance/mutation infrastructure. No new numerical dependency is required by this design; no Lean changes are planned.

The source attestation records the frozen bounded review and its limits. The main artifact records input pins, model identity, units, assumptions, exact/symbolic diagnostic values, midpoint/display/rho dispositions, inherited provisional status, and claim limits. Distinguish computational validation errors from scientific diagnostics. Keep data dependency and file/Git-read closures explicit and bounded; full-file hashing may encounter comparison-only fields, but those fields must not reach the numerical projection.

E-001 remains live outside this scientific dependency boundary. Do not consume HUST authorization artifacts. PR #47's DM-073 and DM-077/DM-070 repairs remain implementer claims pending Claude's disposition; do not close IDs or reopen unrelated maintenance. The new consumer must validate its frozen fields and permanently test its actual read closure. [S2]

## 8. Focused tests and bounded mutation requirements

Behavioral tests must use small hand-checkable examples and an independently structured oracle, not merely compare production code with itself or with a freshly emitted artifact.

**Mathematics:** verify both Q formulas, nonnegativity, common-shift invariance, consistent positive unit rescaling, input/covariance permutation invariance, rank/degrees of freedom, covariance influence, exact cutoff equality, and normalized fixed-weight behavior. Verify BIPM's relative-to-absolute scaling and NIST's inherited absolute model separately.

**Sensitivity:** test all NIST input-box corners and additional interior cases against the conservative bound; include a deliberately unresolved case. Test difference-cell signs and zero crossings, analytic rho extrema and monotonicity, threshold outcomes on both sides, negative correlation, and the singular equal-variance endpoint. Include cases where covariance or display ambiguity changes the disposition.

**Semantics/provenance:** reject unit/order/schema errors, duplicate/nonfinite inputs, invalid covariance, unauthorized upstream states, changed source pins, and malformed/stale artifacts. Test that published terminal values, rounded uncertainties, dark-uncertainty outputs and CODATA cannot influence the numerical projection. Keep these behavior tests distinct from digest-rejection tests. Assert actual repository file/Git-read closure, not only a declared inventory.

Run one new bounded production-source mutation family covering: covariance off-diagonals; BIPM ppm-squared scaling; cross-covariance sign or forced rho-zero substitution; display-cell collapse; wrong degrees of freedom/cutoff mapping; omitted mean fitting; forbidden-terminal consumption; and promotion of nominal diagnostics/provisional outputs into unsupported claims. Tests may share mutants where they cover the same failure boundary, but freeze the actual mapping.

Include a surviving baseline, a killed faulty calibration and a surviving equivalent calibration. Only the designated behavioral failure earns kill credit; import, syntax, runtime, history, skip and infrastructure failures do not. Do not rerun unrelated historical mutation families.

## 9. Final validation and acceptance

Use the standing final-tree protocol once. The materially relevant commands are the new focused test modules, one complete `python -m unittest discover -s tests -v` pass, the two new `--check` guards, and `git diff --check`. Add a directly implicated upstream guard only for an actual consumer-contract ambiguity or relevant change, not merely to repeat retained same-SHA evidence. The current workflow supplies repository-wide guards and Lean attestation on the final PR head. [S8]

Acceptance requires byte-reproducible new artifacts; valid source/freeze chronology; correct identities and units; independently checked diagnostics and sensitivity bounds; all three ordinary scientific outcome classes reachable in synthetic tests; explicit singular handling; preserved Bayesian and target-independence boundaries; inherited provisional labeling; passing focused/mutation/final-suite checks; and successful exact-head CI.

No particular real-data outcome is required for acceptance. An unresolved diagnostic or lack of identified cross-campaign covariance is a legitimate result. A contradictory input authorization, invalid source transcription, non-reproducible result or unsupported scientific claim is a blocker and must not be relabeled scientific indeterminacy.

Publish one bounded scientific PR. Do not merge as part of this specification-preparation task. No maintenance-only closure PR is authorized.

## 10. Independent audit handoff

Audit the new final head together with its PR #47 scientific dependency, reusing retained automated evidence. Focus on: preservation of the two different uncertainty conventions; the nominal Gaussian/known-covariance assumptions; correct three- and one-degree-of-freedom interpretations; conservative NIST display bounds; exact continuous rho coverage; source-supported versus assumed dependence; exclusion of final-value conditioning and dark-uncertainty substitutions; and whether every conclusion remains conditional and provisional.

Check freeze/anchor/source ancestry and the behavioral mutation evidence. Separate BLOCKING, DEFERRED MAINTENANCE and FUTURE HARDENING. Identify the exact reviewed dependency chain; do not infer independent acceptance from merge or CI status. Any consciously deferred repair must be submitted through Miguel using the standing protocol, without assigning a DM ID.

## Source references

[S1] GitHub `main` branch metadata, read during this preparation; merge and parent identities at `4e8acdebc5b03d03d5039c24a73bcc37e44711e2`.

[S2] Live Drive `claude_Current.md` (file `1flh4pHVdz80ClLZO5IQo2xG63EGWVsN0`) and `gpt_RollingAuditHandoff.md` (file `145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd`), read during preparation. These establish recorded audit dispositions, not up-to-date integration metadata; the handoff's PR #47 unmerged label is stale.

[S3] `Notes/BIPM2014CorrelatedEstimator.md` and `Discovery/bipm_2014_correlated_estimator.py`, at the intended base.

[S4] `Experiments/GMeasurements/bipm_2014_correlated_estimator_source_attestation_v1.json`, at the intended base. Primary paper: Quinn, Speake, Parks and Davis, *The BIPM measurements of the Newtonian constant of gravitation, G*, DOI `10.1098/rsta.2014.0032`, sections 11(d) and 12, Table 1; corrected provenance also identifies DOI `10.1103/PhysRevLett.113.039901`. The attestation records its source-access limitations; this preparation does not claim a new independent primary-PDF verification of BIPM's numerical transcription.

[S5] `Experiments/GMeasurements/nist_2026_n4_experimental_estimator_preregistration_v1.json`, `Experiments/GMeasurements/nist_2026_n4_experimental_estimator_v1.json`, and `Discovery/nist_2026_n4_experimental_estimator.py`, at the intended base.

[S6] Schlamminger et al., *Redetermination of the gravitational constant with the BIPM torsion balance at NIST*, *Metrologia* 63 (2026) 025012, DOI `10.1088/1681-7575/ae570f`; NIST-hosted PDF `https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075`. Relevant source locations: printed pages 3–5 (apparatus lineage), 25–27 (experimental versus Bayesian layers), and concluding discussion. PDF screenshot index 27 shows printed page 27, including the distinction between experimental and added dark uncertainty. The remaining bounded review is a pre-freeze implementation step, not falsely reported as completed here.

[S7] NIST/SEMATECH e-Handbook, “Chi-Square Distribution,” section 1.3.6.6.6, and “Critical Values of the Chi-Square Distribution,” section 1.3.6.7.4. Distribution references support nominal calibration; the operational cutoffs, test selection and sensitivity policies are specified by this project. The exact upper-rounded operational constants are not quoted as values from NIST's coarsely rounded table.

[S8] `.github/workflows/verify.yml` at the intended base. Specification preparation does not rerun or replace its retained CI evidence.
