# Physical bridge records for G

This directory contains Milestone 4's deterministic contract artifacts and published-data
source audits. It contains no project-operated experimental dataset and reports no project
measurement of `G`.

`physical_bridge_contract.json` records the general evidence layers, measurement-model
fields, input roles, exact target-path rules, both supported uncertainty bases,
external-reference boundary, cycle rejection within and across provenance layers, Lean
boundary, literature identifiers, limitations, and nonclaims.

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
decision rule before the HUST public inputs are classified. Its exact bytes remain SHA-256
pinned in `Discovery.hust_2018_aaf_source_audit` and are not rewritten by the post-audit
closure.

The completed audit reaches **`GO` at assessed replication depth `2a`, with all 3 of 3
AAF determinations authorized**. This is deliberately narrower than an uncertainty-qualified
empirical reproduction. The public HUST Supplementary Information supplies, separately for
AAF-I, AAF-II, and AAF-III, the summed `P_g,l,2` coupling, the air-density-corrected average
angular acceleration, and the magnetic-damper correction. The supplement's definition keeps
`G` outside `P_g,l,m` as a separate factor. Those public summary inputs therefore permit a
target-clean exact-Decimal reconstruction of all three individual central `G` estimates
without back-solving from a published `G` value.

The original preregistration called the depth field `maximum_supported_replication_depth`.
Independent audit found that wording too strong because four listed Source Data workbooks
were not successfully retrieved, so deeper levels were not actually assessed. The frozen
preregistration is preserved as historical evidence; the current classifier reports
`maximum_assessed_replication_depth`, and explicitly records depths above the assessed level
as `not_assessed` rather than unsupported. The rationale is pinned in
[`hust_2018_aaf_post_audit_clarification_v1.md`](hust_2018_aaf_post_audit_clarification_v1.md).

The reconstructed central values agree diagnostically with the printed AAF-I/II/III
values at approximately `-0.179`, `+0.056`, and `+0.013` ppm, respectively. Agreement does
**not** determine the `GO` classification: graph ancestry and evidence class do. A planted
`TARGET_DERIVED`, `REQUEST_ONLY`, or otherwise unresolved result-driving path removes the
affected AAF determination from authorization. The overall classifier downgrades to
`PARTIAL` only when no experiment retains a target-clean depth-2a path. Every current
headline therefore carries both the assessed depth and the authorized count/list.

The post-audit graph also makes the source transcription more load-bearing. Each direct
summary input stores its printed value, parsed one-standard-deviation uncertainty, unit,
and exact source-scope token. The magnetic-damper node separately records the positive
`multiply_by_1_plus_delta` operator and its source locator. These fields let tests reject
accidental numeric column substitution, scope-token swaps, uncertainty transcription drift,
and correction-direction drift. They remain tamper evidence rather than protection against
a knowing editor who changes code and evidence together.

Depth `2b` is not authorized. The retrieved public record describes uncertainties and AAF
correlations, and the three public summary-input uncertainties are now machine-readable,
but the audit still does not establish a complete itemized machine-reconstructible
uncertainty/covariance model for any individual determination. The combined AAF value is
also comparison-only because its weighting/correlation structure is not reconstructed by
this milestone.

The audit artifacts are:

- [`hust_2018_aaf_external_sources_v1.json`](hust_2018_aaf_external_sources_v1.json):
  recorded retrieval bytes/statuses, including fail-closed classification of source-data
  requests that returned HTML fallbacks instead of XLSX bytes;
- [`hust_2018_aaf_required_inputs_v1.json`](hust_2018_aaf_required_inputs_v1.json): the
  AAF-I/II/III evidence/dependency graph, machine-readable uncertainty records, correction
  direction, source-scope tokens, and terminal published comparisons;
- [`hust_2018_aaf_semantic_source_review_v1.json`](hust_2018_aaf_semantic_source_review_v1.json):
  the byte-pinned second-reader check of the three highest-risk primary-source claims;
- [`hust_2018_aaf_source_audit_v1.md`](hust_2018_aaf_source_audit_v1.md): the human-readable
  source audit and nonclaims;
- [`hust_2018_aaf_source_audit_v1.manifest.json`](hust_2018_aaf_source_audit_v1.manifest.json):
  the deterministic classifier output plus hashes of the reviewed audit documents.

The GitHub runner successfully captured the Supplementary Information PDF, Supplementary
Data workbook, and one figure-source workbook. Four other exact Springer Nature XLSX media
requests returned the same small HTML fallback response and are explicitly *not* promoted
to retrieved source evidence. These failures do not block the assessed depth-2a central
estimator because its inputs are in the retrieved Supplementary Information PDF. They also
do not establish that deeper public evidence is unavailable; depths above 2a are simply not
assessed from those unretrieved files.

