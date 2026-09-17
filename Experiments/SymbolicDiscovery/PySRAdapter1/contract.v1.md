# PySR Adapter 1 — contract and acceptance freeze

Task NP-PYSR-ADAPTER-01 revision 1. This sole-file freeze incorporates the exact
consumed `work_order.r1.md`, SHA-256
`938d7c884cc2b6add3dae4775de8159b387d2addd7fd5654f4cd50eff3670583`,
in full. Its sections 3–13 are normative. No target outcome exists at this freeze.
Base: `9d59d7e7a9e2f056f73d277282a49387287311ff`.
Instruction snapshot: `87780b9e7880b0e7afb8dd6034a609ce1391cf37`.

## Scope and stages

The sole authoritative outcome is `PySRAdapter1/result.json`, schema
`np-pysr-adapter/1/result`. It records `task`, `disposition`, `stage`,
`evidence_integrity`, `adapter_conformance`, `operational_acceptance`,
`review_status`, `outcome_blind`, `search_coverage`, `scientific_evidence`,
`source_binding`, `evidence`, `planned_runs`, `limitations`.
Artifacts use exclusive writes. No output may be replaced to make it favorable.
The result is sealed by its exact evidence introduction commit and file digest.
The source/evidence seal lives outside the result to avoid self-reference.

Stages are setup, qualification, target_runs, selection, heldout, complete.
At every stage retain failures and actual executed versus not-executed counts.
An unqualified prerequisite stops before fresh seed/data creation. In that case
the deliverable is the frozen attempt, exact setup diagnostics, a stage-specific
offline custody/disposition verifier, tests, and decision report. Do not ship
unqualified adapter code or fabricate locks, options, mutations, native output,
or four-run evidence. Mark all unperformed requirements NOT_EXECUTED. The eight
adapter mutations and native fixtures apply once that implementation is reached;
they cannot be claimed for an early setup NO_GO. Later execution needs a new
authorized package, not overwriting or silently resuming this terminal epoch.

## Exact source/environment prerequisites

PySR 1.5.10: astroautomata/PySR@f51299e6dddc7bd2bfd7f473bfddca7c32d83206.
SymbolicRegression.jl 1.11.0:
astroautomata/SymbolicRegression.jl@61e1b36cf5476fe32cd58920d4666d102e3c821c.
Julia 1.10.10, official platform binary SHA-256 check required. CPython 3.12;
qualify exact patch/executable digest; exact Python and Julia transitive locks.
No source version substitutions. One clean venv; one diagnosed setup/transport
retry allowed before target generation. Every attempt preserves command, times,
exit status, stdout/stderr, attempted source, and SHA-256 of retained bytes.
A setup policy/network denial is a prerequisite failure, not an adapter defect.
No access-control bypass or credentials in worker environment/logs.

Two tiny smoke fits at most: <=5 iterations, 1 population, 27 members, fixed
published rows, operators +,-,*,/. Native constructed controls may supplement.
No target seed before qualified source, options, export, fixtures and mutations.
Backend operators, node API and locks must be pinned at qualification, not guessed.
If exact native bindings cannot be qualified, NO_GO is required.

## Target configuration and numerical criteria

Exactly four anonymous runs r01–r04, two independent draws each from M and A in
work-order section 5. 128/64/64 training/validation/heldout rows per run. Inputs
u,v,z iid Uniform[0.5,2.0], exact; known additive y noise Uniform[-0.001,0.001] m.
u,v,y length; z and all native constant leaves dimensionless. Numeric coherent SI.
Private evaluator-only assignment r01,r03=M and r02,r04=A; worker sees neutral
x1,x2,x3 mapped to u,v,z, training rows/responses and fixed options only.

Engine options: niterations=60, populations=4, population_size=27,
ncycles_per_iteration=100, max_evals=200000, maxsize=15, maxdepth=8, precision=64,
parallelism=serial, deterministic=true; distinct committed engine seeds;
warm_start=batching=denoise=turbo=bumper=false, early_stop_condition=null,
timeout_in_seconds=180, X_units=y_units=null. No unary operators/custom loss,
selection, guesses or learned transforms. Serialize all remaining pinned defaults
and relevant backend options before targets. Supervisor deadline 300 s per fit.
Use Linux RLIMIT_AS=6 GiB if qualified in smoke runs; otherwise record observed-only
memory explicitly, without changing fit budgets. Launch with a minimal env, staged
training-only files and no inherited tokens; attempt network-disabled execution
only through supported OS isolation. State actual limitations, never claim hostile
same-identity isolation. No target retries; package-level operational correction
is limited to one retained-identity transport/export/verification correction.

Generate secrets.token_bytes(32) once after qualification; publish SHA-256 first.
Streams use SHA-256(master || UTF8("np-pysr-adapter/1|run|split|purpose|counter")),
with a pinned CPython random.Random integer seed; sample using random() affine
mapping. Purpose labels u,v,z,noise,engine are disjoint. Engine seed is first
8 digest bytes mod (2**31-1); resolve collisions by incrementing the counter in
run order before data generation. Pin Python patch at qualified source epoch.

Commit public training/validation rows and withheld hashes before all target fits.
Seal every native output before validation selection; seal all four choices before
heldout reveal. No refit, replacement, reranking, seed change, extra search or new
target dataset. outcome_blind=false throughout.

## Real export and trusted boundary

