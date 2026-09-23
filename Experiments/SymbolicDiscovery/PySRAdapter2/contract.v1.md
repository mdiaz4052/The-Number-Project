# NP-PYSR-ADAPTER-02 — prospective contract v1

Task NP-PYSR-ADAPTER-02 revision 1; outcome_blind=false.
Base: `79b56e0db86605e569c6d8a68a59315a00ab0177`.
Instruction snapshot: `dfbe2bd9bb6e0197bbb12ded6e0f3f59a1fffd2c`.
Exact consumed work order: `work_order.r1.md`, 81176 bytes, SHA-256
`d6866c119695f40caefd576a8bd0c20acfd7a2441639b8933ed0d273edc73b39`.

The entire consumed work order, especially sections 3–13, is incorporated into
this sole-file freeze as the normative design, criteria, fixtures, source map,
limits and independent-review contract. This file selects concrete mechanisms
and record schemas where that work order permits implementation choices. A later
rolling Drive edit cannot modify either frozen file. No target seed or data exists.
No setup program or new evaluator/exporter has executed at this freeze.

## Objective and hard boundary

Demonstrate faithful custody, complete final retained native output, mathematical
translation and verified evaluation for the fixed four-run PySR pilot. Adapter
conformance is distinct from search quality and from evidence-integrity checks.
Keep every pre-existing repository path byte-identical. No workflow, shared
source, old test, historical evidence, Lean or root dependency change. New guard
is discovered by a new unittest. DM-097 and DM-100 are not repaired globally.
DM-098 controls outcome derivation; DM-099 controls every new trusted card path.
All six scientific promotion axes remain NOT_ASSESSED; candidate status is
GENERATED/FITTED CANDIDATE; search_coverage=NOT_ESTABLISHED.

## Chronology and source custody

Snapshot -> sole-file freeze -> GitHub draft-PR creation timestamp -> committed
setup runner -> Gate R -> committed integration sources/fixtures -> Gate I ->
qualified seals -> published seed commitment -> published public data/private
hashes -> four fits/raw seals -> all four selection seals -> held-out reveal ->
derived result -> exact-head CI -> independent review -> Miguel's true merge.
Commit and publish result-driving sources before their external execution.
Exclusive file creation preserves attempts, logs, raw outputs and results.
Corrections are forward source epochs with original receipts retained. Never
amend/rebase/squash the evidence chain. Same-head checks are reused where valid.
Pins of shared inputs refer to committed source epochs, not all future living
versions. The final result and evidence seal avoid circular self-hashes.

## Gate R recipe and authorized limits

Pinned stack: Julia 1.10.10, CPython 3.12 (patch/executable frozen at setup),
PySR 1.5.10 at `f51299e6dddc7bd2bfd7f473bfddca7c32d83206`, backend 1.11.0
at `61e1b36cf5476fe32cd58920d4666d102e3c821c`. The chosen host is the current
authorized native Linux glibc x86_64 environment; record hardware/process
architecture, virtualization, storage, limits, relevant loader environment and
actual permissions. Never substitute a version or claim a root cause from a crash.

Use a clean task-owned ordinary filesystem directory under `/tmp`, isolated
venv, Julia depot/project and explicit absolute executable path. The controller
retains credentials; child environment is constructed from an explicit allowlist
(PATH, task HOME/TMPDIR, locale, package-local Python/Julia settings, thread
counts and required public CA paths only). No inherited proxy credential,
repository token, connector environment or unrelated file is staged. Do not
modify global environment or security policy. Prefer an existing namespace tool
to expose only system runtime paths and task files. If unavailable, use a distinct
unprivileged numeric UID/GID with cleared supplementary groups, no-new-privileges,
existing controller-directory permission barriers and explicit canaries. Record
whether filesystem/network isolation is enforced; stop before external execution
if credential separation or staged-data restrictions cannot be established.
Offline mode after resolution is mandatory even if OS network isolation is unavailable.

