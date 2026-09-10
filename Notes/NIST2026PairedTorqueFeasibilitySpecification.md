# The Number Project — NIST Campaign-Level Paired-Torque Contrast and Uncertainty Feasibility

Implementation specification, version 1 — September 10, 2026

**Repository:** `mdiaz4052/The-Number-Project`
**Intended base:** `6f722e92a09bc598aa06920e89ba02059bf1e7a4` — true merge of PR #50
**Review qualification:** **PROVISIONAL — INDEPENDENT AUDIT PENDING**
**Scope:** one source-bound feasibility PR; no real-data hypothesis test or torque fit
**Integration:** leave unmerged for Miguel; eventual **Create a merge commit**, never squash or rebase

## 1. Objective and stopping boundary

Determine whether the published campaign-level measurements support a later test of this one restriction:

> After the explicitly documented treatment of corrections, the electrostatic-servo minus free-deflection torque difference has the same expected additive value in all four campaigns, under a declared experimental uncertainty model.

The campaigns are copper at 0°, 120°, and 240° clocking, and sapphire. This question concerns the eight Table 15 torque summaries **before** the copper posterior aggregation. It neither reconstructs that aggregation nor overrides PR #50's final-summary `NO_GO_IDENTIFIABILITY`.

Deliver a deterministic, source-bound certificate of comparison and uncertainty sufficiency. Identify the smallest uncertainty object needed for the restriction, rather than requiring all unavailable details of the experiment. A bounded, supported NO-GO is a completed scientific deliverable, not an implementation blocker.

Even if feasibility is GO, this PR must not calculate an observed paired difference, observed residual contrast, fitted common offset, discrepancy statistic, p-value, confidence interval for an offset, corrected torque dataset, or any new G value. Do not select a mechanism, inflate uncertainties, discard a campaign, choose a favorable covariance, or run another Bayesian reconstruction. No significance cutoff is needed in this freeze.

The sole external deliverable beyond the feasibility record is a **draft technical source request**, not an email to be sent. No author contact, Gmail write, or automated follow-up is authorized.

## 2. Base, dependency boundary, and current audit context

GitHub `main` was checked during specification preparation and equals the intended base above. Retained merge metadata identifies PR #50's reviewed implementation head as `2faefa05689466ef852029d3e4b61dca4c2a2900`. Its final-head Verify #300 and merge Verify #301 are retained successful evidence; do not repeat those checks to prepare this PR. [R1]

At implementation start, verify the intended base once. A substantive base change requires reconciling scope before freezing; do not silently transplant a freeze. Synchronize a local implementation workspace only as needed under the standing protocol.

The last independently accepted checkpoint recorded in the retrieved audit context is PR #46. PRs #47–50 remain independently unaudited. The rolling handoff still described #50 as open when retrieved for this specification; GitHub's confirmed merge controls integration state. Reconcile that status in the next handoff update without changing Claude's records. [R2]

PR #50 and `Notes/NIST2026TorqueResponseFeasibility.md` supply motivation and a protected interpretation boundary. They are **not numerical inputs**. Do not import the #47–50 scientific builders or read their result artifacts to build the new certificate. Reusing the existing source-history helpers is a code dependency, not empirical evidence.

E-001 remains outside the intended numerical, provenance, and claim boundary. Preserve that isolation. Relevant routed patterns from `claude_Current.md` are frozen source quantities and policy consumption (DM-073/076), honest attribution and source access (DM-074/078 and FH-13), full-history chronology (DM-075), and observed read closure (DM-070/077). Inspect only overlapping detail files that are actually retrievable. Do not assign or close Claude-owned IDs or import the full deferred register. [R2]

## 3. Fixed comparison, labels, and units

### 3.1 Two distinct differences

Each source entry is itself a recovered difference between two source-mass positions. The proposed *paired* difference then subtracts the two operating methods. Do not confuse these two operations, replace a peak-to-peak entry by a one-sided amplitude, or introduce another factor of two.

Freeze this canonical order:

```text
copper_0_servo,   copper_0_free,
copper_120_servo, copper_120_free,
copper_240_servo, copper_240_free,
sapphire_servo,  sapphire_free
```

Let `y` denote these eight torque summaries. The paper's Table 15 row-major order is sapphire, copper 0°, copper 120°, copper 240°, with **free before servo** in each row. The zero-based canonical-to-paper permutation is:

```text
[3, 2, 5, 4, 7, 6, 1, 0]
```

