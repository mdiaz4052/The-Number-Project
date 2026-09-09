# The Number Project — NIST Configuration-Model Diagnostics

**Status:** Bounded specification implemented in PR #49 under the separately published JSON preregistration; independent audit pending.  
**Prepared:** September 9, 2026.  
**Intended base:** `61b7b2a0b0136b4859c52a56a8ab8a501284f244`, the verified true merge of PR #48.  
**Working title:** NIST four-configuration contrast and restricted-mean diagnostics.  
**Evidence qualification:** Any scientific result using PR #47's experimental-covariance certificate remains **PROVISIONAL — INDEPENDENT AUDIT PENDING** until that dependency and the new result receive independent acceptance.

## 1. Objective and claim boundary

Determine whether the four existing NIST summary determinations remain flagged under three explicitly restricted extensions of a common-mean model: a measurement-method offset alone, a source-material offset alone, or additive method and material offsets without interaction.

PR #48 already challenges the experimental-only common-mean model. The new capability is to test specified restrictions on the *pattern* of disagreement while retaining the same experimental covariance. It is not merely another rendering of PR #48's Q statistic. It supplies no new observations and no independent confirmation of the original rejection.

All alternatives are project-defined descriptive mean models, not identified physical mechanisms. A non-flagged alternative is not proved correct. No winning model, cause, corrected G, pooled estimate, probability of universality, p-value, variance inflation, configuration removal, Bayesian consensus reproduction, or claim of newly discovering an effect missed by the authors is authorized.

The published source discusses a servo/free offset and its unresolved origin [S3]. Input values, the prior common-mean result, and that discussion have already been seen. Set `outcome_blind=false`; the freeze controls subsequent implementation, not historical knowledge or hypothesis discovery. New candidate-model statistics have not been computed in this planning session.

## 2. Inputs and scientific dependency

Use PR #47's pinned four-input experimental certificate and its NIST source/authorization records [S1]. Freeze an explicit projection of the numerical fields actually consumed: input order, four displayed central values, the full absolute covariance matrix, and the four central-value display cells. Include exact source selectors and SHA-256 pins before publishing the freeze. Retain the exact reported uncertainty/correlation projection as a validation cross-check; it must not silently replace the inherited absolute covariance.

The fixed order is `copper_servo, copper_free, sapphire_servo, sapphire_free`. Coordinates use `U = 10^-11 m^3 kg^-1 s^-2`; covariance uses `U^2`. Copper/sapphire describe source-mass configurations, not suspension-fibre materials. Servo/free mean electrostatic-servo/free-deflection [S3].

Keep `V_ij = rho_ij (x_i s_i/10^6)(x_j s_j/10^6)` fixed at the inherited midpoint summary across every display-cell calculation. This work propagates central-value display ambiguity only, not rounding uncertainty in V.

The new numerical scientific consumer depends directly on PR #47, not on BIPM's aggregate or PR #48's cross-campaign conclusion. PR #48 motivates the question and supplies the retained baseline comparison [S2]. Any verification-only read of its NIST result must be declared separately from production numerical inputs.

Do not consume Table 19, CODATA, terminal consensus values, dark-uncertainty priors/posteriors, or HUST authorization artifacts. E-001 remains outside the intended scientific dependency boundary. Preserve the earlier Bayesian NO_GO/NOT_AUTHORIZED dispositions.

## 3. Frozen contrast geometry and model inventory

For `x = (x_CS, x_CF, x_SS, x_SF)^T`, define three rows:

```text
r_material    = ( 1/2,  1/2, -1/2, -1/2)
r_method      = (-1/2,  1/2, -1/2,  1/2)
r_interaction = (-1,    1,    1,   -1  )
```

The first contrast is the copper-minus-sapphire difference averaged over methods. The second is the free-minus-servo difference averaged over materials. The third is the copper method gap minus the sapphire method gap: a difference of differences. Freeze these signs, scales, names, and order.

Let L stack the three rows. Report `d = Lx`, the complete covariance `S = LVL^T`, and exact linear display enclosures. Each row sums to zero and L has rank three. The contrasts are not generally statistically independent: retain every off-diagonal entry of S. Do not sum their marginal standardized squares or assign unique percentages of Q to them.

Use the following complete inventory; do not add or select alternatives after seeing their outputs.

| Model | Allowed mean pattern | Rows of R required to have zero mean | Residual degrees of freedom |
|---|---|---|---:|
| M0, baseline | One common mean | material, method, interaction | 3 |
| M_method | Common mean plus a free/servo offset identical in G units across materials | material, interaction | 2 |
| M_material | Common mean plus a copper/sapphire offset identical in G units across methods | method, interaction | 2 |
| M_additive | Common mean plus both additive offsets, with no interaction | interaction | 1 |

