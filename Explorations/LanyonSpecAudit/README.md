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

## Results (run 2)

Source: [workflow run 40997601940](https://github.com/mdiaz4052/The-Number-Project/actions/runs/40997601940)
at commit `5c57bcf`. The per-variant table is in [`results/table.md`](results/table.md) and
a parsed summary in [`results/summary.json`](results/summary.json). The first full run
(`results/run1/`) gave the same pass/fail outcome for all 34 variants. Between the two runs
only the diagnostic refutation and re-proof scripts changed.

**H1 (gap): supported.** Six of the ten wrong-physics curated mutants pass every
published Lanyon theorem. In each case a refutation compiled in Lean confirms that the
spec really is wrong:

- B2, eigenvalue `-f`
- B3, Jacobian `f²`
- B5, a different PDE (flux `f³/3`) with the Jacobian, eigenvalue and wave speed left
  for `f²/2`
- M1, Maxwell spectrum `-c,-c,-c,-c,0,0`
- M2, Jacobian entry `c` in place of `c²`
- M3, a sign-flipped Maxwell system with eigenvalues `±ic`, which is not hyperbolic,
  certified alongside the listed real eigenvalues `±c`

In the systematic family, all 10 single-field sign flips of Jacobian entries and
declared eigenvalues pass Lanyon's suite.

**H2 (repair): supported.** L+S passes both controls and fails all 12 curated mutants.
Each of the 12 kills has a compiled Lean proof that the catching statement is false
(column "refuted"). L+S also catches all 10 Jacobian and eigenvalue sign flips.

**Prediction mismatches (3 of 34): B1, B7, M5.** The prediction was that Lanyon's suite
passes these. It failed them, but only because the published proof scripts cannot close
goals that are true:

- B1 needs `2⁻¹ * |f| ≤ |f|`.
- B7 and M5 need `x = x * m / m` with `m ≠ 0`.

Re-proofs (`reproofs/`) of the same statements compile, so these are brittle false
alarms, not detections. The strengthened S3 proof had the same brittleness on B1. In
Lanyon's pipeline a failed proof blocks emission, so all three specs would be blocked by
accident: B1 is wrong physics, while B7 and M5 under-dissipate.

**Wave-speed sign flips (5 of 5) pass both suites, as predicted.** Every theorem uses
`|mu|`, and the published C never reads `mu`, so these appear to be equivalent mutants.

**Positive controls behaved as expected.** Lanyon's suite catches internal flux/wave
inconsistency (B4 and all 5 flux sign flips, via `xFluxConservative`) and an
underestimated wave speed (B6, M4, via `xWaveStability`).

### What this does and does not show

- It shows that the published theorem statements do not pin down the eigenstructure or
  the Jacobian, so wrong physics can be certified. The new statements S1 to S3 close that
  gap for these two files, using only the declared spec.
- It does not show that any published Lanyon solver is wrong. Both unmutated files pass
  L+S.
- It says nothing about floating point, the C code, other solvers, or 2D/3D.
- The curated mutants were chosen with knowledge of the weak points; the systematic
  family covers only sign flips.

A [draft issue](DRAFT_ISSUE.md) summarizing this for Lanyon exists only as a file here.
Whether and how to share it is the repository owner's decision.

## Possible next steps

1. Run the same audit on a 2D/3D or DG solver (Euler or MHD), where eigenstructure is
   harder and an empty hyperbolicity statement is more consequential.
2. Add a units layer: check DSL flux and wave-speed expressions with
   `Discovery/dimensions.py`.
3. Reduce the `0.0` numeral hazard to a minimal reproduction and check whether it is a
   known Lean/Mathlib issue.
4. Preregistered convergence study of a compiled solver kernel with a driver we write.
