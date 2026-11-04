# The Number Project — Current Work Order

**Task:** NP-POWER-THRESHOLD-01  
**Revision:** 1 — prepared 2026-09-28 UTC  
**Title:** Power-aware family rejection with a certified finite-sample moment threshold  
**Stage:** SPECIFICATION PREPARED; NOT FROZEN; PRODUCTION IMPLEMENTATION AND SCIENTIFIC EXECUTION NOT STARTED  
**Destination:** The Number Project repository implementation context  
**Control intensity:** RIGOROUS for statistical inference, numerical qualification, provenance and claims; proportionate additive software validation.

## 0. Authority and verified baseline

On 2026-09-28 Miguel selected the tighter-threshold direction and authorized starting either its implementation specification or bounded repository work. This delivery takes the specification route. It creates no repository branch, commit, PR, scientific seed or study dataset. Continuing the bounded package is within that authorization; do not ask Miguel to repeat it merely because this packet was prepared in Workflow Management. Merge, release, new paid services, outreach and substantive follow-on studies remain separate decisions.

Verified main at preparation: `6fd4b3060d3490e4a2b815ef11bc4570df06c999`, the true merge of PR #61 on 2026-09-27T19:17:27Z. Its parents are `0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f` and `a8d1d1285064e75fecb82ccf26fd27e496de09ad`. Post-merge [Verify #346](https://github.com/mdiaz4052/The-Number-Project/actions/runs/36343810942), run `36343810942`, succeeded at that exact merge SHA. There were no open PRs at preparation. Claude's 2026-09-27 audit accepted the #61 head with zero blocking findings; its unmerged wording was an audit-time snapshot. PR #60 remains merged with independent review deliberately deferred/not completed. This package does not reopen it.

This public-safe work order and its companion JSON may be snapshotted for the bounded repository package. They contain no private Drive identifiers or copied private audit reports. Keep private navigation and retrieval metadata in the GPT handoff. Do not publish that handoff, private audit files, credentials or unrelated materials. Preserve existing sharing permissions.

## 1. Objective and chosen first version

Determine whether a smaller, statistically justified aggregate-error allowance detects more omitted curvature while retaining an at-most-5% marginal probability of rejecting a family containing the true law, under the specified synthetic model.

The first version uses a **finite-sample Cantelli moment bound** for squared validation error, multiplied by an independently calibrated upper noise scale. This is a conservative bound on an error quantile, not an exact or optimal quantile. It avoids adding Monte Carlo quantile-estimation error, multidimensional quadrature, or a new runtime dependency to this bounded package.

The proposed factor is **79/100 = 0.79**, replacing the legacy worst-case factor 2. The new rule uses a 97.5% upper noise bound, reserving another 2.5% for an unusually unfavorable validation-error realization. Its total analytical bound is below 5%. These constants come from the model moments and fixed sample sizes, not from dividing #61's observed errors or tuning old outcomes. No improved-detection result exists yet.

## 2. Controlling specification

Companion: `NP_POWER_THRESHOLD_01_preregistration.prepared.json`.

- Prepared file: **29,183 bytes**, SHA-256 `5f8a9430171abe6938e53f1e9333330ebd2fea34d6878543f8e09e902c581045`.
- Canonical `science` SHA-256: `b6f17e302821191cd6cec6a540f2b12c7a6482d2742271918654393edfcd85b5`.
- Canonical serialization: UTF-8 `json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"`.

This work order governs authority, scope, delivery and routing. The JSON's `science` object fixes scientific and numerical choices. Resolve any material conflict by an explicit revision before scientific seed creation; do not silently choose whichever clause permits execution. Prepared launch bindings are deliberately null and are not executable. The companion remains PREPARED_NOT_FROZEN until properly bound and committed.

`check_preparation.py` and `NP_POWER_THRESHOLD_01_design_checks.json` provide reproducible preparation calculations. They do not constitute the future production implementation, a scientific trial, a formal Lean proof or an independent audit.

