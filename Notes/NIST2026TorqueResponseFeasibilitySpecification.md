# The Number Project — NIST Torque-to-G Response Feasibility

## Implementation specification

**Repository:** `mdiaz4052/The-Number-Project`

**Intended base:** `81169a9d54e1540d82b4ad14ffa7dcd6d4fd3c77` — verified GitHub `main`, the true merge of PR #49.

**Prepared:** September 9, 2026, America/Detroit; following Miguel's request at `2026-09-10T01:14:20Z`.

**Review qualification:** **PROVISIONAL — INDEPENDENT AUDIT PENDING**.

**Deliverable:** one bounded source/response-feasibility PR. This document is a work specification, not a preregistration freeze, completed feasibility certificate, independent audit, or numerical torque-model result.

## 1. Objective and stopping boundary

Determine whether the permitted published record identifies how one precisely specified additive torque-readout bias would propagate into the four NIST configuration summaries:

`copper_servo, copper_free, sapphire_servo, sapphire_free`.

The question is:

> Can the response of these four published summaries to the intervention in §3 be established from the measurement and aggregation procedures, without choosing its coefficients from the observed disagreement?

Separate three capabilities: conversion at the preliminary campaign level; propagation through the final configuration aggregation; and identification of the mean subspace needed by a later residual test. A response subspace may be identifiable even when an absolute torque calibration or the full author estimator is not.

This PR must stop at feasibility. Do not fit a torque magnitude, evaluate a new real-data residual statistic, calculate a p-value, adjust an uncertainty budget, generate corrected or pooled G, choose a winning mechanism, or extend the BIPM–NIST comparison. Even a GO result requires a separate specification and freeze before statistical testing.

No apparatus cause, composition dependence, author-missed effect, raw-data replication, or reproduction of the published Bayesian consensus is claimed. A documented NO-GO is a successful outcome of this task, not an implementation failure.

## 2. Base, evidence dependencies, and audit routing

Verify the intended base once before implementation. If `main` has advanced, assess the intervening changes before selecting the base; do not silently substitute another scientific epoch. Preserve the true-merge ancestry.

PR #49 supplies the motivation and existing claim boundary, not new independent observations. Its note is `Notes/NIST2026ConfigurationModels.md` at the intended base. PR #47's experimental covariance and PR #48's diagnostics are not necessary numerical inputs to this feasibility calculation. Do not import their builders or read their result artifacts merely to obtain familiar labels or constants.

Prefer a narrow implementation using Python's standard library, `Fraction`, and the existing `Discovery.preregistration_history` and `Discovery.source_history` helpers. Do not extract a new shared framework or modify an existing scientific engine. Declare any additional helper dependency before the freeze and pin its source. Git ancestry, source-code reuse, motivation, and numerical scientific dependency must be recorded separately.

Read `claude_Current.md` and the existing `gpt_RollingAuditHandoff.md`. At planning, Current's latest independent audit was PR #46; #47–#49 remained independently unaudited. The handoff still described #49 as open, whereas GitHub had already confirmed its merge. GitHub controls merge state; neither document's older wording reverses that event.

Relevant routed concerns are DM-073/076 (freeze consumption), DM-074 (prior knowledge), DM-075 (chronology), DM-070/077 (actual read closure), and DM-078(a)/FH-13 (source corroboration and bounded absence claims). Inspect only directly relevant available detail files. These references are routing signals, not assertions that those IDs have been independently closed. Claude retains ID ownership.

E-001 remains live on its HUST boundary. This work must not read, modify, depend on, or make claims through the contradictory HUST authorizations. No unrelated maintenance closure is part of this PR.

## 3. One operational intervention, fixed before calculation

Use one project-defined scenario, named `servo_peak_to_peak_readout_offset`:

A signed scalar `tau`, in N m, is added to the **recovered peak-to-peak torque difference in electrostatic-servo mode**, after that campaign's torque extraction and its declared existing corrections, but before conversion to preliminary G. The same `tau` applies to sapphire and all three copper clockings. Free-deflection campaign inputs are unchanged. Geometry, calibration conventions, extraction settings, and the aggregation rule are held fixed.

The scenario concerns an offset in a reported differential-torque observable. It is not an assertion that a physical torque actually acts only in servo mode. In particular, it is not a constant DC torque applied equally at both source positions: such a torque cancels in a difference. It also is not a controller-voltage, thermal-time-series, capacitance-gradient, or pressure-bias model.

