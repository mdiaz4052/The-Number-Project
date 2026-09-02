# Milestone 6B — PySR target-leakage probe

This synthetic-only experiment tests a boundary of the project's provenance machinery by keeping three axes separate: candidate origin, registered algebraic ancestry, and known synthetic generation ancestry.

## Preregistered channels

- `A_clean`: `u_clean` and `r_clean` are upstream of `G = u_clean / r_clean`.
- `B_registered_leak`: `m_P = sqrt(hbar * c / G)` uses the registered Planck-mass dependency.
- `C_hidden_leak`: `k_hidden = G * s_hidden`, while `k_hidden` is deliberately registered as atomic.

## Result

The primary methodological endpoint is **`BOUNDARY_CONFIRMED`**. The Channel C canonical control `k_hidden / s_hidden` is dimensionally valid, has `no_registered_target_path`, and has known target ancestry in the synthetic generation graph. Registered algebraic dependency tracing therefore cannot by itself establish calibration, statistical, experimental, causal, or physical independence.

The frozen PySR experiment used seeds `0`, `1`, and `2` on all three channels and produced 26 finite candidates. The independent project audit classified 9 as dimensionally valid, 17 as dimensionally invalid, 20 as normalized monomials, 6 as representational gaps, 0 as parse failures, 4 as having registered target paths, 16 as using predictors with known target-generation leakage, and 6 as occupying the hidden-target-leakage blind spot.

PySR recovered the canonical signature in `A_clean` and `C_hidden_leak`, but not in `B_registered_leak`. That non-recovery was allowed by the preregistration and was not followed by search-budget, seed, unit, or operator tuning. In Channel C, every seed emitted both `k_hidden` and `k_hidden / s_hidden`; all six are dimensionally valid, have no registered algebraic target path, and reference a predictor known by construction to be downstream of `G`.

Every PySR expression remains permanently `target_exposed_candidate` and promotion-ineligible. It may motivate a new target-clean preregistered investigation, but the original record cannot be relabeled into stronger evidence.

Two selected semantic mutations were killed in the existing disposable-worktree harness: one attempted to bypass the target-exposed promotion valve, and one collapsed generation-DAG leakage into the registered algebraic result, erasing the Channel C distinction.

## Provenance and reproducibility

The external source is pinned to PySR 2.2.0 commit `65b887aeaf97f1c5ae84b0ceffb370551e57ce90`. The run resolved SymbolicRegression.jl 2.2.0 on Julia 1.11.9 and records the complete resolved Julia manifest in the raw artifact. Ordinary CI does not import or rerun PySR.

Evidence SHA-256 values:

- raw external artifact: `5dc9ceae6d49a8bfab8f00fc4e0d4ddba8c3a4b31bfe4b0944a65aa4c5cf5176`;
- normalized result: `ed01adff58bc6b95b1d6281af92b3d97a1f71757da760a36762a2bde8fb654a4`;
- mutation result: `44ab9598fe07c56091f7ebd27266e7d89a553aa370c144c2744b858df7e94015`.

The preregistration was committed at `a3cc025bf41670e37b1f85583205156eea1db2b0`; search-driving source was frozen at `f2c26da24cfa5a463dc2bbadeb83c6bf41cc4689`; the normalized result records corrected audit source `201a65f44ac316ae9e0f48235a73f99498848ded`; and the selected mutation result records source anchor `182e2f3e6129f3a1ffff4890437b8e56119c6575`.

The original `Discovery.pysr_leakage_check.py` is retained as frozen pre-fix history. The successful result and permanent CI use `Discovery.pysr_leakage_check_v2.py`, which delegates candidate auditing to `Discovery.pysr_leakage_audit.py`.

## Execution note

The first frozen search completed with 26 candidates, but the initial normalization step failed on a constant-only expression. Numeric constants were already permitted by the preregistered grammar; the adapter incorrectly passed an empty factor signature into an older helper that rejects empty signatures. The correction introduced a separate post-search audit adapter that explicitly handles a constant-only monomial as dimensionless with no registered target path and adds a regression test. No dataset, seed, operator, unit setting, search budget, or acceptance criterion changed after observing the output. The corrected run uploads raw evidence before normalization so a project-side audit failure cannot discard the external record.

## Nonclaims

This is not a measurement of `G`, evidence for gravity, or independent confirmation of a PySR expression. PySR's dimensional penalty is not a project acceptance rule. Repeated recovery does not remove target exposure. The synthetic generation graph is known by construction and is not a general causal-inference method. Two killed mutants do not establish that the machinery is defect-free.
