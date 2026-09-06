# HUST 2018 AAF Depth-2b Post-Merge Follow-Up

## Boundary and baseline

This bounded follow-up addresses only NB-1 through NB-5 from the independent audit
of PR #35. Work began from merge commit
`e66bb5fc10171ea5dc317206c1daa6274a2a70be`, whose ordered parents are
`37409dcc43ed09655bb1ed3ca64333a40b72fc10` and
`e9036ecad667456988f1e4164f436835434f3a43`, on branch
`codex/milestone-7-post-merge-follow-up`.

No scientific value, uncertainty, estimator, covariance rule, source pin, evidence
classification, apparatus claim, replication claim, authorization scope, or Lean
linkage changed.

## Non-blocking-note dispositions

1. **NB-1 — dead authorization-test residue:** the five unreachable tuple-expression
   fragments after the test file's `unittest.main()` call were removed.
2. **NB-2 — duplicate measurement-test import:** the stray trailing `import io` was
   removed; the legitimate top-level import remains.
3. **NB-3 — bounded lexical evasions:** the deterministic byte-equivalence detector
   now covers the specified byte-for-byte, byte-equivalent, binary-identical,
   octet-identical, publisher-byte, exact-copy, capture-equality, and publisher-tied
   verbatim-copy families after the existing normalization. The exact frozen negative
   disclaimer remains allowed, while an appended affirmative claim is rejected.
4. **NB-4 — terminal published-value regression:** a separate builder-level test now
   changes only baseline `published_G.value` to `Decimal("9e-11")` and confirms that
   reconstructed `G_hat` and its standard uncertainty remain unchanged.
5. **NB-5 — clarification traversal coverage:** the isolated source-path runner now
   carries per-mutant source paths and module names. Its two terminal-input mutants
   retain their behavior, and a third one removes only clarification-record traversal
   of byte-identity overclaims. The new mutant is killed by one designated nested-claim
   test through a unique behavioral marker while the clarification `nonclaims` list is
   unchanged.

## Mutation v3 and preservation

`hust_2018_aaf_depth_2b_mutation_results_v3.json` is the only advanced artifact. It
records 25/25 killed mutations: 22 in-memory and three isolated source-path cases. Its
SHA-256 is
`c114045c78e97b81e70c9a216c279c58076732a6445906effa83bd94f61b7561`.

The v3 builder verifies all four PR #35 v2 artifact hashes before behavioral scoring.
Those frozen-byte checks, source-state checks, canonical tree-state checks,
import-integrity checks, and cleanup checks remain non-behavioral sentinels and receive
no mutation-kill credit. All eight Milestone 7 v1 artifacts and all four PR #35 v2
artifacts remain byte-for-byte identical to the baseline. Mutation-results v2 remains
the frozen 24/24 PR #35 audit record.

## Verification record

Verification used Python 3.12.13 from the clean first implementation commit. The
following checks completed successfully:

- focused source-history, authorization, measurement-model, and mutation suites:
  55/55 passed;
- full Python suite: 331/331 passed;
- all 18 Python `--check` commands in `.github/workflows/verify.yml`, including all
  three HUST depth-2b guards;
- exact preservation of all eight v1 and all four v2 SHA-256 values;
- deterministic freshness of mutation-results v3;
- all required lexical, traversal, invalid-replacement, cosmetic-mutant,
  import-path, syntax, discovery, terminal-value, cleanup, and canonical-state
  adversarial checks;
- both cleaned test files compile, and the measurement-model test imports `io` once;
- no v1, v2, Lean, or workflow file appears in the implementation diff;
- no temporary absolute path, timestamp, random identifier, or environment-specific
  value appears in v3; and
- `git diff --check`.

Exact-head GitHub Actions remains the authoritative external Lean/proof-audit and
Python verification after the final documentation commit is pushed.

## Deferred residuals and tags

R1 (path-freezing ancestry), R2 (absent-path vacuity), R3 (CLI diagnostic precedence),
and R4 (structured exception attribution) remain explicitly deferred. In particular,
`Discovery/source_history.py` was not changed.

No tag was created, deleted, moved, or retargeted. The annotated `milestone-7` and
`milestone-7B` tags still peel to
`37409dcc43ed09655bb1ed3ca64333a40b72fc10`.
