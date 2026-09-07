# The Number Project — Bounded rounding-consistency implementation specification

Status: implementation authorized by Miguel; freeze this specification and its machine-readable protocol before production implementation. One implementation PR covers the protocol and result.

Baseline: `3fb60ecf64a61db2347bb154cc7e20b02b0f6ca3` (PR #38 merge).

## 1. Purpose and bounded scientific question

Add a reusable, exact-arithmetic discrepancy classifier and exercise it on the HUST 2018 AAF combined relative standard uncertainty. The question is:

> Under the declared rounding intervals and the already adopted combination model, can an admissible set of component values produce a combined relative uncertainty that rounds to the published 11.61 ppm?

The existing reconstruction is approximately 11.6161857764 ppm. This result and Claude's exploratory rounding draws are already known. The preregistration freezes implementation and classification rules; it does not establish a blind test or predictive success.

This is a conditional consistency diagnostic, not a new MeasurementModel, an amended measurement, an explanation of the authors' actual calculation, or a physical-theory falsification. Neither a compatible result nor an incompatible result is required for acceptance.

## 2. Frozen inputs and boundaries

- Use the three individual central values from `hust_2018_aaf_depth_2b_measurement_models_v2.json` and the 21 component rows in each AAF column of `hust_2018_aaf_required_inputs_depth_2b_v2.json`. Bind both whole files by byte length and SHA-256, and bind an explicit calculation projection containing only scope IDs, reconstructed central values, component IDs, ppm values, and correlation classes.
- Use the already reviewed combination-rule projection in the PR #38 preregistration for source authority. Table 1's official source record supplies the table locator. Do not reinterpret the historical source audit or change depth-2b authorization.
- Read the published 11.61 ppm as a separate comparison specification. It may enter classification and witness selection only after all target-independent bounds and candidate values are computed. It cannot enter the uncertainty calculator, weights, candidate generation, or source authorization.
- The immutable PR #38 combined artifact supplies context and a terminal regression reference only; the diagnostic calculator must run without it or PR #37's feasibility output. Existing measurement artifacts and evidence statuses remain unchanged.
- Preserve every pre-existing file under `Experiments/GMeasurements/` byte-for-byte. Changes outside the listed implementation surfaces require a concrete correctness reason, not housekeeping.

The 63 printed component cells each have two decimal places in ppm. Assume rounding to the nearest 0.01 ppm: for a printed value c, the admissible closed enclosure is [c − 0.005, c + 0.005]. This is a declared diagnostic assumption, not a verified statement of the publisher's rounding convention. Treat the published combined 11.61 ppm analogously, with enclosure [11.605, 11.615].

An unknown tie convention is handled conservatively: enclosure exclusions use closed bounds; a compatibility witness must lie strictly inside every non-degenerate input interval and the non-degenerate comparison interval. Exact, zero-width synthetic intervals allow equality.

The interval product asserts admissibility bounds, not independent random draws or a probability distribution. It imposes no additional latent equality constraints between repeated printed cells. Their physical error correlations are still the source-prescribed correlations below. All conclusions are conditional on this declared domain. Rounding of central estimates, intermediate apparatus quantities, displayed individual totals, and other publication outputs is outside this PR. Compatibility does not establish joint consistency of every number in the paper.

## 3. Exact calculation and rigorous enclosure

For positive fixed central values g_i and positive candidate component values x_ik in ppm, use:

1. S_i = sum_k x_ik²; v_i = g_i² S_i × 10⁻¹².
2. p_i = (1/v_i) / sum_j (1/v_j); combined central value = sum_i p_i g_i.
3. Same-item non-statistical errors have correlation one across runs. Statistical angular acceleration has zero cross-run covariance. Different component rows do not contribute cross-item covariance.
4. Propagate the covariance with these same recomputed p_i. Do not freeze weights while varying the component budgets, use statistical-only weights, or invert the covariance matrix.

For exact calculation of the squared relative uncertainty in ppm², define a_i = 1/(g_i S_i), q_i = a_i / sum_j a_j. Then:

R² = sum_shared_k (sum_i q_i x_ik)² + sum_independent_k sum_i (q_i x_ik)².

Here q_i = p_i g_i / sum_j p_j g_j; q_i are propagation coefficients, not a replacement estimator. The HUST inventory has 20 shared rows and one independent row. Positive independent contributions make its covariance positive definite; the component construction is positive semidefinite generally.

Parse authoritative finite base-ten strings into exact `Fraction` values. Reject binary floats, malformed or non-positive inputs, inverted intervals, dimension or inventory mismatches, duplicate IDs, unsupported correlation classes, and undeclared calculation fields. Do not use a numerical tolerance to decide compatibility or incompatibility.

Compute one conservative enclosure of R² over the entire declared box using exact rational interval arithmetic. For each a_i enclosure [l_i,u_i], use:

q_i lower = l_i / (l_i + sum_{j≠i} u_j),
q_i upper = u_i / (u_i + sum_{j≠i} l_j).

Propagate these positive q_i and x_ik enclosures through the component-square formula. Retaining dependency overestimation is acceptable. Do not call these endpoints global extrema or claim every enclosed value is attainable. No adaptive subdivision or numerical optimization is required in v1.

Authoritative output bounds are rational ppm² endpoints. Human-readable ppm bounds use integer square-root arithmetic with outward rounding to six decimal places. They must enclose the exact endpoints; formatted decimals never decide a verdict.

## 4. Fixed candidate schedule and three outcomes

Before using the comparison target, evaluate all 15 candidate tables in this fixed order:

`t = 0, −1/8, +1/8, −2/8, +2/8, …, −7/8, +7/8`.

For every cell, x_ik(t) = midpoint_ik + t × half_width_ik. The same t shifts every cell. This sparse schedule is intentionally incomplete and makes no distributional claim. Do not search adaptively toward 11.61, add candidates after seeing a result, or modify the frozen measurement.

Classify a valid problem as:

| Outcome | Required certificate |
| --- | --- |
| `incompatible` | The guaranteed R² enclosure and the closed square of the nonnegative comparison interval are disjoint. This excludes the declared model/domain only. |
| `compatible` | At least one fixed candidate lies inside the admissible input domain and its exact R² lies strictly inside the squared comparison interval (equality allowed for a zero-width comparison). Serialize the first passing candidate, all its component values, exact variance, and membership checks. |
| `unresolved` | The enclosure overlaps the comparison but the fixed schedule supplies no witness. Overlap or failure to find a witness is never enough for a stronger verdict. |

Invalid or missing evidence is an error, not one of these numerical outcomes. A witness outside the guaranteed enclosure indicates an implementation failure and must raise.

Serialize the complete target-independent enclosure and candidate evaluations separately from the comparison and decision. Changing the target may change the decision, never those calculations. Do not report Monte Carlo fractions, p-values, six-sigma significance, probability of truth, or actual-cause attribution.

## 5. Preregistration chronology

Create `Experiments/GMeasurements/hust_2018_aaf_rounding_consistency_preregistration_v1.json` as the only file in the first branch commit, whose sole parent is the baseline above. Include this specification's SHA-256, complete numerical rules, source pins, calculation projection hash, candidate schedule, outcome rules, validation requirements, and explicit prior knowledge.

Push that commit and open the one draft PR before production implementation. Its initial description records the commit SHA, preregistration path and SHA-256, and baseline. Record the GitHub-controlled PR creation timestamp in the implementation. Preserve the preregistration commit and bytes throughout history; amendments require a new version and an explicit explanation. Use a merge commit; no squash or rebase.

Hoist the strict preregistration chronology routine into `Discovery/source_history.py` and route the PR #37, PR #38, and new wrappers through it while preserving their historical pins and PR #37's local-freeze identity check. The shared routine must verify valid immutable commit IDs, the intended sole parent, a preregistration-only first commit adding the file, exact frozen/current bytes and hash, ancestor-of-HEAD, and no intervening modification, deletion, or change-and-revert. Use full reachable history so merge history cannot hide a transient edit. Missing or shallow history fails closed with the existing source-history error convention.

The older general source-state verifier has a different purpose: attesting source bytes at a commit. Do not impose a preregistration-only freeze constraint on its mutation-attestation callers. No unrelated source-history redesign is included.

## 6. Implementation surfaces and validation

New production modules:

- `Discovery/rounding_consistency.py`: positive rational intervals, budget model, exact point evaluation, conservative enclosure, fixed candidate calculations, and certificate classification.
- `Discovery/hust_2018_aaf_rounding_consistency.py`: pinned HUST projection and policy, history checks, canonical artifact builder, read-only `--check`, and explicit `--output` generation.

Add the new specification/result note, versioned preregistration and result JSON, focused tests, and one CI freshness command. Reuse the existing calibrated mutation runner for a bounded new family; update source-bound attestation versions only where the shared chronology changes invalidate existing source snapshots. Preserve retired attestation bytes and hashes. No Lean theorem, physical-bridge schema change, second experiment, new predictor search, or general global optimizer is in scope.

Required tests:

1. Exact point results agree with a separately implemented direct covariance-matrix oracle at midpoint and nonzero shifts, including unequal central values and both correlation classes. Check normalized inverse-total-variance weights and covariance/component agreement.
2. Degenerate intervals collapse to exact results; selected rational points and small exhaustive grids lie inside enclosures. Test endpoint reversal, zero/non-positive inputs, scalar validation, and outward square-root formatting.
3. A single-run component centered at 2 ppm with half-width 0.005 is compatible with 2 ± 0.005; incompatible with 3 ± 0.005; and unresolved with 2.0048 ± 0.0001 under the frozen candidate schedule. Establish all three outcomes independently of the HUST verdict.
4. Boundary-touching enclosures do not establish incompatibility; tie-only candidate contact does not establish compatibility. Enclosure overlap without a witness remains unresolved.
5. HUST source bytes, projection, inventory, two-decimal precision, IDs, units, correlation assignments, bounds, and candidate schedule are pinned. Comparison mutation/deletion cannot enter the calculator. The engine has no import of historical measurement/feasibility calculators or target constants.
6. Existing HUST and bridge artifacts are byte-identical. Do not relax old tolerances or evidence guards to admit diagnostic scenarios.
7. Disposable Git histories independently reject wrong baseline parent, mixed first commit, unchanged pre-existing file/non-freezing ancestor, non-ancestor or squashed freeze, uncommitted edit, deletion, change-and-revert, and hidden side-branch edits. A valid merge history passes. Reuse one fixture helper.
8. A bounded behavioral mutation set attacks classification, enclosure direction, rounding radius/policy, candidate isolation, weighting, and correlation treatment. Include known-killable and equivalent-surviving calibration. Freshness-only failures do not count as semantic kills; invalid runs do not count as kills.

Run a focused development pass and one final full Python suite, affected freshness checks, the required source-bound mutation families once on the committed implementation tree, `git diff --check`, and protected CI at the final PR SHA. Re-run only when changed evidence requires it. Use CI's Lean/proof job; no duplicate local Lean rebuild on untouched Lean surfaces.

## 7. Acceptance, handoff, and exclusions

Accept when the scientific question and limitations are explicit, calculations and classifications have valid certificates, controls and isolation tests pass, chronology and source pins verify, frozen artifacts remain unchanged, and required checks pass. An honest `unresolved` HUST outcome is acceptable and must not trigger unregistered tuning.

The final handoff provides the bounded specification, one implementation PR, immutable verification SHAs, exact scientific conclusion, test/mutation/CI evidence, and an audit prompt for Claude. Ask Claude to attack the rational enclosure, witness validity, target isolation, conditional interpretation, and chronology.

Classify findings as BLOCKING, DEFERRED MAINTENANCE, or FUTURE HARDENING. Keep unrelated audit items deferred; Claude owns the Drive register and IDs. This PR does not modify the contested source-audit/depth-2b classification and cannot resolve E-001 by implication. No standalone cleanup PR is authorized or needed.

References: [PR #38](https://github.com/mdiaz4052/The-Number-Project/pull/38); [Claude's PR #38 audit](https://drive.google.com/file/d/1ZzurGHPZfi3Hd2TV_TI1XRQcNnU8YxPU/view); the pinned official Table 1 and Supplement Section 6 source locators recorded in the repository. Claude's exploratory sampling motivated this diagnostic; its sample frequencies are not scientific acceptance criteria.
