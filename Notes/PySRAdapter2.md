# PySR Adapter 2: isolation prerequisite NO_GO

NP-PYSR-ADAPTER-02 revision 1 stopped before any Julia/PySR execution because
this host could not establish the required worker credential and file isolation.
This is a new adverse archive, not a working adapter or an explanation of #59's
SIGBUS. Independent review is pending. PR #60 remains unmerged for Miguel.

`Experiments/SymbolicDiscovery/PySRAdapter2/result.json` is the authoritative
derived result: `PYSR_ADAPTER_2_NO_GO`, `evidence_integrity=PASS`,
`adapter_conformance=NO_GO`, `operational_acceptance=false`. All six scientific
axes remain NOT_ASSESSED and search coverage remains NOT_ESTABLISHED.

## What actually ran

| Boundary | Retained observation |
|---|---|
| Primary controller | `/tmp/tnp-pysr-adapter2-e01` created; assigning UID/GID 61102 failed with EINVAL. No child launched by that controller. |
| Epoch 1 diagnostic | Single UID/GID map `0 0 1`, no capabilities, NoNewPrivs and seccomp active. Installed `bwrap --unshare-all` failed creating a NETLINK_ROUTE socket, exit 1. |
| One diagnosed recovery | Pre-recorded and committed `setup/recovery_plan.json`; added only `--share-net` to the same installed namespace tool, in a fresh epoch directory. Existing host network restrictions remained. It failed setting up the UID map, exit 1. |
| Runtime qualification | NO_GO before standalone Julia, Python child, dependencies or cold bridge. Two setup epochs; recovery budget exhausted. |
| Integration qualification | NOT_EXECUTED, including exporter, adapter, trusted envelope, smoke fits, positive/negative integration fixtures and eight production mutations. |
| Runs r01–r04 | All NOT_EXECUTED; no master seed, target rows, fits, native outputs, cards, selection seals or held-out evaluation. |

The recovery addresses the observed private-network failure using the work
order's allowance to disclose unavailable OS network isolation. It tests the
same already-installed filesystem namespace facility under the existing host
network; it does not create infrastructure, change host security settings or
substitute runtime versions. The earlier no-remedy assessment remains verbatim
in epoch 1; the committed recovery plan explicitly supersedes that preliminary
assessment. Claude should independently assess this remedy against section 6's
ordered recovery permission. There is no further setup authorization.

The first controller failed **before creating its evidence directory**. Its full,
untruncated execution-tool return is preserved with attribution; original separate
OS stdout/stderr files do not exist. Do not describe that record as a separately
file-captured native log. Both later namespace probes opened exclusive stream
files before launch and retain complete stdout/stderr, commands, allowlisted
environments, deadlines, exit status, executable and source hashes. Neither
probe successfully entered a sandbox or executed its `/usr/bin/true` payload.

No Julia archive was downloaded, authenticated, extracted or started. No lock,
license bundle or installed backend identity can truthfully be supplied. Planned
pins (Julia 1.10.10 / PySR 1.5.10 / SymbolicRegression 1.11.0) remain unqualified.
No physical-memory cap, successful sandbox, network isolation, native parity or
independent native replay is claimed. The recorded traceback and two refusals
support this stopping boundary; they cannot establish arbitrary operator truth.

## Source and evidence custody

The consumed 81,176-byte work order has SHA-256
`d6866c119695f40caefd576a8bd0c20acfd7a2441639b8933ed0d273edc73b39`.
Snapshot `dfbe2bd9bb6e0197bbb12ded6e0f3f59a1fffd2c` precedes sole-file freeze
`e0b13171714a6d359ef442249f4e0e45c5513874`, then the actual draft anchor
2026-09-20T16:04:26Z. Base is `79b56e0db86605e569c6d8a68a59315a00ab0177`.
The explicit public-disclosure authorization and unpublished-to-published
snapshot mapping are recorded in `publication_receipt.json`; no credentials
or unrelated private source files were published.

Runtime source `1c637ce5d5bab28092abb4987ba34071b2406052`, diagnostic source
`ffb1e46c747814c1620d84ee8c3e6e2c59e566e7`, and recovery source/plan
`e6eff4622f0f02c638f31d76c1b6257ba62afec5` each preceded their actual use.
Final offline sources were committed at
`6d68147f41f43f1e212d7c3a151287967bf0f18c` before result generation.
`source_snapshot.json` pins those committed bytes; `evidence_seal.json` binds
the later result commit and all package artifacts without circular self-hashes.
Source pins use committed epochs, not a perpetual freeze on shared living code.
All paths present at the base, including CI, old tests and old failure evidence,
remain unchanged. No global DM-097/DM-100 repair or finding closure is claimed.

## Offline verification and reproduction limits

From a complete repository checkout with history and CPython 3.12:

