# LSA-1: Lanyon spec-adequacy mutation audit

**Question.** Lanyon AI publishes Lean theorems alongside each generated physics solver.
If a solver spec describes the wrong physics, does any published theorem stop being
provable?

**Method.** We pin two published 1D Lean files (Burgers and Maxwell) and plant mutations
in them: 12 hand-chosen and 20 mechanical sign flips. We then compile each variant
against two theorem suites: Lanyon's own (L) and Lanyon's plus three strengthened
statements (L+S). The full design, predictions and decision rules are in
[`PREREGISTRATION.md`](PREREGISTRATION.md). They were committed before any variant was
compiled.

| Path | Contents |
|---|---|
| `upstream/` | Pinned Lanyon files (MIT) and [`PIN.md`](upstream/PIN.md) |
| `strengthened/` | S1 `jacobianIsDerivative`, S2 `realEigenbasis`, S3 `dissipationBound`, with proofs for the unmutated specs |
| `refutations/` | Lean proofs that the statement catching each curated mutant is actually false for that mutant |
| `audit.py` | Mutant definitions, variant assembly, compile and attribution, axiom probes |
| `results/` | Generated `results.json` and `table.md` |

## Running

```bash
python -m Explorations.LanyonSpecAudit.audit --check
```

```bash
python -m Explorations.LanyonSpecAudit.audit --run --verbose --only ALL
```

`--check` needs only Python. `--run` needs `lake env lean` with this repository's
Mathlib pin, which the [`Lanyon spec audit`](../../.github/workflows/lanyon-spec-audit.yml)
workflow provides. The variant ids it compiles are listed in `ci_scope.txt`.

## How a variant is judged

Each variant is a single Lean file: the mutated upstream text, then the strengthened
addendum, then (for curated mutants) the refutation. Each error is attributed to the
declaration that contains it. Lean records a declaration whose proof failed as
`sorry`, so anything that uses it would still compile. To catch this, every theorem is
also probed with `#print axioms`, and a `sorryAx` dependency counts as a failure.

## Amendments made before any mutant was compiled

The preregistration lets the Lean text of S1 to S3 change only to elaborate, or to make
the proofs go through on the unmutated controls. Two such changes were made. Both are
mathematically equivalent to the preregistered statements:

1. S2 asks for `L * R = 1 ∧ R * L = 1` instead of only `L * R = 1`. For square matrices
   one-sided inverses are two-sided. The lemma that shows this was not found under the
   expected name in this Mathlib pin.
2. Proofs rewrite the literal `0.0` to `0` with simprocs disabled before any `simp` or
   `ring` sees it (see below). This changes proofs only, not statements.

Both controls (B0, M0) pass L and L+S with clean axiom probes at commit `ba65794`.

## Numeral hazard (side observation, not yet investigated)

The upstream specs write zero as the scientific literal `0.0 : ℝ`. In the first control
run, `simp` turned the Burgers Jacobian `0.0 * f * f + (1/2) * 1 * f + (1/2) * f * 1`
into the goal `U.f + U.f ^ 2 = U.f`, which treats `0.0` as `1`. The kernel then rejected
a `norm_num`-generated term (`IsNat.of_raw` applied at the wrong type). The kernel caught
it, so no false theorem was accepted, but a tactic produced an ill-typed proof. We have
not yet reduced this to a minimal reproduction, and it may be a known issue.

## Results

Pending the full run.
