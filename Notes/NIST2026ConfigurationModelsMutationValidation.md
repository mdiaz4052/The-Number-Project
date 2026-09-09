# NIST configuration-model mutation validation

**PROVISIONAL — INDEPENDENT AUDIT PENDING.** These are software assurance controls for the new statistical boundary, not empirical confirmation. Eight requirements were fixed in the sole-file preregistration before candidate-model implementation.

| Frozen requirement | Fault injected into actual production source | Designated independent assertion |
|---|---|---|
| contrast_order | Cyclic corruption of constrained contrast selection | Exact named row inventory for all restricted models |
| dropped_covariance | Delete off-diagonal experimental V entries | Hand-computed correlated two-contrast covariance |
| conditional_covariance | Schur-condition on omitted nuisance contrasts | Marginal variance and scalar quadratic oracle |
| rank_df_policy | Return 3 df for every restriction | Frozen 3/2/2/1 ranks |
| forbidden_input_conditioning | Substitute excluded Table 19 container into source selector | Same authorized numeric projection after terminal/dark-field changes |
| saturated_acceptance | Promote zero-df synthetic fit to scientific acceptance | Explicit non-test and false acceptance flag |
| unsound_display_classification | Use upper bound to flag every display value | Conservative straddle remains unresolved |
| frozen_cutoff_policy | Apply 3-df cutoff to all models | Exact per-df cutoffs and equality rule |

The unmodified baseline runs every designated behavioral test and must survive. A separately scored faulty control drops half the linear display term and must die. An algebraically equivalent quadratic implementation must survive. These controls are distinct from the eight scientific requirements.

Every mutant runs in a temporary source copy using Python -I -B, with explicit before/after import-path validation. Only failures of designated behavioral assertions earn kill credit. Errors, missing/simplified history, malformed syntax, imports, skips, unrelated failures and infrastructure failures invalidate the run. The frozen test mapping, unique patch occurrence, exact changed-source SHA-256 and expected outcomes are checked. A faulty production survivor invalidates the family.

The artifact binds the source, test, helper and note snapshots and the preregistration digest. Its recorded execution contains the assertion-specific evidence. `--check` verifies that evidence and source freshness without re-executing the family. Artifact checks are kept out of behavioral mutation targets, so a stale digest cannot masquerade as a scientific kill. Independent full-container numerical-invariance tests and actual production filesystem/Git closure complement the selector mutant.

The source snapshot must be committed before emitting `nist_2026_configuration_models_mutations_v1.json`. The final local suite and the two new read-only guards validate the emitted artifacts; exact-head CI supplies repository-wide automated attestation. The completed run's counts and immutable source epoch are recorded in the artifact and PR handoff. They do not substitute for Claude's eventual semantic review.