## 3. Mathematical contract — qualify before seed creation

For n=64 training and v=48 validation observations, let all standardized training errors U_i and validation errors V_j be mutually independent Uniform[-1,1]. Write A=mean(U), B=mean(V), C=mean(V²), and

`S = mean((V_j-A)^2) = C - 2*A*B + A^2`.

The true candidate's training-only fitted log-intercept absorbs the average training noise. Its validation RMSE is therefore `epsilon*sqrt(S)` in exact arithmetic. All validation residuals share A; they are **not independent**. The derivation must retain this dependence.

Using E[U²]=1/3 and E[U⁴]=1/5:

- E[S] = 1/3 + 1/(3n) = **65/192**.
- Var(C) = 4/(45v).
- Var(-2AB) = 4/(9nv).
- Var(A²) = 2(5n−3)/(45n³).
- The cross-covariances vanish by independence and centered odd moments.
- Var(S) = **4031/1966080** for the fixed n,v.

Cantelli's inequality bounds P(S−mu >= t) by variance/(variance+t²). For c=79/100 and g=c²−mu, require exact rational checks `g>0` and `g²>=39*variance`. The minimum factor supplied by this particular moment inequality for a 2.5% allowance is approximately 0.788235229929064; 0.79 is a conservative upward choice. At 0.79 the calculated tail bound is approximately **0.024526601027452**. This is a bound, not a measured tail rate or exact percentile.

For independent paired errors, d=e1−e2, and F(q)=P(|d|/(2epsilon)<=q)=2q−q² on [0,1]. With m pairs choose q satisfying F(q)^m=alpha. The maximum absolute paired difference divided by 2q supplies an upper noise-scale bound with failure probability alpha in the ideal model. The new rule uses alpha=1/40.

On both events `upper>=epsilon` and `S<=c²`, at least the true candidate has RMSE<=c*upper. Consequently the minimum over the complete candidate family cannot reject. The union bound yields

`P(false family rejection) <= 0.025 + 0.024526601027452 < 0.05`.

This combination does not require independence between the two failure events. The moment and calibration derivations do require their stated distributional, within-dataset independence and fitting assumptions. This is a **marginal family-level** bound at each prescribed budget, not simultaneous coverage across the study or a guarantee that the highest-ranked formula is correct.

**Gate M:** independently re-derive the moments, paired-maximum bound and true-member-to-family implication; verify the numerical implementation before scientific seed creation. The preparation script also verifies the moments through exact integration of independently expanded polynomials at sixteen small n/v pairs, followed by exact parameter checks at n=64,v=48. An implementation must not use the production formula as its own only oracle. If the gate fails, preserve the reason and stop before seed; do not search for a replacement factor on scientific observations.

## 4. Certified numerical thresholds

For alpha in {1/20,1/40} and m in {16,64,256}, compute q_lower as the largest multiple of 1e-15 satisfying `(2q−q²)^m <= alpha`. Use exact rational bisection and verify that the next grid point violates the inequality. Freeze all six certificates before seed. A lower root preserves conservatism; an upper-root substitution does not.

Compute observed differences with the predecessor's binary64 log convention. Let D be the maximum absolute difference for the first m ordered pairs, and form the exact rational

`U_alpha = (Fraction.from_float(D) + Fraction(1,10^12)) / (2*q_lower)`.

Both arms use the same observed pairs, root certification and outward rounding:

`T_old = ceil_binary64(2*U_0.05 + 1e-9)`  
`T_new = ceil_binary64((79/100)*U_0.025 + 1e-9)`.

`ceil_binary64` returns the least finite binary64 value not below the exact argument. Convert to nearest float, advance with nextafter toward positive infinity if below, and verify the returned value and its predecessor against the exact rational. Exercise exact and adjacent-boundary cases independently. Keep exact certificates and human-readable values.

The baseline is the legacy **mathematical** rule with common conservative numerical handling, not a claim of byte-for-byte historical replay. Preflight must explicitly bound this rounding change against independent continuous formulas and the prior numerical convention within unchanged qualification allowances. Do not rescore #61's scientific outcomes to justify it.