Record supervisor source SHA/hash, command, allowlisted environment, child
identity, executable hash, wall/monotonic times, return code/signal, deadline,
capture completeness and output hashes. Open exclusive stdout/stderr files before
launch; monitor process groups and kill all descendants at deadline/cap.
256 MiB captured logs per epoch/worker; 1 GiB retained package evidence.
Preferred 6 GiB enforced address-space cap; distinguish this from physical memory
and report if only observed. Core dumps disabled. A cap stop is explicit.

Primary epoch and at most one diagnosed recovery epoch. Each permits 1200 s total
child execution, 120 s/minimal probe, 600 s/dependency resolution or cold import.
Network downloads are bounded by this same budget. No unchanged failed-stage
repeat. Record recovery rationale/changed conditions before its command; choose
first justified remedy in the work-order order: demonstrable extraction/storage
fault, diagnosed loader/environment contamination, source-supported bridge
conflict, one already available authorized native isolated environment. No
speculative flags, source build, version switch, third epoch or new infrastructure.

First obtain publisher checksum metadata and archive via official HTTPS:
`https://julialang-s3.julialang.org/bin/checksums/julia-1.10.10.sha256` and
`https://julialang-s3.julialang.org/bin/linux/x64/1.10/julia-1.10.10-linux-x86_64.tar.gz`.
Expected SHA-256: `6a78a03a71c7ab792e8673dc5cedb918e037f081ceb58b50971dfb7c64c5bf81`.
Stop on disagreement. No digital-signature claim. Inspect all archive members for
absolute/traversing paths, special files and escaping symlink/hardlink targets;
preserve internal links and extract without archive ownership restoration into
a new directory. Retain validation inventory/hash and extraction status.

Then, in order (stop on a failed prerequisite):
1. Exact Julia executable with `--startup-file=no --history-file=no`: print
   VERSION, Sys.MACHINE and 1+1; separately `using Libdl; println(Libdl.dlpath("libjulia"))`.
   Require 1.10.10, expected platform, arithmetic 2, zero exits and a real loadable
   library path. These are planned distinct probes, not speculative retries.
2. Clean CPython 3.12 child launches that exact Julia library probe; preserve both
   Python-parent and Julia-child exit/signal evidence.
3. Install pinned PySR, resolve exact backend, lock complete Python/Julia sources,
   hashes/versions, Project/Manifest, registry identities and license notices.
   Use PYTHON_JULIAPKG_EXE plus PYTHON_JULIAPKG_PROJECT; verify installed support
   before first bridge import. The prepared JuliaCall EXE+PROJECT alternative is
   reserved for a documented allowed recovery, not silent override mixing.
4. New cold offline process under the proposed worker identity imports bridge and
   PySR, verifies arithmetic, loaded versions/paths and unchanged lock. No fit yet.

Only all four layers on one consistent environment yield RUNTIME_QUALIFIED.
An unsupported prerequisite stops with stage-complete NO_GO/UNRESOLVED as applicable;
do not implement an unused large adapter, fabricate locks or create target data.

## Gate I, four-run design and limits

The work-order sections 5–9 define exact smoke fixtures, all deterministic
positive/negative cases, search options, native arithmetic parity, units and
inventory. They are frozen unchanged. At most two smoke fits total (seeds 101,
202; 16 specified fixture rows), stop after first successful complete nonempty
native census and verified envelope plus all fixtures. At most five iterations,
one population of 27, 20 cycles, 5000 evaluations, size 7/depth 5, serial Float64,
engine 120 s/supervisor 300 s. Failed smoke consumes its slot.

Eight production mutations and a surviving baseline/equivalent control, all
assertion-calibrated before target generation. Exact sites/assertion IDs are pinned
with pre-target sources: operator/column, domain, target path, dimensions/role,
raw binding, census, promotion, outcome routing. Errors/skips/source-pin failures
are not kills. A terminal runtime failure means these are NOT_EXECUTED.

