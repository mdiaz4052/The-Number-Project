# Literature foundation for a physical bridge to G

This note extracts only the architectural lessons needed by Milestone 4. It is not a
history of every measurement, a reanalysis of published data, or an endorsement of one
reported value. A paper's publication does not by itself constitute independent
replication.

The central lesson is that the displayed inverse-square estimator

```math
\widehat G=\widehat F r^2/(m_1m_2)
```

is only the outer shell of a real measurement model. Each experiment uses more primitive
observables and an apparatus-specific forward model for geometry, response, calibration,
corrections, and uncertainty.

## Peer-reviewed review

### Rothleitner and Schlamminger (2017)

C. Rothleitner and S. Schlamminger,
“Invited Review Article: Measurements of the Newtonian constant of gravitation, G,”
*Review of Scientific Instruments* 88, 111101 (2017),
[doi:10.1063/1.4994619](https://doi.org/10.1063/1.4994619).

The review compares the main modern approaches and emphasizes a metrological problem:
published determinations have scattered more than their individual reported uncertainties
would lead one to expect. That is evidence to look for unrecognized systematic effects or
missing uncertainty contributions, not permission to choose a favored result. For this
project it motivates three contract rules:

- do not compress dimensional, algebraic, provenance, uncertainty, and replication
  questions into one score;
- require apparatus-specific uncertainty budgets and corrections; and
- value comparisons across measurement principles whose systematic effects differ.

The review is interpretive context. The experiment-specific statements below are grounded
in the primary papers.

## Peer-reviewed experimental papers

### Gundlach and Merkowitz (2000): angular-acceleration feedback

J. H. Gundlach and S. M. Merkowitz,
“Measurement of Newton's Constant Using a Torsion Balance with Angular Acceleration
Feedback,” *Physical Review Letters* 85, 2869 (2000),
[doi:10.1103/PhysRevLett.85.2869](https://doi.org/10.1103/PhysRevLett.85.2869)
([open manuscript](https://arxiv.org/abs/gr-qc/0006043)).

| Bridge question | Architectural summary |
|---|---|
| Measurement method | A torsion pendulum and rotating source masses are operated with feedback that keeps the fibre twist small. |
| Primary observable | An angle time series from the rotating balance; its second time derivative supplies the angular-acceleration signal, while pendulum deflection is monitored. |
| How `G` enters | The gravitational angular acceleration is proportional to `G` through the modeled multipole coupling between the pendulum and source-mass distribution. |
| Principal reported uncertainty categories | Pendulum width, thickness and flatness; source-sphere masses, diameters, horizontal and vertical separations; dimensional calibration and temperature; residual twist, magnetic and thermal effects; time base, data reduction, and statistical variability. |
| Method-specific effects | Feedback and continuous rotation reduce sensitivity to torsion-fibre anelasticity and low-frequency background, while turntable control, numerical differentiation, multipole corrections, and source-mass geometry become central. |
| Value for independent comparison | Its feedback observable and nearly untwisted operating mode change important systematics relative to free-deflection and time-of-swing torsion balances. That difference makes comparison informative, although the paper alone is not a replication claim. |

This paper is the clearest warning against treating `F` as a primitive number: the force
signal is inferred from angular acceleration, a feedback system, geometry, and a response
model.

The UW pilot used the exact open edition
[`gr-qc/0006043v2`](https://arxiv.org/abs/gr-qc/0006043v2), revised 2000-08-08, for
line-by-line source mapping. The authors' public
[`Big G` apparatus page](https://asd.gsfc.nasa.gov/Stephen.Merkowitz/G/Big_G.html) was
also checked for additional numerical inputs; it is official supporting context, not a
replacement for the paper.

#### Gundlach (1999): prototype and design evidence, not 2000 inputs

J. H. Gundlach, “A rotating torsion balance experiment to measure Newton's constant,”
*Measurement Science and Technology* 10, 454--459 (1999),
[doi:10.1088/0957-0233/10/6/307](https://doi.org/10.1088/0957-0233/10/6/307)
([author-hosted PDF](https://www.npl.washington.edu/eotwash/sites/sand.npl.washington.edu.eotwash/files/documents/mst10-454.pdf)).

This is a valid apparatus-lineage source, but it is explicitly excluded as a source of
numerical inputs for the 2000 result. Its `Q_22 = 0.52 g cm^-3` belongs to a lab-fixed
proof-of-principle Pb attractor that the paper says is about five times weaker than the
planned `G` source. Its Table 1 is a proposed approximate budget, not the 2000 result's
uncertainty budget. Its `125 mm`, approximately `8 kg`, `16.5 cm` design geometry also
differs from the PRL's as-built `124.89 mm`, approximately `8.140 kg`, `16.76 cm` values.
These plausible values must not be substituted for the missing 2000 coupling, measured
budget, or apparatus geometry.

The 2002 CODATA adjustment review, P. J. Mohr and B. N. Taylor, “CODATA recommended
values of the fundamental physical constants: 2002,” *Reviews of Modern Physics* 77,
1--107 (2005), [doi:10.1103/RevModPhys.77.1](https://doi.org/10.1103/RevModPhys.77.1)
([official NIST PDF](https://physics.nist.gov/cuu/pdf/CODATA_RMP2005.pdf)), records on
journal p. 45 that Gundlach and Merkowitz later identified an additional fractional
correction of `6.0e-6` caused by magnetic-damper torque. Its reference list on journal
p. 102 identifies “Gundlach, J. H., and S. M. Merkowitz, 2002” as a private
communication. It is therefore historical comparison evidence, not a public companion
input set.

The suggested citation *Physical Review D* 66, 082001 (2002),
[doi:10.1103/PhysRevD.66.082001](https://doi.org/10.1103/PhysRevD.66.082001), is Milani
et al., “Testing general relativity with the BepiColombo radio science experiment.” It is
recorded here as a bibliographic exclusion so it cannot be reused as UW apparatus
evidence.

### Schlamminger et al. (2006): beam balance

S. Schlamminger et al., “Measurement of Newton's gravitational constant,”
*Physical Review D* 74, 082001 (2006),
[doi:10.1103/PhysRevD.74.082001](https://doi.org/10.1103/PhysRevD.74.082001)
([open manuscript](https://arxiv.org/abs/gr-qc/0609027)).

| Bridge question | Architectural summary |
|---|---|
| Measurement method | A beam balance alternately weighs two test masses while large mercury field masses move between configurations. |
| Primary observable | Differences of test-mass weight differences between the field-mass configurations—the gravitational signal indicated by the balance. |
| How `G` enters | `G` scales an integral of the inverse-square interaction over the measured test- and field-mass distributions; the observed signal is compared with that mass-integration model. |
| Principal reported uncertainty categories | Statistical weighings; test-mass sorption; balance linearity and zero-point behavior; calibration; masses, dimensions, positions, density constraints, and the resulting mass-integration constant. |
| Method-specific effects | A small gravitational signal sits on a much larger weight, making balance drift, nonlinearity, calibration, and temperature-dependent surface sorption important. Mercury-vessel geometry, density, deformation, air density, and correlated geometric constraints matter to the field model. |
| Value for independent comparison | Direct force comparison with a beam balance has substantially different readout and dominant effects from torsion methods. That makes it useful for cross-method diagnosis, without implying that either method is automatically free of hidden bias. |

The paper explicitly uses covariance for constrained geometric quantities. It is a concrete
example of why shared inputs cannot simply be declared uncorrelated.

### Rosi et al. (2014): cold-atom interferometry

G. Rosi et al., “Precision measurement of the Newtonian gravitational constant using
cold atoms,” *Nature* 510, 518--521 (2014),
[doi:10.1038/nature13433](https://doi.org/10.1038/nature13433)
([open manuscript and methods](https://arxiv.org/abs/1412.7954)).

| Bridge question | Architectural summary |
|---|---|
| Measurement method | Two simultaneous atom interferometers form a gravity gradiometer while characterized tungsten source masses move between configurations. |
| Primary observable | Differential atom-interferometer phase, interpreted as the change in differential acceleration of laser-cooled atomic clouds. |
| How `G` enters | A gravitational-field model, evaluated for the source-mass distribution and atomic trajectories, predicts the phase or acceleration difference proportional to `G`. |
| Principal reported uncertainty categories | Statistical phase data; atomic-cloud sizes and positions; launch direction and apogee timing; source-cylinder mass, position, and density inhomogeneity; detection region, source support and translation geometry; air-density and phase-fitting corrections; smaller gravity-gradient, laser-vector, mirror-tilt, and timing effects. |
| Method-specific effects | Atomic trajectories, Raman-laser geometry, cloud phase-space distributions, ellipse fitting, and a Monte Carlo field/trajectory model replace many torsion-fibre effects. Source-mass characterization remains shared in broad form. |
| Value for independent comparison | A quantum phase and freely falling atoms provide a materially different sensor and density regime from macroscopic balances. Agreement or disagreement can therefore probe a different collection of systematics; one paper is still not external replication. |

This experiment illustrates that a different sensor does not eliminate the need for
classical geometry, source-mass characterization, corrections, and uncertainty.

### Li et al. (2018): two torsion-pendulum methods

Q. Li et al., “Measurements of the gravitational constant using two independent
methods,” *Nature* 560, 582--588 (2018),
[doi:10.1038/s41586-018-0431-5](https://doi.org/10.1038/s41586-018-0431-5)
([official supplementary information](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-018-0431-5/MediaObjects/41586_2018_431_MOESM1_ESM.pdf)).

| Bridge question | Architectural summary |
|---|---|
| Measurement method | Two determinations use time-of-swing (ToS) and angular-acceleration-feedback (AAF) torsion-pendulum methods. |
| Primary observable | ToS uses the change in the pendulum's oscillation period as source masses change position. AAF uses turntable angle/acceleration under feedback that minimizes pendulum twist. |
| How `G` enters | For ToS, `G` changes the gravitational contribution to the torsional restoring response and hence the oscillation frequency. For AAF, `G` scales the modeled gravitational angular acceleration balanced by the feedback motion. |
| Principal reported uncertainty categories | Both require source- and pendulum-mass geometry, density distributions, relative positions, environmental controls, and statistical evaluation. ToS additionally depends strongly on period estimation, moment of inertia, fibre anelasticity and drift; AAF depends strongly on angle scale, turntable motion, feedback, residual twist, and angular-acceleration extraction. |
| Method-specific effects | ToS reads a frequency shift in a freely oscillating system; AAF reads controlled angular acceleration with the fibre held near zero twist. The distinct dynamics exchange one set of torsion-fibre and readout sensitivities for another. |
| Value for independent comparison | Applying two dynamical methods makes shared and method-specific effects more visible. Because they were performed by one collaboration and retain some common metrology, their comparison is valuable but is not the same as external reproduction by an unrelated apparatus. |

The word “independent” in the paper title describes the two determinations. The Milestone 4
software deliberately avoids turning that word into a generic machine status: a defensible
independence claim must say exactly which algebraic, calibration, apparatus, personnel, and
analysis dependencies are or are not shared.

The official supplement is the source-completeness reason to audit the AAF determination
next: it publishes an estimator relation, aggregate coupling and angular-acceleration
values, magnetic-damper parameters, standard-uncertainty convention, and a stated
cross-run correlation treatment. Those are candidate locators only until a separate
preregistration and full source map reach `GO`.

## Adjusted external reference

P. J. Mohr, D. B. Newell, B. N. Taylor, and E. Tiesinga,
“CODATA recommended values of the fundamental physical constants: 2022,”
*Journal of Physical and Chemical Reference Data* 54, 033105 (2025),
[doi:10.1063/5.0279860](https://doi.org/10.1063/5.0279860).

The CODATA 2022 values come from a least-squares adjustment using theoretical and
experimental information available through 31 December 2022. A recommended `G` is
therefore an adjusted reference, not a fresh operational observation and not timeless
calibration data for a proposed determination.

The structural artifact records the edition, source, unit, standard uncertainty, and
access date for this value, and gives it only the role
`external_comparison_reference`. It may be used after producing an estimate to describe a
difference. It may not calibrate an input, supply a correction, tune candidates, establish
an acceptance threshold, or decide which result to report.

## Authoritative metrology standards and reference documents

These documents are standards or authoritative references, not peer-reviewed experimental
papers:

1. **JCGM 100:2008**, *Evaluation of measurement data—Guide to the expression of
   uncertainty in measurement* (GUM),
   [official PDF](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf/cb0ef43f-baa5-11cf-3f85-4dcd86f77bd6).
   It grounds the requirement to state a measurement model, input estimates, standard
   uncertainties, covariance information, propagation, and coverage. A correction does
   not erase uncertainty in the corrected effect.

2. **JCGM 200:2012**, *International vocabulary of metrology—Basic and general concepts
   and associated terms* (VIM),
   [doi:10.59161/JCGM200-2012](https://doi.org/10.59161/JCGM200-2012).
   It supplies the vocabulary for measurand, measurement result, calibration,
   metrological traceability, calibration hierarchy, and traceability chain. The contract's
   graph makes these dependencies explicit rather than attaching the word “traceable” to
   an unexplained value.

3. **BIPM**, *The International System of Units (SI Brochure)*, 9th edition (2019),
   version 4.01 (June 2026),
   [doi:10.59161/AUEZ1291](https://doi.org/10.59161/AUEZ1291).
   It provides current SI definition and realization context. Defining a unit and realizing
   it in a calibration chain are related but distinct tasks; a reported measurement result
   needs both an estimated value and associated uncertainty.

## Lessons encoded in the contract

Across these methods, `G` is not read directly. The route is always something like:

```text
angle / period / balance indication / atom phase
-> calibrated physical input estimates
-> apparatus and source-mass model
-> corrections and covariance
-> estimate of G with uncertainty
```

The observables and dominant systematic effects change with the method. Source-mass
geometry and weak-signal extraction recur, but torsion-fibre anelasticity, balance
nonlinearity and sorption, laser/atomic trajectories, or feedback differentiation do not
enter every method in the same way. This is why the physical bridge records recursive
provenance and separate uncertainty contributions, and why cross-method comparison is more
informative than a second symbolic rearrangement of the same equation.
