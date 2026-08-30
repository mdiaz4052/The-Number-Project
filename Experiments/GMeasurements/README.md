# Physical bridge records for G

This directory contains Milestone 4's deterministic contract artifacts. It contains no
experimental dataset and reports no measured value of `G`.

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

## Regeneration

From the repository root, regenerate both JSON files with:

```bash
python3 -m Discovery.physical_bridge
```

Check the committed bytes without rewriting them with:

```bash
python3 -m Discovery.physical_bridge --check
```

The implementation uses only the Python standard library. Exponents and dimensions use
exact `Fraction` arithmetic. Decimal measurement records use `Decimal` and serialize as
base-ten strings; binary floating-point measurement values are rejected.

For the first-principles explanation, read
[`Notes/PhysicalBridgeContract.md`](../../Notes/PhysicalBridgeContract.md). For the review,
experiments, CODATA boundary, and metrology standards supporting the architecture, read
[`Notes/GMeasurementLiterature.md`](../../Notes/GMeasurementLiterature.md).
