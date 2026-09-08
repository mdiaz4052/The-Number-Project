# Newman 2014 multi-resolution terminal-constraint result

## Question

If the same Newman et al. 2014 fibre uncertainty is printed at two different resolutions in the same paper, what exact terminal domain follows from requiring one underlying value to be consistent with both reports, and does the established Table 11 component model remain representable inside that joint domain?

This is an FH-6 capability formalization. It is not a new measurement reconstruction and is not an outcome-blind experiment: Claude's audit of PR #42 had already checked the integer conclusion statements against the Table 11 reconstruction before this PR was frozen.

## Frozen reporting model

For each fibre, the Table 11 one-decimal quadrature sum contributes a closed ±0.05 ppm consistency interval. The conclusion's integer uncertainty contributes a closed ±0.5 ppm consistency interval. The effective terminal domain is their exact closed intersection.

Closed endpoints avoid assuming an undocumented tie-breaking convention. A `compatible` witness must nevertheless land strictly inside a nondegenerate joint terminal interval and use strictly interior component values.

The component model and candidate schedule remain those established in PR #42:

`R^2 = x_statistical^2 + x_systematic^2 + x_analysis_method^2`,

with 3,375 independently shifted component candidates per fibre. Candidate generation receives only the component projection, component half-width, and frozen schedule. Terminal values and terminal resolutions do not enter candidate construction.

## Exact terminal intersections

| Scope | Table 11 report | Table 11 interval (ppm) | conclusion report | conclusion interval (ppm) | joint interval (ppm) | width ratio vs Table 11 |
|---|---:|---:|---:|---:|---:|---:|
| fibre 1 | 14.5 | [14.45, 14.55] | 14 | [13.5, 14.5] | **[14.45, 14.50]** | **1/2** |
| fibre 2 | 22.2 | [22.15, 22.25] | 22 | [21.5, 22.5] | [22.15, 22.25] | 1 |
| fibre 3 | 19.6 | [19.55, 19.65] | 20 | [19.5, 20.5] | [19.55, 19.65] | 1 |

Thus the second published representation materially sharpens fibre 1: its terminal width falls from 0.10 ppm to 0.05 ppm. It does not narrow fibres 2 or 3 because their integer intervals already contain the full Table 11 intervals.

## Result

All three real scopes remain `compatible` under the declared multi-resolution reporting model.

The unshifted midpoint candidate remains a strict-interior witness in every scope:

| Scope | exact midpoint `R^2` (ppm²) | verdict | witness kind |
|---|---:|---|---|
| fibre 1 | 208.91 | `compatible` | `unshifted_midpoint` |
| fibre 2 | 494.53 | `compatible` | `unshifted_midpoint` |
| fibre 3 | 385.49 | `compatible` | `unshifted_midpoint` |

For fibre 1, 208.91 ppm² lies strictly inside the squared joint terminal interval [208.8025, 210.25] ppm². The tighter publication constraint therefore sharpens the certificate without changing its verdict.

This outcome was known before the PR freeze from Claude's PR #42 audit. The scientific contribution of this PR is the reproducible multi-resolution capability, exact provenance boundary, width reporting, and explicit failure semantics—not discovery of the three verdicts.

## New capability

The multi-resolution primitive can now distinguish three important cases:

- mutually inconsistent printed terminal representations → `incompatible` with reason `terminal_constraints_disjoint`;
- a nonempty joint terminal domain that the entire declared component box cannot reach → `incompatible` with reason `component_box_disjoint_from_joint_terminal`;
- a degenerate/boundary-only or schedule-overlap case without a strict scheduled witness → `unresolved`.

Negative labels remain explicitly model-relative. No hidden unrounded values, unique historical rounding procedure, probability model, comparison of central `G` values, universality claim, or joint-measurement estimator follows.

## Implication

FH-6 is useful but bounded: the extra reporting precision increases falsification power only when two publication resolutions cut the allowed domain differently, as fibre 1 demonstrates.

After this capability is established, the higher-value scientific frontier is not another single-run quadrature certificate or another composition layer. It is a published measurement whose reported aggregate is a weighted combination across multiple runs, giving the project's enclosure and weighting machinery its first genuine `n >= 2` scientific use.