Use SI `N m` for internal numerical quantities and exact rational powers of ten for conversions. `1 nN m = 10^-9 N m`; `1 pN m = 10^-12 N m`. Covariance transforms with the **square** of the unit conversion. Torque has dimensions `M L^2 T^-2`; torque covariance has dimensions `M^2 L^4 T^-4`.

Copper clocking is a campaign label, not the source-position azimuth that reverses torque. “Paired” means matching campaign and operating-mode summaries; it does **not** assert simultaneous samples, matched raw observations, independence, or known covariance.

### 3.2 Fixed mean restriction

Define the 8-by-4 replication matrix `E` by `E[2j,j] = E[2j+1,j] = 1`, with all other entries zero, and

```text
b = (1,0,1,0,1,0,1,0)^T.
```

The proposed working mean model is

```text
E[y_star] = E t + b tau,
```

where `t` contains four unconstrained campaign torques, `tau` is a signed relative method offset, and `y_star` denotes the entries under a **specified correction convention**. If the as-published Table 15 entries already have that convention, `y_star = y`. Otherwise record the required source-supported transformation without applying it to the observed data in this PR.

This parametrization does not designate free deflection as a true or unbiased reference method. Assigning the relative offset to the servo coordinate is a choice of coordinates. Neither this parametrization nor GO identifies which method, calibration, or physical mechanism is responsible.

Define `B = I_4 ⊗ (1,-1)` and the fixed 3-by-4 matrix

```text
R = [[1,0,0,-1],
     [0,1,0,-1],
     [0,0,1,-1]].
```

Then `d = B y_star` is the four-vector of method differences, and `z = R d` tests their equality relative to sapphire. These are **symbolic definitions only for the actual measurements** in this PR. Set `A = R B`; establish exactly:

```text
B E = 0;  B b = 1_4;  R 1_4 = 0;
A E = 0;  A b = 0;
rank(B) = 4; rank(R) = rank(A) = 3;
ker(A) = col([E,b]); rank([E,b]) = 5.
```

All eight measurements remain in the restriction. Choosing sapphire as a reference is a frozen coordinate convention, not a preferred measurement. An invertible change of the three contrast coordinates must preserve the represented null restriction.

### 3.3 What the subtraction does and does not remove

The four underlying campaign torques cancel algebraically **under the stated paired mean model**; they need not be equal across campaigns or materials. No density approximation, numerical mass-integration coefficient, G estimate, or copper posterior fit is needed for this cancellation.

The model's applicability is nevertheless a source-review question. Verify that the two methods refer to comparable signals and correction conventions. A table row is not proof that method-dependent drift, pressure extrapolation, readout calibration, or geometry changes have no differential effect.

Do not add separate material offsets, unequal method loadings, or extra free nuisance effects to make this restriction feasible. A newly justified different restriction requires a separate specification.

## 4. Primary source and bounded preparation review

The controlling scientific source is Schlamminger et al., *Metrologia* 63 (2026) 025012, DOI `10.1088/1681-7575/ae570f`, using the NIST-hosted journal PDF. Use the publication landing page for discovery only; its abstract numerics do not control this work. [S1, S2]

During this specification's preparation, model-visible PDF screenshots were inspected at zero-based indices **23, 24, 25, and 26**. These indices equal the printed page numbers in this edition; the physical sheet number is one larger because of the cover. Parsed source review also covered the relevant measurement equations and uncertainty/correction passages in §§3, 7, 8, and 9. This is GPT's planning review, not an independent audit, a new raw-PDF hash attestation, or a retrospective change to earlier access records.

A targeted public search returned indexed publisher material, but direct DOI access failed with a robots restriction. Do not describe the publisher's associated-material index as fully inspected. A prior implementation recorded PDF hash `c79552d62f4d4f4e85cfbbb00f135c1d985b596d9cdcde9bee57cfe4618f33dc`; attribute that to PR #50 unless the implementation actually obtains and hashes bytes itself. [R1]

### 4.1 Starting transcription

The following Table 15 transcription was visually checked for this specification. Preserve decimal strings, source units, and roles. It is **not a new evaluation of the paired differences**. [S1, p.25, Table 15]

| Canonical campaign | Servo reference, nN m | Servo u_A, nN m | Free reference, nN m | Free u_A, nN m |
|---|---:|---:|---:|---:|
| copper_0 | 31.1962 | 0.0004 | 31.1979 | 0.0003 |
| copper_120 | 31.1828 | 0.0006 | 31.1842 | 0.0003 |
| copper_240 | 31.1836 | 0.0003 | 31.1856 | 0.0002 |
| sapphire | 13.9778 | 0.0003 | 13.9799 | 0.0002 |