This choice makes a single testable response question concrete. The paper's servo-offset discussion motivates examining that channel, but does not establish causality. Do not try free-only, equal-and-opposite, material-specific, or clocking-specific loadings and retain whichever looks favorable. Those are different hypotheses.

Use the canonical preliminary order:

```
copper_0_servo, copper_0_free,
copper_120_servo, copper_120_free,
copper_240_servo, copper_240_free,
sapphire_servo, sapphire_free
```

Thus `b = (1, 0, 1, 0, 1, 0, 1, 0)` and the intervention is `n -> n + tau*b`. Explicitly map this order to the paper's table ordering. Keep copper clocking angle theta distinct from the source-position angle used to reverse gravitational torque.

Allow `tau` to have either sign. An overall sign convention can be changed only together with its parameter convention and audit record. A channel swap, relative-sign change, or factor-of-two error is not an overall convention change.

## 4. Bounded source review and planning observations

### 4.1 Controlling sources

The controlling paper is Schlamminger et al., *Metrologia* **63** (2026) 025012, DOI `10.1088/1681-7575/ae570f`.

Canonical PDF: `https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075`.

Publisher record: `https://doi.org/10.1088/1681-7575/ae570f`.

The corpus is this paper and any explicitly associated publisher/NIST supplement, correction, or author code identified and pinned during the bounded pre-freeze review. Check the article's associated-material links once. Do not conduct a general literature search, infer the implementation from a generic Bayesian reference, digitize plot values, or contact authors during this PR.

Freeze the corpus actually obtained. An inaccessible link is an access limitation, not proof that its content lacks a required item. A newly discovered material source outside the frozen corpus must be disclosed; it cannot be silently consumed or ignored to preserve a preferred verdict.

### 4.2 Primary locators

| Locator | Required review question |
|---|---|
| §3.1, equations (1)–(5), printed p.5 | What torque difference, sign, and exact versus symmetric geometry factor are defined? |
| §3.2–3.3, especially equation (20) and following correction discussion | At which corrected torque observable does §3 inject the offset? |
| Table 2 and footnotes, printed p.10 | Which masses and conventions apply? |
| §6.7–6.8, equations (40)–(41), Figure 14 and Table 10, printed pp.15–17 | Which cancellation identities require common geometry, and what full-versus-peak convention applies? |
| §9, Table 15, Figure 25 and Table 16, printed pp.24–25 | How do eight campaign inputs become four configuration summaries? |
| §9, printed pp.25–26 | Where does configuration aggregation end and the later consensus procedure begin? |

The planning session actually inspected rendered PDF pages at zero-based indices **5, 10, 17, 25, and 26**. In this PDF those indices equal printed page numbers; sheet numbers including the cover are one greater. Other review used parsed text and publisher search results. No raw PDF bytes were retained or hashed in this planning session. Do not attribute these observations to Claude or invent a raw-file custody claim.

### 4.3 Starting transcription to verify before freeze

Table 2 gives per-body average masses `mt = 1150.156 g`, copper `ms = 11191.68 g`, and sapphire `ms = 5015.60 g`, not four-body totals. Its source-mass footnote states that the reported apparent masses are air-buoyancy corrected. Table 15 provides these campaign-specific entries:

| Campaign | Rs / mm | Printed Gamma_max |
|---|---:|---:|
| Copper 0 degrees | 213.9642 | 0.485637 |
| Copper 120 degrees | 213.9817 | 0.485467 |
| Copper 240 degrees | 213.9822 | 0.485464 |
| Sapphire | 213.9680 | 0.485613 |

Use campaign-specific Table 15 geometry, not a generic Table 2 radius substituted across campaigns. Do not add another buoyancy correction without source authority. Verify whether the table's named factor represents a peak or an effective half-difference for the required calculation; Table 10 and equation (5) must not be silently conflated.

The paper distinguishes preliminary conversions from copper posterior summaries. Equation (41)'s cancellation identity does not, by itself, specify the final summary estimator. These observations are **starting evidence to investigate**, not a predeclared final-response verdict.

No numerical response coefficients, torque fit, or candidate-model residual has been calculated in this planning session.

## 5. Mathematical contract

### 5.1 Preliminary conversion and units