At each budget, prove exactly `0.79*q_lower(0.05,m) < 2*q_lower(0.025,m)`. Thus T_new<=T_old for the same calibration record, including the common floor and monotone outward rounding. Preparation verifies this for all three budgets. Before the common floor and negligible root rounding, new/old threshold ratios are about 0.4243, 0.4068 and 0.4003 for m=16,64,256. This is threshold reduction, **not measured detection gain**. More rejections may include false as well as correct rejections; the model-conditional theorem controls the former.

Retain fixed numerical allowances: paired-difference pad 1e-12, independent candidate/metric qualification 1e-10, decision floor 1e-9. Independently recompute observed and intended paired differences, coefficients and metrics using 80-digit Decimal arithmetic; do not import the production estimator into the oracle. Verify the true fitted intercept and residual relationship. Never require every realized S to be below c²: exceeding a probabilistic bound can be a legitimate tail event.

Do not reuse DM-101's loose `<=ulp(nearest)` criterion for quantities feeding scientific decisions. New feature/exp provenance checks should use strict independently bracketed floor/ceiling values and fixed expected-result tests; exp(0) accepts only 1.0. Escalate precision 80→160→320 only for numerical ambiguity, then fail closed if unresolved. Do not modify historical bytes or claim finite-precision Decimal is a formal proof of every transcendental value.

## 5. Fixed prospective experiment

| Item | Fixed choice |
|---|---|
| Independent blocks | 64; exponent sequence [-2,-1,1,2] repeated sixteen times |
| Laws | k*x*t^-2*z^p; and the same law times exp(0.01*(log z)^2) |
| Noise | Centered independent uniform log errors; half-widths 0.0001, 0.0016, 0.005 |
| Datasets | 64 blocks × 2 laws × 3 noise levels = 384 |
| Observations per dataset | 64 training, 48 validation, 64 held-out |
| Calibration | 256 independent paired repeats; ordered prefixes 16/64/256 |
| Operational rules | Legacy 2*upper95 and new 0.79*upper97.5, each at all three budgets |
| Post-seal references | 2*epsilon and 0.79*epsilon, using the same sealed fits |
| Primary comparison | Curved law, epsilon=0.0016, m=64: new versus legacy |
| Candidate family | Five x*t^-2*z^j signatures, j=-2,-1,0,1,2; positive fitted coefficient |

The JSON spells out all inherited feature/coefficient ranges, stream and draw ordering, generation, scoring and structural-credit predicates. Use these frozen values, not changing runtime defaults. Generate fresh task-separated seeds and anonymous IDs. The known-noise 0.79 reference deliberately uses the same factor to isolate the cost of estimating noise; it is not an optimized 5% known-noise test.

Each block shares normalized banks across its six law/noise conditions; calibration, training, validation and held-out streams are separate within the block. Calibration pairs share the same clean response, and their two errors are independent. Use one complete five-class ranking per dataset, with training-only intercept fitting and unchanged ranking penalty. All threshold alternatives reuse those same fits. No threshold-specific refitting is allowed.

Total inventory: **67,584 discovery observations; 196,608 calibration responses; 2,304 operational and 768 reference assessments, 3,072 combined; 1,920 principal fits plus 384 inherited diagnostic refits**. Those dependent assessments do not multiply the 64 independent-block analysis units. Keep diagnostics and principal fits separately labeled.

## 6. Analysis, resolution and success criteria

The primary endpoint is the paired change in curved-family rejection at the specified middle-noise condition and primary budget, across all 64 blocks. Report both rejection counts, gains, losses, signed margins, all block values and the four exponent strata. Certified nesting means G_b=I(new rejects)−I(old rejects) is in {0,1}. An old-reject/new-nonreject outcome violates the implementation contract and cannot be hidden or treated as ordinary adverse power evidence.

For the single primary endpoint, report g=mean(G) and the conservative interval

