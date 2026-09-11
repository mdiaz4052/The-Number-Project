# The Number Project — NIST Published-Covariance Precision Robustness
## Bounded implementation specification, version 1

**Prepared:** 2026-09-10. **Repository:** `mdiaz4052/The-Number-Project`.
**Intended base:** `13c6b7b3bcaedda9acb1318c8a96ae39e18f538f`, the true merge of PR #51; verified through connected GitHub during specification preparation.
**Status:** specification only. No new robustness evaluator, freeze, PR, family-validity calculation, perturbation bound, or sensitivity result has been produced by this preparation.
**Implementation qualification:** **PROVISIONAL — INDEPENDENT AUDIT PENDING**.

## 1. Objective and limits

Implement one additive scientific PR answering:

> Under the explicitly declared nearest-rounding enclosure policy below, are the classifications of all four existing NIST configuration-model restrictions invariant over the simultaneous central-value, standard-uncertainty, and correlation precision family?

PR #49 currently varies the four central values within their display cells while fixing the absolute covariance. This extension varies the printed covariance inputs as well, without changing the four restrictions or their cutoff rules [R1–R3]. It is a **conditional representation-precision robustness study**, not an estimate of additional experimental uncertainty.

Evaluate all four models symmetrically. The comparatively small existing margin of `M_material` motivates the study but must not select its policy, budget, tolerances, or claimed outcome. Robust flagged, robust not flagged, witnessed classification variation, and properly bounded unresolved results are all legitimate completed results.

Do not add observations, estimate a new or corrected G, inflate variances, fit a physical mechanism, discard configurations, select a winning model, calculate p-values, assign a distribution to rounding errors, or claim a joint error rate. The inherited Gaussian/known-covariance interpretation remains a working assumption at each candidate matrix, not a newly validated sampling law. Robustness to printed precision does not establish covariance completeness, unbiasedness, physical causation, or universality of G.

**No outreach.** Use the pinned repository and supplied source evidence. Do not contact anyone, prepare correspondence, access Gmail, or reopen the canceled inquiry. No publication search or further manual transcription is needed for this scope. The #50/#51 torque-response and campaign-uncertainty limitations remain parked; no torque calculation or transfer of final-summary covariance to campaign torques is authorized [A1, A2].

## 2. Base, upstream records, and consumption boundary

Before implementation, verify the intended GitHub base once. If main has changed, determine whether the relevant inputs, source claims, model restrictions, or safeguards changed; do not silently substitute a new scientific base. Preserve the standing true-merge workflow.

Read only the current audit routing and the affected surfaces. Current audit routing is `claude_Current.md`, canonical Drive ID `1sGpOKbessezs7bcbWsaA8X-5HbvxUfpS`, as of preparation. Prefer the current same-name file if Claude replaces it. The supplemental audit has accepted #49's numerical and behavior-test layer; do not describe it as unreviewed or independently reconstruct it again merely to start this work [A1].

Pin the following upstream files by base SHA, actual byte SHA-256, and explicit JSON field selectors in the new preregistration. Whole-file hashes bind custody; selectors define numerical and claim consumption.

| Record under `Experiments/GMeasurements/` | Authorized use |
|---|---|
| `nist_2026_n4_experimental_estimator_preregistration_v1.json` | `input_projection`, source identity/locators, required upstream decisions; source of printed x, s, rho and order |
| `nist_2026_n4_experimental_estimator_v1.json` | Published-input order, displayed x, precise s, rho, input cells, baseline absolute V and authorization; no aggregate estimate/weights as scientific inputs |
| `nist_2026_estimator_source_attestation_v1.json` | Table 16/18 ordered transcription and source qualifications; exclude terminal Bayesian/dark-uncertainty values |
| `nist_2026_estimator_feasibility_v1.json` | Identity and existing experimental-covariance authorization/limits only; no new scientific reuse of its calculations |
| `nist_2026_configuration_models_preregistration_v1.json` | Contrasts, model restrictions, allowed mean columns, degrees of freedom, cutoffs, and applicable claim limits only |

The #47 certificate fields are:
`estimator.displayed_values_in_1e_minus_11_units`,
`estimator.relative_standard_uncertainty_ppm`,
`estimator.correlation_matrix`,
`estimator.absolute_covariance_matrix_in_1e_minus_11_units_squared`,
`estimator.input_order`, `finite_resolution.input_cells_in_1e_minus_11_units`, and `upstream_authorization` [R3].

