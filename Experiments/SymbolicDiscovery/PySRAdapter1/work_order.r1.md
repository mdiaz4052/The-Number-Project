# The Number Project — Current Work Order

**Task:** NP-PYSR-ADAPTER-01  
**Revision:** 1 — prepared 2026-09-17 UTC  
**Title:** First Real-Generator Adapter — Pinned PySR Pilot  
**Destination:** The Number Project Work Mode / repository implementation context  
**Stage:** SPECIFICATION READY — NOT EXECUTED  
**Authorization:** Miguel authorized specification preparation on 2026-09-17. Implement only when he launches this packet in the Number Project execution context. Preparation does not install software, run a search, create a PR, or authorize merge. On launch, only this bounded pilot and its directly implicated prerequisites are selected; other external-engine ideas remain parked.  
**Control intensity:** STANDARD integration work; RIGOROUS at source custody, generator/evaluator separation, mathematical meaning, and evidence promotion.

## 1. Decision, deliverable, and nonclaims

> Can a pinned real PySR run's complete declared retained output cross the Number Project exchange boundary with faithful expressions, constants, units, domains, inventory, raw bindings, and claim limits?

Deliver one executable adapter, a verified native-output export route, a trusted ingestion/evaluation entry point, four bounded live runs, retained evidence, and a focused decision report. Reuse Candidate Exchange 1's accepted primitives and scientific distinctions. Do not build a second exchange platform.

The primary outcome is **adapter conformance**, not search success. Search may return poor predictions, dimensionally inadmissible candidates, or no useful law. Preserve those outcomes. An accurate translation of a poor formula is not a failed translation; an accurately archived failed run is not a working adapter demonstration.

The four live runs use fresh synthetic observations, but they are a small engineering pilot, not an engine comparison, population performance estimate, or physical experiment. Report descriptive training/validation/held-out errors separately from adapter integrity. Do not award structural-recovery, formal-proof, empirical-support, significance, or replication labels in this package. All new scientific promotion axes remain `NOT_ASSESSED`; expressions remain `GENERATED/FITTED CANDIDATE`.

**Critical inference boundary:** a heuristic search's failure to return an adequate candidate is not proof that its whole grammar is inadequate. Do not transfer the earlier exhaustive-family conclusion or the `2ε` rule to this output set. Search coverage is `NOT_ESTABLISHED` even when output inventory is complete.

## 2. Rolling instructions, authority, and launch preflight

