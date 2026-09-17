# Candidate Exchange 1 — bounded decision

**Task:** NP-CANDIDATE-EXCHANGE-01 revision 1.

**Disposition:** `CANDIDATE_EXCHANGE_1_PASS`.

**PROVISIONAL — INDEPENDENT AUDIT PENDING.**

Two explicitly mocked output formats and two complete historical rankings can enter
one trusted evaluator without discarding their raw meaning, recorded provenance,
domain restrictions or evidence limits, within the supported fragment and fixtures.
This is an internal exchange-contract result. It establishes neither real-engine
compatibility nor improved discovery, empirical performance, formal derivability,
misspecification-detection capability or a new physical law.

The sole authoritative machine disposition is
[`conformance.json`](../Experiments/SymbolicDiscovery/CandidateExchange1/conformance.json).
[`interface.md`](../Experiments/SymbolicDiscovery/CandidateExchange1/interface.md) documents
record fields and executable usage. The consumed instruction and frozen acceptance
contract are preserved beside it.

## What was demonstrated

| Coverage | Recorded outcome |
|---|---|
| Mock structured tree and postfix formats | Three paired expressions each: monomial, lawful physical sum, dimensionless log inside a physical expression |
| Independent numerical expectations | At (x,t,z)=(8,2,1) and (18,3,e): respectively (2,2), (4,4), (0,2) |
| Historical `b01-adequate-n1` | All five ranked classes, members, values, errors, labels and order preserved |
| Historical `b01-curved-n2` | All five ranked classes, members, values, errors, labels and order preserved |
| Focused conformance suite | 24 methods passed; additional subcases cover resource boundaries and hostile inputs |
| Production mutations | Domain erasure, leakage bypass, dimension bypass, evidence promotion, raw-binding bypass and candidate loss: 6/6 killed by designated semantic assertions |
| Controls | Baseline and semantically equivalent comment-only control both survived |
| New scientific promotion | NOT_ASSESSED on every scientific axis; status remains GENERATED/FITTED CANDIDATE |

`outcome_blind=false`; `evidence_mode=deterministic_contract_conformance`. These
fixtures and expected outcomes are visible by design. Historical imports are
retrospective and outcome-known. Their original reported metrics and dispositions
are source-attributed evidence, not newly tested scientific conclusions.

All nine frozen operations are implemented: literal, variable, parameter, addition,
multiplication, division, integer power, exp and natural log. Exact SI dimensional
operations and existing canonical serialization are reused. The existing monomial
catalog is reused after an original-edge graph check: its zero-exponent normalization
cannot erase a dependency. Reachability is memoized for shared DAGs. No general CAS,
unit conversion, uncertainty propagation, optimizer or Lean bridge was added.

The evaluator visits the original expression. `x/x` retains x≠0; log retains a
positive argument; even zero multipliers cannot hide invalid subexpressions.
`0^0` is domain-invalid. Canonicalization is conservative and domain-sensitive.
Unequal canonical identities yield NOT_ESTABLISHED, not a proof of inequivalence.
Matching sample values do not prove identity. Fitted parameter values and trusted
manifest identity remain part of evaluated model identity.

## Historical source and numerical policy

Both selections are pinned at accepted head
`7405d07e717fbe1e84d3c1afb5b7f737e86c6103`, respectively Git blobs
`7937d9f84d56e2c12a39cbe2e6ee44a21247b338` and
`6e3124c349e746d994d9a860ecd25e193653898f`. Manifests bind the pinned public
input/design metadata and original discovery input digest. The importer reads no
held-out or oracle files and calls no generator, fitting routine or campaign runner.
It preserves all ten original coefficients and log coefficients without refitting.

Fixture predictions compare the expression route against the historical
`exp(log_coefficient + fsum(power*log(value)))` route with relative tolerance 2e-12
and absolute tolerance 1e-14. Different floating arithmetic routes need not be bit
identical. The declared coherent-SI numeric convention is bound to the synthetic
design; it is not metrological certification. Unknown uncertainty/dependence cannot
become zero uncertainty or independence.

**DM-094 forward clarification, attributed to Claude's accepted PR #57 audit:** all
seven Margin1 stable-but-incomplete selections recovered the true base monomial and
missed only the added curvature factor. They did not choose unrelated base laws.
This sentence restates the existing audit; this package did not rerun those seven
cases, and its two imports are not evidence of a new seven-case result. The frozen
fields and reports are unchanged. Claude retains ownership of finding disposition.