The #49 result artifact, `nist_2026_configuration_models_v1.json`, is **verification-only**: exact midpoint and zero-covariance-radius parity checks in tests. Its reported classifications must not drive the production classifier, refinement, or witness search. The #49 preregistration contains unrelated #48 reference material; reading its container does not license consuming those fields.

Production must not invoke any upstream artifact builder or artifact `--check` as a subroutine. Keep mathematical computation restricted to explicitly projected inputs. No BIPM record, #48 result, #50/#51 scientific module or result, HUST/AAF record, or Lean source is an input to the new evaluator. Shared provenance helpers are code dependencies, not scientific observations. Declare and test the exact import and file/Git-read closure.

## 3. Fixed input order and precision family

Use `U = 10^-11 m^3 kg^-1 s^-2`, covariance units `U^2`, and this zero-based order:

| i | Configuration | Displayed anchor a_i, in U | Printed s_i, in ppm |
|---|---|---:|---:|
| 0 | copper_servo | 6.673642 | 23.2 |
| 1 | copper_free | 6.674021 | 30.3 |
| 2 | sapphire_servo | 6.672637 | 37.5 |
| 3 | sapphire_free | 6.673636 | 93.9 |

The correlation center, **not** the mixed diagonal/off-diagonal table representation, is:

```text
P0 = [ 1,    0.42, 0.38, 0.12 ]
     [ 0.42, 1,    0.23, 0.23 ]
     [ 0.38, 0.23, 1,    0.25 ]
     [ 0.12, 0.23, 0.25, 1    ].
```

These are existing frozen inputs, not new results. In particular, `rho_03=0.12` and `rho_12=0.23`; preserve the supplied human report's separate, already-reconciled transposition [R3, A1].

Freeze one primary study family:

```text
x_i in [a_i - 0.0000005, a_i + 0.0000005] U
s_i in [s0_i - 0.05, s0_i + 0.05] ppm
rho_ij in [rho0_ij - 0.005, rho0_ij + 0.005], i<j
rho_ji = rho_ij; rho_ii = 1 exactly.
```

All endpoints are exact rationals and included. The upper triangle supplies six shared parameters, not twelve independently perturbed entries. Four x, four s, and six correlations form a 14-parameter deterministic box. No independence or probability distribution is assigned to these parameters. The box permits every combination as a conservative enclosure; it does not assert that all combinations are realizable hidden author values.

The Table 18 caption establishes what its numbers mean, **not the authors' rounding algorithm**. Required fields include `rounding_policy_origin: project_declared_conditional_nearest_rounding_enclosure` and `source_rounding_convention_verified: false`. Retaining both endpoint ties is deliberate even though a particular tie-breaking convention might exclude one. Do not infer extra unprinted precision, truncate cells, change half-widths after seeing results, or choose a different rounding convention to secure a conclusion.

### Fixed covariance normalization

For every candidate s and P, construct

```text
D(s) = diag(a_i * s_i / 10^6)
V(s,P) = D(s) P D(s).
```

**The a_i are the immutable displayed midpoints, not the variable x_i.** Thus x affects the residual contrasts but not the relative-to-absolute scaling anchor. This preserves the established summary-level normalization while varying the covariance's printed precision. At `(s0,P0)`, V must equal the inherited #47 absolute V exactly.

Changing x to rescale V would define a different study and is not authorized here. A new result must expressly say it is conditional on this fixed-anchor normalization; it does not certify every possible normalization based on hidden unrounded G values. Rounding widths are not standard uncertainties to be added in quadrature.

## 4. Retain the four mathematical restrictions

Use the inherited contrast rows:

```text
material    = ( 1/2,  1/2, -1/2, -1/2)
method      = (-1/2,  1/2, -1/2,  1/2)
interaction = (-1,     1,     1,    -1).
```

| Model | Rows of R | Allowed mean columns | Residual df | Exact decimal cutoff |
|---|---|---|---:|---:|
| M0 | material, method, interaction | common | 3 | 7.814728 |
| M_method | material, interaction | common, method | 2 | 5.991465 |
| M_material | method, interaction | common, material | 2 | 5.991465 |
| M_additive | interaction | common, method, material | 1 | 3.841459 |

Allowed columns are `common=(1,1,1,1)`, `method=(0,1,0,1)`, and `material=(1,1,0,0)`. Check ranks and that these span the relevant nullspace; do not merely trust the df labels. Copper/sapphire denote source-mass configurations, not suspension-fibre materials [R1].

At any valid candidate,

```text
C = R V R^T
Q = (R x)^T C^-1 (R x).
```