CI verifies the frozen preregistration, post-audit clarification, second-reader record,
reviewed external-source hashes/statuses, graph invariants, target ancestry, deterministic
manifest, exact reconstruction arithmetic, source-transcription fields, and correction
direction. It does not re-download or parse the mutable publisher PDF on every run to prove
that a human-written page/table locator semantically supports its transcription. The
second-reader record makes that human semantic check explicit rather than presenting it as
a machine-derived fact.

Any future temporary workflow with `contents: write` must carry both a bot-loop guard and
an exact branch/head-ref guard. A permanent repository test scans workflow files for that
condition. No write-enabled temporary workflow is retained by the HUST audit.

That source-audit stage did not create a HUST `MeasurementModel`. The later, separately
preregistered depth-2a artifact
[`hust_2018_aaf_measurement_models_v1.json`](hust_2018_aaf_measurement_models_v1.json)
contains three individual published central-value reconstructions. Their target standard
uncertainties remain absent and their `uncertainty_status` remains `incomplete`. Milestone
7A changes only the generic representation described below; it does not promote those
historical depth-2a records or authorize a combined AAF estimator.

## Milestone 7A direct uncertainty-budget representation

The additive Milestone 7A contract distinguishes two uncertainty bases:

- `estimator_input_propagation` retains the original behavior: uncertainty is propagated
  from the central estimator's `input_ids` and `correction_ids`.
- `direct_measurand_contributions` represents published budget entries that are already
  contributions to the final measurand. It uses nonempty `component_ids` whose quantities
  have role `uncertainty_component`, while `input_ids` and `correction_ids` are empty.

Direct components must be populated nonnegative `Decimal` values, all dimensionless or
all target-dimensional, and cannot carry uncertainty-on-uncertainty. They and their
ancestors are isolated from central-estimator ancestry and separately audited for any
registered path to `G`. Every populated record in an empirical component's complete
provenance closure requires documented source metadata. A populated target uncertainty
must use the target unit; if the target uncertainty is absent, the model validates but its
uncertainty axis remains explicitly `incomplete`. An empty covariance table requires a
documented explicit zero-correlation assumption. The direct basis is eligible only when a
pinned publication reports contributions already expressed for the final measurand. The
generic validator establishes these representation rules only; choosing the mode does not
establish eligibility, and a future apparatus-specific validator must prove source
completeness and combination arithmetic.

Legacy uncertainty records omit `uncertainty_basis` and `component_ids` from serialized
JSON when the additive defaults are unused. The inverse-square example and HUST depth-2a
artifact therefore remain byte-identical. No HUST depth-2b target uncertainty is populated
by Milestone 7A.

## Milestone 7B HUST individual uncertainty reconstructions

Milestone 7B leaves every historical depth-2a and feasibility artifact byte-identical and
creates three new uncertainty-qualified records, one each for `AAF-I`, `AAF-II`, and
`AAF-III`. It does not construct the combined AAF result.

The preregistered production source gate is satisfied by Nature's public dedicated Table 1
page. The repository stores only metadata and SHA-256 for the browser-rendered first-table
HTML serialization; it does not redistribute publisher bytes. The digest is an
official-source attestation and cannot be reproduced solely from repository contents. The
record expressly does not claim that this serialization is byte-identical to a PDF or raw
HTTP response, and notes that another valid publisher delivery path can have different
bytes. The historical third-party mirror and conversation screenshot are recorded as
history, not production substitutes.

The current post-audit artifacts are:

- [`hust_2018_aaf_depth_2b_official_source_v1.json`](hust_2018_aaf_depth_2b_official_source_v1.json):
  the strict official Nature Table 1 URL, locator, capture representation, byte length,
  hash, access date, storage status, and delivery caveat;
- [`hust_2018_aaf_depth_2b_clarification_v1.json`](hust_2018_aaf_depth_2b_clarification_v1.json):
  the direct-versus-derivable evidence split, candid transcription chronology, qualified
  individual RSS correlation representation, and unchanged authorization boundaries;
- [`hust_2018_aaf_required_inputs_depth_2b_v2.json`](hust_2018_aaf_required_inputs_depth_2b_v2.json):
  the exact ordered 21-by-3 production transcription with exact `printed_row_label`
  strings and unchanged per-scope inputs;
- [`hust_2018_aaf_depth_2b_authorization_v2.json`](hust_2018_aaf_depth_2b_authorization_v2.json):
  the deterministic source/derivation authorization, both verified history anchors,
  recomputed diagnostics, frozen-v1 hashes, and the explicit attestation limitation;
- [`hust_2018_aaf_depth_2b_measurement_models_v2.json`](hust_2018_aaf_depth_2b_measurement_models_v2.json):
  the three individual empirical records with 21 direct ppm components, precision-50 RSS,
  and absolute standard uncertainty derived from each unchanged `G_hat`; and
