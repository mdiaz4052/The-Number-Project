# Newman et al. 2014 Table 11 rounding-consistency result

## Question

Can each one-decimal `quadrature sum` printed in Table 11 of Newman et al. (2014),
*A measurement of G with a cryogenic torsion pendulum*, be represented by some
interior values consistent with the one-decimal printed component cells, under the
paper's stated quadrature rule?

This is a bounded representation audit. It is not a reconstruction of the raw
torsion-pendulum estimator, a comparison of measured values of `G`, a sampling
model, or a test of universality.

## Prospective selection and freeze

Newman 2014 and Rosi 2014 were considered on source quality and reconstructability.
Newman was selected because one table supplies three named component contributions
and three printed aggregate targets, with the surrounding text explicitly stating
quadrature combination. No root-sum-square discrepancy, interval overlap, witness,
or terminal classification was calculated before the preregistration freeze.

The preregistration was frozen at
`77c47c4246746199a625392927d22c921e8d8985`, then externally anchored by GitHub
draft PR #42 at `2026-09-08T02:48:52Z`.

## Frozen model

For each fibre independently,

`R^2 = x_statistical^2 + x_systematic^2 + x_analysis_method^2`.

Every printed one-decimal component is represented by its closed ±0.05 ppm
rounding bin. The terminal one-decimal quadrature sum is likewise represented by a
closed ±0.05 ppm interval. A compatible witness must use strictly interior
component values and place the exact squared quadrature sum strictly inside the
terminal squared interval.

The candidate schedule is richer than the earlier diagonal schedule. Each of the
three component cells receives its own independently frozen shift parameter from

`0, ±1/8, ±2/8, ..., ±7/8`,

giving `15^3 = 3375` candidates per fibre and 10,125 candidates total. All
candidates are constructed before terminal comparisons enter classification.

## Published Table 11 inputs

| Scope | statistical (ppm) | systematic (ppm) | analysis method (ppm) | printed quadrature sum (ppm) |
|---|---:|---:|---:|---:|
| fibre 1 | 7.7 | 10.1 | 6.9 | 14.5 |
| fibre 2 | 15.7 | 10.2 | 12.0 | 22.2 |
| fibre 3 | 11.3 | 12.4 | 10.2 | 19.6 |

The paper's later integer-ppm statements (14, 22, 20 ppm) are outside this audit.

## Result

All three scopes are `compatible`.

The first frozen candidate is the unshifted midpoint `(0, 0, 0)` in every scope,
and it supplies a valid interior witness for each printed Table 11 quadrature sum.

| Scope | exact midpoint squared sum (ppm²) | midpoint uncertainty (ppm, descriptive) | verdict |
|---|---:|---:|---|
| fibre 1 | 208.91 | sqrt(208.91) | compatible |
| fibre 2 | 494.53 | sqrt(494.53) | compatible |
| fibre 3 | 385.49 | sqrt(385.49) | compatible |

The full component-box squared-uncertainty enclosures and terminal squared
intervals are retained exactly in the machine artifact. Classification never
depends on displayed decimal square roots.

## Interpretation

This third real published-table test did not make the falsifying branch fire.
That negative scientific result should be retained rather than selecting another
paper after seeing it. It establishes that Newman Table 11's three printed
quadrature totals are each representable under the declared one-decimal rounding
model, and it demonstrates the prospectively richer independent tensor schedule
on a new publication.

`compatible` does not identify the authors' hidden unrounded component values,
prove nearest rounding, or show uniqueness. `incompatible`, had it occurred,
would have meant non-representability only within the declared Table 11 component
rounding box and quadrature model. `unresolved` remains schedule-relative.

The next independent measurement experiment may therefore proceed to another
source-selected publication, such as the already-deferred Rosi 2014 candidate,
without altering or suppressing this compatible result.
