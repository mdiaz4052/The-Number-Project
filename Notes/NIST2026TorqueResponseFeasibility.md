# NIST torque-to-G response feasibility

**PROVISIONAL — INDEPENDENT AUDIT PENDING.**

**Overall disposition: `NO_GO_IDENTIFIABILITY`, bounded to the reviewed source contract.**
The Table 15 reported-input preliminary conversion is available. A unique global response
of the four configuration summaries, or a unique usable mean subspace, is not established.
This is a completed feasibility assessment, not evidence against an actual torque and not
an implementation failure. No torque magnitude, real-data residual statistic, p-value,
corrected/pooled G, or uncertainty adjustment was calculated.

## Operational question and available conversion

The fixed intervention adds the same signed `tau` to each recovered **peak-to-peak servo
torque difference**, after extraction and existing corrections, before preliminary G.
Free-deflection inputs are unchanged. This is a project-defined readout intervention,
not a claim of a physical torque acting only in servo mode. A DC torque equally present
at both source positions cancels in their difference and is a different intervention.

The controlling source is Schlamminger et al., *Metrologia* 63 (2026) 025012,
DOI [10.1088/1681-7575/ae570f](https://doi.org/10.1088/1681-7575/ae570f),
[NIST PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075), CC BY 4.0.
Equation (5), printed p.5, separates

`K = 8 ms mt (Gamma_plus - Gamma_minus)/Rs`

from its symmetric factor-16 approximation. Table 15's caption, printed p.25, explicitly
prescribes `delta_N = G * 16 * Gamma_max * ms * mt / Rs`. The implementation evaluates
**that reported conversion only**, using the table's individual campaign geometry.
Table 2 (p.10) supplies per-body average masses, with the apparent source masses already
corrected for air buoyancy. No four-body multiplication or extra buoyancy correction is added.
Equation (20) and its following paragraph (p.8) identify the servo torque difference and
the residual elastic-torque correction; the operational offset is placed after it.

Table 10 (p.17) distinguishes the actual full half-difference from the one-sided peak;
it does not authorize replacing the Table 15 entries by its generic row. Its printed
Gamma column also has a dimensional heading inconsistent with the dimensionless factor
in §3.1. Table 15's explicit conversion and §3.1 control the present representation.
No conclusion that Table 15's named factor is a physically exact peak or exact
half-difference is needed or asserted. Separate campaign extrema are not recovered.

In canonical order, `b=(1,0,1,0,1,0,1,0)` and `d_j=b_j/K_j`.
The artifact includes exact fractions, SI dimensions, and the permutation from Table 15's
sapphire-first rows and free-before-servo columns. Copper clocking `theta` is distinct
from the source-position azimuth that reverses gravitational torque.

| Servo campaign | Preliminary response, U per pN m (decimal display) |
|---|---:|
| Copper 0 degrees | 0.000213922926229764 |
| Copper 120 degrees | 0.000214015340143721 |
| Copper 240 degrees | 0.000214017162766368 |
| Sapphire | 0.000477374148955666 |

Every direct free-input response is zero at this **preliminary** stage.
`U=10^-11 m^3 kg^-1 s^-2`; `1 pN m=10^-12 N m`.
`K` has units `kg^2/m` and `1/K` has units `m/kg^2`, so conversion to U per pN m
multiplies `1/K` by `1/10`. Exact arithmetic means exact evaluation of reported decimals,
not unrounded geometry, physical exact symmetry, or robustness to coefficient rounding.
No measured torque central value, G value, torque/G ratio or density approximation enters
these gains.

## Why preliminary conversion does not identify the final response

Section 6.7, equations (40)-(41), p.17, describes cancellation of a common sinusoid over
three equally spaced clockings at common geometry. Section 9 and Figure 25, p.25,
describe a **joint posterior** with two method intercepts and shared amplitude/phase:

`G_i(theta)=G_i + B*cos(theta) + C*sin(theta)`.

The copper summaries are posterior means of the intercepts. They are not identified
in the reviewed passages as independent equal-weight averages. The three preliminary
servo gains above differ. Their perturbation therefore is not a constant shift of the
servo intercept: forcing the three free inputs to stay fixed forces a shared harmonic
shift to vanish, which would require the servo perturbation to be constant too.
This defeats the simple parameter-translation proof; it does not prove that no other
valid equivariance theorem could exist.

The nearest positive description is the joint model and marginal posterior means in
§9/Figure 25. That passage does not specify the copper likelihood/prior distributions
or supply a global directional-equivariance identity. The later consensus prior and
sampler discussion is a separate stage; its missing implementation details are not
borrowed as blockers here. A sampler need not be reproduced if an analytic response
identity can be established.

For sapphire, the nearest positive description is the preliminary conversion and
“corresponding quantities” brought together with copper to form four determinations
in §9, p.25. One clocking by itself does not establish the final summary functional.
An identity map would give the preliminary response under that extra assumption;
no such four-summary source authorization is emitted. Even granting this sapphire
identity would not resolve the copper ambiguity.

## Exact synthetic demonstration and its limits

The frozen six-row design uses columns `(servo intercept, free intercept, cos(theta),
rescaled sin(theta))`. At 0, 120 and 240 degrees the cosine column is `(1,-1/2,-1/2)`
and the rescaled sine column is `(0,1,-1)`. Rescaling the sine coefficient preserves
exactly the common amplitude/phase mean-model family. For synthetic diagonal precision
`W=diag(1,2,3,4,5,6)`, compare Gaussian posterior mean maps

`H_Lambda=(X^T W X + Lambda)^(-1) X^T W`

with fixed precision `Lambda=diag(0,0,0,0)` and `diag(0,0,1,1)`.
Zero precision denotes a flat prior; the full-rank design gives a proper posterior.
The second choice has a proper Gaussian prior on the shared harmonic coefficients,
with the intercept priors still flat. These are completions of the qualitative Bayesian
mean-model contract on synthetic data. Neither is licensed as the NIST algorithm,
chosen to fit NIST outcomes, or claimed to reproduce any published posterior/plot.
The source does not exclude either prior at this stage in the reviewed passages.

For the frozen synthetic servo direction `(1,0,2,0,4,0)`, the two copper responses are

| Prior choice | Servo-intercept response | Free-intercept response |
|---|---:|---:|
| Flat | 811/295 | -111/590 |
| Harmonic precision one | 12221/4403 | -741/4403 |

Thus unchanged direct free inputs do **not** entail an unchanged free summary.
Neither servo response is the equal-weight average `7/3`.
Extending both with the same synthetic sapphire response `(3,0)` produces different
exact row-reduced representations of `span(1,a)`, recorded in the artifact.
Since their common sapphire coordinates are 3 and 0, a transformation
`a2=c*a1+q*1` would force `q=0` and `c=1`, but their copper coordinates differ.
The ambiguity therefore can change the model's mean subspace, not merely the torque scale.

This demonstrates why the qualitative estimator description does not generally imply
one response; it is **not** a theorem that every algorithm reproducing NIST's numerical
posteriors must disagree, nor an enumeration of every possible completion.
The NO-GO states that a source-identified response/subspace was not established from
this bounded record. Unknown quantities remain explicit absence, never numeric zero.

The tests also exhibit a genuine affirmative case: for the constant servo direction
`(1,0,1,0,1,0)`, both posterior maps return parameter response `(1,0,0,0)`.
Translation of an unpenalized intercept leaves likelihood residuals and nuisance priors
unchanged, so the posterior mean translates without requiring sampler details.
Exact subspace tests recognize common nonzero rescaling and common-mean addition;
rank-one responses are `NOT_TESTABLE_AS_INTERNAL_CONTRAST`, not evidence of no torque.
A local Jacobian or bounded-domain identity cannot acquire an unrestricted global label.
Even an affine numerical estimator response would not establish unbiasedness or a
Gaussian sampling law for a future test.

## Corpus, absence and chronology

The supplied specification predates the freeze. Its recorded planning page inspections
are attributed, not relabeled as independent review or newly authored results.
During implementation preparation, raw PDF bytes were obtained:
SHA-256 `c79552d62f4d4f4e85cfbbb00f135c1d985b596d9cdcde9bee57cfe4618f33dc`.
Rendered PDF indices 5, 10, 17 and 25 were actually inspected; parsed passages included
pp.5-8, 10, 15-17 and 24-26. Indices equal printed page numbers here; the cover adds one
to the physical sheet count. PDF custody is an implementer attestation, not independent
corroboration and not a claim that CI redownloads the source.

The NIST publication page's associated links were reviewed once: DOI and local PDF.
No separate associated material was identified there or in the reviewed PDF. DOI/publisher
article access failed, so the publisher's associated-material index was not reviewed.
That access limitation is **not** evidence that a supplement or author code does not exist.
No specific essential unreviewed supplement was identified. The present disposition is
restricted to the obtained article contract. Discovery of material relevant source content
requires disclosure and a new bounded review; it cannot be silently consumed under this freeze.

Verified base: `81169a9d54e1540d82b4ad14ffa7dcd6d4fd3c77` (PR #49 true merge).
Published sole-file freeze: `daf900f5fdac06d47b13c9de9272b9e734245cd6`;
SHA-256 `44f56d0e889474765910439329f81896db61df75d48d7a7e379ea233ff2802bb`.
GitHub draft PR #50 creation anchor: `2026-09-10T01:49:24Z`.
The unsuccessful direct Git push left an unpublished local commit of identical freeze
bytes; the GitHub connector published the authoritative sole-file freeze above before
the draft anchor. No evaluator, response calculation or result note preceded the anchor.
**outcome_blind=false**: prior #47-49 outcomes and incidentally visible source outcomes
were known and explicitly excluded from numerical use.

The result-driving snapshot is committed before artifact emission. Its SHA and hashes
are in both deterministic artifacts. The strict inherited freeze verifier and full-history
first-introduction predicates preserve the chronology through true merges.
No intermediate-commit green requirement is imposed.

## Verification and next scientific request

Behavior tests independently check forward differential torque, units, labels, signs,
coefficient consumption, affine propagation, coupled posterior stationarity, equal-weight
failure, genuine equivariance, exact mean subspaces and every disposition. Artifact tests
check freeze/anchor/source binding, strict JSON, freshness, actual filesystem and Git blob
read closure and allowed repository imports. Excluded-context changes leave authorization
and numerical output invariant without using digest rejection as the oracle.
Builder reads are confined to the new source/projection files, two source-history helpers
and this PR's notes. Mutation verification additionally reads its runner, harness and tests.
No #47-49 result artifact, prior measurement builder, HUST authorization, or Lean source
is a scientific input. The prior note is motivation only; ancestry is not an observation.

Eight isolated production mutations cover the frozen factor, prefix, geometry, excluded
outcomes, unlicensed averaging, erased coupling, subspace equivalence and stage-promotion
boundaries. Each executes its named semantic assertion on a valid fixture. The unmodified
baseline and executable-equivalent control must survive; the faulty affine calibration
must be killed. Runtime/import/syntax errors, skips, digest/history failures and unrelated
assertions earn no kill credit. The read-only mutation guard validates saved execution
evidence without rerunning the family. Final counts and exact-head CI belong in the PR
and rolling audit handoff; this note does not anticipate their success.

The smallest useful next request is the **copper-stage likelihood and priors, or an analytic
proof of directional equivariance for this exact intervention**, plus an explicit sapphire
summary map. A response-only theorem could suffice without raw data or every posterior
sample. Until then no fixed four-summary torque test is authorized. A later GO would still
need its own test specification/freeze and treatment of coefficient precision, estimator
expectation and statistical calibration.

No new in-scope BLOCKING finding is known at source preparation; independent audit remains
pending. E-001 stays live outside this read/claim boundary. No new deferred-maintenance ID
or closure is assigned, and no unrelated hardening is proposed.
Leave PR #50 unmerged for Miguel. Required integration: **Create a merge commit**;
never squash or rebase the freeze ancestry.