Use the **full marginal** C. Nuisance means are profiled, not conditioned on their observed values, fixed at nominal estimates, or reinterpreted as identified instrumental effects. A point is flagged exactly when `Q > cutoff`; equality is not flagged. Retain the inherited cutoff constants, not newly evaluated quantiles.

## 5. Required certificate method

The following is the specified method, derived for this task. It is not attributed to the publication. Its proof obligations must appear in the scientific note and be tested independently. Do not implement a generic nonlinear optimizer, floating-point Monte Carlo, or an unbounded search.

### 5.1 Whole-box covariance validity

Require positive s throughout each interval and valid correlation-coordinate endpoints. Certify positive definiteness of **every** correlation matrix in the root box by exact positive-definiteness tests of all 64 upper-triangle corner matrices. Record their exact leading principal minors; positivity of all leading minors is sufficient for a symmetric matrix to be positive definite.

The certificate is valid because P is affine in its six independent entries: every box member is a convex combination of these 64 matrices, and a convex combination of positive-definite matrices is positive definite. Positive D then gives positive-definite V throughout the family, and full-row-rank R gives positive-definite C. This is a legitimate convexity use of corners for **matrix validity**, not a claim that corners extremize Q.

If a corner is singular or indefinite, record the offending exact matrix/minors, set `family_validity=BOX_CONTAINS_NON_PD`, and return `UNRESOLVED_COVARIANCE_DOMAIN` for each model. The positive-definite subset is not analyzed in this version. Do not silently remove an endpoint, filter invalid matrices, use a pseudoinverse, jitter, nearest-PSD repair, or change residual df. This disposition describes the declared precision box, not a defect in the source. A malformed source, failed pin, wrong symmetry, or arithmetic error remains an error, not this disposition.

### 5.2 Exact covariance enclosure within a subbox

For a subbox in the ten covariance parameters, compute entrywise exact interval enclosures `[V^-_ij,V^+_ij]`. For the diagonal, square the positive s interval correctly. Off-diagonal entries use all needed endpoint products of `s_i*s_j*rho_ij`, including negative and sign-crossing correlations in synthetic tests. Include the immutable `a_i*a_j/10^12` factor. Mirror each off-diagonal enclosure exactly.

Let `Vc` be V evaluated at the subbox's parameter midpoint, which need not equal the midpoint of the entrywise covariance enclosure. Define

```text
E_ij = max(abs(V^-_ij - Vc_ij), abs(V^+_ij - Vc_ij)).
```

Then `abs(V_ij - Vc_ij) <= E_ij` for the entire subbox. Entrywise extrema need not be jointly attainable; E is a safe enclosure only.

### 5.3 Rational congruence and matrix-order sandwich

For each model, factor `Cc = R Vc R^T = L diag(d) L^T` using exact rational LDL with unit lower-triangular L and positive pivots d. Set `T=L^-1` and `Z=T R`. Verify the factorization and `T Cc T^T=diag(d)` exactly.

Compute the nonnegative symmetric radius matrix

```text
F = abs(Z) E abs(Z)^T
 g_i = sum_j F_ij.
```

For `W=Z(V-Vc)Z^T`, `abs(W_ij)<=F_ij`. Consequently

```text
-diag(g) <= W <= diag(g)
diag(d-g) <= T C T^T <= diag(d+g)
```

in symmetric positive-semidefinite matrix order. A short proof uses
`abs(v^T W v) <= sum_ij F_ij*abs(v_i*v_j) <= sum_i g_i*v_i^2`, by symmetry and `2|v_i v_j| <= v_i^2+v_j^2`.

Since `d_i+g_i>0`, define

```text
H_lower = Z^T diag(1/(d+g)) Z.
```

Then `x^T H_lower x <= Q`. If **every** `d_i-g_i>0`, also define

```text
H_upper = Z^T diag(1/(d-g)) Z,
```

and `Q <= x^T H_upper x`. Explain and test the inversion-order reversal and the coordinate identity `Q=(T R x)^T (T C T^T)^-1 (T R x)`. A failed `d-g` test means this upper-bounding method is inconclusive, not that the real candidate C is singular: whole-box validity was established separately. Retain the valid lower bound, with an explicitly unavailable upper bound. Never clamp a nonpositive denominator.

H_lower/H_upper and the sandwich matrices are bounding devices. They are not source measurements, covariance completions, fitted covariances, or candidate witnesses.

### 5.4 Include the whole central-value box

For either positive-semidefinite H, let `h_i=0.0000005`, `q_H=a^T H a`,