Four target IDs exactly r01=M1, r02=A1, r03=M2, r04=A2 (law map evaluator-only).
Each: 128 training, 64 validation, 64 held-out rows. Independently uniform u,v,z
in [0.5,2.0], u/v/y in metres, z and coefficients dimensionless; noise uniform
[-0.001,0.001] m. M=1.5*u*z+e, A=1.25*u+0.75*v*z+e.
After gates, generate 32 secret bytes once; publish SHA-256 commitment before
rows. Domain-separated SHA-256(master || UTF8 labels) streams by run/split/purpose;
use CPython 3.12 random.Random with version-2 seeding of resulting integer.
Derive engine seeds in [1,2147483647], resolve collisions by increasing a suffix
counter before rows, never by outcome. Record exact derivation/source/patch.

Each fit once; operators +,-,*,/; no unary/custom operators/losses/templates,
transforms, guesses, denoising, batching, warm starts or variable selection.
60 iterations, 4 populations, size 27, 100 cycles, 200000 evaluations, maxsize 15,
maxdepth 8, precision 64, serial deterministic execution; distinct sealed seed;
turbo/bumper false; early_stop_condition=None; engine 180 s, supervisor 300 s.
Freeze all effective pinned defaults before data; X_units/y_units=None.

Workers see only training plus configuration/neutral columns. Complete occupied
native hall-of-fame census (including mask) precedes normalization; CSV/frontier
is corroboration only. Preserve native node/operator/constant bits, source metrics
and pointwise native classifications. Translate subtraction as add(left,-1*right),
constants as approximate dimensionless training_fitted scalar leaves with frozen
candidate-specific instantiation. No rationalization, executable candidate text,
SymPy authority, erased domain/edges or inferred physical constants.

Parity: first 16 training features + eight work-order triples, native singleton
evaluations versus independent original-tree Python arithmetic; rtol=1e-10,
atol=1e-12; compare domain/nonfinite/incomplete classifications separately.
Cards at most 32 points; all split rows via ordered <=32-point batches, complete
coverage exactly once, full SSE/full denominator, no averaging batch RMSEs.
Validation selects minimal eligible finite RMSE; exact ties complexity then slot;
NO_ELIGIBLE_SELECTION is sealed. All selections committed before held-out reveal;
held-out only the sealed choice; no replacement/refit/rerank/search repetition.

Accepted per-record limits unchanged: 1 MiB JSON, depth 64, 256 nodes, expression
depth 24, 32 parameters, 32 points/card. Outer limits: 128 slots/run, 32 MiB export,
64 KiB/tree, 256 MiB logs/worker or setup epoch, 1 GiB evidence/package. Explicit
whole-run refusal on caps; retain bytes captured and disclose incompleteness.
One post-data forward transport/export/verification correction permitted using
original sealed evidence only; retain failed version and distinct corrected route.

## Strict record contracts (all fields required; unknown fields rejected)

Namespace `tnp-pysr-adapter/2`; all hashes SHA-256 lowercase hex over exact bytes.
JSON records reject duplicate keys and nonfinite numbers; bounded UTF-8 only.
Timestamps timezone-aware UTC; counters nonnegative integers excluding booleans.
Existing Candidate Exchange projection schemas remain unchanged. Optional/unreached
records are absent and explicitly NOT_EXECUTED in result, not fabricated.

| Suffix | Fields in addition to schema |
|---|---|
| anchor | base_sha, snapshot_sha, freeze_sha, pr, url, created_at |
| host | observed_at, python, platform, machine, libc, uid, gid, storage, limits, isolation, relevant_environment |
| setup-step | epoch, step, source_sha, source_sha256, command, environment, cwd, identity, executable_sha256, started_at, finished_at, elapsed_seconds, deadline_seconds, returncode, signal, termination, capture, stdout_sha256, stderr_sha256 |
| setup-stop | observed_at, source_sha, epoch, failed_step, reason, recovery, runtime_layers, activity, unperformed, evidence_inventory |
| runtime-qualification | state, source_sha, environment_digest, setup_epochs, completed_layers, failures, limitations |
| integration-qualification | state, source_sha, runtime_digest, environment_digest, effective_config_digest, smoke_receipts, fixtures_digest, mutation_digest, limitations |
| source-snapshot | source_sha, files, accepted_source_sha, accepted_files |
| evidence-seal | evidence_sha, files |
| result | task, disposition, evidence_integrity, adapter_conformance, operational_acceptance, review_status, outcome_blind, search_coverage, scientific_evidence, stage, setup, planned_runs, evidence, limitations, source_snapshot_digest |