The table identifies these as Type A standard uncertainties, `k = 1`. Treat Type A/Type B as methods of uncertainty evaluation, not synonyms for random/systematic effects. The labels alone supply neither zero correlation nor a complete uncertainty budget or sampling law. [S1; S3, §3.3]

The torque reference values may be consumed **only as explicitly frozen linearization/scaling anchors** when an authorized uncertainty conversion needs them. They must not be passed to an observed-difference or fitting routine, used to choose covariance assumptions, or used to select the verdict. Keep the full observed-data evaluation API out of the production module. If no uncertainty derivation needs those anchors, leave them as source transcription/context only.

### 4.2 Required locator coverage

Use this bounded locator map to prepare the frozen source projection and effect inventory:

| Surface | Primary locator | Specific question to resolve |
|---|---|---|
| Torque definition and method extraction | §§3.1–3.3, pp.5–8, equations (5)–(20) | Are the two entries the same signed recovered quantity? Which extraction, finite-servo-gain, frequency, inertia, and electrical-calibration terms enter? |
| Sensitivity conventions | §3.4, p.9; §8.5, pp.23–24 | Which signed sensitivities concern inferred G, and which can legitimately be mapped to torque? |
| Campaign and geometry conditions | §3.3, p.8; §9, pp.24–25 | Are calibration runs, campaign averaging, seating changes, and timing sufficiently specified for the paired interpretation? |
| Pressure and thermal corrections | §7.7, pp.20–21; relevant preceding §7 passages only | At what stage is zero-pressure extrapolation applied, and what is shared between methods/campaigns? |
| Mechanical and background contributions | §§8.1–8.4, pp.21–22 | Which corrections and residual uncertainties enter the reported torque entries rather than only the later G conversion? |
| Autocollimator effects | §8.5, pp.23–24, equations (59)–(62), Table 14 | Can signed campaign-level joint effects be identified, including nonzero shifts and dependence? |
| Eight input summaries | §9, p.25, Table 15 | What exactly do the reported u_A values cover, and is their within-/cross-campaign covariance supplied? |
| Later-stage boundary | §9, pp.25–26, Tables 16–18 | Which statements concern four final G summaries and cannot be transferred to the eight torque entries? |

Specific cautions for this review: Table 14 concerns relative G shifts and marginal uncertainty assignments; the nearby full-correlation instruction concerns four final results. Neither should be silently converted into an eight-entry torque covariance. The treatment of a systematic shift together with a standard deviation in §8.5 must not be relabeled as a centered sampling variance. [S1, pp.23–26]

Do not transcribe every historical table or reproduce the thermal, PTB calibration, moment-of-inertia, or Bayesian analyses. Where a source passage does not identify a needed stage-level quantity, record the gap and its nearest positive locator.

### 4.3 Corpus closure and external stopping rule

Before freeze, complete one bounded pass over the journal article and directly associated, accessible material: publication/DOI landing pages, explicit data/code/supplement links, and one targeted search for this article's campaign covariance or analysis material. The planning access record above can be reused where it resolves a step; no ritual re-download is required. Follow at most three directly relevant associated resources. Do not use generalized web speculation, older BIPM results, or private correspondence as substitutes.

Freeze every source and numerical projection actually used, with access mode and locator. Once the specified pass is complete, missing information becomes a documented source request, not an indefinite search or reason to leave the implementation unfinished. Material arriving later must not silently enter this frozen certificate.

If a specific essential supplement is identified but inaccessible, record `UNRESOLVED_SOURCE_ACCESS`. Failure to inspect an unspecified publisher index does not by itself prove that an essential supplement exists, nor does it justify a global absence claim. Otherwise qualify source-based NO-GO conclusions by the reviewed corpus.

## 5. Minimum uncertainty object and permitted derivations

Let `V_y` be an 8-by-8 covariance or metrological uncertainty matrix for the specified `y_star` representation, with its interpretation explicitly identified. The desired objects are

```text
V_d = B V_y B^T                  (4-by-4)
C   = R V_d R^T = A V_y A^T     (3-by-3).
```

**C is the primary sufficiency target.** Do not require all of `V_y` or `V_d` if a source-authorized direct `C`, or a derivation proving `C` fixed over the admitted unknowns, is available. Conversely, an identified C does not recover a fitted tau, its uncertainty, or the covariance of all four differences.

Permit only these bounded routes:

