# HUST 2018 AAF source-availability audit v1

**Decision: `GO` — maximum supported replication depth: `2a`**

This audit evaluates only the angular-acceleration-feedback (AAF) method in Q. Li et al., Nature 560, 582–588 (2018), DOI `10.1038/s41586-018-0431-5`. It does not create a `MeasurementModel` or claim a new measurement of G.

## Public source result

The public Supplementary Information is sufficient to reconstruct the central G value of each named AAF determination from published upstream summary quantities.

Supplementary Information pp. 4-5 defines the gravity-coupling coefficient `P_g,l,m` from the pendulum/source multipole quantities and the pendulum moment of inertia while G remains a separate multiplicative factor in the gravitational angular-acceleration expansion. The same section gives the simplified AAF determination in terms of the measured angular acceleration, the sum of `P_g,l,2`, and the magnetic-damper correction. Therefore the registered `P_g,l,m` definition used by this audit does not contain G.

Supplementary Table 3 (p. 20) directly reports, for AAF-I/II/III respectively:

- `|sum P_g,l,2| = 6926.352(74), 6926.334(75), 6926.415(74) kg m^-3`;
- `<alpha_t(2 omega_d)> = 462.0912(16), 462.0791(12), 462.2941(6) nrad s^-2`;
- published comparison values `6.674534(83), 6.674375(82), 6.674535(75) × 10^-11 m^3 kg^-1 s^-2`.

The table states that the angular-acceleration values have already been corrected for the air-density effect. It also records that the non-`l=m=2` coupling terms through `l=10` are included and that higher `m=2` terms are negligible.

Supplementary Table 1 (pp. 18-19) directly reports the magnetic-damper correction `Delta G/G` as `455.40(1.95) ppm` for AAF-I/II and `25.74(8) ppm` for AAF-III.

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

Agreement is reported as a diagnostic, not used as the GO criterion. GO/2a is authorized because the public dependency graph supplies a target-clean computation for each central estimate; the published G values are terminal comparisons only.

## Why this is depth 2a rather than depth 2b

The public supplement gives many uncertainty contributions and explicitly describes the correlation rule used when combining the three AAF experiments. It also reports one-standard-deviation uncertainties on the summary inputs. However, this audit did not recover a complete itemized, machine-reconstructible uncertainty/covariance budget for each AAF-I/II/III determination from the retrieved public set. The `complete_uncertainty_model` node for each experiment is therefore `UNPUBLISHED_OR_AMBIGUOUS` for this milestone.

That prevents depth 2b and prevents any claim that the project has independently reproduced the published uncertainty or the combined AAF result. A later reconstruction PR may implement only the specifically authorized individual central-value estimators unless a separately audited uncertainty/correlation record is established.

## Deeper reduction evidence and limits

The supplement documents several pre-Table-3 reduction steps. Section 4 (pp. 9-10) gives the data-averaging correction and the attenuation correction from double numerical differentiation: `2.57(1) ppm` and `2058.71(1) ppm` for AAF-I, and `1.14(1) ppm` and `914.35(1) ppm` for AAF-II/III. Section 5 (p. 11) reports residual co-moving background-gradient effects of `1.86`, `1.35`, and `1.72 ppm` for the three experiments and describes frequency separation of the lab-fixed background.

Those procedures explain how the public Table-3 summary observable is obtained, but the audit does not use inaccessible raw time series as a hidden requirement for depth 2a. Depths 3 and 4 would require public run-level/raw records beyond the summary table. The Nature record states that supporting data are available from corresponding authors on reasonable request; request-only material is not treated as retrieved public evidence.

## External-source capture

The GitHub-runner capture successfully retrieved and byte-hashed:

- the Supplementary Information PDF;
- the Supplementary Data workbook;
- the Source Data Extended Data Fig. 2 workbook.

The exact Nature page identifies the additional source-data labels and media URLs. Four of those XLSX media requests returned the same 3,038-byte HTML fallback response to the GitHub runner rather than spreadsheet bytes. The capture artifact records those attempts as `html_fallback_not_source_file`; they are not counted as retrieved evidence. This does not block depth 2a because the central reconstruction depends on the retrieved Supplementary Information PDF, not those figure-source workbooks. It does prevent treating the failed capture attempts as evidence for deeper replication.

## Fail-closed disposition

The executable classifier rejects GO if a result-driving ancestor is `REQUEST_ONLY`, `UNPUBLISHED_OR_AMBIGUOUS`, or `TARGET_DERIVED`, including a target-derived parent-of-a-parent. It rejects cross-experiment dependencies, missing required graph nodes, missing locators, source-hash/status changes, and misclassification of HTML fallback bytes as source files.

The combined AAF value `6.674484(78) × 10^-11` and its `11.61 ppm` relative standard uncertainty remain comparison records. This audit does not reconstruct their weighting/correlation structure and does not authorize a combined estimator.

## Nonclaims

- This result does not establish that the HUST value of G is correct.
- It is not an independent laboratory measurement.
- It does not establish the published systematic-error model.
- It does not authorize an uncertainty-qualified empirical reproduction.
- It does not validate entropic/emergent gravity or any other gravitational theory.
- It does not modify the physical-bridge production schema.

The result is narrower: unlike the UW-2000 pilot, the HUST-2018 public supplement contains enough target-clean summary inputs to reconstruct all three individual AAF central values without back-solving from published G.
