# The Number Project — Current Work Order

**Task:** NP-CANDIDATE-EXCHANGE-01  
**Revision:** 1 — prepared 2026-09-16 UTC  
**Title:** Minimal Candidate Exchange Contract  
**Destination:** The Number Project Work Mode / repository implementation context  
**Stage:** SPECIFICATION READY — NOT EXECUTED  
**Authorization:** Miguel authorized preparation on 2026-09-16. Launch this bounded implementation only when he sends it to Number Project execution. Preparation does not install an engine, create a PR, or authorize a merge.  
**Control intensity:** STANDARD software implementation; RIGOROUS at provenance, mathematical meaning, and evidence-promotion boundaries.

## 1. Decision and intended result

> Can two different candidate-output formats and existing internal results enter one evaluator without losing mathematical meaning, provenance, or the limits on what may be claimed?

Build and demonstrate the smallest working exchange boundary. Deliver executable validation and two explicitly mocked adapters, plus a read-only importer for a small fixed set of existing internal selections. A schema document alone is insufficient. Passing means contract integrity within the supported fragment; it does not mean better discovery, compatibility with an actual external engine, or validated real-data performance.

This is package A from the parked **External Discovery Engines and a Derivability Bridge** idea. Only this bounded interface is selected for implementation on launch. Its other proposed activations remain parked. The design choices below are new implementation requirements, not descriptions of capabilities already present.

## 2. Rolling-document and standing handoff rules

