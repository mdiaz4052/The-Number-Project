# The Number Project — Current Work Order

**Task:** NP-ESTIMATED-NOISE-01  
**Revision:** 1 — prepared 2026-09-23 UTC  
**Title:** Estimated noise and misspecification detection — independent calibration study  
**Stage:** SPECIFICATION COMPLETE / PREREGISTRATION PREPARED — NOT YET FROZEN OR EXECUTED  
**Destination:** The Number Project repository implementation context  
**Control intensity:** RIGOROUS for the estimated-noise inference, outcome custody and scientific claims; proportionate software validation elsewhere.

## 0. Authority and current state

Miguel selected the estimated-noise direction and explicitly requested preparation of the precise work order and preregistration. This packet completes that preparation. It is not an execution record or a claim that a preregistration has already been committed. No scientific seed, target observation, discovery run, new repository branch or PR was created in preparation. Launch the downstream implementation only under an instruction to execute this task/revision. Merge, release, public publication outside the authorized implementation scope, and further studies remain separate decisions.

Verified baseline: `0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f`, true merge of [PR #60](https://github.com/mdiaz4052/The-Number-Project/pull/60). There are no open PRs at preparation. [Verify #340](https://github.com/mdiaz4052/The-Number-Project/actions/runs/35800439539) succeeded at that exact merge head; pre-merge #339 also succeeded. #60 remains a terminal isolation-prerequisite NO_GO with its independent audit deliberately deferred, not completed. This study does not reopen that package or require its audit as a prerequisite.

Benchmark 0, Suite1, Margin1 and Candidate Exchange 1 remain accepted at their recorded independent scopes. Current science reuses the internal benchmark engine, not an external generator. The prior consumed NP-PYSR-ADAPTER-02 packet remains immutable under `Experiments/SymbolicDiscovery/PySRAdapter2/work_order.r1.md`; replacing this rolling work order does not alter it or its exhausted retry budget.

## 1. Deliverable and controlling specification

Answer: **When uniform measurement-noise scale is estimated from independent paired repeats, how do family rejection and missed curvature change relative to knowing the scale, and how much calibration helps?**

Deliver one additive, bounded research package with:

- the consumed instruction snapshot and frozen machine-readable preregistration;
- a calibration estimator, generator, decision/evaluation wrapper and read-only evidence verifier;
- one fixed prospective epoch of 96 datasets with retained calibration, source/seed/data/decision custody and all outcomes;
- a concise scientific report and explicit raw/operational/reconciled routes;
- exact-head CI evidence and one focused independent semantic review handoff.

The controlling scientific specification is the accompanying [prepared preregistration](https://drive.google.com/file/d/1KLnDl47Hpt-eiG-74Gd1IdKERSSEhsa4/view), `NP_ESTIMATED_NOISE_01_preregistration.prepared.json`.

- Prepared file: **24,271 UTF-8 bytes**, SHA-256 **`1c811c465f9d1d404d8a9f11dc4ef1628598045fd4616d50a5ed435cab6dd06f`**.
- Canonical `science` object SHA-256: **`19edaba69d1b2cd8b4d0235180d548eac6387b0b564863c0109a7fec6fb4c312`**.
- Canonical JSON bytes: `json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"`, UTF-8. The science digest covers only the science object, not mutable launch metadata.

This work order controls routing, scope, deliverables and execution permissions. The preregistration's `science` object controls numerical and scientific choices. Resolve any substantive conflict before source freeze and seed creation; do not pick whichever clause permits execution. Editorial or implementation-schema details may not change the science. If a scientific choice must change before launch, issue a clearly identified revision with updated hashes; never edit it silently after freeze.

## 2. Fixed scientific scope

| Item | Fixed choice |
|---|---|
| Truths | `k*x*t^-2*z^p`, and that law times `exp(0.01*(log z)^2)` |
| Noise | Independent centered uniform log errors; half-widths 0.0001, 0.0016, 0.005 |
| Features | Exact positive x,t,z; z dimensionless; y dimension L T^-2 |
| Blocks | 16 independent seeded blocks; exponent sequence [-2,-1,1,2] repeated four times |
| Datasets | 2 laws × 3 noise scales × 16 blocks = 96 |
| Observations | 64 training, 48 validation, 64 held-out rows per dataset |
| Calibration | Separate 256 paired repeats per dataset; nested first 16/64/256 pairs |
| Primary | Upper-95%-bound method, 64 pairs, compared with point/64 and known-noise reference |
| Secondary | Same methods at 16 and 256 pairs; no post-result choice of budget |
| Grammar | Existing exhaustive five-class monomial family; max factors 3, max absolute integer exponent 2 |
| Decisions | Six estimated-threshold assessments + one post-seal known-noise reference per dataset |
| Counts | 16,896 discovery observations; 49,152 calibration response values; 672 dependent assessments |

The independent analysis unit is the block. Matched conditions, shared normalized calibration noise, nested prefixes and multiple judgments do not multiply the independent sample size. The sixteen blocks provide a bounded mechanism study, not a power calculation or accurate empirical calibration of a 5% tail. No target-data pilot, optional stopping, sample expansion or performance requirement is permitted.

Maintain the historical coefficient/feature ranges and fixed scoring values as spelled out in the preregistration; do not retrieve floating defaults at execution. New records are prospective. Historical Margin1 results inform the design but are never pooled as fresh observations.

## 3. Estimated-noise rule and limits

For each paired repeat compute `d_j = log(y_j1) - log(y_j2)` from the observed positive response values. The signal cancels under the assumptions. No clean response, generator error, true noise label or candidate residual may enter estimation.

For m pairs:

- Point estimate: `sqrt(1.5 * fsum(d_j*d_j) / m)`.
- `alpha=0.05`; `q_m = 1 - sqrt(-expm1(log(alpha)/m))`.
- Ideal upper bound: `max(abs(d_j)) / (2*q_m)`.
- Operational upper bound: `(max(abs(d_j)) + 1e-12) / (2*q_m)`.
- Decision threshold: `2*scale + 1e-9`.

Record the ideal and operational upper bounds separately. The `1e-12` log-difference allowance is a fixed numerical safeguard, not fitted noise. It must pass the preregistered independent numerical checks; exceeding the allowance is not permission to enlarge it. The point estimate has no claimed coverage guarantee.

In the ideal uniform model, `P(|e1-e2|/(2*epsilon) <= t) = 2t-t²`; the maximum over m independent pairs gives the stated marginal 95% upper coverage. For the adequate law, a training-only intercept fit leaves each validation residual bounded by `2*epsilon`. Hence, under the model and numerical qualification, false **family** rejection by the upper-bound rule is at most 5% marginally at each fixed budget. This is an analytical, assumption-dependent argument to be independently reviewed, not a measured 5% error rate, a formal machine proof, or a rank-1 correctness guarantee.

Finite PRNG arithmetic is not an ideal continuous random source; the numeric pad and exact environment are disclosed. Calibration cannot identify shared drift or systematic error that cancels between repeats. Unknown distributions, correlated repeats, feature noise, outliers, heteroscedasticity and missing replicate measurements remain outside this package. A nonrejected family is not proven true.

## 4. Read boundaries and shared-fit contract

Use three separate roles with staged inputs and explicit dependency inventories:

1. **Calibration worker:** anonymous `dataset_id`, ordered `{pair_id,response_1,response_2}` records, and only the fixed estimator constants/budgets. Do not provide features, full preregistration, condition mapping, seed, generator, true epsilon, candidate outputs or discovery/held-out rows. Commit all estimates and thresholds before discovery starts.
2. **Discovery worker:** sanitized anonymous train/validation payload and the primary estimated `upper95/64` threshold in `acceptance_validation_rmse`. No calibration truth, full preregistration, old outcomes, generator/evaluator or held-out access. Use the accepted staged runner and its source/cache receipts.
3. **Evaluator:** only after all operational selections are committed, reveal the private mapping, seed, true scales/structures and held-out data; calculate reference and held-out metrics without changing any fit or sealed label.

The estimator's full 256 pairs permit all three fixed prefixes; it does not know which prefix will look favorable. Public dataset IDs are generated by the frozen hash-order permutation and carry no law/noise labels. The designer/operator knows the study families and may infer relationships: this is not global blinding or a hostile-code sandbox.

The accepted engine ranks by validation error plus fixed complexity penalty; the threshold changes decision labels, not fitting or ranking. Preflight must prove this with deliberately different thresholds on fixtures. Reuse one complete ranking per dataset for all six operational rules. All five expected signatures must be verified independently, not merely asserted by a count. An incomplete inventory does not support rejection of the whole family. Keep rank-1 and family-minimum assessments separate. Recompute secondary threshold-dependent decisions in new code; do not relabel inherited primary ablation judgments as applying to every threshold.

## 5. Implementation boundary

Use branch `experiment/np-estimated-noise-01` and artifact directory `Experiments/SymbolicDiscovery/EstimatedNoise1/` at authorized launch. Reuse an existing matching branch/PR rather than creating a duplicate. Expected new paths:

- `Discovery/estimated_noise1_calibration.py`: pure pair estimator and schema validation.
- `Discovery/estimated_noise1_science.py`: private generator, post-seal evaluator and aggregation.
- `Discovery/estimated_noise1.py`: custody stages and staged orchestration.
- `Discovery/estimated_noise1_verifier.py`: read-only evidence/source/history verification.
- `tests/test_estimated_noise1.py` and a narrowly named mutation-preflight module.
- `Notes/EstimatedNoise1.md` and study-local figures/evidence.

Names may be split further within these new package-local paths where necessary; no scientific choice changes. Existing tracked files, historical results, root dependencies, Lean sources, toolchain and `.github/workflows/verify.yml` remain byte-identical. New tests join existing unittest discovery; do not append a workflow step.

Use CPython 3.12 and standard-library facilities, including `decimal` for independent high-precision reference arithmetic. Freeze the exact patch version, executable identity/platform and source closure in preflight. No new binary/runtime setup, Julia/PySR installation, external engine or evidence-card API integration is needed.

New historical source checks must verify committed bytes at the used source epoch and the receipts from execution, not impose permanent equality on future shared working-tree modules. Historical scientific artifacts remain immutable. If additive integration genuinely cannot work, stop before seed and request a scoped revision; this packet does not silently authorize a shared-core/CI refactor or historical guard repair.

## 6. Launch bindings and irreversible scientific chronology

At launch, inspect current main/open PRs, this exact packet, the prepared preregistration, current GPT handoff and current Claude record. Verify relevant code at the actual base. If main advanced compatibly while scientific dependencies and accepted artifacts are unchanged, record the actual base. Conflicting work or a changed inference boundary requires a revision before proceeding. Reuse exact unchanged CI; do not dispatch duplicate checks.

1. Snapshot this exact work-order byte sequence, its receipt and the prepared JSON into the repository. The receipt records SHA-256/length, observed Drive modification metadata, retrieval time and actual base. Preserve source references privately where public disclosure is not covered by launch authorization. Do not silently redact or alter consumed instructions; settle any required public snapshot treatment before its commit.
2. Produce `preregistration.v1.json` by copying the prepared JSON, changing only schema to `tnp-estimated-noise/preregistration-v1`, state to `FROZEN`, and filling the four `launch_binding` values with the actual base SHA, instruction snapshot commit SHA, consumed work-order SHA-256 and prepared-file SHA-256. Its science digest must remain exactly the value above. Commit this file alone, directly after the snapshot commit. No fabricated hashes or remaining nulls.
3. Open one draft PR and record the server creation timestamp strictly after the freeze. Later `anchor.json` holds the freeze SHA and PR timestamp; the preregistration does not self-reference its own commit.
4. Implement and preflight on engineering fixtures only. Commit the passing source/environment/inventory/tests/mutations and anchor. Preserve failed preflight attempts. No scientific seed yet.
5. Generate one scientific master seed. Commit its digest in a sole-file seed-commitment epoch after the source epoch. Publish and read back the actual remote head before generation. Source and preregistration digests bind the seed record; retain the seed privately until reveal.
6. Generate the complete fixed bank once. Commit anonymous public calibration/train/validation records and hashes of private oracle/held-out/seed records. No scientific retry or replacement.
7. Calculate all estimates/thresholds through the staged calibration boundary, then commit the full calibration seal before discovery.
8. Run one discovery evaluation per dataset, retain complete output/receipts, derive all six operational decisions, and commit a complete selection seal before evaluator access to truth or held-out data.
9. Reveal and evaluate. Commit raw results and all integrity checks, including known-noise reference calculations and independent numeric checks. Retain any failure and partial outputs; do not revise sealed labels.
10. Finish read-only verification, report, explicit route index and exact-head CI. Update the existing GPT handoff with factual state and the focused audit prompt. Leave unmerged for Miguel; **Create a merge commit only**, never squash/rebase the custody chain.

The freeze has no source/seed/final-head self-hashes. Later source receipts bind earlier frozen inputs; final CI is attested externally in PR/handoff. Never rewrite an immutable result merely to embed a later successful CI run.

## 7. Required artifact contracts

Freeze exact machine schemas in source before seed creation; enforce missing/extra fields, duplicate JSON keys and numeric types. Each artifact carries task/revision/schema and explicit identity/digest bindings. Required records:

| Artifact | Required content |
|---|---|
| `work_order.r1.md`, `work_order_receipt.json`, `preregistration.prepared.json`, `preregistration.v1.json` | Exact instructions and launch/freeze linkage |
| `anchor.json`, `preflight.json` | Actual base/snapshot/freeze, draft PR timestamp, source closure, environment, fixture and mutation results |
| `seed_commitment.json` | Seed hash and already-known frozen source/scientific-policy digests; no self commit SHA or future publication claim |
| `public.json`, `calibration.json`, `commitment.json` | All 96 anonymous train/validation datasets, 256 pairs each; explicit inventory and private truth/held-out hashes; observed remote seed-commit SHA and timestamp recorded before generation, persisted here afterwards |
| `calibration_estimates.json`, `calibration_seal.json` | For each dataset/budget: prefix input hash, n, sum of squared differences, maximum absolute difference, point, q, ideal/padded upper, pad, both thresholds, worker receipt and committed-seal linkage |
| `selection/<id>.json`, `selection_seal.json` | Full five-class fits/ranking, six family/rank1 labels and signed margins, primary policy consistency, approximation labels, worker receipts, output digests and all-96 inventory |
| `oracle_reveal.json`, `heldout.json` | Original private bytes, seed/mapping and generator truth; verified against commitments after seal |
| `evaluation.json`, `controls.json` | Per-dataset/rule reference and held-out metrics, coverage/ratios, structural match/credit, all numeric/custody/source/inventory controls |
| `summary.json`, `result.json` | Preregistered aggregation, expected/interpretable counts, explicit missing/failed IDs, evidence/study/review axes and immutable raw result |
| `operational_failures/*`, `verification_routes.json` | Every failure's stage/source/stdout/stderr or explicit retention limitation; raw/operational/optional reconciliation routes with explicit disposition keys |
| `Notes/EstimatedNoise1.md` | Question, design, dependence, results and limitations; correct verification command; focused audit scope |

The code-level schemas may add neutral custody fields before source freeze; they may not change estimators, treatment assignment, numerical thresholds, scientific metrics, disposition logic or missing-data interpretation. Preflight validates the schemas and report derivation end to end using fixtures. No post-result schema coercion that hides disagreement.

## 8. Analysis and acceptance

Primary reporting is by each noise level: upper95/64 versus point/64 and known-noise reference. Show both directions of paired decision changes, curved recognition/misses and adequate-family rejection. Secondary reporting covers the fixed other budgets. Include all block values, exponent-stratified counts, actual denominators, and scale/threshold ratios with median/min/max. Do not pool matched copies as independent coverage trials. No population confidence intervals, p-values or chosen best budget.

Report complete candidate metrics and distinguish: best family residual, rank-1 selection, approximate prediction, base-exponent recovery and exact structural match. A stable curved approximation always lacks exact structural credit. Held-out diagnostics do not rescue or rewrite pre-reveal decisions.

Completion is evidence completeness, not a favorable method score. Derive disposition with this precedence:

1. **FAIL:** established integrity, custody, numerical-contract, leakage or unsupported-credit violation.
2. **UNRESOLVED:** material missing/conflicting evidence prevents judgment, with no established violation already determining FAIL.
3. **NO_GO:** a sound accounted failure permits zero fully interpretable datasets.
4. **PARTIAL:** 1–95 fully interpretable datasets; all others accounted, no hidden exclusions.
5. **COMPLETE:** all 96 datasets and all required checks interpretable and integrity-valid, irrespective of recognition/coverage counts.

Use prefix `ESTIMATED_NOISE_1_`. Record `evidence_integrity=PASS/FAIL/UNRESOLVED` separately and retain `PROVISIONAL — INDEPENDENT AUDIT PENDING`. The verifier derives the reached disposition from evidence; it must not reject honest adverse results just because they are adverse or accept arbitrary supplied labels. A missing budget does not become zero error. Preserve post-science operational failure separately from valid raw scientific completion.

## 9. Validation and stop rules

Before the scientific seed, satisfy every fixture and ten semantic mutations in the preregistration. Each mutation needs its intended assertion; a crash before that assertion does not count. Baseline and equivalent control must survive. Include alternate numerical-policy fixtures, not only literals copied from the experiment.

The independent arithmetic implementation must not call the production estimator/evaluator as its oracle. Use 80-digit Decimal reference arithmetic from stored float values for calibration and candidate checks. Qualify the fixed difference pad and adequate-member residual bound. Repeat necessary numeric checks against all revealed actual records after seal; never adjust the pad from outcomes.

At the first scientific-stage failure, stop the scientific pipeline, retain every existing byte, and account for unrun IDs as NOT_EXECUTED. No seed replacement, scientific rerun, excluded dataset, refit, optional stopping or changed criterion. Before seed, engineering corrections and affected requalification are allowed with prior failures retained. After seed, identical-byte transport/readback retries are allowed; they do not authorize regeneration or rediscovery. A necessary post-outcome verifier correction must be detached, separately source-pinned and read-only, preserving the original failure and raw scientific epoch.

Final validation: focused new tests and offline guard; one full Python-suite result at final head (required CI may supply it); both existing CI jobs, including Lean, successful at that exact head; clean whitespace/status and preservation checks. No unrelated local mutation campaign, manual Lean build or historical scientific rerun. Keep scientific failures even if CI/reporting needs a truthful adverse-result route.

## 10. Findings and independent-review scope

DM-093's retained scope condition is directly engaged: this is an estimated-noise decision rule. The bounded assumptions, conditional derivation, numeric qualification and prospective evidence are the proposed scope-specific resolution, **not** a GPT declaration of closure. Independent review must adjudicate that boundary before independent acceptance. No global claim on arbitrary data follows.

Preserve DM-090's CPython 3.12 boundary. Avoid DM-097/DM-100 shared-workflow/core triggers through additive integration. Address DM-098's failure-awareness concern in the new verifier without claiming to repair the old Candidate Exchange guard. No new `evidence_card` call site, hence no claimed DM-099 closure. DM-094 terminology is handled precisely on the new report; no blanket closure or historical rewrite. Release/replication questions DM-095/096 and unrelated findings remain at their recorded scopes. Claude owns finding IDs, severity and closure.

At completion, construct a prompt using actual head/base/CI/artifact hashes and ask Claude to independently assess:

- pair-based separation of signal/noise, ideal-to-numerical coverage reasoning and limits;
- calibration/target independence, intentional matching, prefix nesting and correct analysis unit;
- estimator and threshold seal before discovery; complete five-class enumeration and training-only fits;
- no true-epsilon/residual/held-out leakage into operational decisions;
- primary versus secondary comparisons, adverse outcomes and absence of post-outcome tuning;
- structural-credit limitations, derivation of all dispositions, and source/evidence/true-merge custody.

Reuse unchanged accepted evidence and exact-head CI. Request scope-specific MERGE / DO NOT MERGE, with BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING, and leave merge to Miguel. Do not reopen #60 or run a bookkeeping-only audit.

Include this exact delivery instruction in the eventual reviewer prompt:

> Before finishing, upload the completed audit report and update the affected canonical Claude-owned files in Google Drive, not just local copies. Fetch/read back the remote files to confirm the audited head, verdict and affected finding updates are present. Return their actual Drive links and state whether remote delivery was verified. If upload or verification fails, report the specific failure and mark Drive synchronization INCOMPLETE; do not claim the remote records are current.

Preserve existing rolling-record IDs, historical reports and organization; change only records affected by substantive review. Scientific verdict and delivery status are separate.

## 11. Grounding references

- [Margin1 report](https://github.com/mdiaz4052/The-Number-Project/blob/0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f/Notes/MisspecificationMargin1.md), [frozen design](https://github.com/mdiaz4052/The-Number-Project/blob/0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f/Experiments/SymbolicDiscovery/MisspecificationMargin1/preregistration.v1.json), and [generator/evaluator](https://github.com/mdiaz4052/The-Number-Project/blob/0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f/Discovery/symbolic_margin_science.py).
- [Suite decision engine](https://github.com/mdiaz4052/The-Number-Project/blob/0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f/Discovery/symbolic_suite_engine.py) and [underlying fit/ranking engine](https://github.com/mdiaz4052/The-Number-Project/blob/0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f/Discovery/symbolic_benchmark_engine.py).
- [NIST lack-of-fit strategy](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd446.htm) for model-independent replicate variation; this package does not adopt its F-test.
- [NIST uniform distribution](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3662.htm) for support/scale/standard-deviation distinctions. The paired-maximum bound is derived here, not attributed to that page.
- Current Claude record and affected DM-093/094/097/098/100 detail records were consulted by role during preparation; their independent scope remains controlling. Retrieve only affected records at launch, not the entire historical ledger.

No new standards adoption, permanent telemetry, release, empirical source hunt or other Idea activation is included.