`[max(0,g−0.17), min(1,g+0.17)]`.

For ideal independent bounded block gains, Hoeffding gives a two-sided 95% radius sqrt(log(40)/(2N)). At N=64 this is approximately 0.16976269; the frozen radius 0.17 rounds conservatively upward. Identically distributed blocks are not required, so the balanced fixed exponent strata are permitted. The estimand is the average gain over **this explicitly specified ideal independent-block design**, not arbitrary real-world performance.

This sample size provides coarse ±17-percentage-point resolution for a potentially substantial gain. It is not an 80%/90% power calculation or accurate empirical validation of a 5% tail. No sample expansion follows an inconclusive result. The analytical probability statements concern the idealized model; a finite hash-based generator is not proven to realize exact continuous independence.

Report `GAIN_RESOLVED_AT_PLANNED_RESOLUTION` only if complete evidence and valid nesting permit the interval and its lower endpoint exceeds zero; otherwise report `GAIN_NOT_RESOLVED` with the actual counts. Withhold the primary interval on incomplete data or failed nesting. Do not redefine the denominator or substitute a favorable secondary contrast.

Separately report adequate-family false-rejection counts for every rule/noise/budget, denominator 64, and stratum counts out of 16. Zero is not required. Observing more than 5% false rejections in a finite sample is not alone a contradiction of a probability bound: preserve and assess it, rather than rerunning for favorable counts.

Secondary analyses are descriptive: low/high noise, 16/256 pairs, post-seal known-noise references, both directions of budget/reference changes, calibration coverage and threshold ratios, base signature recovery, missed curvature, and held-out approximation. Coverage uses 64 distinct matched-block vectors, not 384 independent condition copies. Report rounding-induced discrepancies rather than suppressing them. No simultaneous 95% claim follows for all comparisons.

Family rejection, rank-1 abstention, predictive approximation and exact structural credit remain distinct. Curved truths always receive zero exact structural credit when curvature is omitted, even if a candidate predicts well. Nonrejection is not proof of truth.

## 7. Implementation boundary and information separation

Suggested branch: `experiment/np-power-threshold-01`. Reuse a matching existing branch/PR rather than duplicate it. Add package-local `Discovery/power_threshold1_*` modules for theory, calibration, orchestration, evaluation and verification; focused `tests/test_power_threshold1*`; `Experiments/SymbolicDiscovery/PowerThreshold1/`; and `Notes/PowerThreshold1.md`. File splitting within that new scope is implementation discretion.

Keep every pre-existing tracked file, historical experiment, shared module, dependency pin, Lean/toolchain file and `.github/workflows/verify.yml` byte-identical to the verified launch base. Reuse pinned accepted internal modules. New tests enter ordinary unittest discovery. If additive integration cannot work, stop before seed for an explicit scoped revision; do not silently refactor shared code or historical guards.

Use CPython 3.12, the standard library and pinned accepted internal dependencies. Record exact patch/platform/executable identity before seed. No PySR/Julia installation, external engine, evidence-card API integration or new runtime dependency is authorized.

The theory helper receives only fixed sizes and constants. The staged calibration worker receives anonymous ordered positive repeat pairs and fixed settings, not true epsilon, features, fitted residuals or study labels. Discovery receives only anonymous training/validation records plus its sealed primary T_new/64. Keep generator, seed, truth, evaluator, old outcomes and held-out data outside operational workers. Use explicit staged inventories and fresh-cache/read receipts. This is trusted-code separation, not a hostile-code security sandbox.

Source verification binds committed used-source epochs and execution receipts. It must not impose permanent equality on future shared working-tree modules. Keep all five signatures: an incomplete candidate inventory is not evidence that the whole family fails.

## 8. Launch and source-before-outcome chronology

At launch, inspect current project instructions, current GPT and Claude records, main/open PRs, the work order, companion JSON and affected source. Record the actual base. A newer compatible base is permissible only with unchanged scientific dependencies and no conflicting work; otherwise revise before proceeding.

