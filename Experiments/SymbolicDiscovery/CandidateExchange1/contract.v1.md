# Candidate exchange v1 — frozen acceptance contract

Task NP-CANDIDATE-EXCHANGE-01 revision 1. Internal development namespace
`tnp-candidate-exchange/1`; no stable public API or external-engine compatibility.
The consumed work order is controlling. `outcome_blind=false`;
`evidence_mode=deterministic_contract_conformance`.

## Four records and ownership

All records have `schema` (namespace plus `/manifest`, `/receipt`, `/candidate`,
or `/card`) and exact, distinct field sets. Implemented field tables live in the
validator and are documented in the package's forward interface reference.
Unknown versions, semantic fields, types, or symbols fail closed. Opaque metadata
uses colon-namespaced keys and never supplies authority.

The project supplies the manifest independently of generator bytes. It declares
target, feature graph, exact SI dimensions in M,L,T,I,Theta,N,J order, coherent-SI
or dimensionless numeric convention, domains (real, nonzero, positive), source
references, split roles, allowed operations, uncertainty and dependence. Graph
edges precede every normalization. Derived monomial aliases must match their
declared edges and dimensions; observed quantities cannot have derivations.
Fitted parameters are scalar only, with explicit training-only context and input
digest. They are not per-row target features. Unknown dependence stays unknown.

Receipts bind manifest, configuration, adapter source, input digest, exact raw
source hash/location and an ordered inventory. Every source item has a unique
position-based ID and candidate or rejection, including repeated engine IDs and
duplicates. Empty success and operational failure are distinct without scientific
credit. Source metadata not actually recorded is unknown or not_applicable.

Candidates retain original fields/diagnostics and exact raw locator, expression,
parameters, source ancestry and untrusted claims. Trusted verification reconstructs
the translation from raw source and compares semantic fields; a recomputed digest
alone cannot authorize a substituted expression. Manifest claims in mock payloads
must agree exactly with the supplied manifest.

Cards separate integrity, eligibility, dimensions, domains, symbolic representation,
fixture numerics and attributed original metrics. Scientific promotion always
remains NOT_ASSESSED; candidate status is GENERATED/FITTED CANDIDATE. Preserved
claims can never overwrite card fields. Stored cards are verified against the
trusted evaluation, not accepted because their schema or digest looks plausible.

## Fragment and concrete resource limits

JSON nodes: literal (exact rational numerator/denominator integers, or explicitly
approximate finite float); variable; parameter; add; multiply; divide; integer
power; exp; natural log. Display text is inert. Noninteger powers and unknown
operators are UNSUPPORTED. No executable payload interpretation.

- UTF-8 input maximum: 1,048,576 bytes, checked before parsing.
- JSON maximum container nesting 64, total values 100,000, collection size 4,096,
  string length 16,384, integer bit length 256. Duplicate keys and nonfinite
  values fail; lexical nesting is checked before the JSON parser runs.
- Expression maximum depth 24, nodes 256, add/multiply arity 2–32,
  absolute integer exponent 16; bool is never numeric or an exponent.
- Manifest maximum quantities 64, parameters 32, candidates 128, fixture points 32.
- Exact rational intermediates used for normalization are bounded to 4,096 bits;
  exceeding that bound returns UNSUPPORTED, never an approximate identity.

All limits have exact-at-limit and above-limit tests where the bound controls an
input surface. Invalid/unsupported input returns a reason code and explanation.

Dimensions use existing Dimension operations. Addends must match, exp/log inputs
must be dimensionless, parameter dimensions count, final dimension must equal the
target. Units are a separate declared convention; no conversion or metrological
certification. Fixture values are finite scalars in the declared convention.

Domain conditions come from every original subtree: denominator nonzero, log
argument positive, nonpositive powers require nonzero base. 0^0 is domain-invalid.
Every subtree evaluates before arithmetic reduction; zero factors cannot hide
undefined or nonfinite operands. Alias definitions also retain their domains.

Canonicalization proves only associative/commutative sum and product ordering,
exact rational arithmetic, and integer-power monomial normalization. Domain
conditions and parameter roles participate in identity. Approximate constants do
not become rationals. Alias substitution is supported only for declared exact
monomial definitions. Same structural family with different fitted values does
not imply same model. Different canonical keys yield NOT_ESTABLISHED, never a
claim of inequivalence. Finite-point agreement never proves an identity.

## Demonstration and independent expectations

Mocks are explicitly `mock-tree/1` and `mock-postfix/1`; neither is a real engine.
Paired examples: x/t²; x/t² + x/t²; and (x/t²) log(z), with different order/shape
and IDs. At x=8,t=2,z=1 and x=18,t=3,z=e, expected values respectively (2,2),
(4,4), (0,2). An additional exp(0) physical expression and fitted scalar
exercise exp and parameter roles. Expected dimensions L T^-2, eligibility and
domain restrictions are specified independently of either adapter.

Historical imports are exactly b01-adequate-n1 and b01-curved-n2 at
7405d07e717fbe1e84d3c1afb5b7f737e86c6103, blobs
7937d9f84d56e2c12a39cbe2e6ee44a21247b338 and
6e3124c349e746d994d9a860ecd25e193653898f. Preserve complete discovery.ranking
(five entries each), all members/order/coefficients/diagnostics/labels. Manifest
metadata is bound to pinned public design and input digests. No fitting, discovery,
generation, held-out or oracle access. Compare direct expression evaluation with
exp(log_coefficient + fsum(power*log(value))) on fixed positive points using
relative tolerance 2e-12 and absolute tolerance 1e-14. Both stored coefficients
remain unchanged. This tolerates different floating arithmetic routes only.

All work-order conformance boundaries are mandatory. Six production mutants:
domain erasure, transitive/canceled leakage bypass, dimension bypass, evidence
promotion, raw-binding bypass and candidate loss. Each must be killed by its
designated semantic assertion. Baseline and equivalent control survive. Retain
failed mutation calibration evidence and recalibrate only the affected mutant.

## Evidence and acceptance

Snapshot instructions, then this sole-file freeze commit, then GitHub draft PR
server anchor precede evaluator implementation. Pin final source/fixtures/imports,
numeric policy and CPython 3.12 environment before final conformance emission.
One report is the authoritative disposition route. A read-only guard reached by
unittest discovery checks exact record types, source/result bindings, historical
pins and semantic replay; it never writes or regenerates expected artifacts.
No verify.yml edit is planned. Preserve failed published epochs in forward history.

PASS requires both mocks, all ten historical candidates, every work-order boundary,
six calibrated killed mutants and two surviving controls, with final local tests
and exact-head CI. Otherwise use the work order's PARTIAL/FAIL/NO_GO/UNRESOLVED
definitions. New boundary claims remain PROVISIONAL — INDEPENDENT AUDIT PENDING.
True merge only; leave PR unmerged for Miguel. All historical benchmark files and
old scientific claims remain unchanged. No subsequent package is authorized.