```text
B_H = 2 sum_i h_i*abs((H a)_i)
E_H = sum_ij h_i*h_j*abs(H_ij).
```

For every `x=a+delta` with `|delta_i|<=h_i`,

```text
max(0, q_H-B_H) <= x^T H x <= q_H+B_H+E_H.
```

The required local Q certificate is therefore

```text
lower = max(0, q_Hlower - B_Hlower)
upper = q_Hupper + B_Hupper + E_Hupper, if H_upper exists.
```

The lower proof uses PSD to retain the nonnegative quadratic remainder; the upper retains **both** first- and second-order terms. Store exact terms and proof intermediates. Decimal renderings are readability-only and must not round bounds inward.

When covariance half-widths are zero, this construction must reduce exactly to #49's existing central-display bound. When all half-widths are zero, it must reduce to the exact midpoint Q. These are integration tests after the new anchor, not new pre-freeze computations.

## 6. Deterministic refinement, witnesses, and stopping

Use one shared partition of the ten covariance dimensions. The x box is bounded analytically, not subdivided. Freeze the parameter order:

```text
s0, s1, s2, s3, rho01, rho02, rho03, rho12, rho13, rho23.
```

Freeze a maximum of **255 binary splits**, hence at most **511 evaluated nodes and 256 final leaves**, for the entire four-model study—not per model. No wall-clock stopping rule, random seed, optimizer restart, post-result budget increase, or hidden second pass is allowed.

Start at the root box. Each evaluated node obtains per-model local certificates, intersected with valid inherited parent bounds: lower is the larger lower bound; upper is the smaller available upper bound, with unavailable meaning unbounded by this method. An inherited bound is valid on every child. Store its parent/proof reference. A contradiction between valid bounds or witnesses is an error.

Select the next leaf in breadth-first, then lexicographic binary-path order among leaves whose bounds still straddle the cutoff for at least one globally unresolved model, including unavailable upper bounds. Split its widest covariance dimension **relative to that dimension's original width**; break ties by the frozen parameter order. Bisect at the exact rational midpoint into two closed children sharing that boundary. Zero-width dimensions are never split. Keep every sibling and every unsplit leaf in the final cover. Model-specific closure must not remove domain coverage needed by another model.

At the root, retain the exact midpoint point evaluation as the baseline. At an evaluated node, for each still-unresolved model, evaluate at that node's covariance-parameter center with x equal to the fixed a and its 16 central-value-box vertices; deduplicate in deterministic order. These at most 17 point evaluations per node/model are **witness attempts only**. Reuse the center inverse. Save the earliest exact flagged and not-flagged witnesses, if found, with their full x, s, rho, V, Q, cutoff, parameter membership and matrix-validity checks. Do not search any other point family in v1.

A witness must use an actual candidate `V(s,P)` and x in the root box—not an interval endpoint matrix assembled entrywise or a sandwich matrix. Two witnesses, one `Q>c` and one `Q<=c`, establish actual classification variation within the **conditional precision family**. A straddling enclosure, changing bound widths, or corners alone cannot establish this.

Stop when every model is either universally classified or has both witnesses, when the split budget is exhausted, or when no eligible splittable leaf remains. Complete certificates on the entire retained frontier. A model already universally classified need not be reevaluated locally; its inherited proof must remain checkable. No second implementation pass may silently enlarge the budget after viewing NIST results.

## 7. Dispositions and required outputs

For a fully valid covariance box, compute global outer bounds from the complete frontier: minimum of leaf lower bounds, maximum of leaf upper bounds. If any upper bound is unavailable, global upper is unavailable. Use explicit null plus a reason, never JSON infinity or NaN.

Per-model dispositions, with exact cutoff comparisons:

| Disposition | Required evidence |
|---|---|
| `FLAGGED_FOR_ALL_PRECISION_VALUES` | Global certified lower strictly exceeds the cutoff |
| `NOT_FLAGGED_FOR_ALL_PRECISION_VALUES` | Finite global certified upper is at most the cutoff |
| `CLASSIFICATION_VARIATION_WITNESSED` | Two independently checked admissible point witnesses, one in each classification |
| `UNRESOLVED_FROM_CERTIFIED_BOUNDS` | None of the above; valid complete cover and explicit method/budget limitation |
| `UNRESOLVED_COVARIANCE_DOMAIN` | Root box contains a demonstrated non-positive-definite corner; valid-PD subset not analyzed |

A universal certificate contradicted by a witness is a computation/certificate error, never a precedence choice. Reject the artifact. Do not emit a single overall scientific “pass” that hides a per-model unresolved result.

