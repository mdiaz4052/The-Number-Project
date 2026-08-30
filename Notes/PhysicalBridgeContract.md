# Physical bridge contract

Milestones 1--3 checked formal implications, dimensions, and registered algebraic
dependencies. Those are necessary pieces of a careful investigation, but none supplies a
reading from the physical world. Milestone 4 specifies the missing chain:

```text
formal expression
-> physical measurement model
-> operational observables
-> calibration and provenance
-> uncertainty evaluation
-> empirical estimate of G
```

For this project, to **physically establish `G`** means to produce a non-circular,
traceable, uncertainty-qualified estimate of `G` from documented observations under an
explicit physical measurement model, followed by reproducibility and preferably by
comparison across methods with materially different systematic effects. This is an
operational standard of evidence, not a claim of logical certainty.

Milestone 4 defines and validates the contract for that chain. It does not populate it
with experimental observations.

## 1. Dimensions constrain the shape, not the value

The SI dimension of Newton's gravitational constant is

```text
[G] = M^-1 L^3 T^-2.
```

Dimensional equality is a consistency check. It can reject `mass / time` as an expression
for `G`, but it cannot choose one formula from all expressions with the right dimensions.
Milestone 3 made this ambiguity explicit: ten generators give a rank-4 dimensional
system with nullity 6. Any dimensionless multiplier leaves the dimensions unchanged.

Dimensions also contain no numerical reading. A numerical value for a dimensionful
quantity changes when the units change, whereas its dimensional pattern does not. A
physical law and operational data are needed before a value can be estimated.

## 2. Exact Planck reconstructions are dependent controls

The conventional Planck quantities in the registered catalog include `G` in their exact
definitions. For example,

```math
m_P=(\hbar c/G)^{1/2}.
```

Rearranging this equation gives

```math
G=\hbar c/m_P^2.
```

That identity is exact under the definition, and checking it is useful. It is not an
independent determination of `G`: the input called `m_P` already inherited the target.
Using the reconstruction as independent evidence would therefore be circular.
The same target path exists for `l_P`, `m_P`, `t_P`, and `T_P` under the current
registered Planck definitions. Repeated algebra can expose a dependency correctly; it
cannot remove that dependency.

## 3. Law, estimator, and observation answer different questions

Consider the educational inverse-square relation

```math
F=Gm_1m_2/r^2.
```

Three layers must not be collapsed:

| Layer | Example | Meaning |
|---|---|---|
| Physical measurement model | `F = G m_1 m_2 / r^2` | A conditional account of how physical quantities are related in a stated regime. |
| Estimator | `G_hat = F_hat r^2 / (m_1 m_2)` | A rule for computing an estimate from input estimates. |
| Observation | an angle, period, position, balance indication, or acceleration record | Information supplied by an apparatus or procedure. |

Here a physical law or measurement model proposes the relationship to be tested; an
estimator is the inference rule adopted under that model; and an observation is external
information about what an apparatus indicated.

An estimator is not itself an observation. In a real apparatus, `F_hat` is normally
inferred from more primitive observations such as displacement, angle, torque,
oscillation period, or angular acceleration. Its complete provenance must therefore be
expanded recursively. Treating `F_hat` as an unexplained number would hide the most
important experimental assumptions.

## 4. The measurand is what the measurement intends to estimate

A **measurand** is the quantity intended to be measured. Here it is `G` as a parameter of
an explicitly stated Newtonian measurement model, in a declared domain and unit. Naming
the measurand matters because an apparatus directly indicates something else: an angle,
time, position, or balance response. The model maps those indications and calibrated
inputs to an estimate of the measurand.

The contract therefore records the target, theoretical relation, estimator, regime,
hypotheses, input roles, dimensions, units, provenance, corrections, uncertainty model,
and limitations. It cannot silently substitute a convenient observable for the declared
measurand.

## 5. Calibration provenance connects numbers to references

A bare decimal and unit do not show how a value was obtained. A traceable result needs a
documented chain from each input estimate through calibrations to a reference or unit
realization, with every stage contributing uncertainty. The chain may branch because
mass, length, force, angle, and time can have distinct routes.

The code represents provenance as directed edges read as **child depends on parent**. It
keeps two graphs separate:

- the **definitional graph** records algebraic construction; and
- the **metrological graph** records observations, calibrations, corrections, model
  inputs, and terminal comparisons.