1. A directly supplied, source-authorized C with identified coordinates, units, correction convention, and uncertainty scope.
2. A supplied `V_d` or `V_y` projected exactly into C.
3. A finite source-supported input model with signed sensitivity matrix `J` and joint uncertainty matrix `U`, projected as `A J U J^T A^T`, plus other explicitly characterized contributions. Preserve cross-covariances; summing separate components is justified only when the omitted cross terms are specified zero or annihilated by the contrast.

Use exact rational arithmetic on reported decimal quantities. A derivative-based uncertainty budget is a declared linearized model, not an exact physical response theorem. No numerical differentiation of the unavailable NIST pipeline is authorized. A direct source matrix is evaluated as reported; its missing physical precision is not recovered.

Distinguish a centered covariance, a conservative uncertainty assignment, a bound, a second moment, and an interval. The identity `E[e e^T] = Cov(e) + E[e]E[e]^T` prevents an unremoved shift from being silently treated as zero-mean uncertainty. Source-supported conservative assignments may be recorded with their correct interpretation; they do not establish a repeated-sampling covariance or justify Gaussian calibration automatically. [S3, §§3 and 5]

Record the source's uncertainty convention and any additional modeling premise. Never declare a full physical error model merely because a numerical matrix can be built. Validate symmetry, dimensions and positive-semidefinite status by exact algebra; positive diagonal entries alone are insufficient. Distinguish positive definiteness from a valid singular covariance without numerical tolerances or regularization.

### 5.1 Exact cancellation, including irrelevant missing information

For an uncertain input effect with loading matrix `L`, `A L = 0` proves that effect is absent from the restricted contrasts under the stated loading model. Its unknown variance and cross-covariance with retained inputs then drop out without requiring independence. `B L = 0` is the stronger special case of within-pair cancellation.

Also retain the case `B L != 0` but `R B L = 0`: an effect may change all four method differences equally and still be irrelevant to testing whether they are equal. It remains relevant to estimating their common magnitude, which is out of scope.

A statement such as “the same apparatus,” “fully correlated,” “equal relative uncertainty,” or “common calibration” is **not** an equal absolute loading. Apply signed sensitivities in the correct coordinates. Unknown loadings remain unknown; small nominal loadings do not become exact zeros.

For partially known matrices, an all-admissible cancellation certificate must cover the complete frozen unknown component model. Equality for two selected completions is not proof that every admissible completion gives the same C.

### 5.2 Type A information and scope preservation

Record the eight Type A marginals separately from any combined uncertainty. For a pair,

```text
u^2(S-F) = u^2(S) + u^2(F) - 2 Cov(S,F).
```

Cross-campaign covariances also enter C. Do not infer zero covariance from non-simultaneous acquisition, separate method names, or missing off-diagonal entries. A source-backed uncorrelated model is permitted; an implementer-added independence assumption is not evidence that the source specifies it.

A complete Type-A-only covariance does not automatically authorize combined-uncertainty GO. It can suffice for the primary target only if all omitted effects are source-supported as absent at this stage, already included, or exactly eliminated by A. Otherwise report the limited Type A result without promoting it.

Tables 17 and 18 are not an eight-campaign covariance. Do not invert the copper summary aggregation or transplant final-G correlations. Numerical outcome agreement with #47–49 is not a covariance oracle. [S1, §9]

## 6. Effect inventory and feasibility decision

### 6.1 Finite effect inventory

Build a typed inventory covering: Type A extraction/averaging; electrical voltage and capacitance calibration; autocollimator scale and non-linearity; pressure/thermal extrapolation; finite servo-gain correction; free-mode frequency, inertia, and anelasticity; background/zero-torque contributions; campaign seating, geometry and drift where applicable; and effects belonging only to conversion into G.

This is a routing list, not a declaration that every category contributes. Cross-check the relevant source budget categories to avoid omission, but do not import their later-stage numbers. Split or combine rows only for a stated physical/source reason, and disclose that choice before freeze.

Each row must identify its source locator, affected stage and coordinates, evaluation type, correction status, signed loading or specific missing information, covariance scope and meaning, and whether A annihilates it. Useful correction states include `APPLIED_AT_THIS_STAGE`, `SPECIFIED_NOT_APPLIED`, `UNCERTAINTY_ONLY_ASSIGNMENT`, `DOES_NOT_ENTER_THIS_STAGE`, and `UNKNOWN`. An unsupported state cannot default to “already corrected.”

For any pending correction, identify the proposed corrected representation and whether the correction's mean effect and residual uncertainty are specified. No correction is numerically applied to actual outcomes here, and none may be applied twice.

For a missing non-canceling contribution, name the smallest sufficient repair: a signed loading, a projected covariance term, a cross-covariance, a stage declaration, or an applicable correction rule. Do not demand unrelated raw data.

