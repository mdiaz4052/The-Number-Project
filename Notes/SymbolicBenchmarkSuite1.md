# Benchmark Suite 1 — scientific decision

**Technical disposition: `BENCHMARK_SUITE_1_PASS` — PROVISIONAL — INDEPENDENT AUDIT PENDING.**

All **24/24** prespecified realizations met their cell-specific scientific criteria. The engine selected the true structural class in all **12/12** recoverable cases and abstained in all **12/12** negative cases. Both wrong-grammar constructions were rejected before evaluator reveal, including four useful predictive approximations.

An operational failure occurred **after the scientific results were written**: the disposition exporter expected Benchmark 0's accepted reconciliation to contain `disposition`, but its actual field is `final_disposition`. The raw Suite 1 PASS, its complete evidence, and the later `NO_GO_CAPABILITY` operational-failure record are preserved. A separately sourced routing adapter resolves only that schema mismatch. It changes no scientific result or criterion.

- Work and exact completion-head/CI binding: [PR #56](https://github.com/mdiaz4052/The-Number-Project/pull/56), **leave unmerged**.
- Authoritative machine-readable route: [`disposition_index.json`](../Experiments/SymbolicDiscovery/disposition_index.json), schema v2.
- Final Suite 1 disposition: [`routing_reconciliation.json`](../Experiments/SymbolicDiscovery/BenchmarkSuite1/routing_reconciliation.json).
- Immutable scientific aggregation: [`evaluation_summary.json`](../Experiments/SymbolicDiscovery/BenchmarkSuite1/evaluation_summary.json); immutable raw result: [`result.json`](../Experiments/SymbolicDiscovery/BenchmarkSuite1/result.json).
- Current navigation and exact-head Claude prompt: [GPT handoff](https://drive.google.com/file/d/145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd/view).

## Question and prospective design

Can the internal symbolic-discovery capability persist across fresh realizations, stronger nuisance structures and deliberately inadequate symbolic grammar, with credit assigned for structural reasons?

The sole-file preregistration froze **six cells × four realizations** before any Suite 1 data or score existed. Each realization has 64 training, 48 validation and 64 held-out rows, with independent named input/noise streams; the regime cases deliberately contain paired identical inputs. The suite contains 4,224 rows in total. Four repeats allow consistent (4/4), occasional (1–3/4) and absent (0/4) success to be reported in each cell. They do not calibrate a population error rate.

The generator produced 24 distinct child seeds, coefficients and input-scale-center tuples. Discrete parameter collisions were retained: the four realized regime multipliers were **3, 2.5, 2.5, 3**, although the frozen domain also included 5 and 7. No outcome-driven replacement, sample removal, coefficient refit, threshold change or seed retry occurred.

The reused hypothesis family is a positive dimensionless coefficient times a monomial in at most three feature surfaces, integer exponents bounded in magnitude by two. Dimensional enumeration, dependency expansion, exact equivalence grouping, expanded complexity, training-only coefficient fitting, validation ranking and atomic-input ablations use the unchanged Benchmark 0 observation adapter and existing project primitives. A small forward adapter seals separate adequacy and approximation diagnostics. This is not an external symbolic-regression engine or a general expression search.

## Results

Errors below are **natural-log RMS errors**, not p-values or ordinary percentage-error estimates. Ranges are across the four realized selected candidates in each cell.

| Prespecified cell | Successes | Held-out log-RMSE range | Supported interpretation |
|---|---:|---:|---|
| Clean recoverable law | 4/4 | 1.82e-16–3.27e-16 | True atomic class selected at rank 1 |
| Target leakage | 4/4 | 0.002844–0.003205 | True class rank 1; all five target-dependent routes excluded before scoring |
| Nuisance and aliases | 4/4 | 0.008015–0.009096 | Equivalent true class rank 1; stable after each irrelevant atomic-group removal |
| Regime inconsistency | 4/4 | 0.458145–0.549306 | Pre-reveal abstention; paired contradiction and all-family failure |
| Wrong grammar: fractional power | 4/4 | 0.355903–0.405276 | No adequate integer-monomial candidate; pre-reveal family rejection |
| Wrong grammar: subtle curvature | 4/4 | 0.005329–0.007580 | Useful approximation, no structural recovery, pre-reveal family rejection |

There were **636 eligible candidate-class occurrences** and **1,264 surface occurrences** across the suite. These totals include repeated structures in independent realizations; they are not counts of globally distinct discoveries. All candidates retain `GENERATED/FITTED CANDIDATE`; no physical-law significance is assigned.

The full per-realization [`evaluation/`](../Experiments/SymbolicDiscovery/BenchmarkSuite1/evaluation/) records include every class's validation and held-out errors, both tolerance tests, structural match, nuisance/leakage flags, rank and credit. The corresponding [`selection/`](../Experiments/SymbolicDiscovery/BenchmarkSuite1/selection/) records preserve the complete pre-reveal rankings, coefficients, equivalence surfaces, ablations and runner receipts.

### Leakage and nuisance discrimination

The leakage cell supplied direct, transitive, squared, reconstructive and cancelling target routes. Metadata reachability rejects all five before their values enter the engine payload. The reconstructive feature would recover the target by division by `z`; the squared feature also reconstructs it through a square root, which is an evaluator-only counterfactual outside this candidate grammar. All such temptations receive zero credit. Poison-value fixtures verify exclusion before value access.

The nuisance cell includes independent irrelevant acceleration, a dimensionless near-constant factor below the noise scale, a strongly correlated but noncausal length predictor, and operational aliases. The correlated predictor is observationally close to `x` on training data, independently intervened on in half the validation rows, and independently set throughout held-out data. Its exogenous provenance does not make it target leakage. The engine receives these observations, not oracle nuisance labels.

Every selected nuisance-cell class is algebraically equivalent to the true law, with no irrelevant factor. Each remains selected and stable after removing `n0`, `n1` or `q`, including derived descendants. Four wrong near-constant-factor classes per realization nevertheless pass both broad predictive tolerances. These **16 nuisance-contaminated occurrences** demonstrate that predictive survival does not establish governing structure.

### Wrong grammar: what was recognized

The engine seals two different observations:

1. **Approximation:** does the rank-1 candidate's validation error fall below the broad 0.04 tolerance?
2. **Family adequacy:** does *any* member of the exhaustively enumerated eligible family have validation error within `2 × known log-noise half-width + 1e-9`?

The second criterion uses the same frozen rule in every cell. It is calculated before oracle or held-out access. Every candidate is evaluated with its training-fitted coefficient; the selected candidate cannot be rescued by oracle-guided reranking.

The fractional-power law is `y = k*x*t^(-2)*z^(1/2)`. Independent positive `x,t,z` force the length/time powers, while the required one-half power of `z` is absent from the integer grammar and unavailable through aliases.

The subtle-curvature law is `y = k*x*t^(-2)*z^p*exp(beta*(log z)^2)`, with frozen positive `beta`. Every permitted monomial has log-response affine in `log z`; the true response has nonzero second derivative `2*beta`. It cannot be an exactly equivalent member of this family.

All four curvature cases selected a good approximation under the broad tolerance on validation **and** held-out data, but exceeded their noise-based adequacy bound **0.000200001**. Each sealed `no_stable_law` and `family_inadequate_on_validation`. Together with the nuisance cases, **20 structurally wrong candidate-class occurrences** pass both broad predictive tolerances and receive **zero structural credit**. No wrong class was accepted as a stable selected law.

The engine identifies **finite-data family inadequacy**, not the uniquely correct explanation of that inadequacy. The evaluator's knowledge of the controlled generator establishes that grammar misspecification is the cause in these eight cases. Real data could instead implicate noise assumptions, measurement errors, missing inputs, regime changes or other defects. This distinction is essential.

### False universality

The regime worlds supply the same feature vector twice with target ratio `m`. Any deterministic feature-only predictor has paired log-RMS error at least `log(m)/2`. The selected errors equal this lower bound, and all candidates meet or exceed it within the frozen numerical tolerance. All four pre-reveal decisions abstain. Group labels are diagnostics, never candidate factors; group-specific coefficients are not universal-law recoveries.

## Custody and blindness

| Stage | Immutable identity |
|---|---|
| Accepted merged Benchmark 0 base | `c01ecf876969eb28d6426022a6ddadf61f691a06` |
| Sole-file Suite 1 design freeze | `e8625d29aebf7364b7e647ad7c26f124fa7cdfc2` |
| GitHub draft PR server anchor | `2026-09-14T23:55:15Z` |
| Frozen source and 15 passing preflight fixtures | `dc2532ec55d865177144d780bcf3983c1b65a624` |
| Sole-file seed commitment, published before generation | `e43b18b9b43e91a8b2a171c924cbd83ff98d7ac5` |
| Public inputs and private oracle/held-out hashes | `f79aaa0b43ffc2a3fb225923231587cdb9ac3d05` |
| All sealed selections, before evaluator reveal | `55c2783a20edfa2208094129f3c5efa6cf6247cc` |
| Reveals, raw scientific PASS and post-result operational failure | `d5a6845816f8183902ed68f6060becc1f58d8526` |
| Detached routing-correction source and tests | `4e146e71aa97c2e3d7e18832fc1d7ab3f2b51e0d` |

Each GitHub commit object was created and imported before its dependent execution. The design and seed-commitment stages additionally advanced the public PR branch; generation checked that the remote branch pointed to the seed commitment before invoking the generator. Later commit objects were public before the dependent stage even though the branch advances to the completed head only after local verification. Guards inspect the full reachable commit graph, unique artifact introductions, immutable source/epoch bytes and seed/data/selection commitments. **True merge history is required; never squash or rebase.**

The seed commitment binds the permitted realization set to a publicly committed value before generation. Changing that seed while keeping the commitment is cryptographically excluded; replacing the commitment changes verifiable history. This is stronger than relying on deletable local files. It is not proof against an operator performing unlogged private computations or rewriting external history.

The designer knows the families. The generator creates the private truth and held-out files. The evaluator consumes them only after every selection is committed. The engine sees one anonymous sanitized training/validation payload and public policy; feature schemas or noise bounds can suggest family identity. There is no conceptual-ignorance claim.

The staged worker receives nine exact allowlisted source files, no generator, evaluator, seed, oracle, held-out data or repository history. Its v2 receipt records completed reads, expected missing-cache attempts, denied/unexpected attempts, imports and complete before/after directory inventories. Python remains 3.12 / `cpython-312`. This is trusted-code dataflow separation under one OS identity, **not hostile-code isolation**.

## Preserved operational failure and corrected routing

All raw scientific evaluations, controls, aggregation and `result.json` existed before the frozen `reveal()` failed while constructing the disposition index. The failure record remains at [`operational_failures/reveal-55c2783a20edfa2208094129f3c5efa6cf6247cc.json`](../Experiments/SymbolicDiscovery/BenchmarkSuite1/operational_failures/reveal-55c2783a20edfa2208094129f3c5efa6cf6247cc.json). Its `NO_GO_CAPABILITY` is an operational-stage label, not a failed scientific realization or a replacement for the completed raw PASS.

The detached correction verifies the exact failed boundary, pins all 132 raw-stage JSON files and re-derives the scientific evaluation through the unchanged frozen functions. It does not regenerate worlds, select candidates or fit coefficients when producing the reconciliation. Routing schema v2 explicitly names each source field and digest, distinguishing historical raw results, reconciliations, suite aggregation and operational failure records. A reconciliation's producer-source pin is explicitly distinguished from an artifact-state pin; its actual introduction commit is independently checked by chronology.

The frozen Suite 1 writer and its original routing assumptions remain historical source. Use the **forward authoritative guard** below. This operational correction does not make the old exporter reusable as-is for a future suite.

## Validation and scoped maintenance

The completed-head validation consists of the **20 affected tests** (15 frozen preflight contracts plus five routing-correction tests), one explicit fixed-epoch Suite 1 replay, all-candidate independent arithmetic, full custody checks, live target-free cache probes and `git diff --check`. Exact-head completion evidence belongs to PR #56 and the current handoff.

```sh
python -m unittest tests.test_symbolic_suite tests.test_symbolic_suite_routing -v
python -m Discovery.symbolic_suite_routing --check --replay
git diff --check
```

The replay must reproduce the committed generator outputs and all 24 sealed discovery records byte-for-byte. It is a disclosed check of the same epoch, not new prospective evidence or another seed selection. No local Benchmark 0, unrelated empirical, mutation-family or Lean execution is needed. The existing protected CI jobs remain intact, and their inherited full-repository checks run as the repository gate; the only workflow addition is the new Suite 1 guard.

| Finding | Treatment in this package |
|---|---|
| DM-089 | Forward v2 receipts distinguish actual reads, expected cache misses and denials; stale present caches fail closed; full inventory and module/path probes included. Historical receipt untouched. |
| DM-092 | New generator/evaluator consume frozen policy values; deliberately different tolerance, noise-rule and regime-factor fixtures pass. Historical literals untouched. |
| DM-091 | Triggered by aggregation; schema v2 gives one explicit authoritative route, including the preserved post-result operational failure and corrected disposition. |
| DM-090 | Deferred: supported Python minor version and cache-tag boundary remain unchanged. |
| FH-18 | Pre-generation seed commitment adopted with sole-file ancestry and publication verification. |
| FH-19 | Cheap live semantic probes included in the forward guard; archived Benchmark 0 correction untouched. |

These are implementation statements for independent review, not GPT-issued closure of Claude-owned findings. E-001 and unrelated deferred surfaces are not consumed. No new status ledger, retired workflow-observation footer or external outreach was introduced.

## What this establishes and what it does not

The prespecified joint criteria produced consistent correct recovery and discrimination across these 24 controlled realizations, including two distinct forms of deliberately wrong grammar. This strengthens the accepted single-realization Benchmark 0 baseline. Its four known worlds, raw FAIL and accepted reconciliation remain byte-identical.

It does **not** establish discovery of unknown natural laws, arbitrary physical-data performance, a universal false-positive rate, superiority over external engines, or empirical evidence for any Number Project physical hypothesis. The truth families remain narrow, synthetic, designed and known to the implementer/evaluator; coefficients are positive, feature measurements exact, noise specified, and search exhaustively bounded. Performance outside those conditions remains unmeasured.

Independent Claude review of the exact completed head is the next boundary. Leave PR #56 unmerged for Miguel's authorization. No external-engine comparison or new realization follows automatically.