- [`hust_2018_aaf_depth_2b_mutation_results_v2.json`](hust_2018_aaf_depth_2b_mutation_results_v2.json):
  the 24/24 killed behavioral mutations, including two isolated source-path tests of the
  terminal-input boundary. Tree-state, freshness, and historical-byte sentinels remain
  guards but are excluded from mutation scoring.

The corresponding required-input, authorization, measurement-model, and mutation-result
`v1` files remain the byte-frozen Milestone 7 snapshot. The official-source and
clarification records remain pinned at `v1`; they were not copied or rewritten for this
metadata-only migration.

The component values are `PUBLIC_DIRECT`. The per-column RSS rule, within-result qualified
zero-covariance representation, and complete individual uncertainty models are
`PUBLIC_DERIVABLE`. The zero-covariance representation reproduces the published individual
budget; it is not a claim that every physical systematic source is independent. Cross-run
covariance remains reserved for a future separately preregistered combined estimator.

Each valid record reports satisfied dimensional, algebraic, metrological, uncertainty, and
empirical-population axes; the target-path axis reports `no_registered_target_path`, and
replication remains `incomplete`. These are published-data reconstructions, not new
measurements, apparatus validation, raw/run-level replication, Lean certification, or
novel physical predictions. `no_registered_target_path` is not experimental independence
and is not a satisfied target-path gate.

### Source-pin policy

For future paywalled or non-redistributable empirical sources:

1. Prefer official bytes when they can be lawfully stored and reproduced stably.
2. When official bytes cannot be stored or reproduced stably, an official-source
   attestation must record a locator, access date, capture representation, digest,
   structural validation, and explicit delivery and reproducibility caveats.
3. Pin a lawful, stable author manuscript, institutional copy, publisher supplement, or
   comparable reproducible source as secondary corroboration when one is available.
4. A secondary source never impersonates or replaces the official source unless a
   preregistration explicitly authorizes that role.
5. Accessibility alone does not make a third-party mirror an official-source substitute.
6. If a preregistered evidence precondition cannot be met, return `NO_GO`; do not guess,
   back-solve, or silently relax the precondition.

For this reconstruction, no new Table 1 secondary source is authorized. The existing
supplement retains its existing hash and role. The official DOM hash remains an attestation
that a third party cannot reproduce solely from repository contents.

## Empirical source-metadata boundary

For any future `empirical_record`, every populated numerical quantity in estimator
ancestry, every declared calibration or correction, and every quantity in a direct
measurand uncertainty component's full ancestry must declare documented provenance plus a
source identifier, edition, and access date. Source metadata is also form-validated at
`QuantityRecord` construction: access
dates must be valid calendar dates in strict `YYYY-MM-DD` form. Source identifiers must
use one of three explicit channels:
`doi:<DOI>`, an absolute credential-free `url:https://...`, or a namespaced local
`certificate:<issuer>/<record-id>`. Certificate issuer and record components use a
bounded ASCII token grammar: the issuer begins with an ASCII letter and is at most 64
characters, while the record identifier is at most 128 characters. A loose value such as
`certificate:zzz` is not accepted. Source identifiers must already be NFC-normalized and
are rejected rather than rewritten when they are not. This NFC rule is deliberately scoped
to source identifiers; quantity identifiers, unit strings, and descriptive editions are not
silently canonicalized by it. DOI and URL identifiers also reject
whitespace, control characters, nonspacing/enclosing combining-mark categories, and a
bounded set of blank-like Unicode code points; this bounded syntax rule does not claim that
every combining mark is visually empty. Malformed URL parsing and invalid ports are
converted into the schema's controlled `BridgeValidationError`. Edition remains
descriptive nonempty text. Malformed forms are rejected before model-level empirical
evaluation.

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
python3 -m Discovery.hust_2018_aaf_measurement_models --check
python3 -m Discovery.hust_2018_aaf_depth_2b_authorization --check
python3 -m Discovery.hust_2018_aaf_depth_2b_measurement_models --check
python3 -m Discovery.hust_2018_aaf_depth_2b_mutations --check
```

The implementation uses only the Python standard library. Exponents and dimensions use
exact `Fraction` arithmetic. Decimal measurement records use `Decimal` and serialize as
base-ten strings; binary floating-point measurement values are rejected.

For the first-principles explanation, read
[`Notes/PhysicalBridgeContract.md`](../../Notes/PhysicalBridgeContract.md). For the review,
experiments, CODATA boundary, and metrology standards supporting the architecture, read
[`Notes/GMeasurementLiterature.md`](../../Notes/GMeasurementLiterature.md).