Let `n_j` denote the relevant recovered peak-to-peak torque difference. The general geometric relation defines

```
K_j = 8*m_s,j*m_t*(Gamma_plus,j - Gamma_minus,j)/R_s,j
G_pre,j = n_j/K_j
```

The symmetric published approximation gives `K_j = 16*m_s,j*m_t*Gamma_max,j/R_s,j`. Keep these as separately identified conventions. An exact rational evaluation of reported decimals is exact arithmetic **within its declared representation**, not proof of exact physical symmetry.

For fixed `K_j`, the preliminary response is `d_j = b_j/K_j`. Compute it without reading measured torque central values or any reported G value. Do not obtain a gain from `n_j/G_j`, fit it to a material contrast, infer it from a published final estimate, or substitute the rough source-mass density ratio.

Use SI internally: `[K] = kg^2 m^-1`, `[tau] = N m`, and `[1/K] = m kg^-2`. Record the conversion to `U = 10^-11 m^3 kg^-1 s^-2` per pN m explicitly if displayed. A pN m is `10^-12 N m`; an nN m is `10^-9 N m`. A one-sided torque amplitude is not a peak-to-peak difference.

Evaluate only the convention actually supported. A symmetric, reported-input preliminary response may be emitted with that explicit qualification even when a stronger response is unavailable. Do not promote it to the four-summary level.

Printed source decimals are exact rational inputs to this bounded reported-value model. Do not claim recovered unrounded geometry or a joint physical uncertainty enclosure. A later physical test must address coefficient uncertainty or explicitly retain the fixed-reported-coefficient condition; no robustness to coefficient rounding is established here.

### 5.2 Propagation through the actual summary procedure

Write the configuration-summary map as `F(g_pre; eta)`, where `eta` contains the fixed, source-supported aggregation conventions. The desired exact directional response would satisfy

```
F(g_pre + tau*d; eta) - F(g_pre; eta) = tau*a
```

on the declared domain, with a response `a` independent of the measured discrepancy.

A source-supported fixed linear aggregation `F(g) = H*g + c` would give `a = H*d`. A different procedure can also identify the same response through a valid equivariance argument. Establishing this narrower response need not require reproducing every posterior sample or the author's full numerical result.

Conversely, an unspecified sampler is not automatically relevant to a response that can be proved invariant to it. Assess missing items at the stage where they matter.

Require a chain from every preliminary campaign to every affected configuration summary. In a joint copper fit, perturbing servo inputs can change the inferred free intercept through shared nuisance parameters. Do **not** force the copper-free response to zero merely because its direct torque input was not perturbed. Likewise, do not assume independent averaging of the two methods.

Do not replace the documented joint sinusoidal/posterior procedure by equal weights, inverse-variance weights, an average of reciprocal gains, or a new GLS calculation. Such constructions may serve as explicitly synthetic examples, never as unlabelled NIST responses.

A local Jacobian `J_F(g_pre; eta)*d` is not a global affine response. If it depends on observed campaign outcomes, fitted amplitudes, prior choices not fixed by the source, or an unbounded linearization remainder, classify it as conditional/local and do not authorize a fixed four-summary response model. This is a limitation of this contract, not proof that all subsequent analysis is impossible.

Assess sapphire's path too; do not assume its final mean equals a preliminary ratio merely because it has one clocking.

An affine response of a numerical estimator does not by itself establish its expected value, an unbiased common baseline, or a Gaussian sampling distribution. Those assumptions and their statistical calibration belong to the later test specification. Record any restricted validity domain; a local or bounded-domain identity does not authorize unrestricted extrapolation in tau.

### 5.3 Identify the information actually needed by a later test

For a later model with an unrestricted common intercept and signed torque parameter, the allowed means would be

```
mu*1 + tau*a.
```

Its subspace is unchanged by `a -> c*a + q*1` for fixed `c != 0`. A missing common scale or common-mean component therefore need not block a **shape-only** feasibility result. Such equivalence does not identify a physical torque magnitude or an unbiased value of G.

Use exact linear algebra on source-authorized response representatives to check:

- rank of `[1, a]` and a canonical subspace representation;
- invariance to common nonzero rescaling and common-mean addition;
- whether all source-admissible alternatives yield that same subspace;
- whether ambiguity changes the subspace rather than merely its parameterization.

