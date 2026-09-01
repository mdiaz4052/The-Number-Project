# UW 2000 published-data preregistration v1 — clarification 1

**Issued:** 2026-09-01

**Status:** normative clarification; the original preregistration remains unchanged

**Result-sensitive UW numbers entered before this clarification:** none

This clarification resolves an ambiguity found during independent review after the UW
source audit had already reached `NO-GO` and before any empirical transcription or
`G_hat` was created. It does not change the selected source, estimator-selection rule,
acceptance conditions, precision rules, comparison boundary, or audit decision.

Section 3 of the original preregistration permits “exact mathematical constants required
by the published estimator.” Under the current schema, that means constants such as
`pi` may occur symbolically in the documented estimator relation and exact symbolic
derivation. It does **not** authorize an arbitrary decimal `QuantityRecord` to avoid
source-provenance validation merely by setting `exact=True`.

The present schema has no dedicated record type that distinguishes an exact mathematical
constant from a calibration coefficient. Consequently:

- an exact mathematical constant should remain in the symbolic estimator relation rather
  than masquerade as an empirical observation or calibration input;
- if a future transcription needs a materialized numerical approximation of such a
  constant, its representation and computational provenance require explicit review;
- `exact=True` alone never exempts a populated empirical estimator, calibration, or
  correction record from the current source-metadata gate; and
- if faithful computation requires a symbolic coefficient that the current monomial
  schema cannot represent, that is a representational gap to review separately.

These rules preserve the original permission for exact mathematics without creating a
numeric calibration-path loophole.
