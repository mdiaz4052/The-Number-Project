# Physical bridge records for G

This directory contains Milestone 4's deterministic contract artifacts and the first
published-data source-availability pilot. It contains no project-operated experimental
dataset and reports no project measurement of `G`.

`physical_bridge_contract.json` records the general evidence layers, measurement-model
fields, input roles, exact target-path rules, uncertainty requirements, external-reference
boundary, cycle rejection within and across provenance layers, Lean boundary, literature
identifiers, limitations, and nonclaims.

`inverse_square_bridge_example.json` instantiates the contract as an educational skeleton:

```text
theoretical relation: F = G * m_1 * m_2 / r^2
estimator relation:   G_hat = F_hat * r^2 / (m_1 * m_2)
```

The example recursively relates `F_hat` to an angle observation, a force reference, and an
alignment correction. It likewise exposes observation and calibration parents for both
masses and the separation. These are structural placeholders, not readings. The CODATA
2022 reference value is isolated in a terminal post-estimation comparison node and cannot
flow into the estimator, a calibration, a correction, tuning, or acceptance.

The example's Lean link certifies the conditional estimator algebra: if the displayed
inverse-square relation and estimator definition hold with nonzero masses and separation,
then `G_hat = G`. It does not certify the apparatus model or satisfy the empirical,
metrological, uncertainty, or replication axes.

## Assessment axes

The example reports seven separate statuses:

| Axis | Structural-example status | Interpretation |
|---|---|---|
| `dimensional_status` | `satisfied` | Exact `Fraction` dimension arithmetic gives `[G]`. |
| `algebraic_model_status` | `satisfied` | The declared monomial estimator is structurally valid. |
| `registered_target_path_status` | `no_registered_target_path` | No current registered estimator ancestor expands to `G`; this is not experimental independence. |
| `metrological_provenance_status` | `incomplete` | Placeholder chains are present but not documented calibrations. |
| `uncertainty_status` | `incomplete` | Estimates, standard uncertainties, covariance evaluation, and propagation are unpopulated. |
| `empirical_population_status` | `incomplete` | No observations or apparatus records are supplied. |
| `replication_status` | `not_applicable` | There is no empirical result to replicate. |

No single aggregate score is computed.

## First published-data pilot: UW 2000

[`uw_2000_published_data_preregistration_v1.md`](uw_2000_published_data_preregistration_v1.md)
freezes the source, estimator, uncertainty, precision, leakage, acceptance, and terminal-
comparison rules for a proposed reproduction of the University of Washington 2000
angular-acceleration-feedback result.

The original file remains unchanged. A separately recorded
[`clarification`](uw_2000_published_data_preregistration_v1_clarification_1.md) resolves
one pre-transcription ambiguity: exact mathematical constants may remain in exact symbolic
relations, but `exact=True` cannot turn an arbitrary populated decimal record into a
provenance-exempt constant.

[`uw_2000_source_audit_v1.md`](uw_2000_source_audit_v1.md) records the source map and an
explicit **`NO-GO`**. The paper reports the symbolic multipole estimator, apparatus
summaries, correction factors, one-sigma uncertainty budget, and headline result. It does
not report the fitted gravitational angular-acceleration amplitude or the complete
numerical attractor multipole coupling needed to calculate `G_hat`. The proposed 2002 PRD
companion citation is unrelated; the later UW correction identified by CODATA is sourced
to a private communication.

No missing value is guessed, copied from a secondary proposal, or back-solved from the
published `G`. Consequently no UW empirical model or result artifact is created and no
empirical or replication status is promoted. This documented `NO-GO` is a successful
test of the contract's fail-closed behavior, not a criticism of the published experiment.

For any future `empirical_record`, every populated numerical quantity in estimator
ancestry, and every declared calibration or correction, must declare documented
provenance plus a source identifier, edition, and access date. This makes absent source
metadata fail closed. It does not prove that a cited value was experimentally independent
or protect against a knowing editor who fabricates a plausible citation; source auditing
remains an evidence task.

[`uw_2000_published_data_pilot_v1.manifest.json`](uw_2000_published_data_pilot_v1.manifest.json)
pins the exact bytes of the original preregistration, the clarification, and the source
audit, together with the canonical `NO-GO`, missing-input, and next-candidate fields. The
guard is tamper evidence for review; it cannot stop a knowing editor from changing code,
constants, documents, and artifacts together.

## Regeneration

From the repository root, regenerate both JSON files with:

```bash
python3 -m Discovery.physical_bridge
```

Check the committed bytes without rewriting them with:

```bash
python3 -m Discovery.physical_bridge --check
python3 -m Discovery.published_data_pilot --check
```

The implementation uses only the Python standard library. Exponents and dimensions use
exact `Fraction` arithmetic. Decimal measurement records use `Decimal` and serialize as
base-ten strings; binary floating-point measurement values are rejected.

For the first-principles explanation, read
[`Notes/PhysicalBridgeContract.md`](../../Notes/PhysicalBridgeContract.md). For the review,
experiments, CODATA boundary, and metrology standards supporting the architecture, read
[`Notes/GMeasurementLiterature.md`](../../Notes/GMeasurementLiterature.md).
