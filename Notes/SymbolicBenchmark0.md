# Benchmark 0 — controlled symbolic discovery

**Final technical disposition: BENCHMARK_0_PASS.**
**PROVISIONAL — INDEPENDENT AUDIT PENDING.** One realized four-world epoch;
no outcome-based seed retry, criterion change, coefficient refit after training,
or selection after oracle/held-out reveal.

The original integrity gate returned **BENCHMARK_0_FAIL** because it confused
unsuccessful bytecode-cache open attempts with reads. That failed source and
result remain intact. A separately sourced, narrowly validated operational
reconciliation corrects only that receipt interpretation. The final disposition
is in `receipt_reconciliation.json`; `result.json` intentionally preserves the
original FAIL. This distinction is required when citing this experiment.

## Decision and results

The baseline recovered the intended structures, excluded target-dependent
features, collapsed duplicate formulas, tolerated the specified distractions,
and declined to declare a stable formula for the two-regime world.

All errors below are RMS **natural-log prediction errors**, computed with the
training-fitted coefficient held fixed. They are not p-values or certified
error bounds. For small errors their numerical scale approximates fractional
prediction error.

| World | True-class rank | Train error | Validation error | Held-out error | Decision |
|---|---:|---:|---:|---:|---|
| A: clean | 1 / 5 | 1.61e-16 | 1.65e-16 | 1.87e-16 | Recovered |
| B: leakage | 1 / 5 eligible | 0.002917 | 0.002760 | 0.003118 | Recovered; both leaked features excluded |
| C: noise/redundancy/distractions | 1 / 200 | 0.009309 | 0.009023 | 0.008183 | Recovered; stable under each irrelevant-input removal |
| D: regimes | Not applicable | 0.600283 | 0.774962 | 0.774962 | `no_stable_law` |

The realized relationships, disclosed only to the evaluator after selection,
were A: `0.5*x/(t^2*z^2)`; B: `2*x*z^2/t^2`; C: `2*x/(t^2*z^2)`;
and D: `1.25*x/(t^2*z)` multiplied by either 1 or 4 according to regime.
Every expression retains **GENERATED/FITTED CANDIDATE** status.

1. **World A recovered:** the correct class ranked first and predicted held-out
   observations to floating-point precision. Its fitted coefficient equaled the
   planted value at the reported precision.
2. **World B rejected leakage:** `leak=y` and `leak_alias=leak` were classified
   ineligible before scoring and their values were absent from discovery inputs.
   The evaluator-only disabled-eligibility control fit perfectly (zero training
   and validation error), visibly outperforming the lawful noisy fit. It received
   no credit. The eligible coefficient error was about 0.0507%.
3. **World C remained stable:** 319 dimensional surfaces collapsed to 200 exact
   classes; nine surfaces represented the selected true class. Removing each of
   the three irrelevant atomic inputs and its dependent features left the same
   top class. The selected formula contained none of them. Its expanded
   complexity was 5, equal to the true structure; aliases did not earn a lower
   complexity cost. Coefficient error was about 0.1046%.
4. **World D avoided false universality:** one regime alone fitted essentially
   perfectly, but validation and held-out inputs were paired across regimes with
   targets differing by a factor of four. A deterministic feature-only formula
   cannot match both. Even the best possible paired log prediction has error at
   least `ln(4)/2 ≈ 0.693147`; the frozen family failed the 0.03 stability cutoff.
   Regime labels were diagnostic strata, not candidate inputs.

## Surviving false positives

Four incorrect C classes passed both the 0.03 validation and held-out tolerance.
They multiply the true structure by an independent, nearly constant `n1`, whose
log varies within ±0.005. This was an intentional frozen ambiguity stressor.

| Extra nuisance factor | Eligible rank | Expanded complexity | Validation error | Held-out error |
|---|---:|---:|---:|---:|
| `n1^-1` | 2 | 6 | 0.009060 | 0.008723 |
| `n1` | 3 | 6 | 0.009833 | 0.008706 |
| `n1^-2` | 4 | 7 | 0.009932 | 0.010159 |
| `n1^2` | 5 | 7 | 0.011308 | 0.010130 |

None displaced the true class or received a significance assignment. There were
no incorrect tolerance survivors in A, B or D. The complete candidate list,
including poor-fit candidates, is preserved; eligibility never meant discovery
credit. The C expression `velocity` alone was rejected dimensionally:
`L T^-1` differs from the target's `L T^-2`.

## What contributed and what was added

| Existing capability | Actual role |
|---|---|
| `Dimension` / exact rational dimensions | Exact eligibility; no approximate dimension matching |
| `search_candidates` | Existing bounded monomial enumeration, using neutral magnitudes; legacy scalar score discarded |
| `DependencyCatalog` | Validated definitions, reference/cycle/dimension checking and exact expansion |
| `normalize_exponent_signature` | Canonical signatures and equivalence keys |
| `_exponent_complexity` | The existing rational-exponent cost, applied after expansion |
| `solve_monomial_constraints` | Independent dimensional rank/nullity diagnostic: A/B/D rank 2, nullity 1 |
| Existing history verifiers | Sole-file freeze, source identity/freshness and ancestry |

The old engine searches scalar constants; it did not already support an
observation-table experiment. The bounded addition fits one positive
dimensionless coefficient in log space, ranks using validation error plus the
frozen complexity cost, makes an abstention decision, and evaluates untouched
held-out observations afterward. A feature-level reachability gate rejects
target paths even when their net exponents cancel. Leave-one-atomic-group-out
views remove dependent aliases as well.

The historical null sampler was designed for scalar magnitude coincidences;
using its G-specific distribution here would be inappropriate. The new D
paired-regime contradiction and seven adversarial contracts provide this
experiment's negative controls. No historical empirical result, Lean surface,
external-Lean archive or shared primitive was changed. No PySR, external
symbolic-regression engine or LLM candidate generator was executed.