1. Commit exact public-safe work-order bytes, prepared JSON and consumption receipt with byte counts/hashes and actual base. Keep private retrieval identifiers outside the public receipt. Do not call a modified/redacted document an exact snapshot of a different source.
2. Copy the prepared JSON to `preregistration.v1.json`; change only schema to `tnp-power-threshold/preregistration-v1`, state to FROZEN, and the four launch bindings to observed facts. The science object and digest remain identical. Commit the frozen file alone directly after the snapshot.
3. Open one draft PR and record its actual server timestamp strictly after the freeze. The later anchor records the freeze SHA; no self-hashes or fabricated future identifiers.
4. Qualify the mathematical gate, source/environment, numerical and independence fixtures, failure routes and mutations on deterministic engineering fixtures only. Preserve failed attempts and commit the fully qualified source before a scientific seed exists.
5. Draw one master seed, commit its commitment alone, publish and read back the actual remote ref before generating observations.
6. Generate the complete fixed bank once; commit anonymous data and hashes of private truth/held-out records. Publish and read back this bank seal before calibration.
7. Compute and seal all two-alpha/three-budget estimates and thresholds; publish and read back before discovery.
8. Compute every complete ranking and six operational decisions; publish and read back the selection seal before any truth or held-out access.
9. Reveal/evaluate once using sealed fits, with no refitting or label rescue. Preserve every raw result and failure/partial record, then commit the immutable science.
10. Finish read-only verification, concise reporting, existing exact-head CI and a focused independent-audit handoff. Reconcile GPT navigation. Leave the PR unmerged for Miguel; preserve ancestry with **Create a merge commit only**, never squash/rebase.

Persist each publication/readback receipt in the subsequent stage, after the observed event and before any dependent execution. Do not rewrite a seal to claim its future publication. Intermediate remote readback is not a demand to wait for a full CI run at every stage.

## 9. Validation, evidence and stopping rules

Retain consumed/frozen specifications, source/environment inventories, theory/root certificates, all preflight attempts, seed/data/calibration/selection seals and publication receipts, raw anonymous records and worker outputs, complete candidates and decisions, revealed originals, independent numerical diagnostics, block/stratum summaries, immutable result and explicit route index. Bundle complete records by stage where practical, without losing individual identities or hashes.

Qualify all sixteen designated semantic mutations in the prepared JSON, including shared-mean variance omission, wrong tail, unsafe factor, overspent alpha allowance, root/rounding errors, omitted pad, data leakage, magnitude-selected pairs, rank-1/family confusion, missing classes, rejecting equality, false structural credit, dropped failure records, forged seals and inflated independent sample size. Each killed mutation must reach its designated semantic assertion; an earlier crash is not a successful kill. Baseline and equivalent controls must survive. Use independent mathematical/numerical expectations, not self-referential tests.

No scientific retries, replacement seeds, refits, observation regeneration, exclusions or sample expansion. After the first scientific-stage failure, stop and preserve completed/partial outputs with explicit NOT_EXECUTED stages. Pre-seed engineering repairs are allowed with retained failed attempts and affected requalification. Post-seed transport retries may transfer identical existing bytes only. Necessary post-outcome verification corrections must be separately pinned, detached and read-only, preserve original failures and never change data, coefficients, thresholds or labels.

Use explicitly typed failure reasons. FAIL for an established contract/integrity violation takes precedence over UNRESOLVED necessary missing/conflicting evidence; then accounted NO_GO, PARTIAL and COMPLETE. Do not equate a bare exception with an established scientific violation. COMPLETE requires all 384 datasets and every prescribed rule/evidence check, **not favorable detection**. Theoretical qualification, evidence integrity, study completeness, observed gain, operational errors and independent review are separate axes.

The offline verifier derives the reached disposition from raw evidence, including adverse and partial cases. It may reconstruct deterministic draws/arithmetic in memory for checking, but cannot emit a new observation bank, call discovery or replace fitted coefficients. Perform one coherent affected-boundary validation and reuse the existing exact-head Python/Lean CI; no ceremonial historical campaign or local Lean rebuild.