The main artifact must carry: exact input projection and parameter cells; fixed-anchor policy; conditional/nonprobabilistic meaning; full matrix-validity certificate; model ranks/cutoffs; midpoint reference; partition structure and complete frontier; rational LDL/enclosure/bound proof data; exact retained witnesses; global bounds and per-model classifications; consumed budget and deterministic stop reason; source/evidence qualifications; freeze, anchor and source-snapshot provenance. State explicitly that bounds are not necessarily attained extrema. No confidence interval or posterior is produced.

The scientific note should open with a plain-language answer for all four models and distinguish robust flag, robust non-flag, witnessed variation, and inconclusive certification. Explain that even robust non-flagging is not model acceptance, and that a result says nothing about omitted physical uncertainty or the parked torque questions.

## 8. Preregistration and chronological gate

The branch's first new commit must introduce **only**
`Experiments/GMeasurements/nist_2026_covariance_precision_preregistration_v1.json`.
It must have the verified base as its sole parent. Publish that freeze and create a GitHub draft PR; record GitHub's actual `created_at`, PR URL, and freeze head before introducing the new evaluator or calculating family validity, perturbed Q values, witnesses, or robustness bounds.

Pre-freeze activity is limited to source/file reads, existing-record projection, evidence packaging, mathematical design, and validating the new JSON's syntax/schema. Do not run the new family even as a “feasibility check.” Declare **`outcome_blind=false`**, recording prior #47/#49 outcomes, the source-reading/audit history, and the motivation based on a known model margin. This freeze controls future implementation, not the origin of the hypotheses.

Freeze: upstream SHA-256/selector/value pins; the 14-parameter policy and fixed anchors; four models/cutoffs; covariance-validity and LDL-sandwich algorithms; rational decision arithmetic; refinement/witness order and budget; disposition/equality policy; source-provenance fields; planned paths and exclusions; eight semantic mutation requirements; verification obligations; no-outreach/nonclaim boundaries. No TBD scientific choices, absent widths, or missing-input-to-zero defaults.

After the anchor, serialize the source attestation and implement. Ensure implementation, tests, notes and results are introduced through descendants after the anchor; copying the supplied specification/evidence after the anchor must not misdate its earlier authorship/receipt. Sources must be committed before artifact emission. The final source snapshot must be stable across a pure true merge that inherits the complete relevant state from a parent, while a changed conflict resolution must create a new source snapshot. Use the shared strict freeze verifier and bounded caller logic; do not weaken shared history checks or import a torque evaluator just to reuse its provenance code.

## 9. Source evidence and the overlapping audit item

This PR legitimately consumes the Table 18 evidence on DM-081's surface. Add a **new**, structured source-attestation record and the supplied unchanged NIST crop. Do not edit old attestations, frozen preregistrations, old results, or historical audit labels. Do not close Claude-owned IDs.

Supplied crop: `2BC27080-4481-4F8C-9DEC-02A55A853AFC.png`, 142517 bytes;
SHA-256 `78107a66872667edb71eaaa819e6ee716abb0645e89c5c1ee9540789c3db98f5`.
The support capsule contains the exact PNG and a NIST-only receipt/reconciliation [E1]. Copy that supplied receipt unchanged to the declared receipt path. Its internal relative paths describe the original delivery capsule, not live repository paths; the new attestation must explicitly map the retained image and receipt to their repository locations. The original NIST report text is embedded in the receipt, so no extra report file is needed in the repository.

Record and validate these distinctions:

- **Miguel:** reported reading the NIST-served PDF on 2026-09-10 at 12:04 PM; timezone unspecified; printed page 26/viewer page 27 are his attribution. Original report receipt `2026-09-10T16:13:05Z`; NIST crop receipt `2026-09-10T16:15:53Z`.
- **GPT:** transcribed/compared the supplied crop and recorded the two typed pair mismatches separately. Preserve the original typed entries; do not present the corrected pairs as an additional human statement.
- **Claude:** personally inspected the supplied image in the September 10 supplemental audit and discharged the transcription component. Attribute that inspection to its actual report and reviewed heads, not a fresh audit of this PR.
- The crop shows the table number, caption, columns and entries, but not the whole publication identity, page number or URL. Full-document identity/page remain attributed. A PNG hash binds image bytes only. Do not claim original-PDF custody, independent retrieval, or an authenticated full-publication hash.
- Table 16 x values remain inherited from the pinned records; the Table 18 crop is not evidence of those central values. The supplied evidence does not establish the proposed nearest-rounding policy.