Canonical instruction file: [NUMBER_PROJECT_CURRENT_WORK_ORDER.md](https://drive.google.com/file/d/1bJhHoxjzqIopMgASqmUIO71S1SBZP7ly/view), in the [Workflow Management folder](https://drive.google.com/drive/folders/1GSZ6U-0g1_zhWhSdLy4ax55F8vOiktTG). Preserve its Drive ID. This is an instruction packet, not a second status ledger.

On launch, read this revision completely, reconcile live state once, and save the exact consumed bytes, SHA-256, Drive ID, and observed modification/revision metadata in the new repository package. Resolve an already-started matching task through its existing branch and handoff rather than creating a duplicate. Later edits to this rolling document cannot alter the consumed specification or evidence epoch.

**Standing instruction adopted by Miguel on 2026-09-16:** whenever he requests a Number Project status/progress update or presents an audit/merge transition, verify relevant authoritative state and automatically reconcile the existing GPT rolling handoff in place before finishing the response when its navigation is materially stale. This needs no additional approval. Read back the update. If access or writing fails, report the precise limitation; never claim the handoff was updated. If nothing changed, do not rewrite it merely to refresh a date.

**Claude's files remain Claude-owned and may remain administratively stale until his next substantive audit. Do not edit them, trigger a second Claude run, or ask Miguel to relay a bookkeeping-only update.** Preserve Claude's substantive findings, identifiers, and scope; a newer GitHub/CI fact is a navigation reconciliation, not GPT closure of a Claude-owned finding. Route any necessary reconciliation compactly within the next substantive audit, not a separate run.

Apply the same rule at this package's later completion/audit/merge transitions. Keep one compact GPT handoff. No housekeeping PR, duplicate audit row, new status ledger, or retired Workflow Management observation footer.

## 3. Verified baseline and source map

Preparation checked live state on 2026-09-16. GitHub is authoritative for repository facts; CI for executed checks; committed artifacts for scientific evidence; Claude for independent findings; Miguel for authorization and merge.

| Anchor | State / use |
|---|---|
| Repository | [mdiaz4052/The-Number-Project](https://github.com/mdiaz4052/The-Number-Project) |
| Accepted main | `c7229812f4d88c11f958f317b67bb51f7ba0c384` — true merge of #57 |
| Merge parents | `0420b0cadc2019b8497556c8bacd9c93bf5e39c1` and `7405d07e717fbe1e84d3c1afb5b7f737e86c6103` |
| Independent #57 disposition | MERGE — zero blocking; `MISSPEC_MARGIN_1_COMPLETE` supported within the recorded bounded scope |
| Actual merged-main CI | [Verify #326, run 34995766997](https://github.com/mdiaz4052/The-Number-Project/actions/runs/34995766997), push event, success at `c7229812…`; Python and Lean jobs passed |
| Open PRs at preparation | None |
| GPT handoff | [gpt_RollingAuditHandoff.md](https://drive.google.com/file/d/145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd/view) |
| Claude current role at preparation | [claude_Current.md](https://drive.google.com/file/d/1oqEBbREAbbGhUftUc6fPKAe458Wk3hbq/view); resolve the role if superseded |
| Relevant findings | [DM-094–096 / FH-21, including DM-093 partial closure](https://drive.google.com/file/d/19Fd4pKH_BiPQRTA1CzisqY1Psqoz2ELw/view) |
| Conceptual source | [External Discovery Engines and a Derivability Bridge](https://drive.google.com/file/d/1T1ZTXJtidnt6CKau_WgzOJ-LV4d4rU-Q/view), especially Candidate Exchange Contract and modular architecture |

Recheck main on launch. If it advanced compatibly, use the actual base and retain the accepted ancestry. A material concurrent implementation or incompatible change requires a bounded stop/reconciliation, not blind execution against a stale base.

The prior work order, NP-MISSPEC-MARGIN-01 revision 1, is completed and preserved at `Experiments/SymbolicDiscovery/MisspecificationMargin1/work_order.r1.md` in the accepted repository, SHA-256 `57b2270673e179f183103eb3ab8aceaaa26704cf49da039d9aaeaa0a17001cab`. Replacing this rolling instruction does not rewrite that snapshot.

Apply `WORKFLOW_GOVERNANCE.md`, the existing Number Project instructions, and `STANDARDS_REGISTER.md` at their declared scopes. Reuse adopted dimensional/provenance/uncertainty distinctions without claiming whole-standard conformance. This package declares an internal development contract, not a stable public API or a new ecosystem-wide standard.

### Existing surfaces to reuse, not replace

At accepted main, `Discovery/dimensions.py` supplies exact rational SI dimension vectors and explicitly does **not** perform unit conversion. `Discovery/symbolic_benchmark_engine.py` already provides metadata-first eligibility, target-path reachability, monomial equivalence grouping, canonical JSON/digests, and candidate records. `Discovery/symbolic_suite_engine.py` already separates family adequacy from approximation and leaves structural claims false. Inspect these and their directly used dependency helpers before adding parallel machinery.

The current monomial record contains `representative`, `expanded`, `class_id`, `members`, `log_coefficient`, `coefficient`, recorded errors, ranks, and evidence labels. Preserve rather than reinterpret those fields on import. Avoid importing executable campaign runners merely to read JSON.

## 4. In scope and explicit exclusions

Implement one versioned internal exchange contract, bounded expression representation, shared trusted validator/evaluator, two mock-format adapters, a read-only historical importer, deterministic conformance fixtures, focused mutation checks, and one concise decision report. Prefer existing dependencies and standard-library facilities.

Do **not** install or run PySR, PhySO, AI Feynman, SINDy, an LLM formula generator, or any other external discovery engine. Do not claim their formats are supported merely because a mock resembles them. Do not build a plug-in platform, user interface, general CAS, automatic unit-conversion service, full uncertainty engine, optimizer, new search grammar for historical engines, candidate-to-Lean bridge, or public stable API.

No new hidden-law realization, reranking/refitting of historical selections, benchmark rerun, estimated-noise study, comparative engine score, public release, tag, paper, or external-replication claim. No empirical G work, HUST/AAF reopening, external Lean execution, outreach, or automatically authorized follow-on package.

## 5. Contract: four small, linked records

Use one documented version namespace, for example `tnp-candidate-exchange/1`. Record schemas are distinct; do not compare different envelope names as though they must be identical. An explicit mapping defines which semantic fields must agree across record types. Unknown versions and unknown semantic fields fail closed; separately namespaced opaque metadata is never interpreted as authority.

### A. Research-object manifest — trusted upstream input

Capture target and feature identities; quantity roles; exact dimensions; the numeric unit convention; declared domains; direct derivation/provenance edges; source references; train/validation and withheld-data roles; uncertainty/dependence status; and the allowed expression fragment. Reuse existing project vocabulary and dimension order. Include a manifest digest in downstream records.

The manifest is controlled by the project, not supplied as an authoritative replacement by a generator. A generator may reference it but cannot rewrite feature provenance, units, splits, or eligibility. Any metadata inside generator output is untrusted and must agree with the trusted manifest or be rejected/quarantined.

For v1, evaluable quantities use explicitly declared coherent-SI numeric values, or dimensionless numbers, with no implicit scaling or offsets. Unknown or noncanonical unit encodings are unsupported rather than guessed. Preserve the distinction between a dimension vector and a unit convention; a matching dimension does not verify a claimed numeric scale. An internal historical adapter may bind its convention to the pinned synthetic design, explicitly as a declared convention, not as metrological certification.

Represent uncertainty as `exact_by_design`, `known_declared`, `unknown`, or `not_assessed`, with source/parameter references where available. Do not convert unknown uncertainty or covariance into zero or independence. This package transports the declaration; it does not propagate or estimate uncertainty. Likewise, provenance checking establishes consistency with the registered graph, not that undeclared real-world dependencies are impossible.

### B. Generator-run receipt — proposal provenance, never scientific authority

Record generator identity and kind (`mock`, `internal_record_import`, later extensible); adapter source identity; input/manifest/configuration digests; original result location and digest; available seed/environment/budget/stopping metadata; and output inventory. Distinguish recorded facts from `unknown` or `not_applicable`. Never fabricate historical metadata to fill a required-looking field.

Keep training-target exposure separate from prohibited target-derived features. A generator may legitimately fit training responses while being forbidden from using answer-derived inputs, held-out observations, oracle truth, or downstream evidence decisions. Imported historical records are **retrospective, outcome-known contract fixtures**, not fresh blind runs.

Record candidate count, ordered candidate IDs, adapter rejections/unsupported items, and raw-source bindings. Every input item must have a retained output or explicit rejection record; no silent loss of duplicates, invalid expressions, lower-ranked candidates, or failed runs. Preserve the frontier or ranking actually available without inventing a full search history. Empty output and operational failure are distinct and neither earns abstention/detection credit.

### C. Candidate record — raw meaning preserved

Retain raw bytes or a pinned raw source plus an exact locator, a bounded structured expression, parameter values/units/roles, original engine diagnostics, domain restrictions, source ancestry, and declared evidence claims as untrusted metadata. Numerical constants remain exact rationals or explicitly approximate finite values; do not snap decimal fits to recognized physical constants. Record serialization semantics deterministically.

A minimal v1 expression fragment is real scalar `literal`, `variable`, `parameter`, `add`, `multiply`, `divide`, integer `power`, `exp`, and natural `log`. The executor may choose field names but must implement/document every listed operation. Subtraction/negation may be encoded through addition and multiplication by −1. Noninteger powers, complex values, piecewise functions, arbitrary calls, and automatic symbolic identities outside the fragment return `UNSUPPORTED`, not invented translations.

Use structured JSON nodes, not executable text. A display expression is inert. No `eval`, arbitrary import, pickle, shell interpretation, or dynamically executed generator payload. Require exact field/type checks, reject duplicate JSON keys and nonfinite numbers, and bound input bytes, nesting, node count, and collection sizes before expensive work. Freeze concrete limits and boundary tests in the implementation contract.

Integer powers operate on real values with negative-power denominator exclusions. Define the v1 `0^0` convention explicitly as **domain-invalid**, rather than inheriting a language-library default. Boolean values must not pass as numeric parameters or integer exponents.

### D. Evaluation/evidence card — produced by the trusted side

Keep separate axes: contract integrity, provenance eligibility, dimensional admissibility, domain validity, representation/equivalence status, numerical checks on named fixture points, original reported predictive metrics, and scientific evidence status.

The generator cannot award or modify `STRUCTURALLY_RECOVERED`, empirical support, significance, formal proof, independent replication, family adequacy, or trusted eligibility. Preserved historical metrics/dispositions remain **attributed source evidence**, not newly evaluated claims. A contract PASS must leave new scientific promotion `NOT_ASSESSED` and candidate status `GENERATED/FITTED CANDIDATE`.

Evidence is not one automatic ladder: dimensional validity, predictive fit, formal derivability, and empirical support are different questions. Every rejection or unsupported result needs a machine-readable reason and a short human explanation. No single score should hide an unresolved axis.

## 6. Mathematical and provenance invariants

**Dimensions.** Addition requires equal operand dimensions; multiplication/division combine them; integer powers scale them. `exp` and `log` accept dimensionless arguments only. The expression result must match the target dimension, including parameter dimensions. Use existing exact dimension operations; never decide dimensions from numerical sample values.

**Domains.** Derive definedness conditions from the original expression before simplification. Division requires a nonzero denominator; log requires a positive argument. Preserve all subexpression restrictions, even when a zero multiplier or cancellation could hide them. An undefined or nonfinite result must not become a zero, an omitted row, or a successful evaluation.

**Equivalence.** Implement conservative canonicalization for factor/sum order, exact rational constants, and the supported monomial fragment. Retain domains and parameter roles. Prove only identities covered by explicit rules; unresolved comparisons stay `NOT_ESTABLISHED`, not false or equivalent by default. Sample agreement is not proof of symbolic equivalence. A structural-family identifier must not collapse different fitted parameter values into one numerically identical candidate.

**Dependency identity.** Run target-reachability/eligibility on the full registered provenance graph before algebraic simplification, coefficient zeroing, or alias collapse. A canceled dependency path remains a path. Reject cycles, missing nodes, invalid alias definitions, and attempts to reclassify a derived feature as observed through an adapter.

A legitimate training-fitted scalar parameter is not itself a prohibited per-row target feature. Its allowed fitting provenance must be explicit, pinned to the original training context, and incapable of carrying validation/held-out answers as a vector or hidden callable. This package performs no fitting.

## 7. Minimal executable demonstration

### Two deliberately different mock formats

Use one mock structured-tree format and one mock postfix/token-list format, both explicitly labelled mocks. Both adapters must translate into the common record and exercise the shared trusted path. Include at least three paired lawful expressions covering a monomial, a dimensionally valid sum, and a dimensionless logarithm or exponential inside a valid physical expression. Paired representations should agree on normalized semantics, eligibility, domain restrictions, and independently calculated fixture values despite different order/shape/identifiers.

Do not prove adapter correctness by comparing two outputs produced by the same buggy helper. Expected dimensions, domains, dependency outcomes, and elementary fixture values must have an independently specified basis. The evaluator must not call the mock generator's evaluator or accept its cached values as truth. This is implementation-level separation, not hostile-code sandboxing or independent-model review.

### Small fixed historical import

Import complete rankings from exactly two accepted Margin1 selections: `b01-adequate-n1` and `b01-curved-n2`, using the corresponding files under `Experiments/SymbolicDiscovery/MisspecificationMargin1/selection/` at accepted head `7405d07e717fbe1e84d3c1afb5b7f737e86c6103`. The filenames were verified during preparation: `b01-adequate-n1.json` (Git blob `7937d9f84d56e2c12a39cbe2e6ee44a21247b338`) and `b01-curved-n2.json` (Git blob `6e3124c349e746d994d9a860ecd25e193653898f`). The ranking is under the `discovery.ranking` envelope. Confirm the pinned bindings on launch; do not substitute other datasets.

Preserve all five recorded classes per selected dataset, their members, raw order, coefficients, log coefficients, diagnostics, and evidence labels. This is fixed compatibility coverage, not a new scientific sample or an engine comparison. Bind the manifest to the pinned public design/input metadata and the selection's original input digest. Use source references instead of copying large input/held-out/oracle files.

Exercise conversion and numerical evaluation on a few fixed positive fixture points. Do not rerun discovery, regenerate observations, refit coefficients, recompute the old detection campaign, or promote imported outcomes. The original engine computes predictions using `log_coefficient` plus log-monomial terms, while also storing `coefficient = exp(log_coefficient)`: preserve both values and the original numerical convention. Document floating-point tolerance for checking the new expression evaluator against that convention; do not demand bit identity between different arithmetic routes or silently change old numbers to obtain it.

The new report should carry one forward clarification of DM-094: the seven accepted Margin1 stable-but-incomplete selections matched the true base monomial and missed only the added curvature factor. Attribute this observation to Claude's existing audit; do not rerun those seven cases merely to restate it. The two imported selections cannot be portrayed as evidence for a new seven-case result.

## 8. Required conformance cases and validation

The following is the minimum coverage, not a request for a large benchmark. Combine related tests when clear. Fixture choices are visible by design; report `outcome_blind=false` and `evidence_mode=deterministic_contract_conformance`.

| Boundary | Required behavior |
|---|---|
| Equivalent lawful mock outputs | Same supported semantic class, domain and fixture values; raw format identities retained |
| Dimensions versus units | Accept a correctly declared SI record; reject incompatible addition, dimensionful log/exp, missing scale convention, and parameter-dimension mismatch |
| Domain loss | `x/x` at nonzero x behaves as 1 but remains invalid at x=0; unrestricted 1 is not globally the same domain. Retain `log(x)` and denominator restrictions after cancellation or multiplication by zero |
| Target leakage | Direct, transitive, canceled and zero-weighted target-derived routes fail eligibility; a genuine training-fitted scalar remains allowed under its declared fitting role |
| Metadata laundering | Reject mismatched trusted-manifest digest, relabeled derived inputs, incomplete/cyclic graphs, or raw expression/normalized-record mismatches |
| Sample agreement versus identity | Two expressions agreeing at chosen sample points must not receive unsupported symbolic-equivalence credit |
| Parameter identity | Different fitted values may share a structural class but are not the same evaluated model; exact and approximate constants remain distinct |
| Evidence escalation | Forged eligibility, structural recovery, empirical support or significance cannot become trusted card fields |
| Unsupported/hostile payloads | Unknown operator/version, noninteger power, duplicate key, unknown symbol, boolean coefficient, malformed tree, excessive depth/size, code-like display text, NaN/Infinity and numeric overflow are explicitly handled without execution or silent repair |
| Candidate inventory | Reordering/duplication is preserved or explicitly mapped; dropping an item or altering raw bindings is detected; empty output differs from run failure |
| Historical importer | Both fixed source rankings survive with source pins, values, ranks and labels; no generator, fitting, held-out or oracle call is needed |
| Record envelopes and routing | Distinct schemas validate separately; wrong disposition paths, extra semantic fields and substituted summaries are rejected |

Add a bounded mutation set, normally six to eight production mutations, covering domain erasure, transitive/canceled leakage bypass, dimension bypass, forged evidence promotion, raw-binding tampering, and candidate loss. Expected semantic assertions—not syntax/import/runtime/provenance failures—must kill the designated mutants. Retain a surviving baseline and a semantically equivalent control. Recalibrate only a diagnosed failed mutant, retaining its failed evidence rather than rerunning all unchanged cases.

Use one coherent final affected-boundary validation on the completed source/evidence epoch. Preserve the repository's existing Python/Lean CI jobs and all inherited guards. Add at most one cheap read-only conformance/record guard if existing test discovery alone cannot bind the committed outputs. Do not refactor `verify.yml`, change Python 3.12, dispatch old workflows, or manually reproduce unrelated green CI. Reuse accepted historical evidence and leave all old benchmark files byte-identical.

## 9. Source, freeze and operational evidence

This is a deterministic interface package, not a newly blinded experiment. Do not create random seeds, private truth reveals, or a new statistical preregistration ceremony. Preserve the established chronology control where it applies: snapshot this instruction, commit a sole-file contract/acceptance freeze, then create the draft PR/server anchor before implementing the new trust-boundary evaluator and conformance run. Known fixtures and expected outcomes are disclosed, never presented as unseen scientific evidence.

Pin the implementation, fixtures, source imports, numerical comparison policy and environment before emitting the final conformance report. Results bind the source snapshot; the final PR/handoff binds the completed evidence head and CI without circular self-hashes. A read-only guard must fail on changed semantics/evidence, not regenerate expected results to make a comparison pass.

Ordinary software development can correct bugs in forward commits. Preserve any published failed conformance epoch and its source/inputs; never overwrite it as though the first attempt passed. A changed scientific acceptance requirement requires a disclosed forward revision, not retroactive editing of frozen criteria. Do not use a contract correction to rewrite Benchmark 0, Suite 1 or Margin1.

Suggested additive layout, adjustable before freeze to existing conventions:

- `Discovery/candidate_exchange*.py` for the minimal validator, safe evaluator and adapters;
- one focused test module and small explicit fixtures;
- a compact versioned contract, source/input bindings and conformance report under a new package directory;
- `Notes/CandidateExchange1.md` for the bounded decision, limitations, correct invocation, and focused audit prompt.

Use one authoritative package disposition route. Avoid duplicate JSON ledgers, multiple schema engines, separate services, and copied campaign datasets. A README-level pointer may direct readers away from the preserved broken Margin1 checker to `python3.12 -m Discovery.symbolic_margin_verifier check --replay`; do not run it merely to add the pointer and do not modify its frozen predecessor.

## 10. Findings applied to this scope

- **DM-093:** retain the scope half. No estimated-noise rule, population rate, or comparative misspecification result is produced. The new contract must not launder inherited adequacy labels into broader capability.
- **DM-094:** provide the attributed forward explanation above, without renaming frozen fields, editing old Notes/evidence, or closing Claude's ID.
- **DM-095:** document the correct forward reproduction route if referring to Margin1. No release/replication package is created here; frozen source remains unchanged.
- **DM-096:** current merge `c7229812…` has successful push CI #326. Earlier missing runs remain historical; their cause is not established. Supply this evidence during the next substantive audit for Claude-owned reconciliation. No standalone audit/configuration repair follows automatically.
- **DM-090 / DM-092:** retain CPython 3.12; do not change old threshold surfaces or claim portability. Neither finding is silently closed.
- **FH-21:** any new completeness expectation must derive from the declared contract, dimensions and independently specified fixtures, not a transplanted `'t:-2|x:1'` literal. Full search-family enumeration is not this package's claim.
- **E-001 and other unrelated items:** remain scoped to their own boundaries. No HUST or unrelated audit work is required.

## 11. Stop conditions, disposition and review

Use `CANDIDATE_EXCHANGE_1_PASS` only if both mocks, both full historical rankings, every required invariant, and all calibrated mutation assertions are supported at the final exact head. PASS means a bounded internal contract works; it is not an external-engine or scientific-performance endorsement.

Use `CANDIDATE_EXCHANGE_1_PARTIAL` for a useful demonstrable subset with missing required non-integrity coverage; `CANDIDATE_EXCHANGE_1_FAIL` for demonstrated invariant violations; and `CANDIDATE_EXCHANGE_1_NO_GO` or `UNRESOLVED` when source access, incompatible baseline, or bounded implementation constraints prevent a credible decision. No package can claim PASS with an unresolved leakage/domain/evidence-promotion defect.

Stop rather than silently expand into arbitrary CAS equivalence, additional engines, general unit conversions, a full uncertainty model, or historical re-execution. Record exactly what a later package would have to supply. Unsupported inputs should be safely rejected by the running interface, not crash the package or count as discoveries.

Deliver one coherent PR, with exact-head CI and a compact report. Until independent review, retain **PROVISIONAL — INDEPENDENT AUDIT PENDING** on new trust-boundary claims. Independent review is warranted once for this new interface's semantic boundaries, not for the preceding handoff reconciliation.

Focused Claude review: inspect trusted-manifest versus generator ownership; direct/transitive/canceled provenance; dimensions versus unit declarations; parameter-fitting roles; domain preservation under normalization; proof versus numeric agreement; complete candidate inventory; raw/normalized/source bindings; unsupported/empty/failed distinctions; inability to self-award evidence; and the exact limits of the mock and historical demonstration. Reuse exact-head CI and unchanged accepted findings. Challenge concrete unresolved issues with targeted checks only.

Claude owns finding dispositions. GPT updates its own handoff and prepares this substantive audit prompt; it does not rewrite Claude's records. Miguel retains merge authority. **Create a merge commit only; never squash or rebase away accepted ancestry or the new freeze/evidence chain.** After merge, a later requested status update automatically reconciles the GPT handoff against actual merge and CI facts, without an extra Claude run.

## 12. Subsequent direction — not authorized by this package

After this contract is independently accepted and merged, consider one separately pinned static-function generator adapter on newly frozen unseen data. Separately specify estimated-noise reasoning before any realistic misspecification-detection claim. Neither follow-on starts automatically. The present package ends with its bounded interface decision and reconciled GPT navigation.
