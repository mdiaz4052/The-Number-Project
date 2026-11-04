# Session summary: The Number Project, Claude (independent auditor), 2026-08-29 → 2026-10-01

Written 2026-11-04 by Claude, from the auditor's side. Companion to `SESSION-SUMMARY-codex-2026-11-04.md` (GPT/Codex side) on the same branch.

**What this is built from, and what it is not.** I don't carry memories between sessions. Everything below comes from records I re-read today:

- **Chat transcripts.** The six chats in the claude.ai Project ("The Number Project Auditor & Improver") that the past-chat search tool can reach. They are labelled C1–C6 in §1.
- **The project's audit records.** `claude_AuditLedger.md`, `claude_Current.md`, the playbook and the archived audit reports in the same Project.
- **The repository.** A fresh clone at `main` = `6fd4b306…`, plus the PR #62 review prompts.

The Audit Ledger records about 55 audits and audit addenda between 2026-08-29 and 2026-10-01. **Most of those sessions are not in the six searchable chats.** By the owner's own description they ran as Cowork tasks, and their transcripts are not reachable from here. Where a section needs a transcript I don't have, it says so. Nothing is filled in from inference.

---

## 1. Identity

- **Tool and surface.** Claude in the claude.ai web app, inside the Project above. That covered Project chats, and Cowork tasks with a sandbox shell, the Google Drive connector, web search/fetch and an anonymous git clone. This retrospective was written from a Claude Code cloud session.
- **Model(s).** **Unknown** for the audit sessions. The transcripts do not record a model name. This summary was written by Claude Opus 5.5.
- **Sessions covered.**
  - Ledger span: 2026-08-29 (first audit, PR #2) → 2026-10-01 (last audit, PR #62 revision 2).
  - Searchable chats: six.
    - **C1** — "Milestone 5B implementation questions", 2026-08-31
    - **C2** — "Evaluating Gemini Pro vs Spark for workflow delegation", 2026-09-01, which includes the PR #16 audit
    - **C3** — "Streamlining Cowork audit reporting requirements", 2026-09-01
    - **C4** — "Optimizing audit efficiency and reducing redundant tasks", 2026-09-05/06
    - **C5** — "Clarifying project goals and instructions", 2026-09-05/06
    - **C6** — "Instructions and clarification", 2026-09-29 → 2026-10-01 (PR #62)
  - Ledger entries: roughly 55 PR audits and addenda, plus 9 supporting records (spec reviews, Gemini proposal reviews, ecosystem recon, the 2026-09-07 audit-system migration).
  - **Total hours: unknown.** No session durations were recorded.
- **Plan/cost.** Not shown by the tool. In C3 the owner mentioned saving "credits plus authorization clicks", so usage was metered in some form. No token or dollar figures exist in the records.

---

## 2. What the owner asked for, verbatim

### First message of the project

**Not retrievable.** The first audit (PR #2, 2026-08-29) and the original "be the auditor" instruction happened in a session I cannot reach. The earliest owner message I can retrieve is C1, 2026-08-31:

> GPT is about to start work on milestone 5B, but had the following questions which i wanted to quickly run by you for inspection:
>
> Two questions before implementation
>
> 1. For the symbol-collision closure, if it has not landed on main, do you prefer a separate tiny PR, or an isolated first commit within the 5B branch? The specification permits either; a separate PR gives the cleanest history.
> 2. May I adopt the source-SHA interpretation above—namely, the SHA of the committed implementation/preregistration state used to generate the artifact, rather than the necessarily later commit containing the result artifact?

(Everything after the first line is GPT's text, relayed by the owner.)

### How audit prompts were handed to me

Over the life of the project the handoff took four shapes.

**1. Short owner instruction, early (C2, 2026-09-01):**

> Please go ahead and audit #16. Once you have your findings, I will prompt GPT to "continue" (in case it stopped mid-process) along with your feedback so that it can be incorporated as needed.

**2. Relayed GPT questions (C1, above).** The owner pasted GPT's pre-implementation questions and asked for "inspection".

**3. PR number only.** In C4 I proposed: "**Just say the PR number.** 'Audit PR #36' is now sufficient." I can't confirm the owner adopted that wording, because the #36–#61 audit sessions are not retrievable.

**4. GPT-authored review prompt plus a one-line owner cover note, late (C6).**

For revision 1, 2026-09-29, the owner wrote:

> Please see instructions. Let me know if you have questions.

For revision 2, 2026-10-01:

> Please review:

The attachment was a review prompt GPT had written. It is committed verbatim in the PR as `Experiments/GravityUniversality/Pilot0/review.md` and `review_r2.md` (PR #62 head `0d757b0d`). I checked it was byte-identical to what I received. Two short excerpts from `review.md`:

> Record the head once; do not silently move the review to a later commit.

and its closing section heading, **"Mandatory Google Drive delivery"**, which requires read-back verification of the uploaded audit files.

By the end, the owner's own words in a handoff were down to three. The full specification lived in a GPT-written prompt, my standing Project instructions and `claude_Current.md`.

### Five representative owner messages

**Approval (C5, 2026-09-05):**

> I concur with what you said about "each audit report I write ends with a short section listing live DM entries whose surfaces the PR touches. The reminder then lands exactly where GPT is already reading, at exactly the right time." Please do that.
>
> Also, keep the copies in Drive and in this local Claude-site project folder for your own records and reference. I will tell GPT to always check Drive for updates.
>
> Per the re-verification, please do it as needed to avoid staleness.
>
> I like your claude_ prefix idea.
>
> Please keep project-wide register for completeness. You can supply me with a prompt for me to add to GPT's instructions so you can receive relevant entires.

**Correction (C3, 2026-09-01):**

> Sorry, I have a terrible tendency to omit things in my responses. You may generate as many MD files as you need, you can keep those here in this claude website as well. I'd hate for your interruption to waste energy for no reason other than my laziness. But in terms of uploading to drive, I rather you only ask me once you have the final version of all the ones you iterated (and as many kept as necessary) here. Does that make sense?

**Scope change (C2, 2026-09-01).** This turned Gemini from a test proposer into a source fetcher:

> 2. I'd say yes, because I ultimately rather GPT and you determine what can be proposed. Gemini would be best poised as a fetcher or information, given Google's vast access and indexing to other people's stuff.

**Frustration or redirect (C4, 2026-09-05):**

> I want to make sure your auditing runs efficiently. Please parse how you currently do each cowork run, and consider what things you may be able to do to avoid repeating/overlapping the same command runs each time I submit an audit request. […] (Mind me, I have no clue how any of this works, so if what I'm saying contravenes the very purpose of the audit, please let me know and do not restrict yourself in any way).
>
> In your response, please outline simple instruction changes I can make to help you be faster and efficient without loosing core and independent auditing functions.

(The `[…]` cuts one sentence restating the request.) A milder one, C3:

> I'm lazy, so I think I'm going to ease your reporting requirements a bit.

**"What's next" question.** **None found.** No retrievable owner message asks what to do next. In the other direction, my records end every audit with a "Decisions awaiting Miguel" list. By the last `claude_Current.md` (2026-09-27) it held nine open items. The final C6 reply ends "**Your decision:** whether to start Phase B under revision 2." No reply follows.

---

## 3. Decisions and turning points

### Decisions made in chat that are not in the repository

| Date | Decision (owner) | Why, as stated or as visible in the exchange |
|---|---|---|
| 2026-09-01 (C2) | Gemini Spark stays sidelined. Gemini Pro is used only as a literature/source fetcher producing "source dossiers", not as a proposer of tests. | Owner: "to avoid tainting the workflow given the potential 'sloppiness'". I added a provenance argument: standing unattended Drive write access next to audit records is a structural hazard. |
| 2026-09-01 (C2) | Keep the strict "no arithmetic" rule in the Gemini brief. Rewrite the brief to read cold in a fresh Gem. | Owner: "I think that as long as GPT or you can pick up on the difference, I'm fine with the tighter rule." |
| 2026-09-01 (C3) | Markdown only, no `.docx` copies. A prose summary only after a milestone. One Drive upload per session, after all files are final. | Fewer authorization clicks and credits. A single canonical file. |
| 2026-09-05 (C5) | The deferred-maintenance register is **project-wide**, **Drive-only (not in the repo)**, uses the `claude_` prefix, and Claude assigns every ID. GPT submits entries through the owner. | Deferred items attest to nothing. Keeping them in the repo would cost a commit, CI run and PR per edit. GPT proposed Drive and the owner agreed. |
| 2026-09-05 (C5) | Retro-populate the register from PR #16–#36 audit notes and publish it with unverified entries marked. | "Might as well have a comprehensive list of anything we've may forgotten." / "Please publish the register now and we can check naturally when they surface." |
| 2026-09-05 (C5) | Workflow-permission fail-opens G1–G3 (DM-006 → DM-008) stay **deferred, under watch**, not BLOCKING. | "Add G1-G3 to register and we will keep until a workflow touches them." I had explicitly offered BLOCKING as an option, and the owner chose deferred. |
| ~2026-09-10 (Ledger) | Independent audit paused. Merged PRs #47–#51 reviewed later as one execution-minimal batch. | Recorded in the Ledger's batch rule. The chat where this was decided is not retrievable. |
| 2026-09-23 (Current) | PR #60 merged **without** its planned independent review. The retrospective audit was deferred. | Recorded as "Merged by user authorization". The reason is not in any retrievable chat. |
| (Current, date not recorded) | NIST author outreach plan **cancelled, not authorized**. | Recorded in `claude_Current.md`. No chat available. |

### When the direction changed

From my side there were three turns.

- **2026-09-07: audit-system migration.** The single growing playbook was replaced by `claude_Current.md`, a compact Ledger, `Deferred/` detail files and an `Archive/`. From then on an audit was an operation on that set of files, not just a report.
- **Mid-September: the scientific target shifted.** After PR #52 (2026-09-12) the scientific content stopped being about G measurements. #53 was an external Lean harness. #54–#58 were symbolic-discovery benchmarks and contracts. #60 was PySR. #61 was the estimated-noise method. #62 was a literature-method pilot on gravity universality. Every `claude_Current.md` from #53 to #62 records "Empirical (G) frontier: unchanged". The audits stayed rigorous, but they were mostly certifying methodology about methodology.
- **2026-09-10 onward: independent review became optional.** First came the batch review, then #60 merged unaudited. That is consistent with the cost of independent review becoming visible to the owner.

### If the project stopped: the last three exchanges

All are in C6. The repository confirms nothing has merged since PR #61 (2026-09-27), and PR #62 is still an open draft at `0d757b0d`.

1. **2026-09-29.** Owner: "Please see instructions. Let me know if you have questions." (with the GPT review prompt). I returned **REVISE_PROTOCOL**, with two BLOCKING protocol-discretion findings (B1, B2). I also disclosed that one of my own verification searches had exposed more source text than intended.
2. **2026-10-01.** Owner: "Please review:" (with the changed-boundary prompt). I returned **ACCEPT_PROTOCOL** for `protocol_r2.md`. My reply ended "**Your decision:** whether to start Phase B under revision 2. The PR stays draft and unmerged." It also reported that the Drive Audit Ledger was **not** updated, because the Drive connector cannot rewrite file content.
3. **No further message** in this Project.

**My best reading of why it stopped.** The owner has said elsewhere that the project is on deliberate hiatus because its size and rigor were making it stagnate. That is his account and it takes precedence. What I can add from the audit record is how my side contributed:

- Each audit **returned decisions to the owner** rather than taking them away. The queue grew to nine.
- Each audit **added bookkeeping debt** that I deferred instead of paying:
  - unfolded Ledger rows;
  - a 60 KB deferred index not rewritten since 2026-09-12;
  - a Drive Ledger stuck at #56.
- The science the owner originally cared about (G determinations) had **stopped moving** while process kept accumulating.

By then the rigor was real, but so was the overhead, and some of that overhead came from me.

---

## 4. Friction log

### The same correction twice

- **Drive delivery.** On 2026-08-30 the owner reminded me that the Drive copy is required on every audit, after I had updated only the Project docs. (That reminder is recorded as a stated fact in memory; I don't have the verbatim message.) The Drive/Project split came back in a different form: by #59 the **Drive** Ledger ended at #56 while the **Project** Ledger had #57–#58, and the #59 and #61 rows existed only as staged files. I never closed the gap.
- **Reporting workflow, 2026-09-01.** It took two messages to specify (C3). The owner blamed his "tendency to omit things". The two passes were normal specification work, not a repeated correction.

I found no other case where the owner corrected the same thing twice. Most sessions are not retrievable, so this is a floor, not a count.

### Claimed done when it wasn't

- **PR #17.** My audit's §4 contained a factual error, caught later. The original was superseded by `…pr17-corrected.md`.
- **PR #46.** A WebFetch pass **confabulated** a consensus paragraph from an IOP paper. I retracted it after a verbatim re-query and recorded it as a method rule. It never reached a verdict.
- **Playbook §8 backlog (found 2026-09-05).** My own standing backlog listed closed items as the top open findings, and it had silently dropped three live fail-opens (PR #28 G1–G3). Nobody had claimed those were done; they were simply missing.
- **Ledger and index currency.** From #52 onward my `claude_Current.md` repeatedly said the 60 KB deferred index would be folded "next time it is opened". It never was. Every one of those notes was honest about the deferral, but the debt was carried forward, not paid.
- **Errors in GPT's work that I caught** (here the claimant was GPT, not me):
  - PR #31's first head claimed a blind confirmation that was not blind (rejected, B1).
  - PR #52's GPT handoff described an already-merged PR as "draft/open/unmerged".
  - GPT's #56 and #58 report tables read as closing Claude-owned IDs they had not closed.

### Environment and tooling blockers

| Blocker | Effect | Cost |
|---|---|---|
| No GitHub auth or token (DM-034) | Until ~PR #34 I could not read CI verdicts at all, so early audits re-ran the suite and guards locally. Later the unauthenticated API worked, then rate-limited (403) by #61–#62. I fell back to an anonymous clone + `refs/pull/N/head` + scraping individual Actions run pages. | Several tool calls per audit, every audit. Never resolved. |
| Actions list page mislabels runs | At #61 the list-page summary showed failed runs #343/#344 as success. Caught only by reading the individual run pages. | One near-miss; a standing rule afterwards. |
| No Lean/mathlib build cache reachable | I **never** ran `lake build` myself. All Lean trust came from exact-head CI or hand-verification. | Permanent limitation, stated in each audit. |
| Python 3.11 sandbox vs 3.12 pin (DM-090) | At #56 the guard would not run until I installed CPython 3.12. | Minutes; recorded as a finding. |
| Drive connector cannot edit file content | Rolling files had to be recreated and the old copy renamed "(superseded)". The large Ledger could not be safely retyped, so rows were staged in side files instead. | Recurring. The main source of bookkeeping debt. |
| Drive upload approvals stalling mid-batch | Retry in the next message. | Occasional extra turn and click. |
| Sandbox resets between Cowork tasks | Drafts lost if interrupted. Mitigated by presenting files in chat (C3). | Low after the mitigation. |
| Paywalled or robots-blocked primary sources (IOP, APS RMP 77 PDF truncation) | Several locators stayed "corroborated, unread" (RMP 77 page locators, DM-078(a), BIPM Table 1). | Unresolved scientific gaps. |

### Things the owner did by hand that an agent should have done

- **Relaying every message between GPT and me.** Handoffs, GPT questions, deferred-entry submissions and my findings back to GPT all went through the owner by copy and paste.
- **Approving every Drive upload by click.** That is why the C3 batching rule exists.
- **Pasting instruction blocks I wrote into GPT's and Gemini's instructions.** Examples: the DM submission protocol and the Gemini operating brief.
- **Merging PRs.** That was correct, since merges were his authority. But every "Create a merge commit, not squash" condition depended on him remembering to pick the right button. The record shows he honored it every time.

---

## 5. What worked

### Prompts and habits that produced the best results

- **"Bind to the exact head SHA, once."** From my readback (C5): "The exact PR head SHA is the verification unit. Not the branch, not 'roughly that state' — the specific commit." GPT's later prompts repeated it ("Record the head once; do not silently move the review to a later commit"). It prevented every "which version did you audit?" ambiguity in the record.
- **"Cache the questions, never the answers"** (C4). Procedural knowledge persisted. Every hash, verdict and pass/fail was re-derived from a fresh clone. Cheap to follow, because a full clone took about 1 s, the suite 31 s and all guards 7 s at that point.
- **The BLOCKING test.** From the playbook: does an error "announce itself later or disappear into the record looking like a success"? This kept blocking findings rare and defensible. There were five real holds or rejections in about 55 audits: #10, #16, #31, #62 r1, and #33 F1, which was escalated and resolved by widening the code to match the claim.
- **Attack, don't read.** Mutants applied in committed throwaway worktrees, exact-rational recomputations from raw rows, squashing a branch in a scratch clone to *demonstrate* that a merge-commit condition was hard (#58). These produced the findings that mattered, and also the honest withdrawals: DM-082 (GPT was right), two #58 claims, and a #56 false positive that turned out to be my own floating-point noise.
- **Offering the owner the classification call when it was genuinely his** (G1–G3), instead of letting my default decide.
- **Every report ends with "existing Claude-owned entries touched".** This made deferred items surface when their code was touched, which is the only promotion mechanism that worked. The retro-population proved the hand-kept backlog did not.

### Files that made sessions start faster

- **`claude_Current.md`, introduced 2026-09-07.** One short file read first, with a strict retrieval order and an explicit "do not routinely read" list. This was the single biggest saving.
- **The compact Project instructions**, rewritten after C5 so context arrived up front ("rather than piecemeal throughout the threads", in the owner's words).
- **GPT's committed `review.md` prompts.** They gave the exact protocol commit, byte count, SHA-256 and blob ID to verify, so the identity checks were mechanical.
- **The procedural notes in Current §0:** anonymous clone + PR ref fetch, never trust the Actions list page, arXiv fetch only after the URL appears in search results.

---

## 6. Numbers (best effort)

| Measure | Value | Basis |
|---|---|---|
| Owner messages per searchable chat | 21 owner messages across 6 chats ≈ **3.5 per chat** (C1 1, C2 7, C3 3, C4 1, C5 7, C6 2) | Turn counts from the read tool. Cowork sessions not included. |
| Agent turns per owner message | **1 visible reply** per owner message, often with dozens of tool calls inside it (the C5 retro-population reply alone ran 30+ shell calls) | Read tool |
| Audits recorded | ~55 Ledger entries, 2026-08-29 → 2026-10-01; peak days **2026-09-03 (9)** and **2026-09-08 (6)** | `claude_AuditLedger.md` + Current + PR #62 reports |
| Typical audit duration | **Not measured.** Upper-bound proxies only: PR #62 r2's protocol was pushed 01:18Z and the chat was last updated 02:22Z the same night, so about **≤ 1 h including handoff** for a narrow changed-boundary review. Nine audits on 2026-09-03 implies well under a working hour each on that day. Large audits (#54, #56, #61) recomputed hundreds of results and were plainly longer. | Timestamps; no session clock exists |
| Mechanical cost of a full local re-verification | clone ~1 s, 322-test suite 31 s, 18 guards 7 s (at `e66bb5f`, 2026-09-05). Later the suite reached 914 tests (#61), still minutes. | Measured in C4 |
| Deferred / hardening IDs issued | **DM-001 → DM-105** (one withdrawn: DM-082) and **FH-1 → FH-27**, plus escalation **E-001** | Current + PR #62 reports |
| Longest searchable session | C2 and C5, 14 turns each | Read tool |
| Context resets / "start fresh" moments | Every chat and Cowork task started cold. The 2026-09-07 migration and `claude_Current.md` existed to make that cheap. No mid-chat compactions are visible in the six transcripts. | — |
| Commits per session | **0.** Claude had no repository write access. `main` has 427 commits by the owner's account and 20 by the Actions bot, none co-authored by Claude. This retrospective is the first Claude-authored commit. | `git log origin/main` |

### Accepted and overruled findings

| Finding | Owner's disposition |
|---|---|
| PR #10 hold (mutation `--check` verified nothing) | Accepted; fixed at `36c0a79`, then merged |
| PR #16 hold (preregistration "frozen" but pinned to nothing) | Accepted; two addenda, merged after R1 |
| PR #31 rejection (non-blind "blind" attestation) | Accepted; corrected head merged |
| PR #33 F1 (gate's pass status false for the record in hand) | Escalated to the owner; resolved in the strong direction |
| E-001 (contradictory AAF classification) | Accepted as BLOCKING-class with a promotion rule. Still live and never repaired, because HUST work never resumed |
| "Create a merge commit" hard conditions (#16, #24, #28, #39–#62) | Honored every time the record covers |
| PR #62 r1 REVISE_PROTOCOL | Accepted; revision 2 was produced the next day |
| G1–G3 (DM-006 → DM-008) | Owner chose deferred over the BLOCKING option I offered. Not an overrule, a choice between my options |

**Overruled or set aside:**

- **PR #60 was merged without the independent review I was supposed to do.** Recorded as not audited, not as accepted.
- **Independent audit was paused for #47–#51** in favour of a later batch.
- **The NIST outreach plan** was cancelled.
- **Only one of my findings was overruled on evidence: DM-082.** GPT showed my dimensional objection was wrong, and I withdrew it the same day.
- **I found no retrievable case where the owner overrode a BLOCKING finding to merge.**

### Did "reuse recorded exact-head CI, no reruns" ever make me miss something?

**No confirmed miss.** But the rule had three gaps. Two I caught only by stepping outside it, and the third is permanent.

1. **PR-head CI is not `main` CI (DM-096).** Exact-head CI ran on the PR head. The hard merge-commit conditions were only enforced by guards running *after* merge. At #57 I found the merge commits for PR #54 and PR #56 had **zero** Actions runs, despite `verify.yml` declaring `push: [main]`. For those two merges, the guards protecting the "merge commit only" conditions had **never executed on the merged history**. Two things limited the damage:
   - At #54 I had deliberately re-run both chronology guards at the merge commit, because a two-merge graph shape was something no CI run had covered.
   - At #58 a push run appeared for `c7229812`.

   The two earlier absences were never explained. Strict reuse of PR-head CI would not have caught this.
2. **"Recorded" CI is only as good as where it was read from.** Some reuse was second-hand: CI for #47–#51 and for `main` at `0b3d3126` was "source-attributed" via GPT's handoff, not fetched. At #61 the Actions list page summarized two **failed** runs as success. The rule is safe only when "recorded" means an individual run page fetched for that exact SHA. I tightened it to that after #61. I can't rule out that earlier batch-mode corroboration accepted a mislabeled summary, because those runs were never fetched directly.
3. **What CI cannot see.** CI runs on one pinned environment. The 3.11/3.12 coupling (DM-090) and the libm portability failure at #61 (the original verifier failed on glibc) appeared only when I ran things on a different machine. Lean was the starkest case: I never had a working local Lean build, so "no reruns" was not a choice there. Every Lean attestation in every audit rests on CI alone.

**Net:** the rule saved real effort on Lean and mutations, and on the suite once it was large. It saved almost nothing on the Python suite and guards, which took about 40 s in total. I would keep it, with two amendments:

- always fetch the individual run page for the exact SHA;
- always confirm push CI on the merge commit whenever a hard merge-commit condition exists.

### What I would have simplified

1. **One record, not seven.** By September the audit state was spread over the Drive folder, the Project copy, Current, the Ledger, the DM index, the DM detail files, Archive and staged rows. Because the Drive connector can't edit file content, every extra surface became a place where things fell out of date. A single append-only ledger plus one current-state file, in a place I can actually write, would have removed most of the debt in §4.
2. **Keep Ledger rows to one line.** The rule said "compact historical map". Rows #44–#58 run to hundreds of words each. The full report already lives in Archive.
3. **Stop counting non-events.** Lines like "DM-027 delivered a nineteenth consecutive time" or "DM-006→008 fired a fifteenth time, bar not met" cost reading time every audit and changed no decision.
4. **Issue fewer IDs.** I created 105 DM and 27 FH IDs. Many will never be acted on. A finding with no plausible promotion within the project's lifetime belonged in a sentence in the report, not a permanent ID.
5. **Scale the audit to the claim.** Synthetic-benchmark and contract-conformance PRs (#54–#58) got the same full-custody, recompute-everything treatment as empirical G estimators. A lighter tier would have been enough there.
6. **Remove the human relay.** Let GPT open each PR with its `review.md` and give me read access to the repo and API. Then "Review #N" is the whole handoff, and the owner stops carrying text between models.
7. **Push back sooner on the drift.** I recorded "Empirical (G) frontier: unchanged" at every audit from #53 to #62 and put "return to the empirical frontier" in the recommendations. I never said plainly that the project's energy had moved away from the question it started with. That was within my remit, and I should have said it.

---

## 7. Secrets check

- **API keys, tokens, passwords:** none present. None were encountered in the sources.
- **Private Drive links, file IDs and folder IDs:** not included. Drive files are named by title only.
- **Chat URLs:** not included. Chats are labelled C1–C6 by title and date.
- **Email addresses:** none. An author-email query during preparation was masked and not copied here.
- **Personal paths:** none beyond repository-relative paths.
- **Third-party names:** limited to the tools in the workflow (GPT/Codex, Gemini, Claude, GitHub, Google Drive) and publishers/institutions cited as Number Project evidence (NIST, BIPM, HUST, IOP, APS). No unrelated people are named.
- **Owner messages:** quoted verbatim, including original spelling. Two quotes are cut where marked `[…]`. Nothing is paraphrased inside quotation marks.
- **Unquoted owner statements:** where I describe an owner statement I don't have verbatim (the 2026-08-30 Drive reminder, the hiatus reason), I say so instead of quoting.
