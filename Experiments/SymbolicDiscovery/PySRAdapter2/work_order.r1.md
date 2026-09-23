# The Number Project — Current Work Order

**Task:** NP-PYSR-ADAPTER-02
**Revision:** 1 — prepared 2026-09-19 UTC
**Title:** Environment-First PySR Integration — Complete the Real-Generator Connection
**Destination:** The Number Project Work Mode / repository implementation context
**Stage:** SPECIFICATION READY — AWAITING EXECUTION AUTHORIZATION
**Authorization:** Miguel selected option 1 for specification development on 2026-09-19. This preparation does not launch implementation, install software, run experiments, open a PR, or authorize merge. A subsequent instruction to execute this exact task/revision activates only the bounded work below.
**Control intensity:** STANDARD integration; RIGOROUS at source custody, mathematical meaning, data separation, and evidence promotion.

## 0. Executive brief and change from the previous attempt

Build one working path:

```text
qualified Julia/Python environment
  → actual PySR search
  → complete final retained native expressions
  → verified translation and provenance
  → existing Number Project evaluator
  → bounded conformance report and independent audit
```

PR #59 ended NP-PYSR-ADAPTER-01 with `PYSR_ADAPTER_1_NO_GO`: Julia 1.10.10 crashed with SIGBUS during its library-location probe, before any smoke fit, target fit, seed, or target data. Its failure cause remains unknown. Its historical result and diagnostics are immutable. This is **a new package and new verification epoch**, not a continuation of its exhausted retry budget. [S13]

The unchanged objective is a real connection, not another mock adapter. The material implementation changes are:

- qualify the standalone native Julia runtime **before importing PySR or asking JuliaPkg to resolve the backend**;
- separately qualify the Python-to-Julia bridge, dependency lock, native exporter and up to two small engineering smoke fits;
- use explicit executable/project selection, architecture checks, clean local storage and complete file-captured diagnostics; permit only the bounded recovery in §6;
- keep runtime qualification and integration qualification separate from the four prospective target runs; no target seed or dataset exists before both gates pass;
- accommodate the accepted evaluator's 32-point card limit through bounded batches, without altering old code or losing rows;
- place explicit upload-and-readback instructions inside Claude's eventual audit prompt.

**Retained scope:** one PySR/backend version pair; four small live runs on two simple synthetic laws; eight targeted semantic mutations; one unmerged PR. No extra engine, noise-estimation study, experiment-design study, empirical-gravity work, broad cleanup or public release. Failure-aware closure remains legitimate, but a safely archived failure is never a working-adapter PASS.

The task is decision-complete when evidence supports PASS, PARTIAL, FAIL, NO_GO or UNRESOLVED and the handoff identifies exactly what ran. Gate-to-gate progress within this authorized package does not require another human approval, extra PR, or interim Claude audit.

## 1. Decision, deliverable, and nonclaims

> Can a pinned real PySR run's complete declared retained output cross the Number Project exchange boundary with faithful expressions, constants, units, domains, inventory, raw bindings, and claim limits?

Deliver one executable adapter, a verified native-output export route, a trusted ingestion/evaluation entry point, four bounded live runs, retained evidence, and a focused decision report. Reuse Candidate Exchange 1's accepted primitives and scientific distinctions. Do not build a second exchange platform.

The primary outcome is **adapter conformance**, not search success. Search may return poor predictions, dimensionally inadmissible candidates, or no useful law. Preserve those outcomes. An accurate translation of a poor formula is not a failed translation; an accurately archived failed run is not a working adapter demonstration.

The four live runs use fresh synthetic observations, but they are a small engineering pilot, not an engine comparison, population performance estimate, or physical experiment. Report descriptive training/validation/held-out errors separately from adapter integrity. Do not award structural-recovery, formal-proof, empirical-support, significance, or replication labels in this package. All new scientific promotion axes remain `NOT_ASSESSED`; expressions remain `GENERATED/FITTED CANDIDATE`.

**Critical inference boundary:** a heuristic search's failure to return an adequate candidate is not proof that its whole grammar is inadequate. Do not transfer the earlier exhaustive-family conclusion or the `2ε` rule to this output set. Search coverage is `NOT_ESTABLISHED` even when output inventory is complete.

## 2. Rolling instructions, authority, and launch preflight

