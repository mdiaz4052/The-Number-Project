# Milestone 6B — PySR target-leakage probe

This experiment tests a boundary of the project's provenance machinery using synthetic data only.

The central distinction is between:

1. **candidate origin** — PySR saw the target, so every emitted expression is a `target_exposed_candidate`;
2. **registered algebraic ancestry** — whether exact registered definitions expand an expression to a nonzero power of `G`; and
3. **known synthetic generation ancestry** — whether a predictor was actually generated from the synthetic target in the preregistered data-generation graph.

The primary endpoint is deterministic and does not depend on PySR recovering any planted equation. Channel C intentionally makes `k_hidden` an atomic registered quantity even though its numerical values are generated as `k_hidden = G * s_hidden`. Therefore the canonical estimator `k_hidden / s_hidden` should be dimensionally valid, have no registered algebraic target path, and still have known target ancestry in the synthetic generation graph.

## Channels

- `A_clean`: clean negative control. `u_clean` and `r_clean` are generated upstream of `G = u_clean / r_clean`.
- `B_registered_leak`: visible positive control. `m_P = sqrt(hbar * c / G)` uses the existing registered Planck-mass dependency.
- `C_hidden_leak`: hidden calibration-path control. `k_hidden = G * s_hidden`, but `k_hidden` is deliberately registered as atomic.

## Candidate-origin rule

Every expression emitted by PySR is permanently labeled `target_exposed_candidate` because the fitting engine had access to the target. Such a candidate is never promotion-eligible. It may motivate a new target-clean preregistered investigation, but the original record cannot be relabeled into stronger evidence.

## PySR role

PySR is an untrusted external candidate generator. Its dimensional penalty is soft and does not control project classification. The permanent checker uses a narrow standard-library AST parser, exact project `Dimension` algebra, exact registered dependency expansion, and the separate synthetic generation DAG.

The external search is pinned to PySR 2.2.0 commit `65b887aeaf97f1c5ae84b0ceffb370551e57ce90`. The actual resolved SymbolicRegression.jl environment must be recorded by the external runner rather than inferred from PySR's `~2.2.0` compatibility range.

## Nonclaims

This is not a measurement of `G`, not evidence for gravity, and not independent confirmation of any PySR expression. A missing registered algebraic target path does not establish calibration, statistical, experimental, causal, or physical independence. Repeated recovery across seeds does not remove target exposure.