## 10. Independent review and canonical delivery

One focused independent audit of the actual reached head must challenge the two moment derivations, calibration bound, alpha accounting and family-level implication; c/q/rounding certificates and old/new nesting; independent inputs and complete fits; prospective chronology and fresh outcomes; correct block denominators and primary-interval scope; all adverse results, failures and supported dispositions.

DM-093 needs a new scope-specific assessment for this changed rule and narrowly modeled primary interval. Do not claim #61's review automatically certifies the new method. Keep its real-data and selected-model limits. Avoid reusing DM-101's loose criterion and implement the new stage readbacks without asserting that GPT has closed DM-102. Preserve DM-090, DM-097 and DM-100 boundaries. E-001, the #60 retrospective audit and unrelated findings remain outside scope. Claude owns finding IDs and independent dispositions; do not edit Claude-owned files or launch a bookkeeping audit.

Generate the final reviewer prompt from actual exact head/base, source/science/result hashes, CI run, reached disposition, retained failures and read-only commands. No placeholders masquerading as completed facts. Resolve the current Claude file by role rather than a superseded ID. Include the following in the actual prompt, not only by reference:

> Before finishing, upload the completed audit report and update the affected canonical Claude-owned files in Google Drive, not just local copies. Fetch/read back the remote files to confirm the audited head, verdict and affected finding updates are present. Return their actual Drive links and state whether remote delivery was verified. If upload or verification fails, report the specific failure and mark Drive synchronization INCOMPLETE; do not claim the remote records are current.

Preserve rolling file IDs, historical reports and existing organization. Return scope-specific MERGE / DO NOT MERGE and BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING, with verdict and remote delivery distinguished. Reuse unchanged prior evidence and exact-head CI. Miguel retains merge and release authority.

## 11. Completion, limits and source attribution

The bounded execution is decision-complete once its supported disposition, full required evidence or explicit stopping limitation, report, exact-head verification and focused audit handoff are delivered and navigation is reconciled. Independent acceptance and user merge are separate subsequent gates. An inconclusive or adverse result does not authorize a cleanup campaign, replacement study or expansion.

This package does not authorize exact-quantile optimization, adaptive alpha selection, additional curvature grids, external-engine comparisons, arbitrary real-data uncertainty guarantees, empirical gravity claims, release, paid services, outreach or broad source/CI repairs. The model specifies independent centered uniform log errors and independent repeats; unknown distributions, drift, correlated/heteroscedastic errors, outliers and feature noise remain unresolved. Operator-generated seed commitment does not prove absence of pre-commit seed selection. No formal machine proof or independent replication is claimed.

Inherited source: [PR #61 report](https://github.com/mdiaz4052/The-Number-Project/blob/a8d1d1285064e75fecb82ccf26fd27e496de09ad/Notes/EstimatedNoise1.md) and [frozen predecessor specification](https://github.com/mdiaz4052/The-Number-Project/blob/a8d1d1285064e75fecb82ccf26fd27e496de09ad/Experiments/SymbolicDiscovery/EstimatedNoise1/preregistration.v1.json), plus privately retrieved Claude's 2026-09-27 audit/current/finding records. Historical evidence is unchanged.

Mathematical references: Nicola Apollonio, “Cantelli's Bounds for Generalized Tail Inequalities,” Axioms 14(1),43 (2025), https://doi.org/10.3390/axioms14010043; Wassily Hoeffding, “Probability Inequalities for Sums of Bounded Random Variables,” JASA 58(301),13–30 (1963), https://doi.org/10.1080/01621459.1963.10500830. These support the inequalities, not endorsement of this project-specific method.

**New preparation work:** the residual-moment derivation, exact 0.79 certificate, six rational calibration-root brackets, threshold-nesting certificates and N=64/radius0.17 design calculation. These are authored calculations awaiting independent review, not results attributed to #61 or external literature. No production implementation or scientific study has been executed for this package.