## Interpretation and next decision

5. **Existing capabilities contributed materially**, as mapped above, but the
   data-fitting, split/seal and abstention adapter is new and its review is pending.
6. **No frozen scientific dimension failed in this realization.** The preserved
   operational failure was in receipt interpretation, not hidden-law recovery.
   It was diagnosed before the detached correction; the original generator,
   discovery code, seed, data, selections, coefficients and metrics were unchanged.
7. **The four nuisance false positives survived prediction thresholds.** Their
   exact identities and errors are above. They did not become scientific claims.
8. **Dimensional matching is a useful filter, not genuine discovery by itself.**
   In A/B/D it narrows the grammar to five classes but cannot choose the exponent
   of dimensionless `z`. In C it still admits 200 classes. Observations, provenance,
   equivalence and generalization do different jobs; a good held-out fit also
   failed to distinguish the four weak nuisance dependencies from the true class.
9. **A larger, separately frozen suite is justified after independent review.**
   This is one easy positive control and three bounded traps, not a reliability
   estimate. A useful next suite would vary seeds, widen nuisance interventions,
   and include additional non-monomial or misspecified laws without revising this
   epoch. None of that work is activated here.
10. **The baseline is ready for planning a small external-engine comparison,
    conditional on review of these boundaries.** No general platform expansion
    is required first. These particular worlds and their truth are now public,
    so reuse can measure controlled performance on a known benchmark, not fresh
    outcome-blind capability or lack of implementer familiarity. Preserve this
    suite unchanged as a regression baseline; a later prospective comparison
    should precommit additional unrevealed realizations. An external engine would
    supply candidates only and would need the same input, eligibility, sealing
    and evaluator boundaries. A bake-off is not authorized by this package.

## Custody and reproduction

| Stage | Immutable identity |
|---|---|
| Intended base | `d38826b231d0afe524ef4de656ed1ba3e9293bb4` |
| Sole-file preregistration freeze | `a2f2e67ba76c90383e70ac2b6f878e446ec943e4` |
| Draft PR #54 server anchor | `2026-09-13T13:49:08Z` |
| Generator/discovery/evaluator source before realization | `994acc372705155597af86f7d953081c6f0d695e` |
| Public data and oracle/held-out commitments before discovery | `2e7a6b0395d27887dd72292eb8e8027e4bb7b9b2` |
| Rankings and selection seal before evaluator reveal | `a63dec875ebfc0918bc33bd5778a255cb8acaad2` |
| Preserved raw failed receipt epoch and diagnosis | `b01c01af1a30bbf8726842d3b05905a350cd5c1f` |
| Detached receipt-correction source | `8579c249e8dcbba04a44e671a6b7365f1bdb82fc` |

Oracle SHA-256: `68ab617f36a4f9679794ca9bef0e91dabb0dcd8f923854c45bb99a4dcc3f8304`.
Held-out SHA-256: `8e25750b26d880967af34f6478d4965508b1213330465e56869b4530c728b020`.
Sealed selection SHA-256: `d71eba82fcec74a07b8cba385fe2e648912a3971d64c964d7078c05d4af7fb04`.

The GitHub commit objects for each stage were created and imported locally
before proceeding to the next stage. Intermediate stages were not advanced as
the PR head; the completed, validated head is published together. Exact final
verification SHA and CI run identity are recorded in PR #54 and the existing
rolling handoff, avoiding a self-referential hash inside the final commit.

Public operational inputs: independently set length `x` (m), duration `t` (s)
and dimensionless control `z`; target `y` has units m/s². In C, `acc=x/t²`,
`z2=z²` and `velocity=x/t` are declared derived representations; `n0` is an
independent acceleration-dimension nuisance and `n1,n2` are dimensionless.
All draws and domains are frozen in the preregistration.

Discovery workers used a new temporary directory containing only eight
allowlisted Python source files, a strict anonymous JSON API, restricted reads,
forbidden writes and no external subprocess/network actions. The full
preregistration, seed, generator, world identity, truth and held-out files were
not staged. This is engine-level dataflow isolation for trusted code, not a
hostile-code OS sandbox or implementer-blinding claim. The oracle and held-out
JSON files now in the repository are **post-seal reveals**, never worker inputs.

Use a complete Git checkout and Python 3.12:

```sh
python -m unittest tests.test_symbolic_benchmark tests.test_symbolic_benchmark_receipt -v
python -m Discovery.symbolic_benchmark --check
python -m Discovery.symbolic_benchmark_receipt --check
```

`--check` replays the same frozen inputs as an explicit reproducibility check;
it never selects a new seed or updates results. `realize`, `seal`, `reveal` and
`finalize` are write-once stage commands and must not be used to overwrite this
epoch. The original guard intentionally validates the preserved raw FAIL; the
second guard validates the detached final disposition. Ten focused tests cover
the seven original boundary contracts plus three operational-correction tests.
Both guards are part of protected CI. No extra local Lean run is required.

All evidence is under `Experiments/SymbolicDiscovery/Benchmark0/`: freeze and
anchor; public observations and sanitized inputs; eligibility; commitments;
complete rankings, class membership and selection seal; oracle/held-out reveals;
per-world evaluation; original controls/result/defect; and the cache-attempt
probe and receipt reconciliation. No source or outcome record was overwritten.

**Nonclaims:** this establishes only bounded performance on four synthetic
worlds whose evaluator knows the truth. It does not establish discovery of
unknown natural laws, a general false-positive rate, statistical significance,
external-engine superiority, empirical G evidence, or a proof of physical
universality. **Create a merge commit** only; leave PR #54 unmerged for Miguel.