A response parallel to `1`, including zero, is structurally confounded with the free common mean. Record `NOT_TESTABLE_AS_INTERNAL_CONTRAST`; do not call it evidence that no torque exists. A rank-two subspace would leave two residual degrees of freedom in a subsequent four-summary test, but this PR does not perform that test.

For local or bounded families, emit only the identified family and its limitations. Do not arbitrarily choose a representative and label the whole family identified.

## 6. Source evidence and decision policy

Maintain a stage-specific evidence table: required fact, source/version, positive locator, what the source supplies, what remains unspecified, relevance to absolute response, relevance to mean-subspace identification, and the disposition.

Relevant categories include torque convention, units and masses, campaign geometry, injection point, correction placement, copper aggregation/equivariance, sapphire aggregation, input order, and excluded target-bearing fields.

For each missing item, state the passages inspected and the nearest positive description. Phrase absence as “not specified in the reviewed corpus/passages,” not “does not exist.” Do not carry the older equation-(64) Bayesian NO-GO into the earlier copper aggregation by assumption: they are different stages.

Where feasible, demonstrate nonidentifiability with two source-admissible completions giving different responses or subspaces on synthetic data. Explain which published constraints they satisfy. Two arbitrary algorithms are not a proof of nonidentifiability if one violates a stated constraint. An exact affirmative invariance argument is equally acceptable; do not manufacture missing-information blockers.

Emit separate stage results and one overall disposition:

| Disposition | Meaning and required support |
|---|---|
| `GO_FULL_RESPONSE` | The four-summary affine response is source-identified under explicitly declared fixed-input conventions, has usable contrast rank, and is obtained without prohibited outcomes. |
| `GO_MEAN_SUBSPACE_ONLY` | The absolute response is not identified, but every admitted ambiguity preserves one usable mean subspace; provide an algebraic certificate. No physical torque scale is authorized. |
| `CONDITIONAL_MAPPING_ONLY` | Only preliminary conversion, a local response, an identified family, or an additional-assumption-dependent mapping is available. No single four-summary response is authorized. |
| `NO_GO_IDENTIFIABILITY` | A usable four-summary response/subspace cannot be established from the reviewed source contract, or it is structurally confounded. Name the missing information or obstruction. |
| `UNRESOLVED_SOURCE_ACCESS` | Essential source material could not be reviewed. Do not replace this with a scientific absence claim. |

Preliminary conversion can be available even when overall disposition is NO-GO. Distinguish unresolved implementation/contract errors from all scientific dispositions: errors fail the build rather than becoming NO-GO or a non-rejection.

For **every** disposition, set `real_data_torque_fit_performed=false`, `statistical_test_performed=false`, `new_G_estimate=false`, and `independently_audited=false` unless an actual independent disposition has subsequently been supplied. GO authorizes preparation of a separate test specification only, never an automatic extension of this PR.

## 7. Freeze and source-access chronology

Before coding or computing new response results:

1. Complete the bounded input/source inventory and syntax-only validation of the prospective JSON. Source reading, this supplied specification, and prior expectations are allowed before freeze and must be disclosed.
2. Freeze the exact source projection, permitted corpus, intervention, orders, units, mathematical and decision policies, dependencies, exclusions, source-precision convention, planned paths, focused tests and mutation requirements. Declare `outcome_blind=false` and describe known #47–#49 outputs and the pre-freeze source observations. Do not include a claimed final response verdict.
3. Make the preregistration the **sole file in the first commit**, push it, open the GitHub draft PR, and record GitHub's actual creation timestamp.
4. Only afterward implement the response evaluator, evaluate the new feasibility result, and write result-bearing notes/artifacts. Commit the result-driving source snapshot before artifact emission. Preserve the original freeze unchanged.

The GitHub anchor belongs in the later implementation/attestation, not in a self-referential frozen file. Record this specification's pre-existing authorship honestly; copying it into a post-anchor commit does not make its content newly authored after the anchor.

Use the existing strict freeze verifier. For new implementation-chronology checks, avoid history-simplified added-file queries; preserve full-history and first-introduction semantics. Do not require every intermediate commit to be green.

Source-access records must distinguish rendered-page inspection, parsed text, attributed prior inspection, raw bytes actually obtained, and independent review. Hash raw bytes only if actually available; metadata and transcription hashes are not PDF hashes. A bounded source-access limitation may be reported without inventing custody or a visual inspection.