Envelope `np-pysr-native/1`: run_id, parent_manifest_digest, source_binding,
configuration_digest, training_digest, column_map, existence_mask, native_count,
items, frontier, terminal_state. Items retain native slot/index, identifier,
complexity, loss, original tree, display string, native parity observations.
Each tree is a bounded native node record: kind variable/constant/binary;
variable index; Float64 roundtrip decimal plus 16 hex bit digits; or registry
operator and ordered left/right children. Native sharing remains represented by
node identity/references if encountered; detect cycles. Qualification freezes
the exact worker node API/registry without altering this mathematical contract.
Unknown fields/versions/operators are explicitly refused. Display is inert.
Limits: 8 MiB raw JSON, 32 slots, 1024 nodes/item, depth 64, 256 constant leaves;
accepted inner evaluator limits still apply and may reject a whole item. Never
truncate inventory. Duplicate JSON keys, bool-as-number, NaN/Infinity, vector
constants, oversized inputs and invalid graph references are refusals.

Every occupied final hall-of-fame slot must be exported, including slots absent
from the displayed frontier. Bind full native existence mask, independently
counted occupied slots, exact raw bytes and every locator. True repeated formulas
remain separate slots. Source/run/manifest swaps and frontier-only exports fail.
No parsing display equations, eval/sympify, candidate callables or checkpoint loads.

Translate +,* to ordered add,multiply; / to ordered divide; a-b to
add(a,multiply(exact -1,b)). Never simplify away original-domain checks. Each
native constant leaf gets a project-created training_fitted dimensionless scalar
slot in depth-first left-to-right order, bound to training digest. This role means
training-exposed generation/fitting, not proven individual optimization. Native
bit/decimal disagreement or generator metadata overrides fail. Candidate-specific
manifest binds the fixed parent, raw item and this derivation rule.

Only a trusted path taking the fixed manifest, exact raw bytes, and immutable
run/source binding may reconstruct and issue cards. Recompute custody immediately
before cards; no caller-created token or bool can assert integrity. Bind each card
to candidate, manifest and raw digests. Validate full provenance graph before
feature values, including cancelled/zero-weight/transitive target paths. Existing
legacy evidence_card remains internal to this path, with its old direct-call
hazard disclosed rather than declared globally repaired.

Native evaluation: first 16 training feature rows and the eight triples in
work-order section 7. Compare independent original-tree arithmetic with rel_tol
1e-10, abs_tol 1e-12. Invalid/nonfinite/domain states reported separately. No
dropped denominators or invalid rows; dimensional rejection may coexist with
finite native arithmetic. Metrics use all rows or no score plus invalid count.
Selection: minimum eligible full-validation RMSE, exact ties by native complexity
then slot; else NO_ELIGIBLE_SELECTION. Heldout only sealed choice, no replacement.

## Fixtures, mutations and immutable source

All eleven fixture families in section 9 are required before targets. Expected
values are independently authored. Designated production mutation/assertion pairs
(exact source replacement frozen with source before targets): M1 divide child
order / native_operator_order; M2 erase divide under zero multiplication /
original_domain; M3 bypass target-path rejection / target_path; M4 permit altered
parameter dimension / parameter_role; M5 omit raw digest check / raw_binding;
M6 drop last occupied slot / full_census; M7 promote heuristic empty output to
family inadequacy / no_promotion; M8 route failed setup to PASS / outcome_route.
Companion mechanisms are deterministic fixtures. Baseline and equivalent control
must survive; all eight exact designated semantic assertions must kill. Errors,
syntax/import failures, pin failures and skipped tests do not count.

Only new paths under Discovery/pysr_adapter*, tests/test_pysr_adapter*, this package
and Notes/PySRAdapter1.md are permitted. Existing paths remain byte-identical;
verify.yml unchanged, new offline guard reached through unittest discovery.
Epoch source pins cover result-driving new source/tests and adopted primitives,
not living CI configuration. Source/evidence ancestry and sole-file freeze are
checked offline. CI never installs/executes PySR/Julia or launches fits.

## Disposition derivation and precedence

Precedence: demonstrated integrity/translation violation => FAIL; failed required
prerequisite preventing credible live demonstration => NO_GO; irreducible ambiguous
evidence at stop => UNRESOLVED; demonstrated safe subset missing required coverage
=> PARTIAL; only all section 11 predicates established => PASS. Prefix all with
PYSR_ADAPTER_1_. Integrity verification of faithfully retained adverse evidence is
distinct from operational acceptance. Unknown/corrupt evidence causes verifier
failure; it is not silently classified as a legitimate adverse outcome.

For setup NO_GO specifically require observed failed prerequisite, original
diagnostic bytes, unchanged version targets, <=2 setup attempts with diagnosis
for a retry, no qualified environment, zero smoke/target fits, no master seed,
no generated target data, all four planned runs NOT_EXECUTED, no native output,
no trusted cards and no selections/heldout metrics. No PASS, PARTIAL or scientific
promotion can be inferred from this route. Tests flip labels, corrupt logs/source
bindings, fabricate qualification and claim target execution to ensure rejection.
Stage-specific verifier may refuse stages never reached; never pretend supporting
all labels alone supplies full live-epoch validation.

Adapter PASS requires every section 11 predicate including four complete nonempty
exports, real admissible nonconstant output from both families, actual arithmetic,
all fixtures and eight calibrated mutations, chronology and CI. Search error is
descriptive, never a PASS cutoff. Complete retained inventory != grammar coverage.
search_coverage=NOT_ESTABLISHED. Every scientific promotion axis NOT_ASSESSED;
candidate status GENERATED/FITTED CANDIDATE. No structural recovery, proof,
empirical, significance, replication or predictive-validation promotion.

Until Claude's substantive independent review: PROVISIONAL — INDEPENDENT AUDIT
PENDING. One unmerged PR, Miguel's merge authority, Create a merge commit only.
No squash/rebase; no automatic follow-on, outreach, release or alternate engine.
