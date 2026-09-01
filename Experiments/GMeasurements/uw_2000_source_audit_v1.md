# UW 2000 published-data source audit v1

**Decision: `NO-GO`**  
**Audit date:** 2026-09-01  
**Governing preregistration:**
[`uw_2000_published_data_preregistration_v1.md`](uw_2000_published_data_preregistration_v1.md)  
**Normative clarification:**
[`uw_2000_published_data_preregistration_v1_clarification_1.md`](uw_2000_published_data_preregistration_v1_clarification_1.md)
**Empirical record created:** no

The original preregistration, its clarification, and this audit are content-pinned by
[`uw_2000_published_data_pilot_v1.manifest.json`](uw_2000_published_data_pilot_v1.manifest.json).
The clarification resolves how exact mathematical constants may be represented under the
current schema; it does not alter the `NO-GO` decision or any UW result-sensitive rule.

The public record is sufficient to understand the University of Washington method and
to transcribe its published correction and uncertainty summaries. It is not sufficient
to reconstruct `G` independently from documented numerical inputs. In particular, the
publication does not report the fitted gravitational angular-acceleration amplitude or
the complete numerical attractor multipole field used with it. Either missing quantity
could be manufactured by inverting the published `G`; this audit forbids that operation.

This `NO-GO` is a result about independent transcribability from the identified public
record. It does not challenge the authors' experiment or published result.

## 1. Evidence set and bibliographic identity

### Accepted primary source