The attestation must include structured source identity/locator, reported access method/date, receipt timestamps, image path/hash scope, per-reader attribution, transcribed order/entries, original discrepancies, and remaining limitations. Validate its semantic projection against the frozen protocol and source PNG bytes. Validating the existence of prose alone is insufficient; nor does machine validation establish the source's authenticity.

Only the relevant NIST evidence is added. Do not copy BIPM evidence, whole Drive audit files, personal correspondence, or old request documents into the new production read closure. DM-080 is outside this study. DM-079/FH-14 concern the parked torque surface and are not promoted by this task. DM-082 is withdrawn [A1].

## 10. Planned file surfaces

Use the stem `nist_2026_covariance_precision`.

```text
Discovery/nist_2026_covariance_precision.py
Discovery/nist_2026_covariance_precision_mutations.py
tests/test_nist_2026_covariance_precision.py
tests/test_nist_2026_covariance_precision_mutations.py
Experiments/GMeasurements/nist_2026_covariance_precision_preregistration_v1.json
Experiments/GMeasurements/nist_2026_covariance_precision_source_attestation_v1.json
Experiments/GMeasurements/nist_2026_covariance_precision_v1.json
Experiments/GMeasurements/nist_2026_covariance_precision_mutations_v1.json
Experiments/GMeasurements/SourceEvidence/nist_2026_table18_miguel_20260910.png
Experiments/GMeasurements/SourceEvidence/nist_2026_table18_receipt_20260910.json
Notes/NIST2026CovariancePrecisionSpecification.md
Notes/NIST2026CovariancePrecision.md
```

Modify only `.github/workflows/verify.yml` among existing files: add exactly two read-only checks for the new evaluator and mutation-evidence validator. Preserve permissions, jobs, existing guards, Python/Lean versions and shared engines.

Keep exact arithmetic/interval/LDL helpers local to the new module and small; no general-purpose matrix library/refactor is requested. Shared `preregistration_history`, `source_history` and the existing isolated mutation runner may be used with explicitly declared closure. The scientific note is a generated/validated output, not an input to its own numerical artifact. Exclude new result/mutation JSON and the generated result note from the result-driving source snapshot to prevent circular provenance; bind their actual source/renderer/tests and supplied specification instead.

If a genuinely necessary extra source file is identified before freeze, declare it there. Do not expand the delivered subsystem for unrelated maintenance.

## 11. Focused tests and independent oracles

Use `unittest` and exact rationals. Separate mathematical behavior tests from artifact/provenance tests. Test actual field consumption beyond digest rejection. Minimum coverage:

1. **Inputs and meaning:** exact decimal half-widths; all 14 dimensions; endpoints; correlation symmetry/unit diagonal; correct `rho03/rho12`; units/squared scaling; fixed a versus variable x; no zero/default for missing fields; strict schema and duplicate/nonfinite rejection. Synthetic changes to a, s width, correlation width, and h must affect the appropriate computation. Changing x alone must not change V when a is fixed.
2. **Covariance validity:** 64-corner affine-box proof and exact minor inventory; a midpoint-PD synthetic box containing singular/indefinite corners must not acquire full-box validity. No endpoint filtering, inverse of a singular matrix, or invalid-source-as-nonflag behavior.
3. **Interval algebra:** signed and sign-crossing products; positive squares; Vc distinguished from entrywise interval midpoint; exact containment at constructed synthetic points. Show why elementwise interval matrices need not be attainable source candidates.
4. **Sandwich proof:** LDL reconstruction and inverse T; all cross terms in `abs(Z) E abs(Z)^T`; row-sum domination; inversion direction; positive-denominator requirement; a failed upper certificate with a genuinely positive-definite underlying family. Construct an admissible point that escapes an intentionally under-sized off-diagonal radius.
5. **Central box:** first/second-order terms, zero center with nonzero widths, PSD lower truncation, exact zero-width reduction to #49, and candidate points within the certified interval. Point/corner checks supplement the proof, never replace it.
6. **Model mathematics:** independent cofactor/adjugate inverse and mean-space GLS profiling oracle on synthetic fixtures; exact midpoint parity to the already-recorded #49 artifact; rank/nullspace/df; marginal versus conditioned covariance; common-mean shift with a held fixed; consistent unit changes and permutation of labels, anchors, cells and correlations.
7. **Decisions:** strict `>` and equality; universal flag/nonflag, two genuine opposing witnesses, straddling enclosure with no evidence of opposing outcomes, unavailable upper bound, and non-PD domain. Include a quadratic whose corners lie on one side while an interior point lies on the other. No winner or robust-physical-model inference.
8. **Coverage and budget:** exact root-to-leaf coverage; both children and shared midpoint retained; no omitted unfavorable leaf; normalized-width tie breaks and deterministic BFS ordering; inherited bounds; budget exhaustion producing honest unresolved status. Identical synthetic input yields byte-identical output, independent of traversal incidental container ordering.
9. **Evidence and isolation:** cropped-source provenance qualifications; original typed mismatches preserved but never selected numerically; missing/altered record fields rejected; excluded prior estimates, terminal/dark outputs, #48 context and audit prose have no numerical effect in valid in-memory behavior tests. Observe actual filesystem opens/reads, Git blob arguments and imports for builder, main `--check`, mutation execution and mutation `--check`.
10. **Chronology/freshness:** sole-file/single-parent freeze; GitHub anchor identity; full-history introduction checks; source commit precedes outputs; missing pinned files; modified results/certificates; pure-merge stability; changed conflict resolution; canonical serialization. Mutation of saved proof bounds, witnesses, or tree coverage must fail, even if the outer JSON is well formed.