### 6.2 Separate axes; no hardcoded desired result

Return at least these axes:

- `comparison_contract`: source-described paired interpretation / conditional additional premises / contradicted by the reviewed stage contract / unresolved access.
- `type_a_uncertainty`: marginals only / identified projected contribution / missing dependence / conflicting source.
- `combined_contrast_uncertainty`: identified positive definite / identified positive semidefinite singular / partially identified / unidentified / conflicting source.
- `mean_correction_status`, `uncertainty_interpretation`, `precision_scope`, and `sampling_calibration`.

Compute dispositions from validated evidence and algebra, not an unconditional string selected because NO-GO is expected:

| Disposition | Required meaning |
|---|---|
| `GO_CONTRAST_UNCERTAINTY` | The paired stage/correction interpretation is sufficiently specified within the declared source model, and the complete relevant 3-by-3 C is identified and positive definite. Missing full matrices are harmless only when justified in the projected space. |
| `IDENTIFIED_DEGENERATE_CONTRAST` | The source-specified C is valid but singular. Report its exact rank/nullspace; do not add jitter, use a pseudoinverse on outcomes, or silently reduce the scientific restriction. |
| `CONDITIONAL_ASSUMPTIONS_REQUIRED` | A stated extra stage, correction, or dependence premise could complete the question, but is not established by the reviewed source. List premises; no source-supported GO or assumed real-data covariance run. |
| `NO_GO_COMPARABILITY` | The reviewed record does not establish the required paired representation, or positively shows that the proposed representation is inapplicable. Distinguish missing support from a demonstrated mismatch. |
| `NO_GO_CONTRAST_UNCERTAINTY` | A comparison can be specified, but at least one unresolved, non-canceling uncertainty/mean-effect term prevents the required C/correction contract from being identified. |
| `UNRESOLVED_SOURCE_ACCESS` | A specific essential source was identified but could not be reviewed. State exactly which one and its relevance. |

Preserve all limiting axes even when selecting one overall label. State deterministic precedence in the freeze: essential access gap, failed comparison contract, additional unsupported premises needed for a proposed completion, unidentified combined contrast uncertainty, identified singular C, then GO. Do not select the conditional label merely because some arbitrary invented assumptions could always complete an unknown model; it requires an explicit bounded candidate completion linked to the source description.

Malformed inputs, inconsistent units, failed algebra, invalid code-produced matrices, failed provenance, or stale artifacts are **errors**, not successful NO-GO evidence. A faithfully transcribed but conflicting/indefinite published uncertainty assignment is a source-contract limitation: expose it and withhold GO; do not repair it with nearest-PSD adjustment.

Every disposition leaves `real_data_test_executed=false`, `torque_fit_executed=false`, and `corrected_G_produced=false`. GO authorizes only preparation of a separate statistical specification. Statistical calibration, finite-resolution effects on a future statistic, and any physical conclusion remain outside this PR. Unknown quantities are null/explicit unresolved records, never numerical zero.

## 7. Bounded mathematical controls

Use synthetic inputs only for behavioral controls. No real-data Q or fitted tau is needed anywhere in the new test suite.

Required exact controls are:

1. **Contrast construction:** directly expand the pair differences and three residual rows independently of the production matrix multiplication. Verify order, signs, units, ranks, and the mean-space identities in §3.
2. **Covariance projection:** independently expand the covariance sums and compare all three routes in §5 on a small labeled synthetic case, including within-pair and cross-campaign terms.
3. **Same marginals, different C:** compare the synthetic positive-definite matrices `V0=I_8` and `V1=I_8 + (e0 e1^T + e1 e0^T)/2`. They have identical diagonal entries but a different within-pair covariance. Demonstrate that the projected uncertainties differ. These are not inferred NIST covariances.
4. **Missing but irrelevant uncertainty:** use `V(lambda)=I_8 + lambda*b*b^T`, `lambda>=0`. Prove symbolically that the projected C is independent of lambda, although uncertainty of a common method difference is not. Also exercise an unknown within-pair-common loading in `col(E)`.
5. **False common-mode shortcut:** use a synthetic shared input with unequal absolute pair loadings, so its image under A is nonzero. Perfect correlation alone must not erase it. Include a case in which a differential signal has a larger, not smaller, calibration sensitivity.
6. **Meaning and stage controls:** a Type-A-only complete matrix with an uncanceled omitted component cannot obtain combined GO; a later-summary covariance cannot acquire torque-stage authorization; a nonzero mean-square term is not silently a centered covariance; singular, unknown and access-limited cases remain distinct.

