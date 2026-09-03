# HUST 2018 AAF source-availability audit v1

**Decision: `GO` — assessed replication depth: `2a` (3 of 3 AAF determinations authorized)**

This audit evaluates only the angular-acceleration-feedback (AAF) method in Q. Li et al., Nature 560, 582–588 (2018), DOI `10.1038/s41586-018-0431-5`. It does not create a `MeasurementModel` or claim a new measurement of G.

The original preregistration used the stronger label `maximum_supported_replication_depth`. Post-audit review found that wording too broad because four listed Source Data files were not successfully retrieved. The frozen preregistration is unchanged; the current output therefore reports `maximum_assessed_replication_depth` and records deeper levels as `not_assessed`.

## Public source result

The retrieved Supplementary Information is sufficient to reconstruct the central G value of each named AAF determination from published upstream summary quantities.

Supplementary Information pp. 4-5 defines the gravity-coupling coefficient `P_g,l,m` from the pendulum/source multipole quantities and the pendulum moment of inertia while G remains a separate multiplicative factor in the gravitational angular-acceleration expansion. The same section gives the simplified AAF determination in terms of the measured angular acceleration, the sum of `P_g,l,2`, and the magnetic-damper correction.

Supplementary Table 3 (p. 20) directly reports, for AAF-I/II/III respectively:

- `|sum P_g,l,2| = 6926.352(74), 6926.334(75), 6926.415(74) kg m^-3`;
- `<alpha_t(2 omega_d)> = 462.0912(16), 462.0791(12), 462.2941(6) nrad s^-2`;
- published comparison values `6.674534(83), 6.674375(82), 6.674535(75) × 10^-11 m^3 kg^-1 s^-2`.

The table states that the angular-acceleration values have already been corrected for the air-density effect. It also records that the non-`l=m=2` coupling terms through `l=10` are included and that higher `m=2` terms are negligible.

Supplementary Table 1 (pp. 18-19) directly reports the magnetic-damper correction `Delta G/G` as `455.40(1.95) ppm` for AAF-I/II and `25.74(8) ppm` for AAF-III. The simplified AAF equation on p. 5 applies that contribution with a positive `1 + Delta G_MD/G` factor. The machine-readable graph now carries the correction direction/operator separately from its magnitude.

The graph also stores the printed uncertainty notation and parsed one-standard-deviation uncertainty for each of the three summary inputs. Those data do not promote depth 2b; they preserve the public uncertainty information needed for a later uncertainty audit.

Using only those public estimator inputs and the source equation,

```text
G = alpha_t * 1e-9 / |sum P_g,l,2| * (1 + magnetic_damper_ppm * 1e-6)
```

the exact-Decimal reconstructions are:

| Experiment | Reconstructed G (×10^-11) | Published comparison (×10^-11) | Difference |
|---|---:|---:|---:|
| AAF-I | 6.6745328035953125108… | 6.674534 | -0.17925 ppm |
| AAF-II | 6.6743753740743660355… | 6.674375 | +0.05605 ppm |
| AAF-III | 6.6745350870563487749… | 6.674535 | +0.01304 ppm |

Agreement is reported as a diagnostic and is not used as the GO criterion. A contaminated or unavailable path removes only the affected determination; the overall decision falls to `PARTIAL` only when no AAF-I/II/III determination retains a target-clean depth-2a path.

## Post-audit source semantics

The byte-pinned PDF cannot be semantically understood by CI. A separate second-reader record therefore pins a human re-read of the three highest-risk claims:

- `P_g,l,m` keeps G outside its registered source definition;
- the magnetic-damper contribution is applied as a positive `1 + delta` correction;
- Supplementary Table 3 separates AAF-I/II/III and states that the listed angular accelerations are air-density corrected.

This is human semantic verification tied to a byte-pinned source, not automatic PDF comprehension and not independent validation of the experiment.

## Why this is depth 2a rather than depth 2b

The public supplement gives uncertainty contributions and describes the correlation rule used when combining the three AAF experiments. It also reports one-standard-deviation uncertainties on the summary inputs, which are now machine-readable in the graph. However, this audit did not recover a complete itemized, machine-reconstructible uncertainty/covariance budget for any individual AAF determination. The `complete_uncertainty_model` node for each experiment therefore remains `UNPUBLISHED_OR_AMBIGUOUS`.

That prevents depth 2b and prevents any claim that the project has independently reproduced the published uncertainty or the combined AAF result.

## Deeper reduction evidence and limits

The supplement documents several pre-Table-3 reduction steps. Section 4 (pp. 9-10) gives the data-averaging correction and the attenuation correction from double numerical differentiation: `2.57(1) ppm` and `2058.71(1) ppm` for AAF-I, and `1.14(1) ppm` and `914.35(1) ppm` for AAF-II/III. Section 5 (p. 11) reports residual co-moving background-gradient effects of `1.86`, `1.35`, and `1.72 ppm` for the three experiments and describes frequency separation of the lab-fixed background.

Those procedures explain how the public Table-3 summary observable is obtained, but the audit does not use inaccessible raw time series as a hidden requirement for depth 2a.

Four listed Source Data XLSX files were not successfully retrieved by the GitHub runner. Therefore depths above 2a are **not assessed**, not claimed unsupported. Their retrieval attempts remain recorded as HTML fallbacks, and the Nature record separately states that supporting data are available from corresponding authors on reasonable request.

## External-source capture

The GitHub-runner capture successfully retrieved and byte-hashed the Supplementary Information PDF, the Supplementary Data workbook, and the Source Data Extended Data Fig. 2 workbook.

Four other XLSX media requests returned the same 3,038-byte HTML fallback response. The capture artifact records those attempts as `html_fallback_not_source_file`; they are not counted as retrieved evidence. This does not block the assessed depth-2a central reconstruction because its inputs are in the retrieved Supplementary Information PDF.

## Fail-closed disposition

The executable classifier removes an affected AAF determination if a result-driving ancestor is `REQUEST_ONLY`, `UNPUBLISHED_OR_AMBIGUOUS`, or `TARGET_DERIVED`, including a target-derived ancestor at arbitrary depth. It rejects structural cross-experiment dependencies, missing required graph nodes, missing locators, source-hash/status changes, source-transcription mismatches, correction-direction mismatches, and misclassification of HTML fallback bytes as source files.

The direct-source transcription guard pins each AAF summary input's printed value, parsed uncertainty, unit, and exact source-scope token. This catches accidental numeric column substitution in the reviewed graph; it remains tamper evidence, not protection against a knowing editor who changes code and evidence together.

The combined AAF value `6.674484(78) × 10^-11` and its `11.61 ppm` relative standard uncertainty remain comparison records. This audit does not reconstruct their weighting/correlation structure and does not authorize a combined estimator.

## Workflow safety rule

Any future temporary workflow carrying `contents: write` must have both a bot-loop guard and an exact branch/head-ref guard. The permanent test suite scans repository workflows for that condition. No write-enabled temporary workflow is retained by this audit.

## Nonclaims

- This result does not establish that the HUST value of G is correct.
- It is not an independent laboratory measurement.
- It does not establish the published systematic-error model.
- It does not authorize an uncertainty-qualified empirical reproduction.
- It does not establish that depths 3 or 4 are unavailable; they were not assessed from the unretrieved files.
- It does not validate entropic/emergent gravity or any other gravitational theory.
- It does not modify the physical-bridge production schema.

The result remains narrow: the retrieved HUST-2018 supplement contains enough target-clean summary inputs to reconstruct all three individual AAF central values without back-solving from published G.
