# HUST 2018 AAF individual depth-2b MeasurementModels — preregistration v1

Status: FROZEN BEFORE MILESTONE 7B IMPLEMENTATION

Baseline: `715c189818dea258f3c6d447d7854226c1f2a575` (merged PR #33 / Milestone 7A)

Target publication: Q. Li et al., “Measurements of the gravitational constant using two independent methods,” *Nature* 560, 582–588 (2018), DOI `10.1038/s41586-018-0431-5`.

Target method: angular-acceleration feedback (AAF) only.

## Disclosure and purpose

This is an implementation preregistration, not a blind scientific preregistration. The three depth-2a central reconstructions, the Nature Table 1 values, the feasibility decision, and the expected RSS results were known before this document was written. This document freezes how those already-disclosed inputs may be converted into three production depth-2b records.

The milestone will construct one uncertainty-qualified published reconstruction for each of `AAF-I`, `AAF-II`, and `AAF-III`. It will not construct or authorize a combined AAF estimator.

## Blocking source precondition

Before any production `MeasurementModel` consumes Table 1, the implementation must obtain and hash an official Nature-served article artifact containing Table 1. Its record must include the canonical Nature URL, DOI, response/content type, PDF magic validation when applicable, byte length, SHA-256, access date, exact Table 1 locator, storage status, and a caveat that equivalent publisher delivery paths may produce different bytes.

Publisher bytes must not be committed unless redistribution is clearly authorized. A metadata-and-hash record is sufficient.

If an official Nature-served artifact cannot be obtained, Milestone 7B stops at a documented production `NO_GO`. The third-party mirror, the earlier conversation screenshot, the displayed Table 1 totals, and the published final uncertainties are not substitutes for this precondition.

## Frozen scopes and component table

The three scopes are independent. Each must contain exactly the following 21 applicable Table 1 rows, in this order, as direct relative standard-uncertainty contributions in ppm of `G`:

| Component identifier | AAF-I | AAF-II | AAF-III |
|---|---:|---:|---:|
| `pendulum_dimensions` | 0.16 | 0.16 | 0.16 |
| `pendulum_attitude` | 0.06 | 0.06 | 0.03 |
| `pendulum_density_inhomogeneity` | 0.46 | 0.46 | 0.46 |
| `coating_layer` | 0.34 | 0.34 | 0.34 |
| `clamp_and_ferrule` | 0.70 | 1.05 | 0.48 |
| `other_pendulum_effects` | 0.29 | 0.29 | 0.29 |
| `source_mass_masses` | 0.32 | 0.31 | 0.31 |
| `horizontal_source_mass_distance` | 8.98 | 8.98 | 8.98 |
| `vertical_source_mass_distance` | 5.79 | 5.79 | 5.79 |
| `source_mass_positions_alignment` | 0.57 | 0.62 | 0.35 |
| `fibre_anelasticity` | 0.01 | 0.01 | 0.01 |
| `thermal_effect` | 0.91 | 0.91 | 0.91 |
| `time_base` | 0.01 | 0.01 | 0.01 |
| `rotating_gravity_gradient` | 1.86 | 1.35 | 1.72 |
| `shelf_deformation` | 1.51 | 1.51 | 1.51 |
| `magnetic_damper` | 1.95 | 1.95 | 0.08 |
| `air_density` | 1.00 | 1.51 | 1.13 |
| `magnetic_field` | 3.98 | 3.98 | 0.90 |
| `angle_encoder` | 0.72 | 0.72 | 0.72 |
| `residual_twist_angle` | 0.03 | 0.61 | 0.45 |
| `statistical_angular_acceleration` | 3.44 | 2.60 | 1.34 |

The Table 1 AAF rows `fibre_nonlinearity`, `gravitational_nonlinearity`, and `electrostatic_field` are not applicable. They must remain explicit exclusions and must not be represented as zero-valued applicable components.

## Frozen arithmetic

All result-driving arithmetic uses `Decimal` under a local precision of 50. Binary floats are forbidden.

For each scope, using only its 21 component values:

```text
sum_of_squares = Σ u_i²
u_relative_ppm = sqrt(sum_of_squares)
u_absolute_G = abs(G_hat) × u_relative_ppm × 1e-6
```

`G_hat` is the already-reconstructed depth-2a central value for the same scope. No rounding or quantization is applied to either reconstructed uncertainty before serialization.

The disclosed sanity values are:

| Scope | Sum of squares | Reconstructed relative standard uncertainty |
|---|---:|---:|
| AAF-I | `155.0861` | `12.453356977136727047866320298865297714729175627210 ppm` |
| AAF-II | `150.6924` | `12.275683280371809918505072305209443766741467830010 ppm` |
| AAF-III | `125.7279` | `11.212845312408443280940946155017027106000868654421 ppm` |

These numbers are post-computation checks. Production code must not read them as inputs.

## Source and derivation classification

The Table 1 component values are `PUBLIC_DIRECT` once independently re-established from the official Nature-served artifact.

The individual RSS rule is `PUBLIC_DERIVABLE`, not `PUBLIC_DIRECT`. The clarification record must distinguish:

1. the article's direct statements that Table 1 is the main one-standard-deviation error budget and the Supplementary Information's direct statements about cross-run treatment; and
2. the project's derivation that an individual Table 1 column reproduces its displayed total by RSS within the rounding envelope.

Each individual within-result correlation policy and each `complete_uncertainty_model` authorization are also `PUBLIC_DERIVABLE` and must depend on the pinned component table plus the explicit derivation record.

The model may use `EXPLICIT_ZERO_ASSUMPTION` only as a qualified representation of the published individual RSS budget. It must not claim physical independence among all systematic error sources.

The independently audited dominant-pair bounds must be recomputed from the declared rounding envelope rather than copied as assertions. The disclosed approximate checks are `|rho| < 0.0032` for AAF-I and AAF-II, and `|rho| < 0.0025` for AAF-III.

Cross-run covariance is irrelevant to these three individual reconstructions and remains reserved for a separately authorized combined estimator.

## Model-construction contract

For each scope, the production builder must:

1. begin from the already-validated depth-2a central model;
2. preserve its `G_hat` central value exactly;
3. add exactly 21 independently keyed `uncertainty_component` quantities;
4. give each component dimension `dimensionless`, unit `ppm`, no uncertainty-on-uncertainty, documented provenance, the pinned DOI, official source description, and access date;
5. derive the relative RSS from the component quantities only;
6. derive the target standard uncertainty from that scope's reconstructed `G_hat` only;
7. attach `direct_measurand_contributions` uncertainty mode;
8. keep coverage factor and coverage probability absent while recording that the source values are one-standard-deviation standard uncertainties;
9. keep replication identifiers empty and the Lean link absent; and
10. pass an apparatus-specific validator for source binding, exact inventory, order, scope, precision, and arithmetic.

Expected evidence axes for each valid record:

```text
dimensional_status: satisfied
algebraic_model_status: satisfied
registered_target_path_status: no_registered_target_path
metrological_provenance_status: satisfied
uncertainty_status: satisfied
empirical_population_status: satisfied
replication_status: incomplete
```

## Target isolation

The following values are terminal comparisons only and may not enter estimator or uncertainty ancestry:

- published AAF-I: `6.674534(83) × 10^-11 m^3 kg^-1 s^-2`;
- published AAF-II: `6.674375(82) × 10^-11 m^3 kg^-1 s^-2`;
- published AAF-III: `6.674535(75) × 10^-11 m^3 kg^-1 s^-2`;
- displayed Table 1 totals: `12.45`, `12.27`, and `11.21 ppm`;
- combined AAF: `6.674484(78) × 10^-11 m^3 kg^-1 s^-2` and `11.61 ppm`.

Changing a terminal published value, published final uncertainty, or displayed total must not change a reconstructed central value or uncertainty.

Copying a published final uncertainty onto `G_hat`, importing an external comparison value upstream, crossing AAF scopes, or authorizing a combined scope must fail closed.

`combined_aaf_reconstruction_authorized` remains exactly `false` in every new authorization artifact.

## Versioning and preservation

Create new versioned authorization and MeasurementModel artifacts. Do not overwrite or relabel the historical depth-2a model, source-audit graph, feasibility record, or their manifests.

The historical records must remain byte-identical. Their earlier statements may be described as historical outcomes, but they must not be rewritten to pretend they reached depth 2b earlier.

The implementation must record the real transcription chronology: the repository history does not establish which source supplied the initial PR #32 21-by-3 transcription. The production transcription must be independently re-established against the newly pinned official artifact without inventing a cleaner historical origin.

## Frozen adversarial tests

Tests must reject or detect at least:

- missing, extra, duplicate, renamed, reordered, wrong-unit, wrong-role, wrong-source, or cross-column components;
- a sum instead of RSS, a missing square, a missing square root, or an incorrect ppm conversion;
- default precision 28 substituting for the frozen precision 50 where the serialized result differs;
- use of a displayed total or published final uncertainty as a computational input;
- mutation of a published comparison affecting reconstructed output;
- bypass of the official Nature source pin;
- an overclaim of byte identity or a falsified source locator;
- unknown clarification or source-record keys, including `target_derived_note`;
- a correlation justification that claims experimental independence;
- cross-scope ancestry or combined-scope authorization;
- loss of the component-ancestry contribution to the metrological evidence axis; and
- drift in any historical artifact.

Mutation scoring must count only behavioral-test failures. Tree-state sentinels and source-state `--check` guards are excluded from kill scoring.

## Definition of done

Milestone 7B is complete only when:

- the preregistration has a separately committed remote anchor record;
- the official Nature artifact precondition is satisfied;
- the versioned authorization graph classifies all three scopes at depth `2b`;
- all three new MeasurementModels serialize deterministically with the expected evidence axes;
- every required behavioral and mutation test passes for the intended reason;
- historical artifacts remain byte-identical;
- the full Python suite and every permanent guard pass from a fresh clean checkout;
- GitHub Verify passes both Python and Lean jobs at the final head;
- Claude independently audits the final head; and
- any merge uses **Create a merge commit**, never squash or rebase.

## Nonclaims

This milestone reconstructs published empirical central values and standard uncertainties. It does not create a new measurement of `G`, reproduce raw or run-level data, validate the apparatus, establish that the authors found every systematic effect, independently replicate the experiment, authorize a combined HUST AAF value, extend a Lean theorem, or make a novel physical prediction.