These controls establish generic algebraic vulnerabilities, not proof that every possible completion of the actual source yields a different C. A source-specific nonidentifiability conclusion must still identify its actual missing quantities and explain why they survive the relevant contrast.

## 8. Freeze and chronological sequence

Preparation may inspect sources, transcribe the input roles, and finalize this bounded specification. It must not calculate new observed contrasts or implement/evaluate the new feasibility engine before the published freeze and GitHub draft-creation anchor.

Create one new branch from the verified base. The first commit must add only:

```text
Experiments/GMeasurements/nist_2026_paired_torque_feasibility_preregistration_v1.json
```

Validate its JSON/schema locally, publish that sole-file commit, open the draft PR, and record the actual GitHub-controlled creation timestamp and head. Only then introduce the evaluator, implementation source attestation, result-bearing notes, and new covariance-feasibility computations. Even before publication, do not use preparatory scripts to calculate the observed differences or a prospective test result. The supplied specification is pre-freeze planning content and must be attributed as such.

Freeze: objective and nonclaims; source corpus/access boundaries; `outcome_blind=false` and disclosed prior knowledge; input labels, order, units and allowed numerical roles; B/R/E/b; stage and correction questions; effect inventory; permitted uncertainty derivations and source references; expected missing-field representations; decision policy; exact synthetic fixtures; focused tests and eight mutation requirements; planned paths; helper pins; and audit/merge requirements.

Freeze every newly used source numeric, signed loading, covariance convention, and zero-correlation assertion before use. The input projection must be machine-consumed. A post-freeze attestation can cross-check the freeze and append the actual anchor, but cannot supply previously unfrozen decision-driving facts. New material requiring a different scientific contract must be disclosed and handled through an explicit version/replacement, never by editing frozen bytes or silently enlarging the corpus.

Prior #47–50 results, the article's published offsets, and the visible Table 15 values are already known. Target-exclusion controls do not restore blindness. Do not claim that this protocol was selected independently of all previous outcomes.

Commit the complete result-driving source snapshot before deterministic artifact emission. Preserve #50's relevant merge-freshness behavior: a merge inheriting the entire relevant source state from a parent is not a new source snapshot; a genuine conflict resolution changing that state requires new artifacts. Preserve full-history first-introduction checks and the strict existing freeze verifier. This is scoped reuse of a corrected pattern, not authorization to refactor shared history infrastructure. [R1]

## 9. Implementation surfaces and architecture

Use stem `nist_2026_paired_torque_feasibility`. Exactly eleven new paths are planned:

```text
Discovery/nist_2026_paired_torque_feasibility.py
Discovery/nist_2026_paired_torque_feasibility_mutations.py
Experiments/GMeasurements/nist_2026_paired_torque_feasibility_preregistration_v1.json
Experiments/GMeasurements/nist_2026_paired_torque_feasibility_source_attestation_v1.json
Experiments/GMeasurements/nist_2026_paired_torque_feasibility_v1.json
Experiments/GMeasurements/nist_2026_paired_torque_feasibility_mutations_v1.json
Notes/NIST2026PairedTorqueFeasibilitySpecification.md
Notes/NIST2026PairedTorqueFeasibility.md
Notes/NIST2026PairedTorqueSourceRequest.md
tests/test_nist_2026_paired_torque_feasibility.py
tests/test_nist_2026_paired_torque_feasibility_mutations.py
```

Modify only `.github/workflows/verify.yml`, adding the two new read-only `--check` commands. Do not modify earlier scientific engines, freezes, artifacts, Lean files, or audit registers. A genuinely required extra path must be settled in preparation and explicitly included in the sole-file freeze, not presented later as an undisclosed planned surface.

Use standard-library exact arithmetic and small typed records. Separate: source/protocol validation; pure contrast algebra; uncertainty propagation and cancellation; evidence-based classification; deterministic artifact/provenance construction; and the read-only check path. Do not build a generic symbolic language, global covariance optimizer, posterior sampler, external data-ingestion service, or reusable platform in this PR.

The artifact should contain the fixed operators and exact identities; permitted source projection; stage/correction and effect inventory; known projected components and unresolved terms; C only when justified; exact rank/cancellation certificates; separate uncertainty/interpretation axes; synthetic evidence; specific source requests; source/anchor/snapshot pins; and the prohibited-action flags. It must not contain observed d, observed z, a fitted tau, Q, p, or new G outputs.