For each row set R, calculate exactly:

```text
y_R = R x
C_R = R V R^T
Q_R = y_R^T C_R^-1 y_R
A_R = R^T C_R^-1 R
```

This equals the minimized generalized least-squares residual statistic for the corresponding allowed mean subspace. Check that identity against an independent GLS formulation. Use the *marginal* covariance of the retained constrained contrasts, not a conditional/Schur-complement covariance that mistakenly treats fitted nuisance contrasts as known observations.

Whitening by the fixed positive-definite covariance gives a projection with rank equal to the table's residual degrees of freedom. Under the separately declared Gaussian null, Q_R therefore has that chi-square reference distribution. The fixed-known-covariance assumption is a working summary model, not a guarantee about the actual uncertainty-budget estimation process.

Use exact operational cutoffs: `7.814728` for 3 df, `5.991465` for 2 df, and `3.841459` for 1 df. Equality is not flagged. Before freeze, record a data-free check of the new 2-df cutoff against `2 ln(20)`, the exact 95th percentile. The 1/3-df policies inherit the prior upward-rounded conventions. These are separate nominal 5% diagnostics; claim no joint/familywise error rate, independent confirmation, or model-selection guarantee.

A fully saturated four-parameter mean model has zero residual degrees of freedom. Include it only as a synthetic/control identity with `NOT_TESTABLE_ZERO_RESIDUAL_DF`; exact fit is not evidence for its scientific adequacy. Likewise, a smaller raw Q in a model with extra fitted parameters is not by itself a meaningful improvement claim.

## 4. Display sensitivity and structural interpretation

For each A_R and half-width vector h, use exact rational arithmetic to certify:

```text
Q = x^T A_R x
B = 2 sum_i h_i |(A_R x)_i|
E = sum_ij h_i h_j |(A_R)_ij|
Q_low  = max(0, Q - B)
Q_high = Q + B + E
```

These are conservative outer bounds, not necessarily attained extrema. The fitted nuisance parameters may move with x; V and R remain fixed.

Classify `FLAGGED_FOR_ALL_DISPLAY_VALUES` only when the certified lower bound exceeds the cutoff. Classify `NOT_FLAGGED_FOR_ALL_DISPLAY_VALUES` only when the upper bound is at most the cutoff. Otherwise return `UNRESOLVED_FROM_CERTIFIED_BOUNDS`; straddling conservative bounds alone do not establish attainable outcomes on both sides. Give the exact midpoint classification separately. Computational or contract failures are errors, not non-rejections.

Also certify, algebraically and with synthetic checks, that `L 1 = 0` implies invariance under `x -> x + a 1` and `V -> V + t 11^T` for `t >= 0`. An identical additive shift in all four G coordinates, or extra uncertainty having exactly that common loading, cannot remove disagreement in their contrasts. This does not rule out shared apparatus systematics with unequal configuration sensitivities, multiplicative changes, or time-varying effects.

Material and method are configuration labels, not randomized causal interventions. In particular, an equal offset in G units is not the same physical model as an equal parasitic torque when gravitational sensitivities differ. Do not convert the candidate-model verdicts into claims of composition-dependent gravity or a specific instrumental bias. A torque-domain extension requires a separate source-supported mapping through the published configuration aggregation; preliminary torque entries alone do not automatically authorize that mapping [S3].

## 5. Bounded implementation surfaces and sequence

Add only the following new surfaces, plus exactly two read-only guard entries in `.github/workflows/verify.yml`:

```text
Discovery/nist_2026_configuration_models.py
Discovery/nist_2026_configuration_models_mutations.py
tests/test_nist_2026_configuration_models.py
tests/test_nist_2026_configuration_models_mutations.py
Experiments/GMeasurements/nist_2026_configuration_models_preregistration_v1.json
Experiments/GMeasurements/nist_2026_configuration_models_source_attestation_v1.json
Experiments/GMeasurements/nist_2026_configuration_models_v1.json
Experiments/GMeasurements/nist_2026_configuration_models_mutations_v1.json
Notes/NIST2026ConfigurationModelsSpecification.md
Notes/NIST2026ConfigurationModels.md
Notes/NIST2026ConfigurationModelsMutationValidation.md
```

Reuse suitable existing exact-linear-algebra and history helpers without unrelated refactoring. No Lean source or shared scientific-engine change is intended.

Before the sole-file freeze, finish the source-field projection, model/contrast/cutoff inventory, claim limits, serialization policy, and relevant audit routing. Then publish the sole-file freeze, open the draft PR, and record its GitHub-controlled creation timestamp. Only afterward implement and emit the new model results. Commit the result-driving source snapshot before artifact emission. Freeze every verdict-determining choice directly; do not leave it only in a later module constant or attestation.