For historical Margin1 reproduction, the correct existing route is
`python3.12 -m Discovery.symbolic_margin_verifier check --replay`. Its deliberately
preserved predecessor is not the authoritative checker. This package did not execute
either historical campaign merely to add this pointer (DM-095).

## Custody and verification

| Stage | Pin |
|---|---|
| Accepted base | `c7229812f4d88c11f958f317b67bb51f7ba0c384` |
| Consumed work-order snapshot | `b3d81457f1c776655601a3dcfdd6f73feac1fcb5` |
| Sole-file acceptance freeze | `895f6888130e7d16ab3234297b4a6d730418a862` |
| GitHub draft PR #58 server anchor | 2026-09-16 19:46:23 UTC; before evaluator implementation |
| Final source/fixtures | `48bf982096c459ec8126e7a82f1d5224d944415b` |
| Conformance evidence | `d9273e0656bbbc25432635ce2685603215681242` |

Source snapshot and final evidence have separate envelopes and exact digest bindings.
A small mandatory evidence binding checks the unique introduction commit; it is not
a second disposition ledger. The read-only guard rejects changed source, records,
inventory, cards, disposition routing or sealed evidence. It never regenerates or
rewrites expected artifacts. It runs through normal unittest discovery; no workflow
file changed. The final PR/handoff supplies the completed head and CI result without
a circular self-hash in this report. CPython 3.12 remains required (DM-090).

Correct package check:

```sh
python3.12 -m unittest tests.test_candidate_exchange -v
python3.12 -m Discovery.candidate_exchange_conformance check
```

Ordinary development found and repaired rejection of a zero-exponent-only derivation
before source pinning. No failed published conformance epoch was overwritten. All
six production mutations calibrated on their intended semantic assertions; there
was no failed mutant recalibration. The first full local validation ran 852 tests:
850 passed; two inherited mutation-harness integration cases refused the dirty
checkout because the final Notes and evidence binding were still untracked. This
was an operational clean-checkout prerequisite, not a candidate-exchange invariant
failure. The unchanged final tree was committed before the clean-checkout rerun;
its result is recorded in the PR and exact-head CI. No old benchmark artifacts,
thresholds, Lean sources or CI configuration were modified.

## Findings, limits and next substantive audit

**BLOCKING:** no known unresolved defect in this package's declared boundary;
independent semantic review remains pending. E-001 remains live at its unrelated
HUST/AAF surface and is neither invoked nor closed here.

**DEFERRED MAINTENANCE:** no new submission. DM-090/092 and DM-093's retained scope
half remain unchanged. DM-094/095 are addressed by forward explanation/routing only,
not GPT closure. DM-096 has new factual navigation evidence: merged main
`c7229812…` passed push Verify #326, run 34995766997, both Python and Lean jobs.
Earlier absent merge runs and their cause remain historical unknowns; Claude owns
reconciliation. No workflow repair or bookkeeping-only audit follows automatically.

**FUTURE HARDENING:** inherited FH-21 remains scoped to its original surface. The
new expected dimensions and values come from explicit fixture mathematics and the
contract, not a transplanted class-ID literal. No family-enumeration claim is made.

A real generator adapter, unseen data, estimated-noise reasoning, additional
operations, general equivalence, unit conversions, release/replication package or
formal bridge would require a separate authorized scope. None starts automatically.

**Focused Claude prompt:** Audit PR #58 at its final exact head from GitHub, using
this report, the frozen contract, consumed work order and current CI. Challenge the
manifest/generator ownership boundary; original direct/transitive/canceled/zero-weight
provenance; units versus dimensions; fitted scalar roles; original domains and 0^0;
conservative equivalence versus numerical agreement; complete inventory and exact raw
bindings; separate schema/disposition paths; unknown/empty/failed cases; inability to
self-award evidence; and the limited mock/historical claim. Assess the six semantic
mutation kills and surviving controls. Reuse unchanged accepted evidence and exact-head
CI; target any concrete doubt rather than rerunning unrelated campaigns. Carry the
#57 merge/#326 facts and DM-094/095 clarification into this substantive review. Do not
re-audit #57 or refresh Claude's files solely for bookkeeping. Miguel retains merge
authority: **Create a merge commit only; never squash or rebase this custody chain.**