The CLI's `--check` must validate committed artifacts without network access, writes, or rerunning the mutation family. Builders must not download PDFs. Source-access assertions remain human/implementer attestations with explicit limits; hashes do not independently verify transcription or source sufficiency.

Runtime scientific reads must be confined to the new protocol/projection and attestation; provenance reads may include the enumerated new notes, module, and existing source-history helpers. Mutation verification additionally reads its own source, tests, and the existing runner/harness as actually used. Record those roles separately and test the actual file/Git read set, not a list of forbidden filenames asserted by the same code.

## 10. Focused tests and bounded production mutations

Focused tests must cover §7 and all dispositions, source-field consumption, covariance meaning/coverage, correction status, strict JSON/exact-number parsing, input labels and stage tags, canonical serialization, artifact freshness, first-introduction/anchor chronology, source snapshots across inherited and conflict-resolving merges, and observed filesystem/Git/import closure.

Use independent hand-expanded algebra and synthetic fixtures rather than validating a production function with itself. Changes to excluded final G, dark-uncertainty, published-offset, and unrelated artifact context must not change authorization or computed uncertainty. Exercise this behavior beyond digest rejection. A changed permitted torque scale may change its declared uncertainty propagation; it must not cause the program to select a different statistical model based on observed method differences.

Freeze and execute one concrete production-source mutation for each of the following eight rows, eight scored mutations in total. Focused tests must cover every named boundary even where a row offers alternative mutation sites:

| Mutation | Designated semantic failure |
|---|---|
| M1 — wrong method order or sign in B | Independent labeled contrast/response identity fails; use a partial order/sign fault, not an equivalent reversal of every contrast. |
| M2 — covariance unit conversion uses one power rather than two | Independent dimensional/scaling assertion fails. |
| M3 — within-pair or cross-campaign covariance term is dropped | Independent projected covariance fixture fails. |
| M4 — nonzero shared loading is treated as canceled solely because it is common/correlated | Unequal absolute-loading control fails. |
| M5 — unresolved full V blocks GO even when all unknown directions are annihilated by A | Positive minimal-C sufficiency control fails. |
| M6 — Type A completeness or a later-stage matrix is promoted to complete campaign contrast uncertainty | Valid staged/coverage fixture receives unauthorized GO and the behavioral assertion fails. |
| M7 — systematic mean-square assignment or unknown mean correction is treated as centered, fully corrected covariance | Nonzero-mean/correction-status control fails. |
| M8 — explicit unresolved dependence is replaced by zero and authorized | Evidence classifier's missing-dependence fixture fails without relying on a schema or hash error. |

Each mutation must execute its designated behavioral assertion on a valid, relevant fixture. The baseline and an executable equivalent control must survive; a distinct faulty calibration must be killed. Import, syntax, runtime, skip, provenance/digest failures, and unrelated assertions earn no kill credit. Bind the evidence to the production snapshot, oracle/tests and runner actually executed. Do not rerun unrelated historical families or expand this into a new mutation harness.

## 11. Technical source-request draft

Create `Notes/NIST2026PairedTorqueSourceRequest.md` as a standalone, attributable request Miguel can review and send separately. Address the scientific uncertainty, not an alleged defect in the publication. Identify DOI, Table 15, canonical order, sign convention, and A. State that the project has not tested a common offset or produced corrected G.

Ask for the smallest sufficient information, in this order:

1. Confirmation of what corrections and aggregation/extrapolation steps are already reflected in each Table 15 torque entry and its Type A uncertainty, and whether the pair represents the intended common campaign signal.
2. The combined uncertainty/covariance for `A y_star`, with its correction, linearization and distributional meaning; alternatively `V_d`, `V_y`, or signed input sensitivities and covariance sufficient to calculate it.
3. Where the direct object is unavailable, the specific remaining non-canceling terms identified by this implementation: especially Type A dependence, campaign-level autocollimator relationships, and correction/extrapolation cross-covariances as applicable.

Clarify that a common method offset cancels in A, so information needed only to estimate its magnitude is not required for this limited contrast question. Marginal standard uncertainties alone are not the requested joint object. Do not require raw time series, all posterior samples, or the final copper aggregation if a direct contrast-level answer suffices.

Keep #50's separate final-summary response request identified as parked context, not a prerequisite for this route. If the new source review already resolves all required terms, the document should instead record that no request is needed and what established sufficiency. Do not send, schedule, or monitor a message.

## 12. Acceptance, final validation, and reporting

Accept the implementation only when the source review closes within §4.3's limits, each disposition follows its actual evidence, the minimum-C route can succeed on legitimate controls, non-canceling unknowns cannot be promoted, all numerical/provenance artifacts are fresh, and every forbidden actual-data computation remains absent. A negative verdict must be specific enough to identify what new information would change it; do not claim the missing information cannot exist.

