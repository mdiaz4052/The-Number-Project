# PySR Adapter 1 — prerequisite NO_GO

**NP-PYSR-ADAPTER-01 revision 1:** `PYSR_ADAPTER_1_NO_GO`.
**PROVISIONAL — INDEPENDENT AUDIT PENDING.**

The pinned environment did not qualify. Julia 1.10.10 terminated with **SIGBUS
(signal 7)** during JuliaPkg's initial `using Libdl` / `dlpath("libjulia")` probe.
This happened before backend dependency resolution, a PySR import, native-export
qualification, or any smoke/target fit. The underlying cause is unresolved.
This is an execution-environment prerequisite result, not a finding that PySR,
Julia, the proposed adapter, or the search grammar is defective.

The sole authoritative outcome is
[`result.json`](../Experiments/SymbolicDiscovery/PySRAdapter1/result.json).
The consumed packet and sole-file contract freeze preserve the planned design;
they do not imply that its unreached implementation was delivered.

## What actually happened

| Boundary | Observed result |
|---|---|
| Baseline | Accepted #58 true merge `9d59d7e7a9e2f056f73d277282a49387287311ff`; no open task to resume |
| Consumed instructions | Drive revision `0B4E-uj-ArwK4NVI4SXVlQ1hLamFPdStoQmhaZFA2cUhla1AwPQ`; 48,337 bytes; SHA-256 `938d7c884cc2b6add3dae4775de8159b387d2addd7fd5654f4cd50eff3670583` |
| Published instruction snapshot | `87780b9e7880b0e7afb8dd6034a609ce1391cf37` |
| Sole-file freeze | `97002d47a9be50716a24e061567a0b8f9c4c2019` |
| Draft anchor | [PR #59](https://github.com/mdiaz4052/The-Number-Project/pull/59), 2026-09-17 14:33:57 UTC |
| Python | CPython 3.12.14; executable identity recorded in `setup/attempt-01.json` |
| Python dependencies | PySR 1.5.10 and Python dependencies installed in one clean venv; exact versions, distribution URLs/hashes retained; no import/full-stack qualification |
| Julia binary | Official x86_64 1.10.10 archive, 173,848,413 bytes; SHA-256 `6a78a03a71c7ab792e8673dc5cedb918e037f081ceb58b50971dfb7c64c5bf81` matches official checksum receipt |
| First setup failure | `tar` extracted files but could not restore archive uid/gid 1000; exit 2 |
| One allowed setup retry | Same archive, `tar --no-same-owner`; exit 0. No changed versions |
| Terminal prerequisite failure | `juliapkg.resolve()` selected Julia 1.10.10; the child Libdl probe died with SIGBUS; Python wrapper exit 1 |
| Backend and locks | SymbolicRegression 1.11.0 explicitly requested; no Julia Project.toml or Manifest.toml created |
| Smoke fits | 0; neither of the at-most-two allowed smoke fits reached |
| Fresh randomness and target data | No master seed, seed commitment, target rows or withheld data created |
| r01 / r02 / r03 / r04 | Each NOT_EXECUTED because setup failed before target generation |
| Export, parity and trusted cards | NOT_EXECUTED; no native candidates or cards |
| Dimensions/domains/provenance integration | NOT_EXECUTED for a real engine; historical accepted claims unchanged |
| Validation selection / heldout | NOT_EXECUTED; no scores or selections |
| Adapter fixture suite / eight mutations | NOT_EXECUTED; no native exporter or trusted adapter implemented |

The setup retry was exhausted, so no alternate Julia binary, extra resolution
attempt, second environment, package downgrade, or engine substitution followed.
No search was rerolled. No runtime isolation or memory-cap enforcement is claimed:
target workers were never launched. The observed SIGBUS is not attributed to the
proposed 6 GiB target cap; that cap was never applied.

## Evidence versus acceptance

The new code is a **setup-stage offline evidence verifier**, not a PySR adapter.
It validates the exact setup inventory and log digests, pinned component requests,
successful prerequisite receipts, diagnosed retry, terminal failure, chronology,
absence of target artifacts, source bindings and required ancestry. It recomputes
the setup result instead of accepting a disposition label.

`evidence_integrity=PASS` means that this retained, stage-specific record passes
those checks. `adapter_conformance=NO_GO` and `operational_acceptance=false` remain
separate. This route refuses other dispositions and unreached stages; it is not a
general verifier for future PASS/PARTIAL/FAIL/UNRESOLVED live epochs. It neither
loads retained scripts as code nor imports PySR/Julia during ordinary CI.

The 13 focused semantic tests accept the truthful NO_GO and reject unsupported
labels, altered or unrelated diagnostics, lost evidence, version substitutions,
pre-anchor execution, fabricated qualification/run activity, false retry claims,
source/result substitution, duplicate JSON keys and evidence promotion. A 14th
test checks the sealed committed epoch through ordinary unittest discovery.
These tests are not the eight unperformed adapter mutations.

Every scientific promotion axis remains **NOT_ASSESSED**. `outcome_blind=false`;
`search_coverage=NOT_ESTABLISHED`. There are no candidates to evaluate, and no
structural-recovery, predictive-validation, grammar-inadequacy or physical claims.

## Retained limitations and operational corrections

The first extraction failure was emitted directly to the execution tool. Its
output was truncated (the completion reported approximately 89,756 original
tokens). `setup/extraction-failure.json` explicitly retains diagnostic excerpts
and attribution, **not a reconstructed complete stderr**. The terminal SIGBUS
attempt and other wrapped steps have full stdout/stderr files and digest receipts.
The extraction diagnostic loss is a disclosed audit limitation. No empirical or
adapter result depends on treating those excerpts as complete.

Initial shell publication was blocked by automatic review over destination and
payload authorization. The exact repository and packet's explicit publication
requirements were verified; the retry then reached missing shell credentials.
The connected GitHub API published the instruction snapshot and freeze, with the
contract referring to their actual server commits. Unpublished local draft
commits are not evidence anchors. The draft PR preceded all setup commands.

No accepted source, tests, scientific artifacts, Lean files, Python pins or
`.github/workflows/verify.yml` changed. The new guard checks its own immutable
epoch; it does not add a new freeze of living CI configuration. Existing guards
continue to protect the accepted experiments. No Claude-owned record is changed.

## Offline use and review

From a full-history checkout with CPython 3.12:

```sh
python3.12 -m Discovery.pysr_adapter_setup_verifier check
python3.12 -m unittest tests.test_pysr_adapter_setup -v
```

This reproduces evidence validation only. It does not repeat the setup crash or
qualify the stack. Stored setup scripts and logs are inert custody records, not a
resumption instruction. `source_binding.json` pins source/setup bytes;
`evidence_seal.json` binds the unique result introduction. Final exact-head CI and
verification epoch are reported on PR #59 and the existing GPT handoff rather
than added as circular self-hashes here.

**Focused Claude prompt:** Review PR #59 at its final exact head as a bounded
**setup NO_GO archive**, not a functioning adapter. Verify the consumed revision,
sole-file freeze/draft anchor, complete terminal SIGBUS receipts, actual retry
accounting, disclosed truncation of the earlier extraction output, absence of
seed/data/fits, immutable source/result seals and true-merge ancestry. Challenge
whether the offline verifier derives this adverse disposition without converting
integrity PASS into adapter acceptance; probe false labels, altered receipts and
unsupported qualification claims. Reuse exact-head CI and do not rerun Julia,
install dependencies, re-audit #58, or demand native/DM-099 coverage that was never
reached. Decide whether the disclosed retention limitation blocks accepting this
negative archive. Return exact-head MERGE / DO NOT MERGE with scope-specific
BLOCKING / DEFERRED MAINTENANCE / FUTURE HARDENING. No finding IDs are closed by GPT.

DM-099 remains unaddressed because its new adapter call site was not implemented.
DM-098 informs this narrow adverse route; broad closure is not claimed. DM-097
is not triggered. DM-090's CPython boundary is retained. No new deferred-maintenance
ID or cleanup PR is proposed. The root-cause investigation and real adapter remain
unperformed scientific/integration work requiring a separately authorized package.

**Create a merge commit only. Leave unmerged for Miguel.**

## Third-party identity and notices

No third-party binary or source implementation is redistributed by this PR.
PySR 1.5.10's installed distribution declares Apache-2.0, Copyright 2020 Miles
Cranmer; its intended upstream source is
[`f51299e6`](https://github.com/astroautomata/PySR/tree/f51299e6dddc7bd2bfd7f473bfddca7c32d83206).
The backend's intended
[`61e1b36c`](https://github.com/astroautomata/SymbolicRegression.jl/blob/61e1b36cf5476fe32cd58920d4666d102e3c821c/LICENSE)
declares Apache-2.0, Copyright 2020 Miles Cranmer. It was not installed or qualified.
Julia's distribution LICENSE.md declares MIT, Copyright 2009–2023 Jeff Bezanson,
Stefan Karpinski, Viral B. Shah and other contributors; bundled dependencies have
their own notices. Python distribution identities and archive hashes are retained
in `setup/python-resolution.json`; this partial resolution is not a qualified
whole-stack lock, SBOM, source equivalence attestation, or SPDX/SLSA compliance claim.
Repository licensing is unchanged.
