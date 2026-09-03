# Milestone 5B-core: falsification infrastructure and null controls

**Methodological result.** This directory records versioned experiments about the
behavior of the project machinery. It does not contain an empirical observation,
measurement result, theorem about nature, or validation or refutation of a physical
theory.

## Immutable experiment definition

`milestone_5b_core_v1.preregistration.json` freezes the grammar, provenance strata,
primary score, local and global null rules, sample counts, seeds, analytic-calibration
gate, and planted-target controls. Its exact SHA-256 is recorded in each corresponding
result. Amendments require a new experiment identifier and file rather than overwriting
version one.

This mechanism makes material post-hoc changes machine-detectable and visible in
repository history. It does not prevent tampering.

## Null and planted-control result

`milestone_5b_core_v1.null_results.json` records every sampled target, nearest class,
tie, seed, and analytic-calibration result. Trial rows use deterministic, hash-checked
TSV chunks inside the JSON so that the complete 40,000-target record remains recoverable
without overwhelming the structural diff. The committed result derives all counts from
the actual run:

- 21 surface candidates form 10 definitional-equivalence classes;
- 3 classes satisfy `no_registered_target_dependency` and are eligible for the primary
  null;
- 7 classes reconstruct G or retain registered G dependency and are isolated as the
  circularity control;
- both 20,000-target Monte Carlo nulls pass the frozen 0.02 analytic-CDF tolerance; and
- all three preregistered planted targets recover their intended eligible class with the
  expected logarithmic distance.

The local ±3-decade log-uniform null is primary. The deterministic broad interval is
contextual. The primary score is only

```text
abs(log10(candidate magnitude) - log10(target magnitude)).
```

The current primary candidates are `hbar * c / m_e^2`, `hbar * c / m_p^2`, and
`hbar * c / m_u^2`. Their large separation from G is another expression of the familiar
weakness of gravitational coupling at particle-mass scales. Poor matching does not show
that G is fundamentally special.

At the current grammar, the local run is geometrically degenerate: every eligible
position lies outside the local interval, no sampled trial enters the eligible-position
hull, and the same class wins every trial. The recorded local analytic CDF value near
`0.5` is forced by centering the interval on G; it is not a measured or informative
percentile. The result artifact records these regime diagnostics explicitly so the
calibration statistic cannot be mistaken for candidate competition.

All excellent current matches to G belong to one registered definitional-reconstruction
class whose Planck-unit definitions already contain G. Those expressions are excluded
from the primary null to prevent target leakage. The current grammar therefore contains
no strong registered-target-independent numerical match to G.

The present null machinery is mainly calibration infrastructure for future, larger
preregistered grammars. No physical theory is validated or refuted by either null, the
real-G navigation record, or the planted controls.

## Reproduction and integrity checks

From the repository root:

```bash
python -m Discovery.falsification_preregistration --check
python -m Discovery.null_experiments --check
```

The null check verifies the preregistration hash, version, experiment identifier, seeds,
recorded source state, trial-payload hashes, and byte-for-byte deterministic regeneration.
It does not silently replace an existing result.

## Mutation attestations

`milestone_5b_core_v1.mutation_results.json` is the preserved historical first mutation
attestation. It is not overwritten.

`milestone_5b_core_v1.mutation_results_v2.json` is the current mutation attestation. The
same preregistered Milestone 5B experiment is re-anchored because the result-driving source
boundary now explicitly includes `Discovery/physical_bridge_schema.py`, whose constructor
validation can determine whether evidence-bearing records reach the model validator. The
re-anchor also migrates the old `force_reference` test fixture to the namespaced certificate
form and removes the temporary production migration shim instead of silently rewriting a
declared source identifier.

The current artifact records the selected semantic mutants, their predefined behavioral
tests, import-path evidence, canonical-state fingerprints, cleanup confirmation, and the
exact `killed`, `survived`, or `invalid` classification.

The two calibration mutants behaved as required through the same disposable-worktree
path used by production mutants: the known behavioral defect was killed, while the
behavior-preserving source transformation survived. The production results were:

- disabling registered target-path rejection was **killed** by the existing direct-G
  and Planck-input behavioral test;
- substituting target-independent `m_e` for `m_P` before inherited dependency expansion
  was **killed** by the explicit registered-target-path assertion; the replacement keeps
  a valid mass dimension, so this is a behavioral kill rather than an invalid mutation;
- disabling the dedicated calibration/correction reference diagnostic was **killed**
  by fixtures that pin its precedence before the broader terminal-comparison rule. This
  is a diagnostic-precedence, defense-in-depth kill, not an independent safety kill:
  the broader rule still rejects the same paths;
- disabling the complete source-provenance gate for populated empirical estimator,
  calibration, and correction records was **killed** by a behavioral test that populates
  an unsourced calibration coefficient;
- disabling the separate `documented` provenance classification was **killed** while all
  three source fields were present;
- disabling the source identifier, edition, and access-date requirements was **killed**
  by a behavioral test that checks each field separately;
- narrowing the gate back to estimator ancestry was **killed** by declared calibration and
  correction records deliberately placed outside that ancestry;
- inverting the dependency artifact's `--check` comparison was **killed** by a subprocess
  test that exercises the module CLI against both current and stale artifacts.

All eight selected production mutants are detected by behavioral assertions. Seven change
acceptance or checker behavior; the calibration-reference mutant pins an explicit
defense-in-depth diagnostic without changing acceptance. No source-text, literal-string,
or exact-patch detector was added to improve the mutation score.

An additional behavioral test confirms that `exact=True` cannot bypass empirical source
metadata. These source gates verify declared provenance records, not real-world
experimental independence.

The current `SOURCE_PATHS` attestation includes both the physical-bridge schema and validator
alongside the behavioral tests that drive the selected mutation family. This is an explicit
evidence-boundary decision, not a claim that every repository file is source-attested.

The mutation harness automatically creates detached worktrees at the recorded source
SHA, proves relevant module `__file__` paths are under the disposable root inside the
test process, applies exactly one mutation, and removes the worktree. Infrastructure,
collection, import, timeout, or cleanup failures are `invalid`; they never count as kills.

Check the committed mutation metadata with:

```bash
python -m Discovery.mutation_harness --check
```

The mutation guard hashes the recorded source commit, the Git blob object ID of every
result-driving `SOURCE_PATHS` file at that commit, and the complete calibration and
production record arrays. It also requires each record's worktree anchor to match that
source commit; requires clean, unchanged canonical status fingerprints, unchanged HEAD,
and confirmed worktree cleanup; and rederives the classifications, calibration validity,
family status, and production interpretation from the frozen mutant catalog. A one-field
source-SHA bump or a rehashed false safety flag therefore cannot make stale or
methodologically invalid records current. The verifier also compares `calibration_rule`,
`anti_goodhart_rule`, and `nonclaims` with canonical module constants; editing one and
recomputing the record digest does not restore acceptance.

The 34-case leakage corpus validates each advisory `expected_gate` name against an
explicit registry and rejects unknown names. The registry checks test metadata; it does
not turn diagnostic labels into additional acceptance gates.

These controls remain tamper-evidence pins, not reproduction proof or protection against
a knowing forger. A knowing editor can change source, catalog, tests, records, constants,
and digest together. The null artifact remains the byte-for-byte deterministic
reproduction guard.