Apply the standing final-tree protocol once for the final verification epoch: focused new tests; one complete Python suite; the two new read-only guards and only directly implicated additional guards; `git diff --check` for worktree and full PR range; and the bounded mutation evidence. Use the repository's existing test invocation convention. No local Lean/build rerun is needed unless the permitted scope is explicitly changed to a Lean-linked contract; exact-head CI supplies that attestation.

Publish the final head, verify its exact-head CI, and retain the SHA/run identifiers. Do not repeat equivalent checks merely because an independent audit is pending. Leave the PR unmerged.

Update `gpt_RollingAuditHandoff.md` in place at Drive file ID `145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd` and verify readback. Record #50's already-confirmed merge, this PR's actual head/freeze/anchor, disposition and claim limits, actual dependency roles, validation/CI, and pending independent review. Do not edit `claude_Current.md`, close IDs, or invent an audit. No housekeeping PR is requested.

The final report must state: verification epoch; comparison and uncertainty findings; whether C is identified and at what scope; missing information/source request; forbidden computations not performed; materially relevant local checks and CI; BLOCKING, DEFERRED MAINTENANCE and FUTURE HARDENING separately; any actual maintenance submission; and required true-merge history. Preserve the provisional qualification on every scientific consumer until the relevant scope is independently accepted.

## 13. Eventual Claude audit prompt

> Audit the new NIST paired-torque feasibility PR at its exact recorded head, based on `6f722e92a09bc598aa06920e89ba02059bf1e7a4`. Reuse retained same-SHA automated evidence. Review the torque-stage comparison and correction contract; the distinction between source-position and between-method differences; canonical labels/signs/units; cancellation of the four campaign means and a common relative method offset; whether only A V A^T is required; treatment of unknown loadings and cross-covariance; Type A versus combined uncertainty; centered covariance versus systematic shift/conservative assignment; and whether later-summary correlation statements were improperly transferred. Inspect the bounded corpus and positive absence locators, source-dependent versus hypothetical completion claims, field consumption/read closure, freeze/anchor/source chronology and inherited-merge freshness. Check that synthetic witnesses support only their stated general conclusions, and that no observed contrast, fit, statistic or new G was computed. Source/uncertainty sufficiency is not a physical or statistical acceptance verdict. Distinguish the numerical independence from earlier PRs from shared motivation and Git ancestry. Classify findings as BLOCKING, DEFERRED MAINTENANCE or FUTURE HARDENING and record the exact independent coverage.

## 14. Source and repository references

**[S1]** S. Schlamminger et al., “Redetermination of the gravitational constant with the BIPM torsion balance at NIST,” *Metrologia* **63** (2026) 025012. DOI: https://doi.org/10.1088/1681-7575/ae570f . Controlling journal PDF: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075 . Specific locators appear above. The article is CC BY 4.0; this specification attributes the authors and source and does not reproduce its figures.

**[S2]** NIST publication landing page, discovery/identity only: https://www.nist.gov/publications/redetermination-gravitational-constant-bipm-torsion-balance-nist . Access and scientific-source authority must remain distinct.

**[S3]** JCGM 100:2008, *Evaluation of measurement data — Guide to the expression of uncertainty in measurement*, §§3.3, 5.1–5.2. Official PDF: https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf . Official member-organization HTML used for the focused preparation review: https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/03_e.html and https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/05_e.html . General covariance guidance does not supply this experiment's missing correlations; the source-identification requirement is this project's explicit scope.

**[R1]** PR #50: https://github.com/mdiaz4052/The-Number-Project/pull/50 . Immutable scientific note: https://github.com/mdiaz4052/The-Number-Project/blob/6f722e92a09bc598aa06920e89ba02059bf1e7a4/Notes/NIST2026TorqueResponseFeasibility.md . Scoped history behavior: `Discovery/nist_2026_torque_response_feasibility.py` at that same base. These are implementation records pending independent audit, not independent primary-source corroboration.

**[R2]** `claude_Current.md`, Drive ID `1flh4pHVdz80ClLZO5IQo2xG63EGWVsN0`, and `gpt_RollingAuditHandoff.md`, Drive ID `145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd`, retrieved during specification preparation on September 10, 2026. GitHub controls current merge/base state; the audit files control attributed review state.

---

This document is a prepared implementation specification. It is not the published preregistration freeze, an executed feasibility result, an independent audit, or authorization to perform the later statistical test.