- J. H. Gundlach and S. M. Merkowitz, “Measurement of Newton's Constant Using a
  Torsion Balance with Angular Acceleration Feedback,” *Physical Review Letters* 85,
  2869--2872 (2000), DOI
  [`10.1103/PhysRevLett.85.2869`](https://doi.org/10.1103/PhysRevLett.85.2869).
- Open manuscript used for line-by-line access: arXiv
  [`gr-qc/0006043v2`](https://arxiv.org/abs/gr-qc/0006043v2), revised 2000-08-08.
- The authors' public apparatus page was checked for additional numerical material. It
  repeats the method and headline result but supplies no missing fit or multipole table:
  [University of Washington Big G Measurement](https://asd.gsfc.nasa.gov/Stephen.Merkowitz/G/Big_G.html).

### The proposed 2002 “companion” does not exist as cited

DOI [`10.1103/PhysRevD.66.082001`](https://doi.org/10.1103/PhysRevD.66.082001)
is A. Milani et al., “Testing general relativity with the BepiColombo radio science
experiment.” It has different authors and subject matter and is excluded.

The official 2002 CODATA review describes a later 6.0 ppm magnetic-damper correction and
lists “Gundlach and Merkowitz, 2002, private communication” in its references. See P. J.
Mohr and B. N. Taylor, *Rev. Mod. Phys.* 77, 1--107 (2005), journal p. 44 and reference
list p. 101, [NIST PDF](https://physics.nist.gov/cuu/pdf/CODATA_RMP2005.pdf). The minimal
verifying excerpt is “private communication.” This is not a public companion paper and
does not close the input gap.

## 2. Published estimator relation

The primary paper gives the full multipole relation in Eq. (1), the dominant
`l = m = 2` term in Eq. (2), the ideal plate ratio in Eq. (3), the approximate relation

```text
alpha(phi) ~= -sqrt(24*pi/5) * G * Q_22 * sin(2*phi)
```

in Eq. (4), the finite rectangular-plate ratio in Eq. (5), and the first surviving
higher-multipole ratio in Eq. (6). The source says, “Table I contains the numeric values”
for the `alpha_62` and `alpha_82` corrections. These locators establish the symbolic
model and some correction factors, not a complete numerical estimator instance.

A faithful numerical reconstruction needs at least the fitted `2*omega_d` acceleration
amplitude, the numerical external-field coupling (`Q_22` or an equivalently complete
aggregate coupling), the finite-pendulum treatment, every applied correction, and the
combination rule for the six runs and two sphere sets. The first two indispensable
numerical inputs are absent.

## 3. Core numerical source map

All values below are copied from the accepted primary manuscript unless a different
source is named. `NR` means not reported. Bounds and approximations are not relabeled as
standard uncertainties.

| Quantity and physical meaning | Value, unit, reported uncertainty | Exact locator | Direct or derived; role | Provenance parents and shared sources | Target-reversal risk | Independently transcribable? |
|---|---|---|---|---|---|---|
| `alpha_2omega`, fitted gravitational angular-acceleration signal | **NR**, `rad s^-2`; fit scatter not tabulated | PRL pp. 2870--2871, data-reduction paragraph; Fig. 2 is illustrative | Observation; required estimator numerator | Twice-differentiated encoder angle, timing, twenty-cycle least-squares fits, run pairing | **Yes.** It could be back-solved from published `G` and a coupling value. | **No; essential.** |
| `Q_22`, external quadrupole field, or equivalent aggregate coupling | **NR**, expected `kg m^-3`; uncertainty NR | PRL Eqs. (1), (2), and (4), pp. 2869--2870 | Calibration/model input | Individual sphere masses, density distributions, diameters, and measured three-dimensional coordinates | **Yes.** It could be back-solved from published `G` and the missing signal. | **No; essential.** |
| `q_22 / I`, pendulum quadrupole-to-inertia ratio | Eq. (5) from `w` and `t`; no evaluated value or standard uncertainty | PRL Eqs. (3) and (5), p. 2869 | Derived model input | Pendulum width, thickness, shape, attachment, and imperfections | Not inherently; the formula is target-free. | Partial only; the idealized ratio is derivable, while the implemented finite/imperfection treatment is not fully expanded. |
| Pendulum thickness `t` | `1.506 mm`; Table II gives thickness/flatness bound `<4.0 micrometre`, contribution `4.0 ppm` | PRL apparatus paragraph, p. 2870; Table II | Direct geometry/model input | Dimensional metrology; detailed calibration record NR | No evident algebraic route, but source independence cannot be proved from the summary. | Nominal value only. |
| Pendulum width `w` | `76 mm`; Table II gives width bound `<20 micrometre`, contribution `0.4 ppm` | Same apparatus paragraph; Table II | Direct geometry/model input | Dimensional metrology | Same limitation | Nominal value only. |
| Pendulum height `h` | `41.6 mm`; standard uncertainty NR | Same apparatus paragraph; Eq. (6) design discussion | Direct geometry/model input | Dimensional metrology | Same limitation | Nominal value only. |
| Sphere radial centre location `rho` | `16.76 cm`; standard uncertainty NR | PRL apparatus paragraph, p. 2870 | Direct geometry/model input | Before/after sphere-position measurements and attractor assembly | Same limitation | Nominal value only; not the complete coordinates. |
| Attractor sphere diameter | average `124.89 mm`; Table II bound `<1.5 micrometre`, contribution `2.6 ppm` | Same apparatus paragraph; Table II | Direct calibration/model input | Multiple spheres; shared machining and dimensional calibration | Same limitation | Average only; individual values and correlations NR. |
| Attractor sphere mass | approximately `8.140 kg`; Table II bound `<3.0 mg`, contribution `0.4 ppm` | Same apparatus paragraph and ref. 11; Table II | Calibrated model input | Comparator balance; certificate `1170W` named but not included | Could be independently calibrated, but the public value is approximate. | No; individual masses and certificate data NR. |
| Horizontal distance calibration | ball bar calibrated to within `0.2 micrometre`; contribution `1.4 ppm` | PRL distance-measurement paragraph and ref. 12; Table II | Calibration | NIST test report, internal control `M6482`, not included | No declared target path; real-world independence not machine-proved. | Calibration claim is reported, underlying report unavailable here. |
| Difference angular velocity `omega_d` | `20.01015 mrad s^-1`; standard uncertainty NR | PRL operating-frequency paragraph, p. 2870 | Observation/model input | Encoder and time base | No evident target route | Directly transcribable, but not enough to recover the fitted signal. |
| Pendulum-turntable rate `omega_i` | approximately `5.3 mrad s^-1`; standard uncertainty NR | Same paragraph | Operating condition | Encoder and time base shared with `omega_d` | No evident target route | Approximate only; not material after the reported tests. |
| DSP averaging interval `tau` | exactly `1 s`; time-base contribution `<10^-7` or `0.1 ppm` | PRL timing paragraph, p. 2870; data-reduction paragraph and Table II | Calibration/model input | Quartz oscillator calibrated by GPS; shared by rates and derivatives | No evident target route | Reported sufficiently for the published averaging factor. |
| Numerical derivative increment `Delta t` | `10 s`; uncertainty NR | PRL data-reduction paragraph, p. 2871 | Model/data-reduction input | Recorded turntable angles and time base | No evident target route | Reported sufficiently for the published derivative factor. |
| Run structure and combination | six runs of about three days; paired configurations and two sphere sets; numerical fit values and weights NR | PRL acquisition and result-combination paragraphs; Fig. 3 | Observation aggregation | Shared apparatus, sphere-set swaps, individual fit scatter | **Yes** if missing run values are replaced from headline `G`. | No; essential to reproduce the reported aggregation. |
| Initial published `G` | `(6.674215 +/- 0.000092) * 10^-11 m^3 kg^-1 s^-2` | PRL Eq. (7), p. 2871 | **Terminal comparison output only** | Authors' complete unpublished/unsummarized reduction chain | This is the target; reversing it is prohibited. | Reported, but cannot serve as an input. |
| Later UW value in CODATA review | `6.674255(92) * 10^-11 m^3 kg^-1 s^-2`; additional `6.0 ppm` magnetic-damper correction | CODATA 2002 review, Table X and journal p. 44 | Historical terminal comparison/correction notice | PRL result plus 2002 private communication | Reversing it is prohibited; the underlying private record is unavailable. | No independent transcription. |

The directly reported geometry summaries are not silently promoted into a complete
`Q_22`. Doing so would require assumptions about individual masses, sphere density and
shape, all measured coordinates, temperature corrections, and the exact numerical
integration described but not published.

## 4. Reported correction map

PRL Table I reports these multiplicative factors. They are directly reported
corrections, not values derived in this audit. No standard uncertainties or covariance
matrix are attached to the individual factors.

| Correction | Factor | Locator | Role and parents | Sufficient for transcription? |
|---|---:|---|---|---|
| Finite pendulum thickness | `1.0007857` | PRL Table I; Eq. (5) supplies the idealized relation | Correction; `w`, `t`, pendulum model | Factor yes; derivation audit partial. |
| Pendulum attachment and imperfections | `1.0000433` | PRL Table I | Correction; detailed geometry NR | Factor yes; provenance expansion incomplete. |
| `alpha_62` | `0.9998767` | PRL Table I; Eq. (6) | Correction; `w`, `t`, `rho` | Factor yes. |
| `alpha_82` | `0.9999951` | PRL Table I | Correction; higher multipole calculation NR | Factor yes; derivation not published. |
| One-second data averaging | `1.0000667` | PRL Table I; attenuation relation in data-reduction paragraph | Correction; `tau`, `omega_d` | Factor and relation reported. |
| Numerical derivatives | `1.0134544` | PRL Table I; derivative attenuation relation | Correction; `Delta t`, `omega_d` | Factor and relation reported. |
| Product labeled “Total” | `1.0142322` | PRL Table I | Derived product of listed factors | Arithmetically checkable, but it cannot repair missing signal/coupling inputs. |

The paper also describes pressure-dependent air-density and thermal-expansion corrections
without publishing their run-level values. Their residual effects appear in the
uncertainty budget, but an independent run-level correction cannot be reconstructed.

## 5. Reported uncertainty map

PRL Table II is labeled a one-sigma error budget. The listed relative contributions are:

| Component | Reported measurement bound | Relative contribution (ppm) | Role / shared source note |
|---|---:|---:|---|
| Pendulum width | `<20 micrometre` | `0.4` | Geometry calibration; shared with finite-plate model. |
| Pendulum thickness and flatness | `<4.0 micrometre` | `4.0` | Geometry calibration; shared with finite-plate and imperfection corrections. |
| Attractor diagonal separation | `<1.0 micrometre` | `7.1` | Dominant position calibration; common assembly and metrology. |
| Ball-bar calibration | `<0.2 micrometre` | `1.4` | NIST length-reference calibration shared with separation. |
| Attractor vertical separation | `<1.0 micrometre` | `5.2` | Position calibration. |
| Sphere diameter | `<1.5 micrometre` | `2.6` | Shared sphere geometry. |
| Temperature | `<100 mK` | `6.9` | Shared thermal expansion of attractor assembly. |
| Sphere mass | `<3.0 mg` | `0.4` | Shared comparator/reference route. |
| Air humidity | NR | `0.5` | Air-density correction. |
| Residual twist angle | NR; text assigns about `0.35 ppm` | `0.3` | Residual feedback effect. |
| Magnetic fields | exaggerated-field test `(6 +/- 8) * 10^-12 rad s^-2` | `0.6` | Systematic test observation, not the main signal. |
| Rotating temperature gradient | heater test `(21 +/- 22) * 10^-12 rad s^-2` | `0.4` | Systematic test observation. |
| Time base | `<10^-7` | `0.1` | Common clock/encoder derivative route. |
| Data reduction | NR | `2.0` | Shared fitting and numerical differentiation. |
| Statistical error | scatter of individual fits | `5.8` | Observation repeatability. |
| **Total** | quadrature rule stated | **`13.7`** | Published combined one-sigma relative uncertainty. |

The source says the “statistical error was derived from the scatter” and that the total
is a quadrature sum. It does not publish a covariance matrix or a component-by-component
correlation assessment. The table is enough to reproduce the displayed total after
interpreting the listed components as the paper instructs; it is not enough to verify
that every material correlation or shared calibration source was modeled.

## 6. Why the decision is `NO-GO`

Each of the first two gaps is decisive; the remaining gaps reinforce the decision:

1. The fitted gravitational `2*omega_d` angular-acceleration amplitude is not reported.
2. `Q_22` or an equivalent complete attractor coupling is not reported.
3. Individual source-mass values, complete measured coordinates, and the numerical
   integration inputs needed to derive that coupling are not reported.
4. Run-level fit results and numerical combination weights are not reported.
5. Several run-level corrections are described without values, and correlations among
   shared sources are not documented.
6. The purported 2002 PRD companion is unrelated; the actual 2002 update cited by CODATA
   is a private communication.

The missing signal and coupling cannot be treated as merely absent uncertainty details:
they are the two sides of the numerical estimator. Supplying either by reversing Eq. (7)
would produce target leakage. Copying Eq. (7) would produce a published-output record,
not a reconstruction.

No apparatus-specific `MeasurementModel`, empirical JSON record, Lean link, computed
`G_hat`, or promoted empirical/replication status is therefore created for UW 2000.

## 7. Next candidate

The next source-availability audit should examine the HUST 2018
angular-acceleration-feedback result in Q. Li et al., *Nature* 560, 582--588,
DOI [`10.1038/s41586-018-0431-5`](https://doi.org/10.1038/s41586-018-0431-5), using the
[official supplementary information](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-018-0431-5/MediaObjects/41586_2018_431_MOESM1_ESM.pdf).

This recommendation is based on source completeness, not the experiment's fame or
agreement with a preferred value. The supplement gives the AAF estimator relation,
reports the aggregate `l = 2..10, m = 2` coupling and average angular acceleration in
Supplementary Table 3, reports magnetic-damper parameters in Supplementary Table 1, and
states a correlation policy for combining the three AAF runs in Section 6. Its tables
state, “Uncertainties are quoted as one standard deviation.”

On preliminary inspection, the reported aggregate coupling can be represented as one
source-backed calibration quantity, avoiding a sum-of-monomials schema extension. This
is not a `GO` decision. A new audit must still verify every material correction,
uncertainty component, provenance parent, covariance assumption, and whether the
published aggregate coupling is genuinely sufficient without reverse engineering. If
that audit fails, the detailed 2014 BIPM torsion-balance publication is the next
reasonable source-completeness candidate.