Do not execute old #47/#49 reconstructions or unrelated mutation families as a development ritual. The one final full suite remains required by the standing protocol; new focused parity tests exist to validate the new consumer, not to reissue Claude's audit.

## 12. Eight bounded production mutations

Freeze exactly these eight **semantic requirements and designated behavior assertions**. Do not freeze artificial override statements merely to make source patching convenient. After implementation, bind each actual natural-source patch, source hash and exact assertion identity before executing the family. Production must not contain redundant assignments or dead branches whose sole role is hosting a mutant.

| ID | Deliberate fault | Required semantic counterexample |
|---|---|---|
| M1_precision_width | Collapse or understate a consumed last-digit half-width | Exact synthetic cell/enclosure differs from its declared policy |
| M2_anchor_scaling | Omit or replace an individual fixed a factor in absolute-covariance construction | Heterogeneous-anchor synthetic covariance and Q disagree with an independent oracle |
| M3_signed_interval | Drop a necessary endpoint product or use unsigned-only interval multiplication | A valid negative/sign-crossing fixture escapes the computed enclosure |
| M4_covariance_radius | Omit cross terms/off-diagonal radius contribution from the sandwich | An admissible synthetic Q escapes the purported bound |
| M5_inverse_order | Use `d+g` where the upper inverse bound requires `d-g` | A nonzero-radius synthetic case is falsely underbounded |
| M6_display_remainder | Remove a required central-value quadratic remainder from the upper bound | A zero-center/nonzero-width synthetic residual violates the result |
| M7_partition_coverage | Accept a frontier missing one required branch or silently drop an unresolved leaf | The coverage validator or universal classifier wrongly accepts an incomplete-domain fixture |
| M8_false_variation | Treat straddling certified bounds as witnessed classification variation | No opposite-class point witnesses exist in the provided evidence; the false status is rejected |

Each is an actual isolated production-source mutation executed on an otherwise valid synthetic fixture. A designated failed assertion earns the kill, not digest rejection, syntax/import/runtime errors, source-history failure, a skip, or an unrelated failure. Use the existing `-I -B` isolated runner. The unmodified baseline and executable-equivalent control must survive; a distinct faulty calibration must be killed. Save runner evidence and actual module-path bindings, including the runner itself, before and after execution.

If a selected patch cannot produce a legitimate semantic failure, fix the implementation/test/patch mapping within the already-frozen semantic requirement; do not manufacture a no-op host or relabel an infrastructure failure. The saved mutation validator must not execute the family again.

## 13. Final validation and publication

On the final tree, run the new focused tests, one complete Python suite, both new read-only checks, and `git diff --check`. Representative final commands:

```sh
python -m unittest tests.test_nist_2026_covariance_precision tests.test_nist_2026_covariance_precision_mutations -v
python -m unittest discover -s tests -v
python -m Discovery.nist_2026_covariance_precision --check
python -m Discovery.nist_2026_covariance_precision_mutations --check
git diff --check
```

The main guard checks canonical artifact/note freshness and the complete new certificate; it may recompute this bounded new study, but it must not run unrelated builders or network requests. The mutation guard validates saved execution evidence only. Execute the new mutation family once on its final mutation-relevant source tree; rerun only for a changed relevant source or plausible blocker. No local Lean run is required unless the implementation unexpectedly changes a Lean-linked contract—which is outside this specification's intended scope.