Canonical packet: [NUMBER_PROJECT_CURRENT_WORK_ORDER.md](https://drive.google.com/file/d/1bJhHoxjzqIopMgASqmUIO71S1SBZP7ly/view), in the existing Workflow Management folder. Keep the same Drive ID. This packet replaces the completed NP-CANDIDATE-EXCHANGE-01 instructions; that consumed predecessor remains committed under `Experiments/SymbolicDiscovery/CandidateExchange1/work_order.r1.md` at the accepted #58 head.

At launch, read this revision completely and reconcile once: live main/open PRs, current GPT handoff, current Claude role, affected code, and only relevant finding notes. Snapshot the exact consumed bytes and SHA-256, Drive ID, and observed modification/revision metadata before the contract freeze. An already-started matching task resumes through its existing branch; it is not a new experiment. Later rolling-document edits cannot change consumed instructions or frozen epochs.

Preparation verified main `9d59d7e7a9e2f056f73d277282a49387287311ff` and no open PRs. Accepted #58 head is `abe6c20332776740022cff6fee1756373022fc8c`; true-merge parents are `c7229812f4d88c11f958f317b67bb51f7ba0c384` and that audited head. Claude supported `CANDIDATE_EXCHANGE_1_PASS`, MERGE, zero blocking in its bounded scope. Actual merge Verify #329, run `35172864707`, and audited-head Verify #328, run `35145166144`, are retained successful evidence. These are distinct attestations; neither is a new verification run in this preparation. [S1–S3]

If main advanced compatibly, use the actual base while preserving accepted ancestry. Stop for a material conflicting implementation or changed relevant boundary; do not execute against a guessed base. Do not spend a separate audit on reconciling administrative wording.

**Standing handoff instruction:** when Miguel requests status/progress or presents an audit/merge transition, verify relevant authoritative facts and automatically update the existing `gpt_RollingAuditHandoff.md` in place if materially stale. Verify the saved update; report access/write failure precisely. Do not rewrite unchanged content solely to refresh a date. Leave Claude-owned files unchanged until his next substantive audit. Do not request a bookkeeping-only Claude run, duplicate audit row, housekeeping PR, or new status ledger. [S4]

Authority remains subject-specific: Miguel authorizes execution and merge; GitHub controls repository/history; exact-head CI controls performed checks; committed artifacts control result evidence; Claude owns independent dispositions and finding IDs. Apply `WORKFLOW_GOVERNANCE.md` and `STANDARDS_REGISTER.md` at their established scopes. No new whole-standard compliance or stable public API is declared.

## 3. Pinned external target and preparation evidence

Use the following **chosen target**, not an instruction to install whatever is latest:

| Component | Target / evidence requirement |
|---|---|
| PySR | **1.5.10**, upstream `astroautomata/PySR` commit `f51299e6dddc7bd2bfd7f473bfddca7c32d83206` (tag resolved during preparation) |
| SymbolicRegression.jl | **1.11.0**, upstream `astroautomata/SymbolicRegression.jl` commit `61e1b36cf5476fe32cd58920d4666d102e3c821c`; annotated tag object `4ee31dfe90178f0fca5b58d249d813c6db39b3f3` |
| Julia | **1.10.10**; verify the platform-specific official distribution checksum at setup |
| Python | CPython **3.12**, preserving the repository's interpreter boundary; freeze the exact patch version and executable identity at qualified setup |
| Transitive dependencies | Resolve and lock exact Python packages and Julia `Project.toml` / `Manifest.toml`, including DynamicExpressions, JuliaCall/JuliaPkg, NumPy, pandas, and SymPy. Record sources/hashes and platform; no floating resolution after qualification |

The PySR tag's own `juliapkg.json` declares SymbolicRegression `~1.11.0` and a Julia compatibility expression. That is compatibility metadata, not evidence that this exact combined environment runs. The Julia release exists, but **this planning session did not install, execute, or qualify the stack**. Setup and native-export qualification below must establish it. Do not silently substitute a 2.x/alpha engine or another backend. If these pins cannot be qualified within scope, return `NO_GO` with the exact reason. [S5–S7]

Inspected primary source establishes that PySR exposes `equations_`, `julia_state_`, and `julia_options_`; the backend retains a hall of fame with member/existence slots, whereas the formatted frontier is a subset. The pinned expression-spec source demonstrates retrieval of native expressions by complexity. This is a version-specific implementation surface, not a promised stable API. [S8–S10]

The integration design below is newly specified work. In particular, preserving a raw/native representation before adapter simplification, the trusted binding gate, and the failure-aware verifier are requirements, not capabilities inferred from upstream marketing or automatically supplied by PySR.

## 4. Scope and prerequisite strategy

### Preserve accepted history; extend additively

Leave all accepted experiment directories, shared pinned Discovery modules, existing `candidate_exchange*.py`, existing exchange tests, Lean files, and `.github/workflows/verify.yml` byte-identical. Add narrowly named modules/tests under new paths, with the engine dependency optional to ordinary imports. Do not edit the old source snapshot or test inventory to make a new implementation look historical.

Candidate Exchange 1's source checker pins its own source/tests and living `verify.yml`; a naive one-line correction would collide with its own evidence bindings. The preferred path for this pilot is therefore an **additive real-adapter facade and new conformance verifier**, using unchanged accepted arithmetic/validation primitives. CI reaches the new offline guard through a new unittest module, without a workflow edit. [S2, S11–S12]

### DM-099 — mandatory at the new trust boundary

Expose one trusted public path accepting the project manifest, exact raw-export bytes, and run/source binding. It must validate custody and reconstruct the entire normalized output before issuing any integrity-PASS card. Derive each card's binding from that verified reconstruction and bind the result to the exact candidate/manifest/raw digests.

A caller-supplied boolean, forged receipt, or a freely constructible object named `VerifiedBinding` is not verification. Mutation after verification must invalidate the binding. Prefer an immutable internal representation or immediate recomputation before card creation. A lower-level legacy `evidence_card()` call may be used only inside this verified path; it is not the public real-engine API. The new facade must not simply trust its literal PASS field. Prove direct fabrication and cross-candidate token/receipt substitution cannot produce a trusted card. Document any legacy direct-call hazard as remaining outside this new entry point; Claude decides scope-specific closure. [S2]

### DM-098 — mandatory design rule for the new epoch

Do not reuse the historical PASS-only verifier as the new outcome authority. The new verifier must derive/check disposition from frozen criteria and retained evidence, including legitimate adverse outcomes. Validate schemas, chronology, inventory, immutable bindings, failure stages, and the consistency of each reported outcome. An enumerated-label membership test alone is insufficient.

Use separate fields for `evidence_integrity`, `adapter_conformance`, run execution state, and descriptive search diagnostics. A validly retained failed run can pass evidence-integrity checks while adapter conformance is PARTIAL or NO_GO. A demonstrated integrity or translation defect remains FAIL and forbids operational acceptance. Never redefine adapter correctness so an unresolved defect becomes green. [S2]

### DM-097 — not triggered by the preferred layout

Do not edit `verify.yml` or add a new workflow merely for convenience. If an unavoidable dependency makes a workflow change necessary, stop that change and report the bounded incompatibility; propose a separately reviewable forward/pinned-epoch route. Do not weaken or bypass the accepted guard, blanket-skip old tests, update its frozen comparison SHA, or refactor CI. A later explicit scope may repair the living-configuration/frozen-evidence mismatch; this packet does not require it. [S2]

## 5. Data, visibility, and four-run design

### Fresh, deliberately small input family

Use exactly four target datasets: two independent realizations of each of these source-known laws. Inputs `u` and `v` are positive length quantities, represented numerically in metres; `z` is positive and dimensionless; output `y` is a length in metres. Coefficients are dimensionless.

\[
\begin{aligned}
\text{M:}\quad y &= 1.5\,u z + e,\\
\text{A:}\quad y &= 1.25\,u + 0.75\,v z + e,\\
e &\sim \operatorname{Uniform}[-0.001,0.001]\ \mathrm{m}.
\end{aligned}
\]

For each dataset independently, sample numeric `u`, `v`, and `z` independently and uniformly from `[0.5, 2.0]`. Inputs are exact by design; output has the correctly declared known additive noise above. These are invented engineering fixtures, not models fitted to any physical measurement. The additive law broadens formula shape beyond one monomial without creating a large grammar campaign.

Each dataset has **128 training, 64 validation, and 64 held-out rows**: 1,024 rows in total. Separate random streams by dataset, split, input/noise purpose, and engine seed. There is no within-pair matching and no population-rate interpretation. Use anonymous run IDs; preserve evaluator-only law mapping. No historical benchmark rows, selections, oracle files, or fits are reused as target inputs.

### Custody of fresh randomness and outcomes

After source/environment/fixture qualification, generate one new master seed and publish its cryptographic commitment before generating these rows. Freeze a domain-separated deterministic stream derivation (for example SHA-256 over the master plus explicit dataset/split/purpose labels). Pin the RNG implementation and keep all derived engine seeds within the engine's allowed integer range. Check seed uniqueness before data generation; any rare collision follows a predeclared deterministic derivation rule, never outcome inspection.

Commit every dataset's public training/validation payload and hashes of withheld data before any target fit. Engine workers receive **training features and training responses only**, plus the fixed configuration and neutral column mapping. The evaluator keeps validation responses, held-out rows, and law labels outside the worker's staged files. The trusted validator sees provenance metadata before any ineligible feature values. Training responses used for fitting are not themselves prohibited leakage.

After each fit, seal raw retained outputs and native parity observations without modifying them. After all four are sealed, compute validation selection using the trusted evaluator and seal all four choices, including explicit no-selection outcomes. Only then reveal held-out data and evaluate those sealed choices. No held-out-driven refit, candidate replacement, post-selection reranking, or engine rerun.

Report `outcome_blind=false` globally: the designer knows the families, and preflight fixtures are visible. The four realized datasets/output outcomes are new; worker access is stage-limited. Do not claim human conceptual blindness, unknown-law discovery, or protection against malicious code sharing the same machine identity.

## 6. Engine configuration and bounded setup

### Fixed target-run configuration

Use ordinary static real expressions with binary operators **`+`, `-`, `*`, `/`** and no unary operators, templates, guesses, custom loss/operator functions, variable selection, denoising, warm starts, batching, or learned transforms. Use standard squared-error loss. Constants may be generated/optimized from training observations, but their admissible dimensions in the Number Project contract are fixed as dimensionless.

| Setting | Required target value |
|---|---:|
| `niterations` | 60 |
| `populations` | 4 |
| `population_size` | 27 |
| `ncycles_per_iteration` | 100 |
| `max_evals` | 200000 |
| `maxsize` | 15 |
| `maxdepth` | 8 |
| `precision` | 64 |
| `parallelism` | `serial` |
| `deterministic` | `True` |
| `random_state` | distinct committed stream-derived seed for each run |
| `warm_start`, `batching`, `denoise`, `turbo`, `bumper` | `False` |
| `early_stop_condition` | `None` |
| `timeout_in_seconds` | 180 |

Use a separate supervisor hard deadline of **300 seconds per target worker**, with a preferred enforceable memory cap of **6 GiB**. Freeze the enforcement mechanism and report whether memory was actually enforced or only observed. Warm up/import/compile on preflight fixtures before target generation. Engine timeout is a predeclared resource stop, not permission to run longer because a fit looks poor. Preserve exact termination reason and available output; wall-clock truncation limits any determinism claim.

All remaining defaults are those of the pinned stack. Serialize the complete effective Python configuration and relevant backend options before target generation, including resolved simplification/optimization settings. No default may float with a package upgrade. Use isolated per-run output directories; retain native output, logs, and available engine counters. Do not claim unavailable evaluation counts from the configured cap alone. [S8]

**Units:** this initial engine search may operate on the declared coherent-SI numeric columns without engine-side unit penalties (`X_units=None`, `y_units=None`). The independent Number Project evaluator enforces the manifest dimensions; the engine cannot infer dimensionful coefficients to rescue a candidate. This intentionally tests a unit-agnostic proposer behind a unit-aware gate, not PySR's unit-aware-search capability. Never relabel a dimensionally invalid expression as eligible because its predictions are good.

### Setup and qualification, not a tuning campaign

Use one clean local/container environment, retaining Python 3.12 for the repository. Network access is permitted only for the authorized dependency/source setup; prevent target workers from receiving connector credentials, repository-write tokens, or unrelated project files. Prefer network-disabled target execution after setup. Record actual isolation; do not call a working directory alone a security sandbox.

Before target seed creation, permit at most **two tiny real-engine smoke fits**, each at most five iterations, one population, 27 members, and the same operator fragment. They use fixed published engineering rows, not any target realization; they qualify startup, retained-output export, and native numerical evaluation. They do not tune search parameters or establish recovery rates. Directly constructed native expression fixtures may also test operators without a search.

Allow one diagnosed setup/transport retry before target generation, preserving the first failure and unchanged version targets. No paid service, broad dependency migration, or alternate engine is authorized. If package installation, native export, dimension/parameter mapping, or safe execution remains unresolved, close NO_GO before generating target data.

## 7. Native output boundary, translation, and independent parity

### Define what “complete” means before searching

The authoritative exported inventory is **every occupied final native hall-of-fame slot** at worker termination, in native slot/complexity order. Capture the complete existence mask and a count cross-check from the pinned backend, not a count inferred from already filtered Python records. Keep every corresponding raw tree, value, loss, complexity, and available identifier. Capture the ordinary final CSV/frontier and map its entries to native slots; do not replace the native inventory with the smaller displayed frontier or `get_best()` result. [S8–S10]

This is complete **final retained output**, not every transient expression considered during search and not exhaustive grammar coverage. Retain available intermediate files as such, without calling them additional independent runs. Different formulas or duplicate-looking entries must remain individually locatable. A size-limit rejection retains an explicit whole-run status and original archive binding; it must not silently truncate the census.

### Capture actual native structure, not a rewritten display

Within the trusted, pinned engine worker, obtain each native retained expression and export its node structure directly through a small source-pinned walker. Validate the exact node API, child ordering, operator registry, variable indexes, constant types, and hall-of-fame indexing in qualification. Resolve expression wrappers through the backend's supported unwrapping mechanism; do not assume a printed string is the original tree.

Keep raw CSV and equation strings as inert corroborating records, but do not parse `sympy_format` as the authoritative tree, use unrestricted `sympify`/`eval` on candidate output, or rely on a prettified formula's inferred domain. No candidate-specific code or callable crosses into the trusted evaluator. Engine-created pickle/Julia serialization can be retained as opaque evidence if useful, but the evaluator and ordinary CI must not load it. In-process access to the worker's own fresh engine state is distinct from deserializing an externally supplied checkpoint.

The claim begins at the **final native export boundary**. Upstream search may simplify candidates before that boundary; this pilot does not reconstruct deleted search-history restrictions or establish fidelity to every precursor expression. Preserve the final native tree's restrictions during all subsequent normalization.

The pinned real exporter must reject unknown node/operator variants explicitly. An unresolved native-to-row binding is NO_GO for that route, not permission to fall back silently to evaluated strings. Exporter traversal is separately checked against native evaluation so a mistaken operator mapping cannot validate itself.

### Map the supported fragment and constants faithfully

Map native `+` to `add`, `*` to `multiply`, `/` to ordered `divide`, and binary `-` to `add(left, multiply(exact −1, right))`. Preserve original child order and references before canonicalization. Do not reinterpret protected division, absolute-value operators, general powers, custom calls, complex numbers, or unsupported unary nodes as ordinary arithmetic. They are not in this pilot's grammar.

Keep each native Float64 constant's original value with a round-trip representation, including a bit/hex representation in the raw export. Verify decimal/bit agreement before normalization. Do not rationalize fitted decimals, round them for identity, or identify them with physical constants. Distinguish a native numerical constant from the exact −1 introduced by the documented subtraction translation.

Use the accepted parameter roles without allowing the generator to set them. A project-owned deterministic instantiation rule may create a candidate-specific manifest from the fixed run manifest and native constant-leaf positions: one scalar slot per leaf, dimensionless, bound to the run's training input digest and training-exposed generation/fit context. The rule, slot ordering, and source ancestry are frozen before the target runs; the public verifier recomputes the manifest and mapping from raw bytes. Generator-supplied unit, role, fit-context, or manifest overrides are rejected. Do not assert that every native constant was individually optimized when only training-exposed search provenance is known.

If the accepted schema cannot represent that narrow derivation unchanged, use a small explicitly versioned outer adapter envelope with a documented projection into the accepted evaluator. Do not pretend real output is `mock-tree/1`, fabricate historical source metadata, or edit the accepted format registry. Candidate-specific manifest identity must still bind the fixed parent manifest, raw item, and parameter-instantiation rule.

### Native versus independent numerical evaluation

For every occupied retained slot, the worker records native numerical evaluations on the first sixteen training feature rows and these eight fixed feature triples, in the same declared SI conventions:

`(0.5,1,0.5), (1,0.5,1), (2,1,2), (1,2,0.5), (0.75,1.5,1.25), (1.5,0.75,1.75), (2,0.5,1.5), (0.5,2,0.75)`.

Use the native expression's evaluator, not PySR's SymPy-backed prediction export and not the new adapter's own evaluator. A tiny static source-pinned Julia helper is permitted for export/evaluation; this is not permission for custom search operators or candidate-generated executable code.

The independent side evaluates the translated original tree using the accepted Python arithmetic. Compare finite values with **relative tolerance `1e-10`, absolute tolerance `1e-12` in the declared numeric units**. Compare invalid/nonfinite/domain classifications separately. A point outside the expression's original domain is retained as a diagnostic, not converted to zero or dropped to improve parity. Engine numeric failure, Number Project domain rejection, and numerical translation disagreement remain distinct.

Document the denominator and coverage of every parity statistic. Source-derived dimensional rejection can be correct even when native numerical evaluation is finite. Do not demand equality of an engine's unit-agnostic eligibility decision to the project's dimensional gate; the parity test concerns the formula's arithmetic and definedness.

Unknown units, a swapped column map, lost denominator, wrong subtraction order, changed constant bits, or an unbound candidate cannot be excused by a low aggregate loss. The numerical comparison policy is fixed before target output exists. Any post-output diagnosis must retain the original discrepancy and cannot quietly loosen tolerance.

## 8. Trusted gate, output accounting, and descriptive selection

The trusted path validates the fixed manifest and complete registered dependency graph before reading feature values, then binds raw source/run receipts, reconstructs native-to-exchange mappings, instantiates allowed parameter metadata, and issues cards. Preserve target-reachability through transitive, cancelled, and zero-weight edges. Coherent-SI unit declarations are explicit; matching dimensions do not prove a numeric scale. Exact inputs and known additive output noise are declarations of this generator, not calibrated measurement claims.

Record every raw item as retained/evaluable, retained with a semantic rejection, unsupported, or malformed, with its immutable raw locator and a human-readable reason. Run states distinguish setup failure, engine failure, timeout with partial output, no output, exporter failure, completed export, and evaluation failure. Empty output never earns abstention or grammar-rejection credit. Output hashes establish consistency and custody, not that an arbitrary malicious worker is truthful.

Retain ordinary engine scores/losses under source-reported diagnostics. Independently compute new training/validation RMSE only for candidates eligible and finite on every row of the named split. Keep the row denominator fixed; record invalid-row counts and no numeric score rather than dropping rows. No refitting occurs in the adapter.

For each run, choose the eligible candidate with the smallest validation RMSE; break exact ties by native complexity then native slot index. No closeness-based tie band or post-hoc complexity penalty. When none qualifies, seal `NO_ELIGIBLE_SELECTION`. The whole final inventory remains available even when only one candidate is chosen.

After every run's selection is sealed, compute held-out RMSE for the sealed candidate only. Retain its failure without replacing it. These metrics describe four observations of the pinned workflow; they do not produce a comparison, confidence interval, general success rate, or predictive-validation promotion. Neither training nor validation quality is part of the primary adapter PASS threshold.

The engine may see only training data. The adapter may see validation data for this declared selection. The reporting evaluator sees held-out data only after all selection seals. Architecture may share a trusted operator/OS identity, but data arguments and staged files must enforce the declared software access paths, with explicit canary tests and honest access limitations.

## 9. Precommitted conformance cases and mutation coverage

Before generating target data, pass bounded deterministic fixtures through the **new public real-adapter path**, not merely the old tests. Hand-author expected outcomes independently of the translator. Construct native operator fixtures in the engine environment where needed; these are visible engineering controls, not additional live discovery attempts.

| Boundary | Required positive and negative coverage |
|---|---|
| Native traversal and operator mapping | Correct `+`, binary `-`, `*`, `/`, child order, variable indexes, constant leaves, shared-node handling, slot/existence mask; swapped division/subtraction and wrong column order detected |
| Constant fidelity | Approximate Float64 identity survives native export and accepted parameter representation; tampered bit/decimal pair, rounding, boolean, vector, nonfinite value, and false fit-context rejected |
| Mathematical domains | `u/u` retains `u ≠ 0`; division-by-zero stays invalid; zero multiplication cannot erase an invalid subexpression. Use a separate real-domain fixture manifest for zero probes so a positive-input restriction cannot hide the check |
| Dimensions and numeric conventions | Length plus length accepted; length plus time, an impermissibly dimensionful coefficient, a changed SI scale declaration, and an engine-provided unit override rejected. Engine-finite numeric output is not enough |
| Provenance and data visibility | Direct/transitive/cancelled/zero-weight target-derived inputs rejected before values; valid scalar training exposure allowed; validation/held-out canaries cannot enter worker arguments or accessible staged inputs |
| Full inventory | Missing occupied slot, duplicated/laundered ID, wrong census, altered raw row, swapped run/manifest, and frontier-only substitution detected; true repeated items retained |
| DM-099 gate | Fabricated binding, direct candidate-only call, forged verification flag/token, mutation after verification, and cross-candidate substitution cannot issue trusted integrity PASS |
| No evidence escalation | A generator's forged structural/empirical/eligibility claims remain untrusted and cannot set card authority; an empty heuristic output cannot become whole-family inadequacy |
| Safe handling | Unknown version/operator, excessive size/depth, duplicate JSON keys, code-like display text, NaN/Infinity, and overflow produce explicit refusal without executing payload text |
| DM-098 outcomes | Valid PASS and honestly retained PARTIAL/FAIL/NO_GO/UNRESOLVED fixtures are verified according to their evidence; flip a disposition while keeping evidence fixed and verification must fail |
| Frozen history and offline guard | New modules may be added without editing old evidence or CI; old scientific-artifact tampering still fails; the new guard requires no PySR/Julia installation, search, fitting, network, or secret |

Use **eight designated production mutations** in new source, one for each of: native operator/column mapping, original-domain erasure, target-path bypass, dimensional/parameter-role bypass, raw-binding/verification bypass, candidate census loss, evidence-promotion/heuristic-family escalation, and outcome-routing misclassification. Where one named mutation would ambiguously test two mechanisms, select one exact site and cover its companion with a deterministic fixture. Specify sites and intended assertion IDs before target generation.

All eight must be killed by their designated semantic assertions; syntax, import, runtime, unrelated source-pin, and skip failures earn no kill credit. Keep a surviving baseline and one equivalent control. Preserve failed calibration and recalibrate only the diagnosed mutant at unchanged relevant source. Do not rerun unrelated mutation families. A small mutation result file is evidence, not a new standing maintenance register.

## 10. Chronology, immutable attempts, and verification

### Required sequence

1. Reconcile baseline; commit exact consumed packet and launch receipt.
2. Commit a **sole-file contract/acceptance freeze** stating this design, values, tolerances, schemas, source maps, safety boundaries, dispositions, resource limits, retry rules, and negative-control expectations. Then create the draft PR/server timestamp anchor before implementing the new evaluator/exporter.
3. Implement additively and qualify the pinned environment, native export path, fixtures, and mutations. Commit source, tests, exact environment locks, qualified setup receipt, and frozen effective options. Routine forward software corrections before target generation are allowed and recorded; no result-driven scientific change is allowed.
4. Publish the master-seed commitment, then generate and commit all public data plus private hashes. No engine state or candidate output may predate the required source/data commitments.
5. Execute exactly the four target fits. Store run receipts, native census/tree bytes, CSV/frontier, native parity observations, logs and terminal states with exclusive writes. Complete each evidence binding before any dependent selection stage.
6. Seal all raw outputs; compute and seal all validation choices. Reveal held-out rows only after every choice/no-choice is committed. Produce descriptive held-out outcomes without modifying selections.
7. Emit one authoritative package report with explicit outcome axes and exact evidence routes. Bind final source/evidence and CI through the PR/current handoff, avoiding circular self-hashes. Keep a clean committed tree for the inherited test prerequisites.

Use existing chronology/serialization helpers where they fit without modifying frozen source. Do not invent source-access or hostile-code-isolation assertions. Record actual read access, versions, local failures and server anchors. Familiar benchmark families or a precommitted seed are not independently outcome-blind evidence by themselves.

### No scientific rerolls; bounded operational treatment

Once target generation starts, no additional data, replacement seeds, extra search restarts, warm starts, changed operators/budgets/tolerances, or new target fits are authorized. Native restarts inside the pinned engine's predeclared constant optimizer are part of that one run; an operator-triggered new fit is not.

A finished run with unfavorable results is retained unchanged. A target worker failure is retained at that run ID. Remaining independent planned runs may proceed only when the failure is not an unresolved integrity problem affecting them. No target rerun follows automatically.

A failure confined to transport/export/verification may receive **one package-level forward operational correction**, without new search, data generation, fitting, changed native expressions, or altered selection criteria. Use already retained raw bytes or the still-live sealed worker state only if its original native identity can be demonstrated. Keep the original failed source/output/traceback. A separate correction-source pin and route states exactly what was recovered; inability to establish the original output closes PARTIAL/NO_GO rather than reconstructing a desirable result. Reusing a saved untrusted pickle to recover output is prohibited.

Do not delay sealing output while deciding whether a run is attractive. Never delete an initial failure or overwrite a write-once result. A necessary change to frozen requirements requires an explicit later revision, not a discretionary retry within this packet.

### CI verifies evidence, not another stochastic experiment

Add one new test module discovered by existing `unittest discover`; keep `verify.yml`, existing tests, interpreter pins, and inherited guards unchanged. Ordinary CI must not install PySR/Julia or launch live searches. It verifies raw hashes, source/environment/configuration/data/selection chronology, native census correspondence, deterministic translation and numerical evaluation, valid failure routes, and derivation of the reported disposition. Recompute expected records from sealed inputs; never overwrite expected evidence.

Native numerical outputs are **source-bound external-engine receipts**. CI may check them against the independent evaluator but must not claim it reran Julia. The live-run integration evidence and the offline verifier's coverage remain separately identified. Exact bitwise native rerun reproducibility across hardware is not claimed.

Keep result-driving source pins epoch-specific; do not newly classify living repository configuration as immutable scientific data. Do not build a generalized historical replay framework unless a concrete conflict requires it and fits the authorized scope. Preserve all accepted #54/#56/#57/#58 source/evidence bindings and rely on their existing guard coverage.

Perform focused affected-boundary tests and new mutation calibration once at the completed epoch. Preserve the repository's normal complete Python and Lean CI jobs. Do not manually repeat unrelated green suites or historical campaigns; run a clean-tree full suite locally only if a concrete integration uncertainty makes it necessary, with the reason recorded. Reuse exact-head results where code, inputs and semantics are unchanged.

## 11. Dispositions and exit semantics

Use one authoritative report route, for example `Experiments/SymbolicDiscovery/PySRAdapter1/result.json`. Choose its exact schema and path before source freeze; distinct raw/export/selection/correction records are not competing dispositions.

`PYSR_ADAPTER_1_PASS` requires all of the following:

- the declared version/environment/source chain was qualified and preserved;
- all four planned target runs reached normal or predeclared engine-budget termination with complete nonempty native retained output and no unresolved output loss; a supervisor-killed or unexportable run cannot satisfy PASS;
- every occupied slot is accounted for, every supported expression is translated without loss, and every required native/independent numerical comparison is consistent, with explicit domain and unit rejection where appropriate;
- at least one actual nonconstant, dimensionally admissible expression is evaluated from **each law family**, and the combined actual output exercises at least one arithmetic operator; a mock or hand-written formula cannot satisfy this real-output requirement;
- all required fixtures, eight assertion-calibrated mutation kills, and both controls pass;
- all selection/no-selection and held-out routes are retained with no prohibited access, re-fit, reroll, evidence promotion, or historical alteration;
- exact-head integrity verification supports the report and the required repository CI gates pass.

There is **no required hidden-law recovery count or prediction-error cutoff** in this primary PASS definition. Conversely, lawful rejection of every item can show a safe gate but cannot satisfy the real-adapter demonstration requirement. Lack of arithmetic/nonconstant coverage is PARTIAL, not permission to rerun the search.

Use `PYSR_ADAPTER_1_PARTIAL` for a demonstrated safe subset with missing live-run/noncritical coverage; `PYSR_ADAPTER_1_FAIL` for a demonstrated invariant/translation/integrity violation; `PYSR_ADAPTER_1_NO_GO` for a failed prerequisite preventing a credible live demonstration; `PYSR_ADAPTER_1_UNRESOLVED` for irreducible ambiguity at the declared stopping boundary. Preserve the most consequential adverse axis instead of hiding it under a favorable summary. Freeze precedence and explicit stage-specific reasons in the contract.

**Verifier semantics:** an offline evidence check succeeds when it establishes that an immutable PASS or adverse report is truthful, complete for its declared stage, and consistent with the contract. It fails on corruption, missing required bindings, altered criteria, or an outcome label unsupported by evidence. Report adapter acceptance separately: an honestly retained FAIL does not authorize deployment or a compatibility claim. Unit tests must demonstrate both truthful adverse reports and forged adverse/PASS reports.

Until substantive independent review, every new trust-boundary claim is **PROVISIONAL — INDEPENDENT AUDIT PENDING**. A passing CI job is not independent scientific review and not a statement of arbitrary-engine safety.

## 12. Deliverables and completion report

Deliver one coherent unmerged PR rather than a maintenance PR followed by a separate pilot. Suggested additive layout (names may be consolidated before freeze):

- a small optional-dependency engine worker/native exporter and new real-adapter facade;
- a new offline conformance/route verifier and focused test module;
- one `PySRAdapter1/` directory containing the consumed packet, frozen contract, qualified dependency/source bindings, data/seed commitments, four run records, raw retained output, selections, failure/correction evidence if any, and one authoritative result;
- `Notes/PySRAdapter1.md`, with exact usage, bounded result, nonclaims, correct reproduction levels, and the focused Claude prompt.

Use source references instead of copying large dependencies or old datasets. No general plug-in framework, UI, CAS, unit-conversion engine, uncertainty-propagation system, container-distribution project, or stable external API. Record third-party package identities and source/license notices needed for this new dependency boundary, without changing the repository license or claiming full SPDX/SLSA compliance.

The decision report must distinguish: setup qualification; actual four-run terminal states; native output inventory; adapter parity; dimensional/domain/provenance rejections; validation/held-out diagnostics; scientific evidence remaining NOT_ASSESSED; retained failures; and exactly what was independently verified versus reused or source-attributed. State that the output inventory is not grammar completeness. Do not report selected-case discovery percentages as a general performance rate.

Update the existing GPT rolling handoff with the actual completed head, exact-head CI, all pending limitations, authoritative result route and one next substantive audit prompt. Leave Claude's files untouched. After review and Miguel's true merge, later status requests automatically reconcile GPT navigation without a separate audit.

## 13. Findings and independent-review focus

DM-099 is directly implicated: assess the new verified public entry point, raw reconstruction, parameter instantiation and resistance to forged verification. DM-098 governs the new outcome path: assess whether adverse evidence remains verifiable without declaring a defective adapter accepted. DM-097 stays deferred if no CI edit occurs. The additive facade does not silently close those IDs or rewrite their historical surfaces. [S2]

Keep DM-090's CPython boundary; this internal pinned pilot is not a public reproduction/release package. Keep DM-093's estimated-noise/broader-detection limit; neither the old rule nor whole-family rejection is used. Preserve DM-094's base-monomial/missed-curvature explanation and DM-095's correct historical pointer if referenced, without recomputation. DM-096 remains Claude-narrowed, not GPT-closed; the successful #58 merge run is factual context. FH-22 does not justify more old-corpus imports. E-001 remains unrelated and live at its own HUST/AAF boundary.

**Focused Claude prompt for the eventual implementation:**

> Review NP-PYSR-ADAPTER-01 at its final exact PR head, using this consumed work order, frozen contract, accepted #58 interface, relevant current findings, and actual CI. Challenge the real PySR/backend/Julia identity; native retained-slot census versus formatted frontier; source-pinned tree/constant export; raw/native/normalized correspondence; feature order and original domains; unit-agnostic proposing versus trusted dimensional rejection; fitted-scalar provenance and deterministic manifest derivation; non-bypassable DM-099 entry point; run/output/selection/reveal chronology; fixed resource limits and no target rerolls; honest failures and evidence-versus-adapter exit semantics under DM-098; preservation of old pins without CI freeze expansion; and absence of whole-grammar, exact-recovery, or real-physics claims. Test concrete unresolved risks rather than repeating unrelated green CI. Treat native engine receipts and independent Python checks as different evidence. Return exact-head MERGE / DO NOT MERGE with scope-specific BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING. Claude retains finding ownership; Miguel retains merge authority. Do not re-audit #58 or update old files solely for bookkeeping.

**Create a merge commit only. Never squash or rebase away accepted ancestry or the new freeze/evidence chain.** No automatic merge, release, tagging, outreach, empirical-G work, external Lean execution, multi-engine comparison, estimated-noise study, or speculative-physics activation follows from this package.

## 14. Source map and preparation limits

These references distinguish inherited facts and upstream interfaces from the new design requirements above. Private navigation can be stale; use current roles and exact repository pins at execution. No old benchmark, new engine, or scientific experiment was run to prepare this packet.

- **S1 — accepted repository state:** [#58](https://github.com/mdiaz4052/The-Number-Project/pull/58), [merged head](https://github.com/mdiaz4052/The-Number-Project/commit/9d59d7e7a9e2f056f73d277282a49387287311ff), [Verify #329](https://github.com/mdiaz4052/The-Number-Project/actions/runs/35172864707). Main/open-PR metadata rechecked 2026-09-17; unchanged-head audit/CI evidence reused.
- **S2 — independent findings:** [DM-097–099 / FH-22](https://drive.google.com/file/d/1k8Pg5CmpzsRsfnL-JdyMysD9FSvergOn/view); [current Claude role observed](https://drive.google.com/file/d/1r3-FRMF68tcM_FTtadM-6M7mByw8kI3m/view). No findings closed by this specification.
- **S3 — accepted internal contract:** [CandidateExchange1 report](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Notes/CandidateExchange1.md), [interface](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Experiments/SymbolicDiscovery/CandidateExchange1/interface.md).
- **S4 — current GPT handoff:** [gpt_RollingAuditHandoff.md](https://drive.google.com/file/d/145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd/view); prior completed work order's section 12 supplies the separately selected real-adapter direction.
- **S5 — PySR identity/compatibility:** [resolved v1.5.10 tag](https://github.com/astroautomata/PySR/tree/f51299e6dddc7bd2bfd7f473bfddca7c32d83206), [pinned juliapkg.json](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pysr/juliapkg.json), [pyproject.toml](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pyproject.toml).
- **S6 — backend identity:** [SymbolicRegression.jl v1.11.0 commit](https://github.com/astroautomata/SymbolicRegression.jl/commit/61e1b36cf5476fe32cd58920d4666d102e3c821c). Tag resolves to this commit; signature/trust is not inferred merely from a hash.
- **S7 — Julia release:** [official Julia 1.10.10 release announcement](https://discourse.julialang.org/t/julia-v1-10-10-has-been-released/130351). Platform binary and checksum still require setup verification; no claim this is the latest release.
- **S8 — pinned PySR API source:** [sr.py](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pysr/sr.py), especially configuration, `julia_state_`, `julia_options_`, `_run`, `get_hof`, and `predict`. Dev/2.x documentation is not the contract for this pin.
- **S9 — native expression access:** [expression_specs.py](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pysr/expression_specs.py), especially `_search_output_to_callable_expressions`. Exact node APIs and the resolved DynamicExpressions dependency require qualification; source inspection is not a successful smoke test.
- **S10 — output census:** [HallOfFame.jl](https://github.com/astroautomata/SymbolicRegression.jl/blob/61e1b36cf5476fe32cd58920d4666d102e3c821c/src/HallOfFame.jl), occupied members/existence mask versus `calculate_pareto_frontier`.
- **S11 — accepted raw-binding caller:** [candidate_exchange_adapters.py](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Discovery/candidate_exchange_adapters.py), `verify_records`, `evaluate_records`, `verify_cards`.
- **S12 — historical source/self/test pins:** [candidate_exchange_conformance.py](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Discovery/candidate_exchange_conformance.py), `SOURCE_PATHS`, `source_check`, and `check`.

**End condition:** one bounded real-adapter decision and a resumable handoff. A useful result may be PASS, PARTIAL, FAIL, NO_GO or UNRESOLVED; no follow-on is automatically activated.
