# The Number Project — Current Work Order

**Task:** NP-MISSPEC-MARGIN-01  
**Revision:** 1 — prepared 2026-09-15 UTC  
**Destination:** The Number Project Work Mode  
**Purpose:** Misspecification Detection Margin Study  
**Activation:** Prepared at Miguel's request for downstream execution when he launches this work order in The Number Project. This preparation session does not execute the scientific phase.  
**Control intensity:** RIGOROUS at the scientific boundary; affected-boundary validation.

## How this rolling document works

This is the current bounded instruction packet in the [Workflow Management folder](https://drive.google.com/drive/folders/1GSZ6U-0g1_zhWhSdLy4ax55F8vOiktTG). Keep the same Drive file ID when updating it. It replaces repeated long context prompts; it does not replace the Number Project handoff, scientific evidence, or Claude's audit records.

On user launch, read this document completely, confirm task ID and revision, and reconcile the live sources below once. Save the exact consumed bytes and their SHA-256 in the new repository work package before freezing the scientific design. Record the Drive file ID and observed modification/revision metadata when available. Resume an already-started matching task through its existing branch and handoff; do not create a duplicate experiment.

Later edits to the rolling file cannot silently change the consumed instructions, preregistration, or running epoch. Keep the active instruction revision stable during execution. Replace the current task only after completion or explicit user redirection; new task text alone does not authorize unrelated work. The repository retains the consumed instruction snapshot, so this file needs no growing history or status ledger.

The current GPT handoff remains the execution-status surface. GitHub controls repository and merge facts; exact-head CI controls automated checks; committed artifacts control scientific evidence; Claude controls independent findings; Miguel controls authorization and merge. Stale navigation wording yields to newer authoritative evidence. Apply the existing WORKFLOW_GOVERNANCE.md, STANDARDS_REGISTER.md and project controls where relevant; the bounded instructions below are self-contained for this task.

## Controlling baseline and source anchors

- Repository: [mdiaz4052/The-Number-Project](https://github.com/mdiaz4052/The-Number-Project).
- Accepted Benchmark 0 merged base: `c01ecf876969eb28d6426022a6ddadf61f691a06`.
- Suite 1 [PR #56](https://github.com/mdiaz4052/The-Number-Project/pull/56), independently accepted at `e0c018923c799c41870cb1c11eef7d1f6b5741ba`.
- Observed merged main: `0420b0cadc2019b8497556c8bacd9c93bf5e39c1`. Its parents are exactly the accepted Benchmark 0 base and the audited Suite 1 head. Its file tree is identical to that audited head. Recheck live main at launch; preserve relevant ancestry if it has advanced.
- Audited-head CI: [Verify #322, run 34912747416](https://github.com/mdiaz4052/The-Number-Project/actions/runs/34912747416), both jobs successful.
- [Suite 1 scientific decision report at audited head](https://github.com/mdiaz4052/The-Number-Project/blob/e0c018923c799c41870cb1c11eef7d1f6b5741ba/Notes/SymbolicBenchmarkSuite1.md).
- [Claude's full PR #56 audit](https://drive.google.com/file/d/1BnWrPfXqSc5oZM7KD87IcjnilOGPaN_K/view), [DM-093 / FH-20 notes](https://drive.google.com/file/d/1D1-A1JuGQ44W7Z0iGeAcn5JdYuPUjPDx/view), and [current Claude record observed at preparation](https://drive.google.com/file/d/14AXp7ZnxGuhoiMl7UwgmQYFi7JSsG9tb/view). Resolve the current role if that last file has been superseded.
- [Current GPT handoff](https://drive.google.com/file/d/145QAdhOeEC8Ef1j3gLnw8YuI_ej9e0sd/view), to be updated in place during this work.

Claude supported `BENCHMARK_SUITE_1_PASS`, with zero blocking findings, over 24 prospectively frozen synthetic realizations: 12 successful recoverable cases, 12 justified abstentions, eight evaluator-confirmed wrong-grammar cases, and 20 predictively surviving but structurally wrong candidate-class occurrences denied structural credit. This is bounded synthetic evidence, not evidence for a physical hypothesis.

The historical report, PR body and GPT handoff retain pre-audit/pre-merge wording. Reconcile current navigation and add a forward explanatory note within this substantive package; do not rewrite historical scientific artifacts or reinterpret accepted evidence.

## Initial merge-CI check

A one-time read-only automation titled **Check merged-main CI** was created on 2026-09-15, scheduled for **15:27:05 UTC / 11:27:05 America/Detroit**. It checks the exact merge SHA above and reports the result to Miguel. Do not create a duplicate automation. If its outcome is unavailable in the execution context, read GitHub directly.

At preparation, GitHub exposed no Actions run or commit check run for `0420b0c...`. Check Actions and commit checks for that exact SHA, including both Verify jobs. Record success, pending, failure, absence or access uncertainty accurately, with the available run links. Never substitute the PR-head run or identical trees for a merge-head CI result.

This check does not authorize workflow dispatch, repeated benchmark execution, or unrelated test runs. A missing run is an evidence gap, not a failed scientific realization. Continue nondependent preparation while investigating the gap proportionately. Resolve any actual relevant integrity or chronology failure before relying on the affected boundary for new realization generation. Update the existing handoff with the verified state; do not create a CI ledger.

## Scientific decision to close

> With the permitted grammar and decision rule held fixed, how does recognition of family inadequacy change as a controlled departure from that grammar becomes small relative to known observation noise?

Determine the observable detection margin, including where inadequacy goes unrecognized and where adequate-family controls are rejected. Preserve the distinction between approximation, structural recovery, and family inadequacy. The goal is an honest boundary measurement, not a benchmark engineered to reject every wrong-grammar world.

DM-093 supplies the motivation. Suite 1 used the adequacy bound `m * epsilon + delta`, with frozen `m = 2` and `delta = 1e-9`. Its subtle-curvature cell used `epsilon = 1e-4`; its smallest realized family validation error was approximately 0.00251. Judging the same committed residuals at assumed `epsilon = 0.005` removes all four curvature inadequacy verdicts. This counterfactual changes a threshold on fixed observations; it is not a regenerated higher-noise experiment. The roughly 13-fold curvature and 27-fold wrong-power noise headroom are realized diagnostic margins, not universal detection guarantees.

## Workstream A — retrospective margin diagnosis

Use only committed Suite 1 observations, metrics and frozen policy. Do not regenerate worlds, refit coefficients or rerun discovery to produce this diagnosis. Verify the necessary source pins and derive the quantities from existing records.

For each realization, let `r_family` be the smallest raw validation log-RMSE across the exhaustively enumerated eligible candidates with their sealed training-fitted coefficients. Read `m` and `delta` from frozen policy. The fixed-residual boundary is:

`epsilon_critical = (r_family - delta) / m`

For nonnegative assumed epsilon, family inadequacy is declared exactly when `r_family > m * epsilon + delta`; equality counts as adequate under the frozen rule. Handle nonpositive critical values and zero original noise explicitly. Report rank-1 stability separately: its threshold can differ from the all-family minimum.

Produce a concise supplemental table or artifact with original noise, family error, rank-1 error, adequacy bound, critical assumed noise and dimensionless margin where defined. Clearly label every conclusion retrospective. Use the result to explain DM-093 in a forward note without changing old preregistrations, evaluations, raw results, sealed selections or disposition files.

## Workstream B — separately frozen prospective study

Choose and document the smallest defensible design before any new outcomes exist. A suitable starting design is **two law conditions × three noise levels × four fresh realization blocks = 24 datasets**. Retain that size unless an explicit pre-reveal design argument justifies a smaller or different bounded design; do not expand merely to collect more successes.

- Use an adequate monomial control and the same base law with one fixed nonzero curvature departure outside the permitted grammar. Hold curvature strength fixed for the primary noise comparison. Do not also launch a broad grammar, engine or feature search.
- Choose three known noise levels spanning a predicted detectable region, transition region and likely nondetection region. Justify levels analytically or using the disclosed retrospective diagnosis. Freeze numerical settings before generating prospective observations; prior known-world information may inform design but is not outcome-blind evidence.
- Hold the permitted grammar, ranking, fitting and primary adequacy rule fixed. Vary the actual generated noise and supply its correct known scale to the primary diagnostic. Treat changing assumed noise on fixed data as the separate retrospective analysis. Estimating unknown noise is outside this package.
- Preregister block independence, any matching or common random numbers, and the analysis unit. If law conditions/noise levels share inputs or noise streams within a block, call them matched conditions, not 24 independent replicates. Use fresh precommitted random streams across blocks. Prespecify stratified assignment of relevant discrete settings to address FH-20 without rerolls.
- Keep feature measurements exact and the feature set minimal. Retain existing dimensional, provenance and leakage eligibility boundaries. Existing leakage/nuisance stress families need only narrowly affected regression checks; they do not need another prospective campaign here.
- Preserve training-only coefficient fitting, validation-only ranking and pre-reveal adequacy decisions, sealed selections, held-out evaluation, oracle comparison, exact equivalence classification, and interpretation as separate steps.

Freeze the design, generator/evaluator source, environment, metrics, numerical policy and aggregation before outcomes. Publish a cryptographic seed commitment before generation and preserve exact stage chronology, exclusive writes, source pins, private held-out/oracle commitments and true ancestry. Qualify the forward operational path with independent fixtures before the target epoch. Do not reuse the frozen Suite 1 exporter's known field-name failure; consume the explicit-key routing mechanism through a tested forward adapter.

State actual blindness: designer/family knowledge is retained; realized outcomes are unseen at freeze; engine dataflow is isolated; evaluator truth is withheld until sealing; hostile-code isolation is not claimed. Preserve every realized dataset and operational failure. No retries, exclusions, criterion changes or sample additions in response to scientific outcomes.

## Metrics and interpretation to preregister

For each realization and each prespecified condition, retain:

- best-family and rank-1 validation errors, held-out error, known noise and adequacy margin;
- pre-reveal family-adequacy verdict and selected-law/abstention verdict separately;
- approximation status separately from oracle-confirmed exact/equivalent recovery;
- missed inadequacy in deliberately wrong-grammar worlds and unjustified rejection in adequate controls;
- structurally wrong selected candidates, contamination where applicable, and structural-credit assignment;
- bounded counts across independent blocks, including occasional or systematic behavior and nonmonotonic outcomes.

Neither low-noise success nor high-noise nondetection establishes the uniquely correct cause of model failure on real data. The engine measures finite-data inadequacy; the controlled generator identifies grammar misspecification as its cause. A wrong-grammar candidate can be predictively adequate yet structurally wrong and must never receive structural recovery credit. An empty/failed search is a capability problem, not successful recognition.

Define dispositions and any substantive performance requirements before reveal. Distinguish valid completion of the margin study from favorable detector performance; high-noise nondetection can be the scientifically informative result. Use explicit PARTIAL, FAIL, NO_GO or UNRESOLVED when frozen criteria or integrity cannot be met. Do not invent success criteria after observing outcomes, call small designed counts a general false-positive rate, or attach population confidence statements without a supporting sampling design.

## Triggered findings and limits

- **DM-093:** address the presentation gap and quantitative scope in this substantive package before making broader detection claims. Claude owns finding closure.
- **FH-20:** use prospective stratified coverage where coverage supports the new claim; disclose matched dependence.
- **DM-089 / DM-091:** accepted forward repairs; reuse and test only changed boundaries. Retain explicit disposition routing for raw results, operational failures, reconciliations and study-level conclusions.
- **FH-18 / FH-19:** delivered controls; retain applicable seed and live semantic safeguards.
- **DM-090:** keep CPython 3.12 and its receipt semantics pinned. Cross-interpreter reproduction, publication-readiness and environment migration are outside this task.
- **DM-092:** remains deferred on immutable Benchmark 0 code. New scientific quantities must derive from the new frozen policy, with a fixture using deliberately different values so stale literals fail.

Benchmark 0 and Suite 1 remain immutable historical evidence. Preserve Benchmark 0's raw `BENCHMARK_0_FAIL`, accepted `receipt_reconciliation.json`, Suite 1's raw PASS, its post-result operational failure and accepted routing reconciliation. Use the authoritative disposition routes; do not repair historical bytes for cleaner presentation.

Do not introduce PySR, AI Feynman or other external engines. Do not reopen empirical G measurements, external Lean work, unrelated mutation families, or the retired Workflow Management observation period. No new status ledger, observation footer, external outreach, automatic merge or publication is authorized. A public-data readiness screen is a separate project direction, not part of this work order.

## Completion and execution autonomy

After user launch, complete design, implementation and bounded execution autonomously within this scope. Decide routine implementation details without requesting approval. If a genuine ambiguity would require changing frozen scientific criteria, preserve it and report a bounded unresolved or adverse disposition rather than tuning or silently replacing the epoch.

Deliver one coherent unmerged PR with the consumed work-order snapshot, frozen design, source, all realized evidence and retained failures, retrospective supplemental margins, prospective condition-level results, and a concise scientific decision report. Include a standard scientific plot of detection/margin versus noise if it clarifies the transition; do not imply smooth or monotonic behavior unsupported by the observations.

Validate affected code and scientific boundaries, including explicit adequacy-threshold equality/flip behavior and policy-value fixtures. Reuse immutable accepted evidence. Do not manually rerun unrelated suites; preserve the repository's existing required CI gates. Bind the completed report/evidence and CI to the exact final head through the PR and current handoff without circular self-hashes. Any permitted same-epoch replay is reproducibility checking, never a new independent realization.

Update the existing GPT handoff in place with the exact head, CI, disposition, remaining limitations and source links. Prepare a focused Claude review prompt centered on the distinction between retrospective threshold sensitivity and prospective noise variation, noise assumptions, matched design and independent blocks, frozen thresholds/aggregation, structural-credit separation, and provenance. Leave the PR unmerged for Miguel, preserving true-merge history.

The final decision must say what detection boundary was observed and what remains unmeasured. It must not claim unknown-natural-law discovery, arbitrary physical-data performance, a universal false-positive rate, external-engine superiority, or empirical support for any Number Project physical hypothesis.