Canonical packet: [NUMBER_PROJECT_CURRENT_WORK_ORDER.md](https://drive.google.com/file/d/1bJhHoxjzqIopMgASqmUIO71S1SBZP7ly/view), in the existing Workflow Management folder. Keep the same Drive ID. This packet replaces the terminal NP-PYSR-ADAPTER-01 rolling instructions. That exact consumed predecessor remains at `Experiments/SymbolicDiscovery/PySRAdapter1/work_order.r1.md` in merged main, 48,337 bytes, SHA-256 `938d7c884cc2b6add3dae4775de8159b387d2addd7fd5654f4cd50eff3670583`. Do not amend or relabel that old epoch. The current Drive file is the preparation master until execution snapshots this revision into the repository.

At launch, read this revision completely and reconcile once: live main/open PRs, current GPT handoff, current Claude role, affected code, and only relevant finding notes. Snapshot the exact consumed bytes and SHA-256, Drive ID, and observed modification/revision metadata before the contract freeze. An already-started matching task resumes through its existing branch and recorded stage; it is not a new experiment. Use branch `feature/np-pysr-adapter-02`; reuse it if it belongs to this exact package rather than creating a duplicate. Merely fetching this specification does not constitute activation. Later rolling-document edits cannot change consumed instructions or frozen epochs.

Preparation rechecked main `79b56e0db86605e569c6d8a68a59315a00ab0177`, the true merge of #59. Its parents are `9d59d7e7a9e2f056f73d277282a49387287311ff` and `0a598b8ab473a202e9ff15efb9f42428af29eceb`. The earlier September 19 status review verified PR-head Verify #331 (`35236112374`) and merge-head Verify #332 (`35415276376`) as successful. Those exact-head attestations are reused, not rerun here. Accepted #58's independently audited head remains `abe6c20332776740022cff6fee1756373022fc8c`, with MERGE / zero blocking for its limited internal contract. [S1–S4, S13]

The latest retrieved Claude record ends at #58; #59's separate independent verdict was not located in the prior reconciliation. Do not infer that no audit occurred or that a merge proves an audit. At launch, consult the current Claude role and any newly supplied #59 report once. Absent a newly applicable blocker, proceed from the merged code while treating #59 only as a preserved setup archive, not an independently accepted adapter. The new package must stand on its own verification and independent audit. Do not impose a bookkeeping-only re-audit or repeated source hunt as a prerequisite.

If main advanced compatibly, use the actual base while preserving accepted ancestry. Confirm that the #59 result and setup directory and #58 interface bytes are unchanged. Check live open PRs for overlap. Snapshot the actual base and its CI state; a retained PR-head success is not a substitute for unknown merge-head CI. Stop for a material conflicting implementation or changed relevant boundary; do not execute against a guessed base. Do not spend a separate audit on reconciling administrative wording.

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

The PySR tag's own `juliapkg.json` declares SymbolicRegression `~1.11.0` and a Julia compatibility expression. That is compatibility metadata, not evidence that this exact combined environment runs. The Julia release exists, but **this planning session did not install, execute, or qualify the stack**. Retaining these versions isolates environment/integration changes from an engine upgrade; it is not a recommendation that they are the latest maintained releases. Ordinary compatibility metadata does not explain or fix #59's SIGBUS. Setup and native-export qualification below must establish it. Do not silently substitute a 2.x/alpha engine or another backend. If these pins cannot be qualified within scope, return `NO_GO` with the exact reason. [S5–S7]

The predecessor's pinned source review records that PySR exposes `equations_`, `julia_state_`, and `julia_options_`; the backend retains a hall of fame with member/existence slots, whereas the formatted frontier is a subset. Its cited expression-spec source records retrieval of native expressions by complexity. Reconfirm these exact APIs against the installed locked sources during qualification. This is a version-specific implementation surface, not a promised stable API. [S8–S10]

The integration contract below retains the predecessor's unexecuted design where unchanged and adds the environment-first and delivery controls in §0. The actual Candidate Exchange source was inspected again during this preparation; its limits and legacy card precondition govern the new wrapper. In particular, preserving a raw/native representation before adapter simplification, the trusted binding gate, and the failure-aware verifier are requirements, not capabilities inferred from upstream marketing or automatically supplied by PySR.

## 4. Scope and prerequisite strategy

### Preserve accepted history; extend additively

Leave all existing repository files byte-identical: accepted and historical experiment directories (including `PySRAdapter1/`), shared pinned Discovery modules, existing `candidate_exchange*.py`, existing tests, Lean files, toolchain/dependency files, and `.github/workflows/verify.yml`. Place new package source, configuration, tests and evidence only at new paths. New package-local optional dependency locks do not change the repository's root environment. Add narrowly named modules/tests under new paths, with the engine dependency optional to ordinary imports. Do not edit the old source snapshot or test inventory to make a new implementation look historical.

Candidate Exchange 1's source checker pins its own source/tests and living `verify.yml`; a naive one-line correction would collide with its own evidence bindings. The preferred path for this pilot is therefore an **additive real-adapter facade and new conformance verifier**, using unchanged accepted arithmetic/validation primitives. CI reaches the new offline guard through a new unittest module, without a workflow edit. [S2, S11–S12]

### DM-099 — mandatory at the new trust boundary

Expose one trusted public path, proposed as `verify_and_evaluate_run`, accepting the project manifest, exact raw-export bytes, controller-held run/source binding, and named evaluation inputs. The expected binding is read from a project-controlled sealed run record, not a second user-supplied digest next to the same untrusted bytes. A cryptographic hash alone establishes consistency, not origin or truthful native execution. It must validate custody and reconstruct the entire normalized output before issuing any integrity-PASS card. Derive each card's binding from that verified reconstruction and bind the result to the exact candidate/manifest/raw digests.

A caller-supplied boolean, forged receipt, or a freely constructible object named `VerifiedBinding` is not verification. Mutation after verification must invalidate the binding. Prefer an immutable internal representation or immediate recomputation before card creation. A lower-level legacy `evidence_card()` call may be used only inside this verified path; it is not the public real-engine API. The new facade must not simply trust its literal PASS field. Prove direct fabrication and cross-candidate token/receipt substitution cannot produce a trusted card. Document the unchanged legacy direct-call hazard as remaining outside this new entry point; Claude decides scope-specific closure. A card is authoritative for this package only inside its new verified envelope, checked through this public path. An independently submitted legacy card with `integrity: PASS` is not an accepted envelope. Do not claim every Python caller is prevented from invoking old code or that arbitrary same-process code is a security boundary. [S2]

### DM-098 — mandatory design rule for the new epoch

Do not reuse the historical PASS-only verifier as the new outcome authority. The new verifier must derive/check disposition from frozen criteria and retained evidence, including legitimate adverse outcomes. Validate schemas, chronology, inventory, immutable bindings, failure stages, and the consistency of each reported outcome. An enumerated-label membership test alone is insufficient.

Use separate fields for `evidence_integrity`, `adapter_conformance`, run execution state, and descriptive search diagnostics. A validly retained failed run can pass evidence-integrity checks while adapter conformance is PARTIAL or NO_GO. A demonstrated integrity or translation defect remains FAIL and forbids operational acceptance. Never redefine adapter correctness so an unresolved defect becomes green. [S2]

### DM-097 — not triggered by the preferred layout

Do not edit `verify.yml` or add a new workflow merely for convenience. If an unavoidable dependency makes a workflow change necessary, stop that change and report the bounded incompatibility; propose a separately reviewable forward/pinned-epoch route. Do not weaken or bypass the accepted guard, blanket-skip old tests, update its frozen comparison SHA, or refactor CI. A later explicit scope may repair the living-configuration/frozen-evidence mismatch; this packet does not require it. [S2]

## 5. Data, visibility, and four-run design

### Fresh, deliberately small input family

Use exactly four target datasets (run order r01=M1, r02=A1, r03=M2, r04=A2, with this law map restricted to the evaluator): two independent realizations of each of these source-known laws. Inputs `u` and `v` are positive length quantities, represented numerically in metres; `z` is positive and dimensionless; output `y` is a length in metres. Coefficients are dimensionless.

\[
\begin{aligned}
\text{M:}\quad y &= 1.5\,u z + e,\\
\text{A:}\quad y &= 1.25\,u + 0.75\,v z + e,\\
e &\sim \operatorname{Uniform}[-0.001,0.001]\ \mathrm{m}.
\end{aligned}
\]

For each dataset independently, sample numeric `u`, `v`, and `z` independently and uniformly from `[0.5, 2.0]`. Inputs are exact by design; output has the correctly declared known additive noise above. These are invented engineering fixtures, not models fitted to any physical measurement. The additive law broadens formula shape beyond one monomial without creating a large grammar campaign.

Each dataset has **128 training, 64 validation, and 64 held-out rows**: 1,024 rows in total. Separate random streams by dataset, split, input/noise purpose, and engine seed. There is no within-pair matching and no population-rate interpretation. Each target run invokes `.fit()` exactly once; returned empty output and crash records count as executed attempts, never as unused slots. Use anonymous run IDs; preserve evaluator-only law mapping. No historical benchmark rows, selections, oracle files, or fits are reused as target inputs.

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

### Gate R — qualify runtime before the scientific pilot

This gate is newly specified. Freeze its recipe and retry limits in `contract.v1.md`, publish the draft-PR anchor, then commit the setup runner/logger before executing the new diagnostics. Host metadata may be inspected for planning; new setup/program-output evidence must follow this chronology. Forward source fixes before target data are permitted only with retained old receipts and a new source pin before affected execution.

**Environment selection.** Use a task-owned clean directory and venv in the authorized implementation environment. Match the Julia binary to the actual OS, libc and process architecture; record hardware architecture and any virtualization/emulation separately. Use native Linux glibc x86_64/aarch64 or native macOS x86_64/aarch64. Do not install an x86 binary on ARM through implicit emulation. A container is acceptable only if already available, isolated and pinned by image digest; introducing paid infrastructure, a new service/account, privileged containers, a new workflow, or remote access to Miguel's computer is not authorized.

**Worker access and isolation.** The trusted controller may use the authorized GitHub/Drive connections to retrieve and publish this package. Dependency-installation children, Julia/PySR smoke workers and target workers must not receive connector credentials, repository-write tokens, unrelated personal/project files or the controller's authenticated environment. Use an allowlisted environment and explicitly staged inputs; record actual file permissions, worker identity and isolation mechanisms. Network access by these children is permitted only for authorized dependency/source setup. After setup, use offline dependency mode and prefer enforceable network-disabled smoke/target execution; if an OS network restriction is unavailable, disclose that limit rather than claiming a network sandbox. A working directory alone is not a security sandbox. If credential separation or required staged-data access restrictions cannot be established, stop before external execution. Do not grant new permissions, disable security controls or claim protection against malicious same-identity code merely because normal software paths are restricted.

Use an ordinary task-owned writable local filesystem, not a guessed shared-memory location. Record free space, mount/storage type when observable, process limits, environment variables relevant to dynamic loading and the supervisor's resource controls. Treat low space, incompatible architecture and unavailable isolation as detected prerequisites, not as diagnoses of the historical SIGBUS. Do not disable host security controls or change global shell startup files.

**Official binary and extraction.** Obtain the exact Julia 1.10.10 official archive for that platform over the official HTTPS path and check its SHA-256 against the publisher's recorded value. Retain the source URL and downloaded-byte digest. For the allowed tar archives, the preparation-time references are:

| Platform | Official archive SHA-256 |
|---|---|
| Linux glibc x86_64 | `6a78a03a71c7ab792e8673dc5cedb918e037f081ceb58b50971dfb7c64c5bf81` |
| Linux glibc aarch64 | `a4b157ed68da10471ea86acc05a0ab61c1a6931ee592a9b236be227d72da50ff` |
| macOS x86_64 | `942b0d4accc9704861c7781558829b1d521df21226ad97bd01e1e43b1518d3e6` |
| macOS aarch64 | `52d3f82c50d9402e42298b52edc3d36e0f73e59f81fc8609d22fa094fbad18be` |

These are platform-dependent binary pins, not four allowed version experiments. Recheck official metadata at execution; a discrepancy stops that download rather than changing the expected digest silently. A checksum is not proof of a trusted digital signature; follow current publisher key guidance before claiming signature verification. [S7, S15]

Extract into a new task-owned directory without restoring archive owners (`--no-same-owner` with a compatible tar, or its validated equivalent). Check archive members for path traversal and escaping links, preserve legitimate internal links, verify extraction completion and the expected executable. The already-known ownership fix is part of the first recipe; do not deliberately repeat the earlier ownership failure to spend a retry. Never overwrite the historical installation/evidence directory.

**Layered startup tests.** Run in this order, retaining full stdout/stderr, exact arguments, allowlisted environment, executable/source hashes, timestamps, exit/signal and timeout records. Open log files before starting the child; terminal-tool previews are not evidence storage. Do not dump credentials or the entire process environment.

1. **Standalone Julia:** with the exact executable, `--startup-file=no --history-file=no`, print `VERSION`, platform identity and a trivial arithmetic result. Then run `using Libdl; println(Libdl.dlpath("libjulia"))`. Require version 1.10.10, zero exits and a real loadable library path; separately preserve a failing command or signal. These tests involve no PySR, network resolution or target observations.
2. **Python child launch:** run the same library probe from a clean CPython 3.12 subprocess using that exact absolute Julia path. Record the observed Python patch/executable. This separates native launch from Python-parent/environment effects; it does not by itself prove a crash cause.
3. **Pinned backend and bridge:** install PySR 1.5.10 into the task venv and resolve its compatible Python dependencies once. Explicitly require backend SymbolicRegression.jl **1.11.0**, not merely any `~1.11` version. Use a task-local Julia depot/project and explicit executable selection, preventing an implicit replacement Julia download. Pin installed PySR/backend sources to the declared upstream identities and lock the full dependency result. Record Python wheels/source artifacts, package versions, Julia registry/source tree identities, `Project.toml`, `Manifest.toml`, JuliaCall/PythonCall compatibility, DynamicExpressions, NumPy, pandas and SymPy.
4. **Cold bridge confirmation:** in a new process under the exact proposed target-worker identity/environment, import the installed bridge and PySR, exercise trivial Julia arithmetic, inspect loaded Julia/backend/PythonCall versions and paths, and confirm that the source/dependency lock is unchanged. Offline dependency mode is required after resolution; it does not replace an OS network restriction. No fit has occurred yet.

Current JuliaPkg documentation exposes `PYTHON_JULIAPKG_EXE`, `PYTHON_JULIAPKG_PROJECT` and offline mode. The preferred route uses the selected executable with a task-local project and resolved lock. Current JuliaCall also permits an explicitly prepared environment via **both** `PYTHON_JULIACALL_EXE` and `PYTHON_JULIACALL_PROJECT`, with matching JuliaCall/PythonCall versions. Verify the installed versions' source support before using either route, choose and record one before its first bridge import, and do not mix incompatible overrides. The prepared-environment route is permitted only as the documented recovery below, not a way to skip dependency checks. An explicit path is not a remedy for an independently crashing Julia binary. [S14]

**Operational recovery budget.** Permit at most **two setup epochs total** in this new package: one primary epoch and one diagnosed recovery epoch, both before any target seed/data. Each has a maximum **1,200 seconds total setup/diagnostic child execution**, with a **120-second deadline per standalone/minimal probe** and **600 seconds per dependency resolution or cold import** (the epoch total still controls). Record termination and kill remaining child processes at deadlines. The two successful standalone probes and the required Python/cold-bridge confirmations are planned coverage, not retries. Do not repeat a failed stage with an unchanged recipe.

A recovery must retain the first failure and pre-record the concrete changed condition: a demonstrable incomplete extraction/storage fault; a diagnosed loader/path/environment contamination; a source-supported bridge configuration conflict; or moving the same pinned recipe out of an identified restricted/emulated context to **one already available, authorized native isolated environment**. Select the first justified remedy in that order; do not try all alternatives. The host/container identity, changed variables, archive hashes and rationale must be recorded before the recovery command. If there is no supported remedy or accessible environment, stop NO_GO instead of speculative flag sweeps, repeated installs or telling Miguel to provision infrastructure. A successful recovery establishes a functioning recipe, not necessarily the root cause of #59.

Version upgrades, backend switches, source builds, CPU/JIT/security flag sweeps and a third setup epoch are excluded. Automatic package-manager retries inside one logged invocation do not create new operator epochs, but the total deadline and complete logs still apply. An operator-initiated repeat does count. Do not reset the budget on resuming the task.

`RUNTIME_QUALIFIED` requires all four layers on one consistent final environment. A stopped setup emits a stage-complete NO_GO or UNRESOLVED archive and records all later activities as NOT_EXECUTED. Do not implement a large unused adapter after a terminal runtime failure merely to fill the planned file list.

### Gate I — qualify the actual integration before target data

After Gate R, implement the native exporter and new trusted entry point additively. Bind the test fixture definitions, software sources and expected outcomes before running their qualifications. Use directly constructed native arithmetic fixtures plus at most **two tiny live PySR smoke fits total for the package**, not two per setup epoch. Each fit has at most five iterations, one population, 27 members, 20 cycles per iteration, maxsize 7, maxdepth 5, max_evals 5,000, serial Float64 execution and no unary operators. Use the target binary-operator fragment and all its no-transform/no-warm-start restrictions. Allow 120 seconds engine budget plus a 300-second supervisor deadline per smoke fit. A failed smoke fit consumes its slot; no replacement seed or extra fit.

Use these visible engineering inputs, never a prospective target realization: for `i = 0,...,15`, set `u = 0.5 + i/10`, `v = 0.5 + ((5*i) mod 16)/10`, `z = 0.5 + ((7*i) mod 16)/10`. Smoke A uses `y = 1.5*u*z` and seed 101; smoke B uses `y = 1.25*u + 0.75*v*z` and seed 202. All are exact fixture declarations in the same SI/dimension conventions as §5; both smoke outcomes are qualification evidence, not scientific recovery trials. Do not tune the target parameters after viewing them.

At least one allowed smoke fit must finish with a complete nonempty native census, faithful round-trip export, consistent native/independent arithmetic and a verified evidence envelope. A second successful fit is not mandatory: stop smoke execution when the requirement is met, leaving the unused slot NOT_EXECUTED. Direct native fixtures must cover all four operators whether or not the search produced them. Retain any attempted failure. Any diagnosis/correction is subject to the same two-epoch setup/bridge budget when those layers change; never reset it through this gate.

All required deterministic fixtures and eight mutation checks must pass before target generation. Bounded software debugging before target data is allowed at committed forward sources; do not mutate requirements, erase failed controls, replace native outputs, or exceed smoke limits. A mismatch on the same captured smoke output may be re-evaluated after a documented source fix without another fit. There is no claim of independent replication from such reuse.

Seal `runtime_qualification.json`, `integration_qualification.json`, full dependency/configuration/source identities and the final fixture/mutation result before publishing the target seed commitment. The target-worker identity must have been exercised, including ownership/read access to staged files; a successful administrator-only smoke run is not qualification of a different restricted worker.

This seal is an **execution qualification record**, not a retroactive design freeze. The design/criteria were already frozen before setup. The new target outcomes remain unseen. If a later worker changes platform, executable, backend, dependencies, trust boundary or operator semantics, this qualification no longer applies; stop the target stage rather than silently carrying the PASS across.

Do not perform an independent audit between Gates R and I or before the four planned runs. The one substantive independent review covers the final reached package. Completion of these gates alone does not establish adapter-wide acceptance.

## 7. Native output boundary, translation, and independent parity

### Define what “complete” means before searching

The authoritative exported inventory is **every occupied final native hall-of-fame slot** after search stops and before the worker exits, in native slot/complexity order. Capture the complete existence mask and a count cross-check from the pinned backend, not a count inferred from already filtered Python records. Keep every corresponding raw tree, value, loss, complexity, and available identifier. Capture the ordinary final CSV/frontier and map its entries to native slots; do not replace the native inventory with the smaller displayed frontier or `get_best()` result. [S8–S10]

This is complete **final retained output**, not every transient expression considered during search and not exhaustive grammar coverage. Retain available intermediate files as such, without calling them additional independent runs. Different formulas or duplicate-looking entries must remain individually locatable. A size-limit rejection retains an explicit whole-run status and original archive binding; it must not silently truncate the census.

### Capture actual native structure, not a rewritten display

Within the trusted, pinned engine worker, obtain each native retained expression and export its node structure directly through a small source-pinned walker. Validate the exact node API, child ordering, operator registry, variable indexes, constant types, and hall-of-fame indexing in qualification. Resolve expression wrappers through the backend's supported unwrapping mechanism; do not assume a printed string is the original tree.

Keep raw CSV and equation strings as inert corroborating records, but do not parse `sympy_format` as the authoritative tree, use unrestricted `sympify`/`eval` on candidate output, or rely on a prettified formula's inferred domain. No candidate-specific code or callable crosses into the trusted evaluator. Engine-created pickle/Julia serialization can be retained as opaque evidence if useful, but the evaluator and ordinary CI must not load it. In-process access to the worker's own fresh engine state is distinct from deserializing an externally supplied checkpoint.

The claim begins at the **final native export boundary**. Upstream search may simplify candidates before that boundary; this pilot does not reconstruct deleted search-history restrictions or establish fidelity to every precursor expression. Preserve the final native tree's restrictions during all subsequent normalization.

The pinned real exporter must reject unknown node/operator variants explicitly. An unresolved native-to-row binding is NO_GO for that route, not permission to fall back silently to evaluated strings. Exporter traversal is separately checked against native evaluation so a mistaken operator mapping cannot validate itself.

### Map the supported fragment and constants faithfully

Map native `+` to `add`, `*` to `multiply`, `/` to ordered `divide`, and binary `-` to `add(left, multiply(exact −1, right))`. Preserve original child order and references before canonicalization. Do not reinterpret protected division, absolute-value operators, general powers, custom calls, complex numbers, or unsupported unary nodes as ordinary arithmetic. They are not in this pilot's grammar.

Keep each native Float64 constant's original value with a round-trip representation, including a bit/hex representation in the raw export. Verify decimal/bit agreement before normalization. Do not rationalize fitted decimals, round them for identity, or identify them with physical constants. Distinguish a native numerical constant from the exact −1 introduced by the documented subtraction translation.

Use the accepted parameter roles without allowing the generator to set them. Float64 values remain approximate. For this legacy schema, `training_fitted` means the scalar value is selected or optimized in the training-exposed search context; record `individual_optimizer_history=NOT_ASSESSED` unless separately available. Do not call such coefficients fixed external constants or independent measurements. A project-owned deterministic instantiation rule may create a candidate-specific manifest from the fixed run manifest and native constant-leaf positions: one scalar slot per leaf, dimensionless, bound to the run's training input digest and training-exposed generation/fit context. The rule, slot ordering, and source ancestry are frozen before the target runs; the public verifier recomputes the manifest and mapping from raw bytes. Generator-supplied unit, role, fit-context, or manifest overrides are rejected. Do not assert that every native constant was individually optimized when only training-exposed search provenance is known.

If the accepted schema cannot represent that narrow derivation unchanged, use a small explicitly versioned outer adapter envelope with a documented projection into the accepted evaluator. Do not pretend real output is `mock-tree/1`, fabricate historical source metadata, or edit the accepted format registry. Candidate-specific manifest identity must still bind the fixed parent manifest, raw item, and parameter-instantiation rule.

### Native versus independent numerical evaluation

For every occupied retained slot, the worker records **pointwise** native numerical evaluations on the first sixteen training feature rows and these eight fixed feature triples, in the same declared SI conventions. If the backend supplies one whole-array completion flag, obtain singleton native evaluations for this small parity set so one invalid point cannot erase the valid points or be fabricated as pointwise failure. Retain the raw flag/return contract and map classifications explicitly:

`(0.5,1,0.5), (1,0.5,1), (2,1,2), (1,2,0.5), (0.75,1.5,1.25), (1.5,0.75,1.75), (2,0.5,1.5), (0.5,2,0.75)`.

Use the native expression's evaluator, not PySR's SymPy-backed prediction export and not the new adapter's own evaluator. A tiny static source-pinned Julia helper is permitted for export/evaluation; this is not permission for custom search operators or candidate-generated executable code.

The independent side validates bounded node shape, symbol/parameter binding and the original graph, then evaluates the translated original tree using the accepted Python arithmetic. Keep this arithmetic check separate from dimensional eligibility: a unit-agnostic native expression can have finite matching values while correctly failing the Number Project's unit gate. Domain, nonfinite and native-evaluation-incomplete outcomes must not be conflated; unresolved completion semantics stop qualification. Compare finite values with **relative tolerance `1e-10`, absolute tolerance `1e-12` in the declared numeric units**. Compare invalid/nonfinite/domain classifications separately. A point outside the expression's original domain is retained as a diagnostic, not converted to zero or dropped to improve parity. Engine numeric failure, Number Project domain rejection, and numerical translation disagreement remain distinct.

Document the denominator and coverage of every parity statistic. Source-derived dimensional rejection can be correct even when native numerical evaluation is finite. Do not demand equality of an engine's unit-agnostic eligibility decision to the project's dimensional gate; the parity test concerns the formula's arithmetic and definedness.

Unknown units, a swapped column map, lost denominator, wrong subtraction order, changed constant bits, or an unbound candidate cannot be excused by a low aggregate loss. The numerical comparison policy is fixed before target output exists. Any post-output diagnosis must retain the original discrepancy and cannot quietly loosen tolerance.

## 8. Trusted gate, output accounting, and descriptive selection

The trusted path validates the fixed manifest and complete registered dependency graph before reading feature values, then binds raw source/run receipts, reconstructs native-to-exchange mappings, instantiates allowed parameter metadata, and issues cards. Preserve target-reachability through transitive, cancelled, and zero-weight edges. Coherent-SI unit declarations are explicit; matching dimensions do not prove a numeric scale. Exact inputs and known additive output noise are declarations of this generator, not calibrated measurement claims.

Record every raw item as retained/evaluable, retained with a semantic rejection, unsupported, or malformed, with its immutable raw locator and a human-readable reason. Run states distinguish setup failure, engine failure, timeout with partial output, no output, exporter failure, completed export, and evaluation failure. Each r01–r04 must have exactly one terminal run record with counters for actual fit invocations; an untouched run is explicitly NOT_EXECUTED, not absent or silently successful. Empty output never earns abstention or grammar-rejection credit. Output hashes establish consistency and custody, not that an arbitrary malicious worker is truthful.

Retain ordinary engine scores/losses under source-reported diagnostics. Independently compute new training/validation RMSE only for candidates eligible and finite on every row of the named split. Existing `evidence_card()` accepts at most **32 points**. Keep that bound unchanged: use the 24 parity points for its compact card and evaluate dataset rows through verified candidate arithmetic in named, deterministic batches of at most 32. Bind the batch index and ordered row IDs to the sealed split; prove every row appears exactly once, without gaps, overlaps, reordered labels or substituted splits. Accumulate the full sum of squared residuals and full denominator; do not average batch RMSEs. Test a deliberately unequal final batch. A failed row invalidates that candidate's score for the entire split; it does not reduce the denominator. [S16] Keep the row denominator fixed; record invalid-row counts and no numeric score rather than dropping rows. No refitting occurs in the adapter.

For each run, choose the eligible candidate with the smallest validation RMSE; break exact ties by native complexity then native slot index. No closeness-based tie band or post-hoc complexity penalty. When none qualifies, seal `NO_ELIGIBLE_SELECTION`. The whole final inventory remains available even when only one candidate is chosen.

After every run's selection is sealed, compute held-out RMSE for the sealed candidate only. Retain its failure without replacing it. These metrics describe four observations of the pinned workflow; they do not produce a comparison, confidence interval, general success rate, or predictive-validation promotion. Neither training nor validation quality is part of the primary adapter PASS threshold.

The engine may see only training data. The adapter may see validation data for this declared selection. The reporting evaluator sees held-out data only after all selection seals. Architecture may share a trusted operator/OS identity, but data arguments and staged files must enforce the declared software access paths, with explicit canary tests and honest access limitations.

### New-envelope resource limits

Freeze a distinct `tnp-pysr-adapter/2` outer namespace with strict schemas. Reuse the unchanged accepted per-record limits: 1 MiB JSON input, 64 JSON depth, 256 expression nodes, 24 expression depth, 32 parameters and 32 points per card. Subtraction expansion must fit these limits. Do not silently enlarge them or split one expression to evade them. For the new outer package set: at most 128 retained candidate slots per run, 32 MiB total structured native export per run, 64 KiB per expression-tree record, 256 MiB total captured logs per setup epoch or worker, and 1 GiB total retained package evidence. These caps include rejected items; an over-limit census cannot be hidden by truncating the accepted subset.

Stream capture to files, not an unbounded in-memory buffer. On a cap/deadline, stop the process, preserve complete bytes up to the stopping boundary and an explicit `OUTPUT_LIMIT`/`LOG_LIMIT` receipt with capture status; do not claim a full log or full native output. An incomplete essential capture forbids PASS and may make evidence UNRESOLVED. Chunking for transport preserves a manifest of ordered chunks and the original full-stream digest; it does not raise an acceptance cap. Do not archive the installed interpreter or large dependency binaries in the repository; retain their hashes/source identities instead.

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
| Bounded full-split evaluation | Batches of at most 32 cover each split exactly once; a 65-row fixture exercises 32+32+1; missing, duplicated, relabeled or overlapping rows fail; aggregate squared error is not an average of batch RMSEs |
| Runtime gate and custody | Standalone failure cannot become runtime PASS; changed loaded executable/backend/lock invalidates qualification; no target seed/data before both qualified gates; exhausted setup/smoke counts cannot reset on resume; incomplete logs cannot be reported complete |
| Frozen history and offline guard | New modules may be added without editing old evidence or CI; old scientific-artifact tampering still fails; the new guard requires no PySR/Julia installation, search, fitting, network, or secret |

Use **eight designated production mutations** in new source, one for each of: native operator/column mapping, original-domain erasure, target-path bypass, dimensional/parameter-role bypass, raw-binding/verification bypass, candidate census loss, evidence-promotion/heuristic-family escalation, and outcome-routing misclassification. Where one named mutation would ambiguously test two mechanisms, select one exact site and cover its companion with a deterministic fixture. Specify sites and intended assertion IDs before target generation.

Before any target generation, all eight must be killed by their designated semantic assertions; syntax, import, runtime, unrelated source-pin, and skip failures earn no kill credit. Keep a surviving baseline and one equivalent control. Preserve failed calibration and recalibrate only the diagnosed mutant at unchanged relevant source. Do not rerun unrelated mutation families. A small mutation result file is evidence, not a new standing maintenance register. If runtime/export prerequisites fail first, mark integration fixtures/mutations NOT_EXECUTED and test only the reached negative-archive path; never fabricate mutation success or require a full unused adapter as a condition of honest NO_GO closure.

## 10. Chronology, immutable attempts, and verification

### Required sequence

1. Reconcile baseline; commit exact consumed packet and launch receipt.
2. Commit a **sole-file contract/acceptance freeze** stating this design, values, tolerances, schemas, source maps, safety boundaries, dispositions, resource limits, retry rules, and negative-control expectations. Then create the draft PR/server timestamp anchor before implementing the new evaluator/exporter.
3. Commit the setup logger/runner; execute Gate R before new target generation or broad adapter implementation. If it passes, implement and qualify Gate I, native export, fixtures and mutations. Commit source, tests, exact environment locks, qualified setup receipt, and frozen effective options. Routine forward software corrections before target generation are allowed and recorded; no result-driven scientific change is allowed.
4. Verify both qualification seals and their exact environment/source identities. Publish the master-seed commitment, then generate and commit all public data plus private hashes. Never create a seed early and claim it remained prospective by simply delaying publication. No target-run engine state or target candidate output may predate the required source/data commitments. Engineering smoke outputs belong to their separately source-bound, predeclared fixture epoch and are never target evidence.
5. Execute exactly the four target fits. Store run receipts, native census/tree bytes, CSV/frontier, native parity observations, logs and terminal states with exclusive writes. Complete each evidence binding before any dependent selection stage.
6. Seal all raw outputs; compute and seal all validation choices. Reveal held-out rows only after every choice/no-choice is committed. Produce descriptive held-out outcomes without modifying selections.
7. Emit one authoritative package report with explicit outcome axes and exact evidence routes. Bind final source/evidence and CI through the PR/current handoff, avoiding circular self-hashes. Keep a clean committed tree for the inherited test prerequisites.

Use existing chronology/serialization helpers where they fit without modifying frozen source. Do not invent source-access or hostile-code-isolation assertions. Record actual read access, versions, local failures and server anchors. Familiar benchmark families or a precommitted seed are not independently outcome-blind evidence by themselves.

### No scientific rerolls; bounded operational treatment

Once target generation starts, no additional data, replacement seeds, extra search restarts, warm starts, changed operators/budgets/tolerances, or new target fits are authorized. Native restarts inside the pinned engine's predeclared constant optimizer are part of that one run; an operator-triggered new fit is not.

A finished run with unfavorable results is retained unchanged. A target worker failure is retained at that run ID. Remaining independent planned runs may proceed only when the failure is not an unresolved integrity problem affecting them. No target rerun follows automatically.

A failure confined to transport/export/verification may receive **one package-level forward operational correction**, without new search, data generation, fitting, changed native expressions, or altered selection criteria. Use already retained raw bytes or the still-live sealed worker state only if its original native identity can be demonstrated. No output-dependent environment switch, additional smoke fit or target rerun is included in this correction. Keep the original failed source/output/traceback. A separate correction-source pin and route states exactly what was recovered; inability to establish the original output closes PARTIAL/NO_GO rather than reconstructing a desirable result. Reusing a saved untrusted pickle to recover output is prohibited.

Do not delay sealing output while deciding whether a run is attractive. Never delete an initial failure or overwrite a write-once result. A necessary change to frozen requirements requires an explicit later revision, not a discretionary retry within this packet.

### CI verifies evidence, not another stochastic experiment

Add new focused unittest modules discovered by existing `unittest discover`, with one offline committed-evidence guard entry point; keep `verify.yml`, existing tests, interpreter pins, and inherited guards unchanged. Ordinary CI must not install PySR/Julia or launch live searches. It verifies raw hashes, source/environment/configuration/data/selection chronology, native census correspondence, deterministic translation and numerical evaluation, valid failure routes, and derivation of the reported disposition. Recompute expected records from sealed inputs; never overwrite expected evidence.

Native numerical outputs are **source-bound external-engine receipts**. CI may check them against the independent evaluator but must not claim it reran Julia. The live-run integration evidence and the offline verifier's coverage remain separately identified. Exact bitwise native rerun reproducibility across hardware is not claimed.

Scope evidence immutability to exact retained package inputs and source epochs, not to every future descendant version of living shared files. Do not repeat the already recorded error of treating unrelated living configuration as scientific evidence. This instruction does not authorize modifying any existing file in this additive package.

Keep result-driving source pins epoch-specific; do not newly classify living repository configuration as immutable scientific data. Do not build a generalized historical replay framework unless a concrete conflict requires it and fits the authorized scope. Preserve all accepted #54/#56/#57/#58 source/evidence bindings and rely on their existing guard coverage.

Perform focused affected-boundary tests and new mutation calibration at the final pre-target source epoch. Reuse those results at the completed evidence epoch only when all relevant sources, tests, fixtures and dependencies match. A source correction requires only the affected checks to be repeated and re-pinned; run the final read-only evidence guard after the complete tree is committed. Preserve the repository's normal complete Python and Lean CI jobs. Do not manually repeat unrelated green suites or historical campaigns; run a clean-tree full suite locally only if a concrete integration uncertainty makes it necessary, with the reason recorded. Reuse exact-head results where code, inputs and semantics are unchanged.

## 11. Dispositions and exit semantics

Use the sole authoritative report route `Experiments/SymbolicDiscovery/PySRAdapter2/result.json` with schema `tnp-pysr-adapter/2/result`. The contract freezes its fields and referenced stage schemas before implementing the verifier; distinct raw/export/selection/correction records are not competing dispositions.

`PYSR_ADAPTER_2_PASS` requires all of the following:

- both `RUNTIME_QUALIFIED` and `INTEGRATION_QUALIFIED` records are supported and the exact final version/environment/source chain is preserved;
- all four planned target runs reached normal or predeclared engine-budget termination with complete nonempty native retained output and no unresolved output loss; a supervisor-killed or unexportable run cannot satisfy PASS;
- every occupied slot is accounted for, every supported expression is translated without loss, and every required native/independent numerical comparison is consistent, with explicit domain and unit rejection where appropriate;
- at least one actual nonconstant, dimensionally admissible expression is evaluated from **each law family**, and the combined actual output exercises at least one arithmetic operator; a mock or hand-written formula cannot satisfy this real-output requirement;
- all required fixtures, eight assertion-calibrated mutation kills, and both controls pass;
- all selection/no-selection and held-out routes are retained with no prohibited access, re-fit, reroll, evidence promotion, or historical alteration;
- deterministic integrity verification supports the report at its exact committed evidence/source epoch.

There is **no required hidden-law recovery count or prediction-error cutoff** in this primary PASS definition. Conversely, lawful rejection of every item can show a safe gate but cannot satisfy the real-adapter demonstration requirement. Lack of arithmetic/nonconstant coverage is PARTIAL, not permission to rerun the search.

Use `PYSR_ADAPTER_2_PARTIAL` for a demonstrated safe subset with missing live-run/noncritical coverage; `PYSR_ADAPTER_2_FAIL` for a demonstrated invariant/translation/integrity violation; `PYSR_ADAPTER_2_NO_GO` for a failed prerequisite preventing a credible live demonstration; `PYSR_ADAPTER_2_UNRESOLVED` for irreducible ambiguity at the declared stopping boundary. Preserve the most consequential adverse axis instead of hiding it under a favorable summary. Use this exact precedence: (1) an established unremedied contract, translation, custody or isolation violation gives FAIL; (2) missing or conflicting evidence that prevents determining whether the relevant requirements held gives UNRESOLVED; (3) a supported failed prerequisite with no credible target-run demonstration gives NO_GO; (4) some trustworthy real-target coverage but insufficient complete-run or semantic coverage gives PARTIAL; (5) only fulfillment of every PASS condition gives PASS. Absence of optional evidence is not automatically UNRESOLVED. An honestly captured native startup failure with zero later activity is NO_GO, not FAIL merely because software could not start.

In the immutable result, `operational_acceptance` means only technical acceptance of this bounded integrated demonstration: it is true exactly when the derived conformance is PASS, and false for all adverse dispositions. It is not deployment permission or independent acceptance. Keep `review_status = PROVISIONAL — INDEPENDENT AUDIT PENDING` in the original result.

**CI is a separate delivery gate, not a circular input to its own evidence artifact.** Produce and seal the result, commit the completed head, then obtain exact-head CI. Record the actual CI attestation in the PR/current handoff, not by repeatedly rewriting the result to embed its own future successful run. The offline verifier derives conformance solely from frozen criteria and sealed evidence; it does not call the network or require an in-progress CI run to have already succeeded. Review-ready delivery additionally requires the unchanged repository CI gates to pass on the actual final head; failure of that gate prevents claiming readiness even if the stored bounded conformance is PASS. Independent review and Miguel's merge remain separate authorizations. An accepted negative archive may have green archive-integrity checks while `adapter_conformance=NO_GO` and `operational_acceptance=false`; a live unsafe public adapter cannot be accepted as operational merely by labeling its archive FAIL. Suspected invalid raw evidence must cause a refusal, not a fabricated verification of its truth.

Before target data, retain failed software/control versions and fix only within the fixed design; the final qualification may describe the corrected source. After target data, use only the one permitted detached operational correction and otherwise retain the adverse result. Never turn a failed scientific epoch into PASS by changing criteria. Preserve separate original and reconciled fields/routes when correction is used.

**Verifier semantics:** an offline evidence check succeeds when it establishes that an immutable PASS or adverse report is truthful, complete for its declared stage, and consistent with the contract. It fails on corruption, missing required bindings, altered criteria, or an outcome label unsupported by evidence. Report adapter acceptance separately: an honestly retained FAIL does not authorize deployment or a compatibility claim. Unit tests must demonstrate both truthful adverse reports and forged adverse/PASS reports.

Until substantive independent review, every new trust-boundary claim is **PROVISIONAL — INDEPENDENT AUDIT PENDING**. A passing CI job is not independent scientific review and not a statement of arbitrary-engine safety.

## 12. Deliverables and completion report

Deliver one coherent unmerged PR rather than a maintenance PR followed by a separate pilot. Required additive layout (small helper splits may be frozen before source execution; keep these entry points and authoritative paths):

```text
Discovery/pysr_adapter2_runtime.py       # explicit setup gates and logging; opt-in
Discovery/pysr_adapter2_worker.py        # optional PySR import, native export, one fit
Discovery/pysr_adapter2.py               # verified public entry point; no engine import
Discovery/pysr_adapter2_verifier.py      # offline check; never install, fit or emit
Experiments/SymbolicDiscovery/PySRAdapter2/
  work_order.r1.md / work_order_receipt.json / contract.v1.md / anchor.json
  setup/                               # all attempted epochs, unchanged after capture
  runtime_qualification.json / integration_qualification.json
  environment/ / fixtures/ / source_snapshot.json
  runs/ / data/ / selections/ / result.json
Notes/PySRAdapter2.md
tests/test_pysr_adapter2*.py
```

Folders/files for stages not reached need not be fabricated; the result lists those stages NOT_EXECUTED. For terminal setup failure, deliver only the reached evidence, narrow verifier/tests and report. The native walker/helper may live as a package-local `.jl` file; it is source-pinned and never runs in ordinary CI.

Required entry points are `python3.12 -m Discovery.pysr_adapter2_verifier check` (read-only deterministic evidence validation) and an explicit opt-in execution route documented in the Notes. The offline check must not import the engine worker or install optional dependencies. An attempted import in an engine-free venv should fail only for an explicitly requested live command, not for normal tests.

The full successful-path deliverable consists of:

- a small optional-dependency engine worker/native exporter and new real-adapter facade;
- a new offline conformance/route verifier and focused test module;
- one `PySRAdapter2/` directory containing the consumed packet, frozen contract, qualified dependency/source bindings, data/seed commitments, four run records, raw retained output, selections, failure/correction evidence if any, and one authoritative result;
- `Notes/PySRAdapter2.md`, with exact usage, bounded result, nonclaims, correct reproduction levels, and the focused Claude prompt.

Use source references instead of copying large dependencies or old datasets. No general plug-in framework, UI, CAS, unit-conversion engine, uncertainty-propagation system, container-distribution project, or stable external API. Record third-party package identities and source/license notices needed for this new dependency boundary, without changing the repository license or claiming full SPDX/SLSA compliance.

The decision report must distinguish: setup qualification; actual four-run terminal states; native output inventory; adapter parity; dimensional/domain/provenance rejections; validation/held-out diagnostics; scientific evidence remaining NOT_ASSESSED; retained failures; and exactly what was independently verified versus reused or source-attributed. State that the output inventory is not grammar completeness. Do not report selected-case discovery percentages as a general performance rate.

Before finishing, verify the current rolling work order still names this consumed task/revision. If it does, update only its delivery/status banner with actual completion and report/PR pointers; preserve the consumed snapshot in Git. Re-read its revision/modified-time metadata immediately before writing. If the rolling file has moved to another task or changed concurrently, do not overwrite it; reconcile the current content and preserve the newer instructions. Do not rewrite the contract or science after execution.

Update the existing GPT rolling handoff with the actual completed head, exact-head CI, all pending limitations, authoritative result route and one next substantive audit prompt. Leave Claude's files untouched. After review and Miguel's true merge, later status requests automatically reconcile GPT navigation without a separate audit.

## 13. Findings and independent-review focus

DM-099 is directly implicated: assess the new verified public entry point, raw reconstruction, parameter instantiation and resistance to forged verification. DM-098 governs the new outcome path: assess whether adverse evidence remains verifiable without declaring a defective adapter accepted. DM-097 stays deferred if no CI edit occurs. The additive facade does not silently close those IDs or rewrite their historical surfaces. [S2]

Keep DM-090's CPython boundary; this internal pinned pilot is not a public reproduction/release package. Keep DM-093's estimated-noise/broader-detection limit; neither the old rule nor whole-family rejection is used. Preserve DM-094's base-monomial/missed-curvature explanation and DM-095's correct historical pointer if referenced, without recomputation. DM-096 remains Claude-narrowed, not GPT-closed; the already verified #59 merge CI is factual context, not proof of a general reliable CI history. FH-22 does not justify more old-corpus imports. E-001 remains unrelated and live at its own HUST/AAF boundary.

**Focused Claude prompt for the eventual implementation:**

The implementer must replace the descriptive header below with the actual PR number, complete head SHA, base SHA, final CI URL/outcome, consumed packet SHA-256 and actual result path before delivery. Do not submit a prompt with unresolved placeholders or claim it describes an existing PR during specification preparation.

> Independently review NP-PYSR-ADAPTER-02 revision 1 at the exact final head identified above, using its consumed work order, frozen contract, reached evidence, accepted #58 interface and only the affected current findings. Treat #59 as an unchanged terminal setup archive; its separate audit status is not established by a merge. Resolve an existing #59 report if now available, without another bookkeeping-only audit or native rerun.
>
> Challenge the separation of native Julia startup, Python child launch, dependency resolution, cold bridge identity and native-export qualification; preservation of both setup epochs and bounded smoke counts; archive extraction safety and complete file-captured diagnostics; the failure's actual scope rather than an invented SIGBUS cause; and target generation only after both gates passed. Review the final pinned environment/source identities, not merely the requested versions.
>
> For stages reached, challenge the native occupied-slot census versus formatted frontier; node/constant/column/domain fidelity; independent pointwise arithmetic; numeric units and parameter provenance; all-row bounded batching; the non-bypassable new DM-099 entry point and externally anchored raw binding; fixed run/selection/reveal chronology; absence of rerolls; and failure-aware disposition derivation under DM-098. A public envelope cannot trust an arbitrary caller's `verified=True`, digest, card or normalized expression. Inspect the new envelope rather than claiming the unchanged legacy helper was repaired globally.
>
> Require only evidence appropriate to the reached stage. A setup NO_GO is not a working adapter. Green CI verifies stored evidence, not native Julia replay; recorded native checks and independent Python checks remain different evidence. Do not require a favorable discovered equation or claim whole-grammar coverage, physical discovery, independent replication or estimated-noise capability. Preserve source/evidence immutability, existing CI and all unrelated findings.
>
> Reuse exact-head CI and accepted unchanged evidence. Execute focused probes only for concrete semantic risks; do not reinstall Julia, repeat target searches or re-audit #58 solely for assurance. Report what you independently verified, what was source-attributed, and what remains unreviewed. Return MERGE / DO NOT MERGE at the exact head with separate BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING findings. Claude owns all IDs and scope-specific dispositions; Miguel owns merge, by Create a merge commit only.
>
> **Before finishing, upload the completed audit report and update the affected canonical Claude-owned files in Google Drive, not just local copies. Fetch/read back the remote files to confirm the audited head, verdict and affected finding updates are present. Return their actual Drive links and state whether remote delivery was verified. If upload or verification fails, report the specific failure and mark Drive synchronization INCOMPLETE; do not claim the remote records are current.**
>
> Use the existing canonical current-state and affected finding file IDs wherever supported, retain historical reports in the existing Archive organization, and do not create a second ledger or rewrite unrelated notes. A scientific/audit verdict and Drive-delivery status are separate. Remote-delivery failure requires delivery correction, not another substantive audit.

At preparation, the relevant canonical references are the [current Claude file](https://drive.google.com/file/d/1r3-FRMF68tcM_FTtadM-6M7mByw8kI3m/view) and [DM-097–099 / FH-22 file](https://drive.google.com/file/d/1k8Pg5CmpzsRsfnL-JdyMysD9FSvergOn/view). Resolve the current roles if legitimately superseded; do not update a stale duplicate just because its title matches.

**Create a merge commit only. Never squash or rebase away accepted ancestry or the new freeze/evidence chain.** No automatic merge, release, tagging, outreach, empirical-G work, external Lean execution, multi-engine comparison, estimated-noise study, or speculative-physics activation follows from this package.

## 14. Source map and preparation limits

These references distinguish inherited facts and upstream interfaces from new requirements. The new runtime strategy, numerical batching, explicit caps and remote-delivery rules are specification decisions, not previously executed results. S8–S12 include pinned references inherited from the complete predecessor; actual runtime-specific APIs still require qualification. Private navigation can be stale; use current roles and exact repository pins at execution. No old benchmark, new engine, or scientific experiment was run to prepare this packet.

- **S1 — merged repository state:** [#59](https://github.com/mdiaz4052/The-Number-Project/pull/59), [main](https://github.com/mdiaz4052/The-Number-Project/commit/79b56e0db86605e569c6d8a68a59315a00ab0177), [merge Verify #332](https://github.com/mdiaz4052/The-Number-Project/actions/runs/35415276376). Main rechecked during September 19 specification preparation; earlier same-day merge/CI reconciliation reused. Recheck overlapping PRs at launch.
- **S2 — independent findings:** [DM-097–099 / FH-22](https://drive.google.com/file/d/1k8Pg5CmpzsRsfnL-JdyMysD9FSvergOn/view); [current Claude role observed](https://drive.google.com/file/d/1r3-FRMF68tcM_FTtadM-6M7mByw8kI3m/view). No findings closed by this specification.
- **S3 — accepted internal contract:** [CandidateExchange1 report](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Notes/CandidateExchange1.md), [interface](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Experiments/SymbolicDiscovery/CandidateExchange1/interface.md).
- **S4 — current GPT handoff:** [gpt_RollingAuditHandoff.md](https://drive.google.com/file/d/145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd/view); September 19 instructions explicitly require remote audit delivery and distinguish specification from execution. The complete predecessor design is preserved in #59's consumed `work_order.r1.md`.
- **S5 — PySR identity/compatibility:** [resolved v1.5.10 tag](https://github.com/astroautomata/PySR/tree/f51299e6dddc7bd2bfd7f473bfddca7c32d83206), [pinned juliapkg.json](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pysr/juliapkg.json), [pyproject.toml](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pyproject.toml).
- **S6 — backend identity:** [SymbolicRegression.jl v1.11.0 commit](https://github.com/astroautomata/SymbolicRegression.jl/commit/61e1b36cf5476fe32cd58920d4666d102e3c821c). Tag resolves to this commit; signature/trust is not inferred merely from a hash.
- **S7 — Julia version and binaries:** [official old-release index](https://julialang.org/downloads/oldreleases/) and [1.10.10 announcement](https://discourse.julialang.org/t/julia-v1-10-10-has-been-released/130351). The four selected archive checksums in §6 were read from the official index on September 19, 2026. Downloaded bytes and actual runtime remain unqualified until execution; this is not a latest-version claim.
- **S8 — pinned PySR API source:** [sr.py](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pysr/sr.py), especially configuration, `julia_state_`, `julia_options_`, `_run`, `get_hof`, and `predict`. Dev/2.x documentation is not the contract for this pin.
- **S9 — native expression access:** [expression_specs.py](https://github.com/astroautomata/PySR/blob/f51299e6dddc7bd2bfd7f473bfddca7c32d83206/pysr/expression_specs.py), especially `_search_output_to_callable_expressions`. Exact node APIs and the resolved DynamicExpressions dependency require qualification; source inspection is not a successful smoke test.
- **S10 — output census:** [HallOfFame.jl](https://github.com/astroautomata/SymbolicRegression.jl/blob/61e1b36cf5476fe32cd58920d4666d102e3c821c/src/HallOfFame.jl), occupied members/existence mask versus `calculate_pareto_frontier`.
- **S11 — accepted raw-binding caller:** [candidate_exchange_adapters.py](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Discovery/candidate_exchange_adapters.py), `verify_records`, `evaluate_records`, `verify_cards`.
- **S12 — historical source/self/test pins:** [candidate_exchange_conformance.py](https://github.com/mdiaz4052/The-Number-Project/blob/abe6c20332776740022cff6fee1756373022fc8c/Discovery/candidate_exchange_conformance.py), `SOURCE_PATHS`, `source_check`, and `check`.

- **S13 — terminal predecessor:** [result.json](https://github.com/mdiaz4052/The-Number-Project/blob/79b56e0db86605e569c6d8a68a59315a00ab0177/Experiments/SymbolicDiscovery/PySRAdapter1/result.json), [Notes](https://github.com/mdiaz4052/The-Number-Project/blob/79b56e0db86605e569c6d8a68a59315a00ab0177/Notes/PySRAdapter1.md), [exact consumed work order](https://github.com/mdiaz4052/The-Number-Project/blob/79b56e0db86605e569c6d8a68a59315a00ab0177/Experiments/SymbolicDiscovery/PySRAdapter1/work_order.r1.md). The local planning copy of that packet matches its recorded SHA-256. Its old outcome cannot be upgraded by the new task.
- **S14 — explicit Julia selection:** [JuliaPkg configuration](https://github.com/JuliaPy/pyjuliapkg#configuration), [JuliaCall existing environments](https://juliapy.github.io/PythonCall.jl/stable/juliacall/#Using-existing-environments). Current primary documentation checked September 19; installed exact-version support and PythonCall matching must be checked before using these options. These references support configuration possibilities, not a diagnosis or proof of recovery.
- **S15 — publisher verification guidance:** [official Julia manual downloads](https://julialang.org/downloads/manual-downloads/). Current signature/key guidance is distinct from historical checksum comparison; do not conflate them.
- **S16 — exact accepted evaluator constraints:** [candidate_exchange.py at merged main](https://github.com/mdiaz4052/The-Number-Project/blob/79b56e0db86605e569c6d8a68a59315a00ab0177/Discovery/candidate_exchange.py), especially `LIMITS`, `evaluate` and `evidence_card`. Re-read for this preparation: 32-point cards, original-tree arithmetic, strict manifest/parameter contracts and the legacy binding precondition.

## 15. Launch instruction

Send this only when choosing to activate implementation:

> Execute **NP-PYSR-ADAPTER-02, revision 1**, from the existing `NUMBER_PROJECT_CURRENT_WORK_ORDER.md` in the Workflow Management Drive folder. This authorizes that bounded implementation, its declared runtime qualification/recovery, four-run pilot, verification and one unmerged PR. Follow the qualification gates before target generation, preserve the old NO_GO and all standing provenance/true-merge rules, and include explicit Google Drive upload-and-readback instructions in the Claude audit prompt. Do not merge or activate options 2 or 3.

Preparation has executed none of those actions. A successful remote save of this specification confirms document delivery only.

**End condition:** one bounded real-adapter decision and a resumable handoff. A useful result may be PASS, PARTIAL, FAIL, NO_GO or UNRESOLVED; no follow-on is automatically activated.