```sh
python3.12 -B -m Discovery.pysr_adapter2_verifier check
python3.12 -B -m unittest tests.test_pysr_adapter2 -v
```

The verifier uses the standard library and local git objects only. It installs
nothing, imports no native engine, emits no evidence files, and performs no fits
or network requests. It derives only this reached negative route. Invalid raw
evidence causes refusal; unsupported PASS, PARTIAL, FAIL or UNRESOLVED labels
cannot be substituted into an unchanged NO_GO archive. This is not evidence of
correctness for unimplemented positive adapter routes.

The tests challenge rehashed unrelated failures, altered logs, incomplete
capture, retry resets, boolean counters, late recovery plans, altered commands,
source substitution, seed/fit claims, isolation claims and result promotion.
They are adverse-archive unit tests, **not the eight adapter mutations**.
The new committed guard is discovered through the existing unittest suite;
the workflow remains byte-identical. Exact final head and CI attestation are
kept in PR #60 and the rolling GPT handoff, outside the immutable result, to
avoid a self-referential rewrite. Green CI checks the archive, not native replay.
The source and both failed attempts are preserved for inspection; do not rerun
the opt-in runtime entry points or reset the exhausted setup budget.

## Maintenance submission for independent disposition

No new finding ID is assigned by GPT. This is a concrete proposed DEFERRED
MAINTENANCE item for Claude to accept, reject, narrow or promote:

- Affected surface: initial controller in `Discovery/pysr_adapter2_runtime.py`,
  around task ownership assignment before evidence-directory creation.
- Source/head: executed source `1c637ce5d5bab28092abb4987ba34071b2406052`;
  unchanged in final source epoch `6d68147f41f43f1e212d7c3a151287967bf0f18c`.
- Observation: `os.chown` raised before the runner's file logger existed;
  only the attributed complete tool return survives for that controller failure.
- Proposed nonblocking rationale: no external child, target or fit executed;
  complete later capability-probe logs independently establish the prerequisite
  refusal, and the initial capture limitation is explicit. This rationale applies
  only to archive acceptance, not approval to reuse the runner operationally.
- Repair: initialize controller-level exclusive diagnostic capture before the
  first fallible filesystem/identity operation, retaining any partial attempts.
- Acceptance test: inject a pre-child ownership/setup failure; require preserved
  separate controller streams, a structured stop and zero child launches.
- Promotion trigger: any proposed operational reuse of this runtime controller,
  or evidence that the missing streams make the current stopping boundary
  irreducibly ambiguous. The latter would require current UNRESOLVED/DO NOT MERGE.

DM-098 is exercised only on this NO_GO archive. DM-099 is unexercised because no
new card path exists; its unchanged legacy direct-call hazard remains. DM-090
and other relevant scopes stay unchanged. No maintenance follow-on is activated.

## Focused Claude review scope

The ready-to-send prompt in the existing GPT handoff carries the actual final
head, exact-head CI URL/outcome, base, packet digest and result route. Use that
complete delivery header with the following scope; the result is provisional.

Independently review PR #60's reached isolation NO_GO. Challenge source-before-use
and draft-anchor chronology, exclusive attempt preservation, single recovery
rationale/permission, diagnostic completeness and initial capture limitation.
Distinguish a refused prerequisite from an actual isolation violation, ambiguity
or working adapter. Check outcome derivation and operational refusal under
DM-098, not mere enum membership. Verify no native run, integration qualification,
eight-mutation success, seed, target fit, selection or held-out use is claimed.
Keep archive integrity separate from adapter conformance. Assess the maintenance
submission above without assigning a global closure to unrelated findings.

Reuse final-head CI and accepted unchanged #58/#59 evidence. #59's complete
independent audit has now been located and supports MERGE/zero blocking for its
archive; its merge is not proof of that audit. Use canonical Claude current
file `11Jc9-qPUYoWPqurOqWvlziRdYK4DUX_x`, not the superseded older ID embedded
in the consumed packet. No reinstall, search rerun, broader mutation campaign
or housekeeping audit. State independent checks, attributed observations and
unreviewed stages separately. Return MERGE / DO NOT MERGE at the reviewed full
head, with BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING separated. Claude
owns finding IDs and dispositions; Miguel owns merge by Create a merge commit.

**Before finishing, upload the completed audit report and update the affected
canonical Claude-owned files in Google Drive, not just local copies. Fetch/read
back the remote files to confirm the audited head, verdict and affected finding
updates are present. Return their actual Drive links and state whether remote
delivery was verified. If upload or verification fails, report the specific
failure and mark Drive synchronization INCOMPLETE; do not claim the remote
records are current.** Preserve rolling IDs where supported, historical reports
and the existing Archive organization. Update only substantively affected
records; no second ledger. Verdict and remote-delivery status are separate.
Options 2 and 3 remain unactivated; PR #60 remains unmerged.