Publish the final implementation head only after required local validation. Record the exact PR head and protected Verify status. Exact-head CI is the final repository-wide automated gate; do not repeat equivalent local checks when Claude begins review. Leave the completed PR unmerged for Miguel; eventual integration must be **Create a merge commit**, never squash or rebase away the freeze/history.

Update `gpt_RollingAuditHandoff.md` in place (Drive ID `145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd`) and verify readback. Report actual results/limits, final SHA, local checks, CI, and BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING separately. Do not claim a new audit or a DM closure. No cleanup PR.

## 14. Acceptance criteria

Accept delivery only when the sole-file freeze and genuine draft-PR timestamp precede new computation; all fixed inputs/rounding/model/budget choices are consumed and enforced; all four models receive a supported disposition; the entire domain is certified or its validity limitation is explicit; every universal claim has complete coverage and every variation claim has checked witnesses; exact baseline/zero-radius parity and independent synthetic oracles pass; the eight legitimate mutations and controls have actual execution evidence; source attribution remains bounded; final local validation and exact-head CI succeed; and old frozen/source/result bytes remain unchanged.

**No favorable scientific result is required.** A mathematically justified unresolved result after the frozen budget is a completed study. An exception, bad proof, missing evidence file, or broken implementation is not.

## 15. Focused Claude audit prompt for the eventual PR

Review the exact final head and its new contract, not the whole repository history. Reuse recorded exact-head CI and prior #47/#49 audits. Inspect whether the fixed-anchor family is honestly distinguished from hidden author values; the 64-corner SPD proof is not misused to extremize Q; the interval/congruence/inverse/display bounds are valid for all parameters; full partition coverage survives early stopping; and witnesses are actual admissible points. Challenge equality handling and unresolved-versus-variation semantics. Check that the NIST crop receipt preserves the human/GPT/Claude distinction and does not imply full-PDF authentication or source endorsement of nearest rounding. Inspect natural mutation sites for actual boundary protection, not manufactured host operations. Preserve no outreach, no torque calculation, and exact coverage-qualified acceptance. No routine suite/Lean/guard/mutation reruns; targeted execution only for a concrete unproved issue.

## References and provenance of this specification

**[R1]** Repository at the intended base: `Notes/NIST2026ConfigurationModels.md`; `Discovery/nist_2026_configuration_models.py` (blob `cb758a81945cab2a6ef37b3c9f65dbdda732bdbb`). This preparation inspected the mathematical functions, input selectors, model contract and relevant chronology code; it did not rerun them.

**[R2]** `Experiments/GMeasurements/nist_2026_configuration_models_preregistration_v1.json`, PR #49 head `c329ead29399699164b8ff305530a0ee9a9300f0`, inherited at the intended base. The specification's model rows, cutoffs and nonclaims preserve that contract; the covariance-precision family and certificate algorithm above are new project-defined work.

**[R3]** #47 preregistration/certificate and #46 NIST source/authorization records listed in §2. #47 reviewed head `621f5ddc938bc62273eac42004e56d940ef376fa`. Preregistration blob `58d7946560150947a92d6a91dcc4379277de9966`. The source is Schlamminger et al., *Redetermination of the gravitational constant with the BIPM torsion balance at NIST*, *Metrologia* 63 (2026) 025012, DOI `10.1088/1681-7575/ae570f`; source URL `https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075`. Source identity and Table 16/18 locators are inherited/attributed, not newly authenticated in this preparation.

**[A1]** Claude Current, supplemental-pass version, `https://drive.google.com/file/d/1sGpOKbessezs7bcbWsaA8X-5HbvxUfpS/view`, and its named supplemental report `https://drive.google.com/file/d/1vs_7eTG60upfg8kLX-VwA2i-iLbs24d2/view`. Current was fetched during preparation; pertinent attribution, scope and DM-081 status were inspected. Superseded same-name records do not control.

**[A2]** GPT rolling handoff, `https://drive.google.com/file/d/145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd/view`, current operating boundary and proposal sections; GPT source-readiness record `https://drive.google.com/file/d/1OzUN3bkubA3JdfnZvfiTR9ofy_V9lIjW/view`. These provide context, not scientific inputs or proof of correctness.

**[E1]** User-supplied NIST Table 18 PNG and original September 10 reading report, preserved in this specification's support capsule. The PNG hash was checked locally during preparation. No OCR, source re-retrieval, new scientific numerical experiment, or preregistration publication was performed. Mathematical inequalities in §5 are design derivations to be implemented and independently checked, not claims that the NIST family already passed them.