Setup-step capture: {status,stdout_bytes,stderr_bytes,total_log_limit_bytes};
status COMPLETE or LIMIT_STOP/INCOMPLETE. termination EXIT/SIGNAL/TIMEOUT/LOG_LIMIT/
SPAWN_ERROR. identity records effective UID/GID, groups, no_new_privileges and
restriction mode. Host isolation records actual capabilities and limitations.
setup-stop activity: master_seed_created, target_rows_created, smoke_fits_executed,
target_fits_executed, cards_issued, selections_sealed, heldout_evaluations;
all zero/false on a pre-integration terminal stop. runtime_layers lists each of
standalone, python_child, pinned_dependencies, cold_bridge with NOT_EXECUTED/PASS/FAIL.
Recovery: budget=1, used=0 or 1, rationale, changed_conditions, prior_failure;
no plausible supported remedy means no recovery, not a speculative second attempt.
Unperformed lists integration, fixtures, mutations, native_export, seed, data,
target_fits, selections, heldout with NOT_EXECUTED when not reached.
evidence_inventory is the exact mapping of setup-relative file path to bytes/hash.

Result setup: runtime_qualification, integration_qualification, setup_epochs,
failed_step, failure_reason, recovery_used, limitations. planned_runs always four
objects {run_id,state,fit_invocations,reason}. evidence: setup_inventory_digest,
native_output_inventory, adapter_parity, dimensional_domain_provenance_checks,
validation_diagnostics, heldout_diagnostics, fixtures, mutations, raw_bindings.
scientific_evidence has the six inherited NOT_ASSESSED axes. limitations is a list
of explicit factual scope statements. stage is the last reached gate/stage.
Result is recomputed from sealed records, never validated by enum membership alone.
Full-path native/run/selection schemas are defined by work-order sections 7–10
and frozen with Gate I fixture sources before any target data. Their required
facts and acceptance thresholds may not be weakened by representation choices.

## Disposition derivation and verification

Precedence: established unremedied contract/translation/custody/isolation violation
FAIL; missing/conflicting essential evidence UNRESOLVED; supported failed
prerequisite without credible target demonstration NO_GO; trustworthy real-target
subset without complete coverage PARTIAL; only all work-order section 11
conditions PASS. Native startup failure alone is NO_GO. Incomplete optional
evidence alone is not UNRESOLVED. Integrity of a truthful adverse archive may
PASS while adapter_conformance remains adverse and operational_acceptance=false.
Operational acceptance true exactly for conformance PASS. Original review_status
is always PROVISIONAL — INDEPENDENT AUDIT PENDING.

Offline `python3.12 -m Discovery.pysr_adapter2_verifier check` reads only retained
evidence and git objects, performs no installation, network, native execution,
fit or file emission. It rejects unsupported relabeling, tampered logs, missing
inventory, forged qualification/activity/source/history or false promotion.
For a terminal setup stop implement/test only the reached archive route; do not
claim broad outcome coverage, live fixtures or mutations. Preserve all prior
failures, partial capture declarations, source pin chronology and retry counts.
Evidence proves receipt consistency, not arbitrary operator truthfulness.

Review-ready delivery additionally requires exact-head existing Python and Lean
CI, separate from the immutable result. Record CI in PR/handoff, avoiding a
self-referential result rewrite. No local Lean changes/build required. One final
full Python suite is justified to test additive unittest integration against
inherited clean-tree/source guards; no repeated historical mutation campaigns.
Claude reviews reached semantic boundaries, receives exact PR/head/base/CI/packet
digest/result route, and must upload audit/current/finding changes to canonical
Google Drive files and fetch/read them back. Return actual links and explicitly
mark failed remote delivery INCOMPLETE. Leave PR unmerged for Miguel. True merge
only. No options 2/3, engine comparison, outreach, release or new science follows.
