# Candidate Exchange 1: implementation reference

Internal development contract `tnp-candidate-exchange/1`. The frozen contract and
work order define acceptance. This reference explains the implemented field mapping.
All semantic fields are required; extra fields are rejected. The functions operate
on inert JSON data. Python helpers `analyze`/`evaluate` are trusted implementation
internals; callers use `ingest` → `evaluate_records`, which validate and bind input.
This is implementation separation, not a hostile-code sandbox.

## Invocation

```python
from Discovery.candidate_exchange_adapters import ingest, evaluate_records
bundle = ingest(trusted_manifest, raw_utf8_bytes, "mock-tree/1", source="fixture-file")
result = evaluate_records(trusted_manifest, raw_utf8_bytes, "mock-tree/1", bundle,
                          [{"name": "fixture-a", "values": {"x": 8., "t": 2., "z": 1.}}],
                          source="fixture-file")
```

Rejects are structured as `run_rejection` with status/code/message, or as retained
inventory rejections for individual items. An expression that is well formed but
ineligible, dimensionally inadmissible or undefined still has a retained candidate
and a rejecting card. No exception from malformed generator bytes is an intended
user protocol. Display strings are never interpreted.

`python3.12 -m Discovery.candidate_exchange_conformance check` is read-only. It
checks the committed source/evidence bindings and semantic record replay; it does
not execute discovery or refit old results. The ordinary unittest discovery step
already reaches this guard, so verify.yml is unchanged. Developer-only `pin-source`
and `emit` use exclusive file creation and cannot replace existing evidence.

## Separate record schemas

Each listed set additionally contains `schema` with its distinct envelope name.

| Record | Fields / interpretation |
|---|---|
| manifest | `target`, `quantities`, `parameters`, `sources`, `splits`, `input_digest`, `uncertainty`, `dependence`, `allowed_ops`, `opaque` |
| receipt | `generator`, `kind`, `manifest_digest`, `input_digest`, `configuration`, `configuration_digest`, `adapter`, `source`, `run_status`, `failure`, `metadata`, `input_count`, `candidate_count`, `candidate_ids`, `inventory` |
| candidate | `candidate_id`, `manifest_digest`, `raw_binding`, `expression`, `parameters`, `diagnostics`, `claims`, `display`, `opaque`, `ancestry`, `source_item` |
| card | `candidate_id`, `manifest_digest`, `candidate_digest`, `integrity`, `eligibility`, `dimensions`, `domain`, `representation`, `numerical_checks`, `original_reported_metrics`, `source_claims`, `scientific_evidence`, `candidate_status`, `outcome`, `reasons` |

Mapping: receipt and candidate manifest digests equal the supplied manifest digest;
card candidate digest equals its complete candidate digest. Candidate diagnostics
map to card original_reported_metrics; claims map to source_claims only. Neither
maps to trusted scientific_evidence. Record envelopes are never compared as if
receipt and card shared one schema. `verify_records` reconstructs the raw translation
and compares every receipt/candidate field, including diagnostics and original item.
`verify_cards` validates the separate card envelope and recomputes trusted fields.

Quantity spec: role (target/observed/derived/alias), exact dimension mapping, numeric
unit convention, domain (real/nonzero/positive), definition (null or integer-power
monomial mapping), direct dependencies. A true alias is exactly one identity edge.
All original edges are validated before existing monomial helpers normalize zero
exponents. The project-owned manifest is the authority; checking its registered
graph does not prove that undeclared real-world dependencies are absent.

Parameter spec: dimension, unit, role (fixed/training_fitted), fit_context. Candidate
parameter values add a single `value` number record to that spec. Fitting context
is null for fixed parameters, or exactly the original training split and input
digest. Scalar training fits are allowed; vectors, callables, unknown contexts,
validation-derived or held-out fits are rejected. The exchange performs no fitting.

Uncertainty and dependence each contain status and reference strings. Allowed
statuses are exact_by_design, known_declared, unknown, not_assessed. Known declarations
need references. Unknown does not mean zero uncertainty or independence. This
package neither propagates nor estimates uncertainty.

## Expression nodes and arithmetic

| Operation | Additional fields |
|---|---|
| literal | `number` = `{kind: exact, numerator: int, denominator: int}` or `{kind: approximate, value: finite float}` |
| variable, parameter | `name` |
| add, multiply | `args` (2–32 nodes) |
| divide | `numerator`, `denominator` (nodes) |
| power | `arg` (node), `exponent` (integer −16…16; not bool) |
| exp, log | `arg` (node); log is natural log |

Exact ratios are reduced mathematically for identity while original raw bytes remain
bound. Approximate values retain their IEEE float identity without snapping. JSON
serialization uses the existing canonical sorted/indented UTF-8 encoder with a final
newline and no NaN; SHA-256 binds exact serialization. Raw source hashes bind original
bytes, and item hashes bind canonical item content at the exact indexed locator.

Representation contains exact dimension vector, original domain conditions,
model_id, structural_id, conservative normal_form, and original references. An
identity is established only by the implemented commutative/associative or monomial
rules with matching domains and parameter roles. Unequal IDs mean NOT_ESTABLISHED.
Numerical overflow remains invalid even if real algebra has a finite simplification;
this is a conservative numerical evaluation limit, not a false symbolic identity.

A structural ID erases parameter values from the expression structure only; retained
parameter-dependent domain conditions can still distinguish structures. It never
provides permission to merge differently fitted models. Values are always included
in model IDs. Existing exact Dimension arithmetic is reused; it does not convert units.

## Mock formats and historical binding

Both mocks have schema, manifest_digest, manifest_echo (null or exactly matching),
items, status (success/failed), failure, and namespaced metadata. Formats are invented
for this test; no compatibility with PySR, PhySO or another real engine is claimed.

| Tree item | Postfix item | Common meaning |
|---|---|---|
| id | label | Original opaque engine identifier; duplicates retained |
| expression | tokens | Structured tree / inert postfix tokens |
| parameters | coefficients | Scalar parameter records |
| diagnostics | metrics | Untrusted original metrics |
| claims | assertions | Untrusted claims |
| display | render | Inert human display |
| opaque | opaque | Namespaced uninterpreted data |

Postfix atoms are literal/variable/parameter nodes. Unary `exp`, `log`; binary `+`,
`*`, `/`; power token `{operator: power, exponent: integer}`. Operand order for /
is earlier/later. Any malformed stack is explicitly rejected. Position-based
candidate IDs preserve order and repeated expressions even when engine IDs collide.

The importer reads fixed Git objects only: two rankings, their pinned public input
metadata/digests, and their pinned design. It does not import campaign runners or
read heldout/oracle data. Complete original source items, coefficients,
log_coefficient, members, rank, errors and evidence labels are preserved. Source
receipts retain the available environment and upstream metadata; unavailable seed
is unknown. The manifest's numeric SI convention is declared from the synthetic
design, not metrological certification. Imported metrics and adequacy remain
attributed historical evidence; the new card's scientific axes stay NOT_ASSESSED.

Prediction comparison uses fixed positive fixture points and original
exp(log_coefficient + fsum(power*log(value))) versus new expression evaluation,
relative tolerance 2e-12 / absolute 1e-14. No bit-identity claim or old-value edits.
The importer preserves the available complete five-class rankings, not an invented
full search history. It does not test family completeness or discovery quality.

All resource limits and boundary tests are frozen in contract.v1.md. Unsupported
operator/unit/version/resource requests are explicit UNSUPPORTED outcomes; malformed
or semantically inconsistent inputs are REJECTED. Empty output and failed run never
earn abstention, inadequacy-detection, or scientific credit.
