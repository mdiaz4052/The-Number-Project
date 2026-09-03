# Physical bridge records for G

This directory contains Milestone 4's deterministic contract artifacts and published-data
source audits. It contains no project-operated experimental dataset and reports no project
measurement of `G`.

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
explicit **`NO-GO (INCOMPLETE_REPRODUCTION)`**. The paper reports the symbolic multipole
estimator, apparatus summaries, correction factors, one-sigma uncertainty budget, and
headline result. It does not report the fitted gravitational angular-acceleration
amplitude or the complete numerical attractor multipole coupling needed to calculate
`G_hat`. The proposed 2002 PRD companion citation is unrelated; the later UW correction
identified by CODATA is sourced to a private communication. A 1999 predecessor's
prototype `Q_22`, proposed error budget, and design geometry are explicitly excluded as
substitutes for the 2000 inputs.

No missing value is guessed, copied from a secondary proposal, or back-solved from the
published `G`. Consequently no UW empirical model or result artifact is created and no
empirical or replication status is promoted. This documented outcome records that the
source audit found the publication set insufficient for a complete transcription; it is
not a criticism of the published experiment.

[`uw_2000_published_data_pilot_v1.manifest.json`](uw_2000_published_data_pilot_v1.manifest.json)
pins the exact bytes of the original preregistration, the clarification, and the source
audit, together with the canonical `NO-GO`, missing-input, and next-candidate fields. The
guard is tamper evidence for review; it cannot stop a knowing editor from changing code,
constants, documents, and artifacts together.

## HUST 2018 AAF source audit

[`hust_2018_aaf_preregistration_v1.md`](hust_2018_aaf_preregistration_v1.md) freezes the
decision rule before the HUST public inputs are classified. Its exact bytes are SHA-256
pinned in `Discovery.hust_2018_aaf_source_audit`.

The completed audit reaches **`GO` at replication depth `2a`**. This is deliberately
narrower than an uncertainty-qualified empirical reproduction. The public HUST
Supplementary Information supplies, separately for AAF-I, AAF-II, and AAF-III, the summed
`P_g,l,2` coupling, the air-density-corrected average angular acceleration, and the
magnetic-damper correction. The supplement's definition keeps `G` outside `P_g,l,m` as a
separate factor. Those public summary inputs therefore permit a target-clean exact-Decimal
reconstruction of all three individual central `G` estimates without back-solving from a
published `G` value.

The reconstructed central values agree diagnostically with the printed AAF-I/II/III
values at approximately `-0.179`, `+0.056`, and `+0.013` ppm, respectively. Agreement does
**not** determine the `GO` classification: graph ancestry and evidence class do. A planted
transitive `TARGET_DERIVED` ancestor or a `REQUEST_ONLY` result-driving input downgrades
the executable classifier to `PARTIAL`.

Depth `2b` is not authorized. The retrieved public record describes uncertainties and AAF
correlations, but this audit did not establish a complete itemized machine-reconstructible
uncertainty/covariance model for any individual determination. The combined AAF value is
also comparison-only because its weighting/correlation structure is not reconstructed by
this milestone. Depths 3 and 4 remain unauthorized because run-level/raw time-series data
were not recovered from the public set.

The audit artifacts are:

- [`hust_2018_aaf_external_sources_v1.json`](hust_2018_aaf_external_sources_v1.json):
  recorded retrieval bytes/statuses, including fail-closed classification of source-data
  requests that returned HTML fallbacks instead of XLSX bytes;
- [`hust_2018_aaf_required_inputs_v1.json`](hust_2018_aaf_required_inputs_v1.json): the
  AAF-I/II/III evidence/dependency graph and terminal published comparisons;
- [`hust_2018_aaf_source_audit_v1.md`](hust_2018_aaf_source_audit_v1.md): the human-readable
  source audit and nonclaims;
- [`hust_2018_aaf_source_audit_v1.manifest.json`](hust_2018_aaf_source_audit_v1.manifest.json):
  the deterministic classifier output plus hashes of the reviewed audit documents.