The planning review on September 9 obtained and visually inspected rendered NIST PDF pages at zero-based indices 25 and 26 (printed pages 25 and 26), including Tables 16 and 18. Their displayed values and covariance entries match the existing projection. This is a new GPT source check, not Claude's audit, not retrospective proof of earlier screenshot access, and not a raw-PDF custody/hash attestation. Preserve all older freeze/correction records unchanged.

## 6. Focused tests and adversarial requirements

Use exact independent GLS/cofactor oracles rather than validating production results only against their own serialization. Cover row rank and nullspaces; positive definiteness; covariance propagation; unit scaling; label-preserving permutations; sign/scale conventions; the M0 residual identity; and nonincreasing residual Q under the specified nested enlargements. These are mathematical controls, not independent empirical findings.

Synthetic cases must distinguish common shifts, pure method effects, pure material effects, and interactions. Include unequal/correlated covariance examples that fail when off-diagonals are dropped or conditional covariance is substituted. Exercise threshold equality, both all-display classes, conservative-bound unresolved cases, signed linear enclosures, and the zero-df saturated non-test. Box-corner examples alone must not be treated as proof of the global quadratic lower bound.

Instrument actual production file/Git-read closure. Independently test numerical invariance to excluded terminal/dark-uncertainty fields where valid input containers permit it; whole-file digest rejection alone is insufficient. Test consumption of frozen contrasts, constraints, df, cutoffs, and decision policy.

The bounded mutation family must challenge contrast/order corruption, dropped covariance, mistaken conditional covariance, wrong rank/df policy, forbidden-input conditioning, false saturated acceptance, and unsound display classification. Include a surviving baseline, killed faulty control, surviving equivalent control, and assertion-specific kill credit. Run this family because a new statistical claim boundary is being implemented, not as a rerun of historical mutation families.

## 7. Acceptance, merge, and independent review

Accept the implementation only when all four declared models produce exact, reproducible midpoint outputs and sound display classifications; full covariance and nuisance fitting agree with the independent oracle; common-mode and zero-df limitations are enforced; the upstream experimental covariance remains unchanged; and no causal, Bayesian-reproduction, or independent-evidence claim appears.

Apply the standing final-tree validation protocol once at the final implementation epoch: focused tests, one complete Python-suite pass, relevant new artifact/mutation guards, and `git diff --check`. Unchanged Lean/proof surfaces may rely on exact-head protected CI. Do not rerun passed prior-epoch checks merely to plan this work or maintain the handoff.

Use a **true merge commit, never squash or rebase**. Record the new head, CI run, actual merge, and precise dependency qualification in the existing rolling handoff. Known in-scope blockers remain stop conditions; independent review timing follows Miguel's accepted temporary workflow. No new deferred-maintenance ID is assigned by this specification.

Claude's eventual semantic review should focus on: whether the restricted mean subspaces match the labels; correct nuisance profiling and residual rank; retention of contrast correlations; sound conservative display classification; separation of equal-G and equal-torque hypotheses; and the limits imposed by four already-seen summaries. Review PR #47 first. Treat PR #48's baseline relationship as shared-data context, not additional empirical evidence.

## 8. Source and provenance pointers

[S1] Repository at the intended base: `Experiments/GMeasurements/nist_2026_n4_experimental_estimator_v1.json`; NIST feasibility/source records from PR #46. PR #47 validated head: `621f5ddc938bc62273eac42004e56d940ef376fa`; actual merge: `4e8acdebc5b03d03d5039c24a73bcc37e44711e2`.

[S2] `Notes/BIPMNISTCommonConstantDiagnostic.md` and corresponding exact artifact at PR #48 head `f3efeedb5b34bb051ce0c10d60dd14c1b8b8a87a`; merged by `61b7b2a0b0136b4859c52a56a8ab8a501284f244`. Retained Verify #293: run `34306824244`. `gpt_RollingAuditHandoff.md` and `claude_Current.md` supply review status, not scientific numerical authority.

[S3] Schlamminger et al., *Metrologia* 63 (2026) 025012, DOI `10.1088/1681-7575/ae570f`, NIST-hosted primary PDF: `https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075`. Section 4.4 identifies sapphire source masses; printed p.25 discusses configuration aggregation, Table 16 and method offsets; printed p.26 contains Tables 17/18 and the unresolved-offset discussion. Accessed September 9, 2026. This source motivates configuration labels and limitations; it does not supply or endorse the project's proposed restricted-mean tests.
