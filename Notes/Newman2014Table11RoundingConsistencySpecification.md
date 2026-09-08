# The Number Project — Newman 2014 Table 11 Rounding-Consistency Specification

## Objective

Implement one bounded empirical-reproduction PR for Newman et al. 2014 (UCI-14) that asks whether each printed Table 11 quadrature-sum uncertainty is representable by component values inside the rounding bins implied by the same printed table.

This is the first post-PR-41 test intended to let the existing `incompatible` branch confront a new real published table. No outcome is required in advance.

## Selection and nonclaims

The source-feasibility selection precedes all rounding calculation. Newman 2014 is selected over the standing Rosi 2014 alternative because the peer-reviewed measurement paper exposes, in one explicit table, three uncertainty components and a printed quadrature sum for each of three fibre results, and the surrounding text states that the components are combined in quadrature. The choice is based on source quality and reconstructability, not on any precomputed RSS discrepancy.

This PR does not reproduce the raw torsion-pendulum estimator, reanalyse the underlying data, audit the final integer-ppm uncertainty statements, compare central G values, infer a common constant, assign probabilities, diagnose discrepancies, or update the cross-measurement joint object.

## Intended base

`96ec62325d2f5b5e78dee36754ed934234c5d0e1`, the true merge commit of PR #41.

## Source surface

Peer-reviewed source: Riley Newman, Michael Bantel, Eric Berg, and William Cross, “A measurement of G with a cryogenic torsion pendulum,” Philosophical Transactions of the Royal Society A 372:20140025 (2014), DOI `10.1098/rsta.2014.0025`.

Numerical authority: Table 11, printed/PDF page 22, containing the rows `statistical`, `systematic`, `analysis method`, and `quadrature sum` for fibres 1–3. The explanatory text states that the three contributions and their quadrature sum are the assigned uncertainty components.

The source attestation must freeze the exact transcription before any terminal classification. CI performs no live network access.

## Declared mathematical model

For each fibre independently, let the three unrounded positive component uncertainties be `x_1`, `x_2`, and `x_3`, each lying inside the open interior of the rounding bin implied by its one-decimal printed value. The represented uncertainty is

`R = sqrt(x_1^2 + x_2^2 + x_3^2)`.

The printed Table 11 quadrature sum supplies only the terminal comparison interval. It must not enter candidate generation, source selection, or the conservative enclosure.

All arithmetic is exact rational arithmetic on `R^2`; square-root values are display-only.

## Rich preregistered schedule

Use a full independent tensor grid across the three component bins, not the historical one-dimensional diagonal schedule. Each component independently uses the frozen interior parameters

`0, ±1/8, ±2/8, ±3/8, ±4/8, ±5/8, ±6/8, ±7/8`.

This yields `15^3 = 3375` predetermined candidates per fibre. Every candidate for all three fibres must be constructed before any terminal comparison is loaded or classified.

This richer grid handles FH-2 prospectively. `unresolved` remains schedule-relative: enclosure overlap plus no witness among the 3375 frozen candidates.

## Classification

- `compatible`: at least one frozen interior grid point yields an exact squared uncertainty strictly inside the nondegenerate printed terminal rounding interval.
- `incompatible`: the conservative exact enclosure over the entire three-dimensional component box is disjoint from the closed squared terminal interval.
- `unresolved`: the enclosure overlaps but the frozen grid supplies no witness.
- malformed or missing evidence is invalid and never a numerical verdict.

A negative result is explicitly model-relative: it means `not_representable_under_the_declared_table11_rounding_model`, not impossibility in physical reality.

## Required implementation surfaces

Add only:
- `Experiments/GMeasurements/newman_2014_table11_rounding_consistency_preregistration_v1.json`
- `Experiments/GMeasurements/newman_2014_source_attestation_v1.json`
- `Experiments/GMeasurements/newman_2014_table11_rounding_consistency_v1.json`
- `Experiments/GMeasurements/newman_2014_table11_rounding_consistency_mutations_v1.json`
- `Discovery/newman_2014_table11_rounding_consistency.py`
- `Discovery/newman_2014_table11_rounding_consistency_mutations.py`
- `tests/test_newman_2014_table11_rounding_consistency.py`
- `tests/test_newman_2014_table11_rounding_consistency_mutations.py`
- `Notes/Newman2014Table11RoundingConsistencySpecification.md`
- `Notes/Newman2014Table11RoundingConsistency.md`
- two read-only `--check` steps in `.github/workflows/verify.yml`.

Do not modify `Discovery/rounding_consistency.py`, the joint-inference module, historical G artifacts, Lean sources, or shared preregistration/history infrastructure.

## Verification

Focused tests must cover all three scopes, source-schema exactness, one-decimal rounding bins, 3375-candidate tensor enumeration, terminal isolation, exact enclosure classification, witness membership, all three verdict meanings on synthetic controls, central-value invariance, source/provenance freshness, and model-relative negative wording.

Because the new schedule and epistemic classification boundary are new, add one bounded mutation family. It must challenge at least: collapsing the tensor grid to the old diagonal, dropping a required scope, allowing terminal data into candidate generation, promoting `unresolved`, weakening `incompatible`, changing component half-width, and erasing the model-relative negative qualifier. Include distinct killable and executable-equivalent calibration controls and reject infrastructure failures as kills.

Final local validation: focused tests, one full Python-suite pass, both new guards, relevant mutation guard, and `git diff --check`. Exact-head GitHub CI is the repository-wide final automated gate. No local Lean run is required because no Lean-linked surface changes.

## Merge semantics

The preregistration is the only file in the first commit, whose sole parent is the intended base. Push that freeze and create the draft PR before implementation. Record the GitHub-controlled creation timestamp as the external anchor. Merge by true merge commit only; never squash, rebase, or rewrite the freeze.