Unknown parents, duplicate identifiers, and cycles within either graph or across their
combined dependency relation are rejected. Missing required provenance fails closed: it
is unresolved or incomplete, never silently promoted to a clean result. This reflects the
calibration and traceability vocabulary in
[JCGM 200:2012 (VIM)](https://doi.org/10.59161/JCGM200-2012) and the SI realization
context in the [BIPM SI Brochure](https://doi.org/10.59161/AUEZ1291).

## 6. Algebraic target-cleanliness is weaker than independence

Milestone 3 can expand a registered expression and ask whether a nonzero power of `G`
remains. That is algebraic provenance. Experimental independence is a metrological claim
about the origins of actual observations, calibrations, corrections, and model inputs.

The required distinction is:

```text
No registered algebraic path to G is necessary for a target-clean input,
but it is not sufficient to establish experimental independence.
```

An item marked atomic in the current catalog is simply an endpoint of the registered
substitutions. It has not thereby acquired a calibration history or become physically
independent. For this reason, the bridge never uses a bare status called `independent`.

## 7. The target-path gate reports three honest outcomes

For every estimator input and every recursively reached ancestor, exact `Fraction`
substitution reuses the Milestone 3 dependency catalog. The gate reports:

| Status | Meaning |
|---|---|
| `target_path_detected` | A documented registered expansion reaches a nonzero power of `G`. |
| `no_registered_target_path` | No path reaches `G` under the current complete algebraic records. This is not a claim of independence. |
| `unresolved` | Required ancestry cannot be fully established. |

The gate rejects direct `G`, registered Planck dependence, target-dependent ancestors,
and any calibration or correction chain that consumes a reference `G`. It detects cycles
in both provenance graphs and treats missing records as a reason to stop, not a reason to
pass.

A recommended value such as CODATA 2022 is allowed only in a terminal
`external_comparison_reference` node after `G_hat` has been produced. It cannot enter the
estimator, calibration, correction, candidate selection, tuning, or acceptance threshold.
The checked-in comparison record states its edition, source, unit, standard uncertainty,
and access date.

## 8. Uncertainty is part of a measurement result

An estimate without an uncertainty model is not a complete physical result. Repeated
observations address variability, but the budget must also cover calibration uncertainty,
finite geometry, environmental effects, corrections, model approximations, and other
material systematic contributions.

Applying a correction does not make the associated effect disappear. The correction is
an input estimate and carries its own uncertainty. A missing standard uncertainty is
reported as `incomplete`; the software never invents a zero. The contract requires:

- the measurand and input estimates;
- standard uncertainties and units;
- corrections and uncertainties associated with them;
- correlations or a justified explicit zero-correlation assumption;
- a propagation method; and
- coverage information when applicable.

The structure follows the principles of
[JCGM 100:2008 (GUM)](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf/cb0ef43f-baa5-11cf-3f85-4dcd86f77bd6).
Milestone 4 validates that these fields are declared; it does not implement a general
uncertainty-propagation engine.

## 9. Correlations cannot be assumed away

Two inputs may share an instrument, calibration reference, environmental disturbance, or
data-reduction step. Their errors can then vary together. Propagating their uncertainties
as if they were unrelated can understate or overstate the uncertainty of `G_hat`.

The contract therefore requires either an explicit covariance declaration, a documented
reason for treating correlations as zero, or an `incomplete` marker saying the evaluation
has not been populated. An empty covariance table is not automatically a zero matrix.

## 10. Lean checks implications, not experimental premises

The example links through an explicit Python catalog to

```text
TheNumberProject.EntropicGravity.
force_eq_gravitationalConstant_mul_masses_div_radius_sq
```

Python does not parse Lean source. The existing theorem kernel-checks a conditional
inverse-square force conclusion from its named equations and nonzero hypotheses. It does
not directly certify the estimator rearrangement, so the machine-readable linkage says
`estimator_rearrangement_certified: false`.

Even a direct rearrangement theorem could establish only: **if the stated relation and
side conditions hold, then the algebraic estimator equals `G`**. Lean cannot establish
that an apparatus obeyed the model, a reading occurred, a calibration was correct, every
systematic effect was found, or nature selected a dimensionally valid candidate. Formal
verification secures an inference from premises; empirical work must secure the premises.

## 11. Cross-method comparison tests more than repeated algebra

Repeating the same symbolic identity supplies no new empirical information. Repeating one
apparatus can reveal stability and some run-to-run effects, but it may preserve a shared
blind spot. A beam balance, torsion balance, and atom interferometer use different primary
observables and have materially different dominant systematics. Agreement across such
methods is therefore more informative than repeated algebra or a single-method repeat.

It is still not logical proof. Publication alone is not replication, and agreement does
not demonstrate that every method is bias-free. The experimental motivation for this
separation is summarized in
[`GMeasurementLiterature.md`](GMeasurementLiterature.md).

## 12. What this milestone supplies—and what must come next

Milestone 4 supplies:

- immutable validated records for quantities, provenance edges, uncertainty structure,
  theorem links, and measurement models;
- exact dimensional checking of `G_hat = F_hat r^2 / (m_1 m_2)`;
- separate definitional and metrological acyclic graphs;
- a fail-closed target-leakage audit using the Milestone 3 catalog;
- separate machine-readable assessment axes rather than one score;
- an isolated CODATA comparison boundary;
- uncertainty and correlation requirements; and
- a deterministic, unpopulated inverse-square structural example.

The seven separate axes are:

```text
dimensional_status
algebraic_model_status
registered_target_path_status
metrological_provenance_status
uncertainty_status
empirical_population_status
replication_status
```

Before reporting an empirical estimate, a future experiment would still need a complete
apparatus-specific model, documented observations, calibration records, recursively
expanded force inference, evaluated corrections, an uncertainty and covariance budget,
an estimated value with coverage information, reproducibility evidence, and comparison
that was not used to tune or accept the result. No real dataset, fit, apparatus validation,
or new value of `G` is part of this milestone.

## Artifacts and commands

The general contract and the structural example are stored in:

```text
Experiments/GMeasurements/physical_bridge_contract.json
Experiments/GMeasurements/inverse_square_bridge_example.json
```

Regenerate them or verify their byte-stable committed form from the repository root:

```bash
python3 -m Discovery.physical_bridge
python3 -m Discovery.physical_bridge --check
```

The example intentionally reports `empirical_population_status: incomplete`,
`uncertainty_status: incomplete`, and `replication_status: not_applicable`. Passing the
exact dimensional and registered-target-path checks does not change those empirical axes.

Milestone 4 defines what a non-circular, uncertainty-qualified empirical bridge to `G`
would require. It does not itself measure `G`, validate an apparatus, or turn a Lean
theorem into experimental evidence.