## 8. Data boundary and deterministic artifact

Separate frozen, result-driving inputs from known-but-excluded outcomes. The response builder must not numerically consume:

- measured Table 15 torque central values or their inter-method differences;
- Table 16 G values, #47 aggregate values, #48 statistics, or #49 contrasts/model results;
- Table 19 dark uncertainties, equation (64), CODATA G, or fitted posterior amplitudes/phases.

Reported sampling/error-design information may be reviewed to establish an aggregation contract, but must not be substituted by downstream covariance to invent an upstream estimator. Any new numerical use must be explicitly projected and frozen before implementation. Source URLs, page locators, and known-outcome disclosures are not numerical authorization.

Instrument actual builder file reads and Git blob reads, and separately declare verification-only reads. Test the allowed import closure. Require numerical/authorization invariance to changes in excluded context fields independently of digest rejection. A changed allowed source coefficient must affect the appropriate response or raise a specific contract error; a mismatched digest alone does not prove behavioral input use.

Produce deterministic JSON containing the protocol and source identities; freeze/anchor/source-commit provenance; source-access record; intervention; unit and order maps; permitted input projection; preliminary response records; aggregation findings; identified response/subspace or explicit absence; evidence-backed limitations; disposition; prohibited-action flags; and review qualification.

Use canonical rational records for rational quantities and explicit symbolic/conditional records otherwise. Do not turn an unknown into zero, assume a finite value from an absent field, or write a speculative response as an authoritative numeric vector. Canonical JSON must reject duplicate keys and nonfinite values. The read-only `--check` must validate provenance, field consumption, dispositions and exact artifact freshness without network access or recomputation of historical scientific outputs.

## 9. Bounded implementation surfaces

Proposed new paths, to pin before freeze:

```
Discovery/nist_2026_torque_response_feasibility.py
Discovery/nist_2026_torque_response_feasibility_mutations.py
Experiments/GMeasurements/nist_2026_torque_response_feasibility_preregistration_v1.json
Experiments/GMeasurements/nist_2026_torque_response_feasibility_source_attestation_v1.json
Experiments/GMeasurements/nist_2026_torque_response_feasibility_v1.json
Experiments/GMeasurements/nist_2026_torque_response_feasibility_mutations_v1.json
Notes/NIST2026TorqueResponseFeasibilitySpecification.md
Notes/NIST2026TorqueResponseFeasibility.md
tests/test_nist_2026_torque_response_feasibility.py
tests/test_nist_2026_torque_response_feasibility_mutations.py
```

Modify `.github/workflows/verify.yml` only to add the two read-only guards for the new feasibility and mutation artifacts. Record mutation interpretation in the main result note; no additional maintenance document is necessary.

Do not change existing scientific artifacts, freezes, Lean sources, toolchains, shared mutation infrastructure, or prior measurement modules. If a genuine blocker requires a departure, identify it explicitly rather than expanding the PR silently.

The results note must explain the intermediate-to-final distinction, mathematical support for the actual disposition, and the smallest missing-information request or next scientific question. Do not append an implementation of that next question.

## 10. Focused validation and bounded mutations

Use behavior tests separate from artifact/provenance tests. Cover the new boundary with:

- Independent exact checks of the preliminary formula, units, signs, campaign-to-summary order, and peak-versus-difference convention; use an algebraically distinct inverse/forward identity, not the production routine as its own oracle.
- Synthetic response propagation through fixed affine maps and a coupled nuisance fit; include a servo-only input perturbation that induces a nonzero free-summary response.
- Synthetic failure of a naive equal-weight rotation substitution under unequal gains/weights or a relevant prior; also test a genuine equivariant case that succeeds without full posterior reproduction.
- Exact subspace equivalence under `c*a + q*1`, an alternative changing the subspace, a rank-one/confounded response, and a local-only map that must not acquire a global label.
- Every disposition, complete versus missing evidence, access failure versus documented absence, required source locators, finite-input handling, frozen-field consumption, excluded-field invariance, and actual read/import closure.
- Sole-file freeze, anchor chronology, source-snapshot binding, canonical serialization, freshness, and the explicit absence of fitted torque/statistical/G outputs.

Run **eight** isolated production mutations, specified before freeze:

1. Use the one-sided factor for the peak-to-peak conversion.
2. Corrupt one metric-prefix conversion.
3. Replace campaign-specific geometry with a single copper/nominal row.
4. Introduce a numerical dependency on excluded torque/G outcomes; use a valid synthetic input fixture to expose the dependency rather than scoring digest failure.
5. Substitute an unlicensed equal-weight final copper aggregation.
6. Erase a coupled cross-method response solely because that method's direct injection is zero.
7. Treat any nonidentical response vectors as different mean subspaces, rejecting a valid scale/common-mean equivalence.
8. Promote a preliminary/local/assumption-dependent result to final-response GO.

Each mutant must reach a designated semantic assertion on a suitable real or synthetic fixture, even when the actual source verdict is NO-GO. Retain a surviving baseline, a killed faulty calibration, and a surviving executable-equivalent control. Infrastructure, syntax, import, runtime, skipped-test, digest and history failures earn no mutation kill credit. Reuse the existing runner; do not rerun unrelated families.

On the final tree, run the focused tests, one complete Python suite, the two new read-only guards, and worktree plus PR-range `git diff --check`. Run directly implicated inherited guards only when needed by a real dependency or changed surface. No local Lean run is required when its sources and linked contracts remain unchanged; obtain final proof attestation through exact-head CI. Publish only the ready tree and retain the exact-head CI evidence.

## 11. Acceptance and handoff

Accept the implementation when the frozen intervention and complete input projection are machine-consumed; the preliminary/final/shape-only distinctions survive adversarial tests; the actual source disposition is supported without outcome-tuned gains; required automated validation passes; and the artifact clearly preserves all nonclaims. Do not require a GO outcome for acceptance.

Continue under the accepted provisional workflow while independent review is unavailable. Do not create a scientific dependency on unaudited result values unnecessarily. Mark any genuine inherited dependency and preserve **PROVISIONAL — INDEPENDENT AUDIT PENDING**.

Update the existing `gpt_RollingAuditHandoff.md` **in place**, Drive ID `145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd`, and verify readback. Reconcile #49's already-confirmed merge with its obsolete open status; distinguish current GitHub state from last independent acceptance. Do not rewrite `claude_Current.md`, assign DM IDs, or close Claude-owned findings.

Report the actual disposition and limits, final verification SHA, focused/full-suite/guard/mutation evidence, exact-head CI, BLOCKING findings separately from DEFERRED MAINTENANCE and FUTURE HARDENING, and any needed source clarification. Preserve prior same-SHA evidence rather than rerunning checks for the handoff.

Leave the completed PR **unmerged for Miguel**. Required method: **Create a merge commit**; never squash or rebase the freeze/anchor ancestry.

### Eventual Claude audit prompt

Audit the exact final head and its actual scientific dependencies, reusing retained same-SHA automated evidence. Focus on the intervention's physical-versus-operational meaning; differential torque, units and factor conventions; target-independent gains; campaign and configuration ordering; propagation through coupled copper aggregation; legitimate equivariance versus invented averaging; mean-subspace identification despite scale/common-mode ambiguity; local versus global response; stage-specific missing-information evidence; genuine read closure; and whether the disposition authorizes only what the record supports. Distinguish source-feasibility approval from causal or statistical acceptance. Classify BLOCKING, DEFERRED MAINTENANCE and FUTURE HARDENING separately.

## 12. Provenance references

Primary source: Schlamminger et al., *Redetermination of the gravitational constant with the BIPM torsion balance at NIST*, *Metrologia* 63 (2026) 025012, DOI `10.1088/1681-7575/ae570f`; specific locators are in §4. The publisher identifies the article as CC BY 4.0. Source-derived facts above are limited to the measurement-chain observations and starting transcription; the intervention, feasibility taxonomy, mathematical requirements and implementation design are project proposals.

Repository context, all at `81169a9d54e1540d82b4ad14ffa7dcd6d4fd3c77`: `Notes/NIST2026ConfigurationModels.md`, `Discovery/nist_2026_configuration_models.py`, and `Discovery/nist_2026_estimator_feasibility.py`.

Audit context: the live `claude_Current.md` and `gpt_RollingAuditHandoff.md` retrieved in this planning session. No independent audit, repository edit, preregistration publication, source-response computation, or scientific result was performed to prepare this specification.