The GitHub runner successfully captured the Supplementary Information PDF, Supplementary
Data workbook, and one figure-source workbook. Four other exact Springer Nature XLSX media
requests returned the same small HTML fallback response and are explicitly *not* promoted
to retrieved source evidence. These failures do not block depth 2a because the central
estimator inputs are in the retrieved Supplementary Information PDF; they do block any
attempt to treat those failed captures as deeper evidence.

CI verifies the frozen preregistration, reviewed external-source hashes/statuses, graph
invariants, target ancestry, deterministic manifest, and exact reconstruction arithmetic.
It does not re-download or parse the mutable publisher PDF on every run to prove that a
human-written page/table locator semantically supports its transcription. The external PDF
bytes are pinned, the locators are reviewable, and independent source verification remains
part of the Claude audit. This distinction is intentional: tamper evidence is not the same
as automatic literature comprehension.

No HUST `MeasurementModel` is created here and the physical-bridge production schema is
unchanged. A later implementation may use only the specifically authorized individual
central estimators unless a separate audit establishes the missing uncertainty/correlation
record.

## Empirical source-metadata boundary

For any future `empirical_record`, every populated numerical quantity in estimator
ancestry, and every declared calibration or correction, must declare documented
provenance plus a source identifier, edition, and access date. Source metadata is also
form-validated at `QuantityRecord` construction: access dates must be valid calendar dates
in strict `YYYY-MM-DD` form. Source identifiers must use one of three explicit channels:
`doi:<DOI>`, an absolute credential-free `url:https://...`, or a namespaced local
`certificate:<issuer>/<record-id>`. Certificate issuer and record components use a
bounded ASCII token grammar: the issuer begins with an ASCII letter and is at most 64
characters, while the record identifier is at most 128 characters. A loose value such as
`certificate:zzz` is not accepted. DOI and URL identifiers reject whitespace, control
characters, nonspacing/enclosing combining marks, and a bounded set of blank-like Unicode
code points that can render as empty text while remaining printable; malformed URL parsing
and invalid ports are converted into the schema's controlled `BridgeValidationError`.
Edition remains descriptive nonempty text. Malformed forms are rejected before model-level
empirical evaluation.

The historical `force_reference` test fixture now uses the namespaced
`certificate:project/force-reference` form directly. No construction-time migration or
silent source-identifier rewrite remains in the schema.

These checks establish only syntax and project-local identifier shape. They do not prove
that a DOI, URL, or certificate resolves, that a host is publicly reachable, that the
claimed source contains the asserted value, or that the value was experimentally
independent. A single-label HTTPS hostname can therefore be syntactically valid, while a
hostname containing no alphanumeric character is rejected as degenerate. General Unicode
homoglyph/confusable detection is deliberately out of scope: the form gate removes bounded
invisible classes, but it does not claim that visually similar identifiers are equivalent or
that an identifier resolves to the intended source. Future `access_date` values also remain
syntactically valid: temporal plausibility is deliberately outside this deterministic form
gate and would require a separately pinned audit date if ever enforced. Python's frozen
dataclass mechanism is likewise an authoring-time check, not a security boundary against a
knowing in-memory mutator. Source auditing remains a separate evidence task.

## Regeneration

From the repository root, regenerate the structural bridge JSON with:

```bash
python3 -m Discovery.physical_bridge
```

Check committed bytes without rewriting them with:

```bash
python3 -m Discovery.physical_bridge --check
python3 -m Discovery.published_data_pilot --check
python3 -m Discovery.hust_2018_aaf_source_audit --check
```

The implementation uses only the Python standard library. Exponents and dimensions use
exact `Fraction` arithmetic. Decimal measurement records use `Decimal` and serialize as
base-ten strings; binary floating-point measurement values are rejected.

For the first-principles explanation, read
[`Notes/PhysicalBridgeContract.md`](../../Notes/PhysicalBridgeContract.md). For the review,
experiments, CODATA boundary, and metrology standards supporting the architecture, read
[`Notes/GMeasurementLiterature.md`](../../Notes/GMeasurementLiterature.md).
