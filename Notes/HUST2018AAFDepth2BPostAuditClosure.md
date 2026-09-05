# HUST 2018 AAF Depth-2b Post-Audit Closure

## Boundary and baseline

This bounded closure addresses the six non-blocking notes from Claude's 2026-09-05
audit of PR #34. The annotated `milestone-7` tag peels to merge commit
`37409dcc43ed09655bb1ed3ca64333a40b72fc10`, with audited implementation parent
`07d119e1d343c8d4d5ca97d5a515b8a3152c6c6e` and mainline parent
`715c189818dea258f3c6d447d7854226c1f2a575`.

No Milestone 7 scientific result, numerical input, estimator scope, covariance
authorization, apparatus claim, replication claim, or Lean linkage changed.

## Audit-note dispositions

1. **N1 — history anchors:** strict parsing now validates the frozen remote-anchor
   record. Shared source-history verification reports `verified` for the
   preregistration commit `c153b1a2079a5112f28e43263fb7986f393c19ca` and remote-anchor
   commit `d0eaaa7b36817e9381fb45c7655df01ece149f70`, with their exact source paths. A
   structurally valid synthetic squash using the implementation tree and only
   `715c189818dea258f3c6d447d7854226c1f2a575` as parent fails specifically with
   `ancestry_violated`.
2. **N2 — printed labels:** v2 uses `printed_row_label`. The two corrected official
   labels are exactly `Positions, alignment` and `Statistical error of Δω² or αₜ`.
3. **N3 — assessment prose:** the README now states that the target-path axis is
   `no_registered_target_path` and replication is `incomplete`; it does not call the
   target-path axis satisfied or experimentally independent.
4. **N4 — byte-identity defense:** the official-source `nonclaims` list is exact and
   ordered. A directly tested lexical detector rejects the two audit evasions plus
   normalized Unicode-hyphen and `bit-for-bit` forms while allowing the frozen
   canonical negative disclaimer.
5. **N5 — terminal leakage:** `displayed_total_as_input` and
   `published_final_uncertainty_as_input` are isolated source-path mutations of the
   maintained builder. Each exact replacement must apply once, compile, import from a
   disposable copy, and fail only its designated behavioral test through the target
   uncertainty guard. Invalid, unapplied, ambiguous, import-failing, or sentinel-killed
   mutants receive no kill credit. The final score remains 24/24 killed.
6. **N6 — attestation limit:** v2 and the README state that publisher bytes are not
   committed and that the browser-rendered official DOM digest cannot be reproduced
   solely from repository contents. No mirror or secondary source was promoted to
   official-source status. The source-pin policy preserves this limitation.

## Version and preservation decision

The required-input graph, authorization, measurement-model, and mutation-result records
advance to v2. Their v1 predecessors and the other four Milestone 7 source/freeze records
remain byte-identical behind automated SHA-256 sentinels. Earlier records protected by
`HISTORICAL_ARTIFACT_SHA256` remain protected separately.

The four v2 SHA-256 values are:

- required inputs: `ef8a23cee8d1d7c7e417ca69d8b0e75a66d5cf272e6fcd59ba92fb84d1468326`;
- authorization: `2bf6bb803d18600147c17bd94f5b05a3118f9bfd76136e0b7c22c5dfa1e77170`;
- measurement models: `9ab68481e2f11a08dd184aec25781822fd4c3b9beaa13fc5edb34cfa4e5a7b00`;
- mutation results: `5d7f197b9eae5a18f302eb9eca3073346106d6363c59cbd35573e6a53fcb9809`.

## Unchanged numerical and epistemic boundaries

All 21 component identifiers, their order, all 63 values, the three non-applicable rows,
central estimates, terminal comparisons, precision-50 RSS values, and absolute standard
uncertainties are identical between v1 and v2. Components remain `PUBLIC_DIRECT`; RSS and
complete individual models remain `PUBLIC_DERIVABLE`. Only `AAF-I`, `AAF-II`, and
`AAF-III` are authorized. Combined estimation, cross-run covariance, apparatus validation,
raw/run-level replication, physical-independence claims, and Lean apparatus certification
remain outside scope.

## Verification record

The implementation used Python 3.12.13. The following checks completed successfully:

- focused source-history and HUST suites: 46/46 passed;
- full Python suite from a clean committed tree: 322/322 passed;
- all three HUST depth-2b module `--check` commands;
- every Python `--check` command in `.github/workflows/verify.yml`;
- all eight frozen Milestone 7 v1 SHA-256 checks;
- deterministic parsing and freshness of all four v2 JSON artifacts;
- absence of temporary absolute paths and nondeterministic fields in v2 artifacts;
- `git diff --check`.

The synthetic-squash test returned `ancestry_violated`, and the changed frozen
preregistration-path test returned `source_state_violated`. Local Lean verification was
not run because `lake` is unavailable in this environment; the GitHub Actions Lean job is
therefore required for the exact PR head.

This closure work did not merge a pull request and did not create, delete, move, or retarget
any tag.
