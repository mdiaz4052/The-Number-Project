# UW 2000 published-data reproduction preregistration v1

**Frozen scope:** source-availability audit followed by a published-data transcription
only if the audit reaches `GO`  
**Preregistered:** 2026-09-01  
**Project measurement:** no  
**Independent replication:** no

This contract was checked in before any UW result-sensitive number was entered into a
repository measurement record. Its first purpose is to decide whether the public record
permits a faithful transcription. A documented `NO-GO` is an admissible and successful
outcome of the pilot.

## 1. Experiment and source edition

The candidate is the University of Washington angular-acceleration-feedback torsion
balance reported by J. H. Gundlach and S. M. Merkowitz in *Physical Review Letters* 85,
2869--2872 (2000), DOI
[`10.1103/PhysRevLett.85.2869`](https://doi.org/10.1103/PhysRevLett.85.2869).
The open manuscript edition is arXiv
[`gr-qc/0006043v2`](https://arxiv.org/abs/gr-qc/0006043v2), revised 2000-08-08.

The proposed companion citation, *Physical Review D* 66, 082001 (2002), is not accepted
as part of the evidence set until its title, authors, DOI, and relevance are verified.
Any genuinely related official correction, erratum, supporting material, or later
apparatus paper must be identified independently and cited by exact edition.

## 2. Estimator relation

The transcription must use the relation actually supported by the selected primary
source. The audit begins with the paper's full multipole angular-acceleration relation
and its stated approximations and corrections; it does not assume in advance that a
single convenient monomial is adequate.

Before implementation, the audit must identify all quantities required to solve the
published relation for `G_hat`, including the observed signal amplitude, the complete
mass-distribution or multipole coupling used in that solution, and every material
correction. If the paper's faithful estimator cannot be represented by the current
schema, that is a representational gap, not permission to change the estimator.

## 3. Permitted and excluded inputs

Permitted inputs are limited to:

- observations directly reported by the primary source;
- calibration values with an independently identifiable source and exact locator;
- values derived only from reported parents using a displayed derivation and unit
  conversion;
- corrections explicitly reported for the selected result; and
- exact mathematical constants required by the published estimator.

Excluded inputs include inferred digits, guessed apparatus parameters, secondary-source
values presented as primary, and any value obtained by algebraically inverting a
published `G` result or a recommended `G`. A source map must classify every number as an
observation, calibration, correction, model input, derived value, or terminal comparison
and must list its provenance parents.

The published UW value of `G`, any later corrected UW value, and every CODATA value are
comparison references only. They may not affect source selection, calibration,
correction, tuning, candidate choice, acceptance thresholds, or rounding.

## 4. Uncertainty and covariance method

Reported standard uncertainties are transcribed as one-standard-deviation quantities
only when the source says so. Bounds, approximate values, fit scatter, and correction
uncertainties retain their published meanings rather than being silently converted into
standard uncertainties.

The propagation method must follow the publication if it is sufficiently specified. A
quadrature combination is permitted only for components the source treats that way.
Documented correlations and shared calibration sources must be represented. An explicit
zero-correlation assumption is permitted only with source support or a separately
reviewed justification; an absent covariance account remains incomplete.

## 5. Precision, rounding, and coverage

- Decimal text is transcribed exactly as printed; no unpublished digits are appended.
- Unit conversions use exact decimal scale factors where available.
- Intermediate calculations retain all transcribed digits and at least ten additional
  decimal guard digits.
- Rounding occurs once, at terminal presentation, to the precision of the published
  comparison or the propagated uncertainty, whichever is less permissive.
- The expected coverage convention is one standard deviation. No confidence probability
  or coverage factor is invented when the paper does not provide one.

These rules are fixed without consulting whether a rounding choice improves agreement
with the published value.

## 6. Decision and acceptance conditions

`SUCCESSFUL_REPRODUCTION` requires all material estimator inputs, calibrations,
corrections, uncertainty components, and correlation declarations to be independently
transcribable; a target-clean `G_hat` and combined uncertainty must then agree with the
paper under the frozen precision and coverage rules. Agreement is assessed only after
the estimate exists.

`INCOMPLETE_REPRODUCTION` applies when an essential quantity, calibration, correction,
uncertainty component, or correlation is unavailable or cannot be mapped without an
assumption. It must not be replaced by the paper's headline output.

`SOURCE_CONTRADICTION` applies when authoritative editions give materially inconsistent
inputs or methods and the conflict cannot be resolved by edition history.

`TARGET_LEAKAGE` applies when a published or recommended `G` enters any estimator,
calibration, correction, tuning, candidate-selection, acceptance, or rounding path, or
when an output is inverted to manufacture an input.

`UNSUPPORTED_CALIBRATION` applies when a populated coefficient lacks a direct source
locator and independently documented provenance. Merely declaring no registered
algebraic path to `G` does not prove real-world experimental independence.

The audit decision is `GO` only if `SUCCESSFUL_REPRODUCTION` remains possible without a
schema distortion. Otherwise it is `NO-GO`, with the exact missing information or
representational gap recorded.

## 7. Terminal comparison

If and only if the audit reaches `GO`, the computation must produce `G_hat` before
loading the published UW output into a terminal external-comparison node. A CODATA value
may be added only as a second terminal comparison. Numerical closeness can trigger human
review but cannot by itself prove leakage or justify rejection.

## 8. What this pilot can establish

A successful result would show that the repository can transcribe and recompute one
published result from public documented inputs while preserving evidence boundaries. It
would not be a new value of `G`, a project-operated measurement, an apparatus validation,
an independent replication, or a new physical prediction.

A `NO-GO` would establish only that this selected public record and current schema do not
support an independent transcription under these controls. It would not dispute the
authors' measurement or its scientific validity.
