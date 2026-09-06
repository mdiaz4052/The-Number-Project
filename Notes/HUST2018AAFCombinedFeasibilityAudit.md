# HUST 2018 AAF combined-estimator feasibility audit

**Decision: GO for feasibility from the pinned, rounded published inputs.**
The source provides the component inventory, correlation model and combination
prescription. No combined MeasurementModel is created or authorized here. A later
PR must separately preregister its contract after independent audit of this result.

## Preregistration and chronology

Baseline main: `86479a55dfdc0c631845910ce92679c152c9f0af`.

The question, allowed artifact identities, forbidden inputs, evidence requirements,
decision rule and numerical policy were frozen before source combination review in
local commit `607143cb15528f19b670d66910833ce79d7982b9`.
Direct Git push lacked credentials. The identical preregistration-only tree was
therefore published through the GitHub connector as
`9c5a30361af60bfc9831da6c5c6bb867727b1b70`, before any covariance or combination
arithmetic. Source Section 6 was initially inspected between those two events.
This is not a claim of a remote timestamp before that initial source inspection.

The preregistration bytes have SHA-256
`14cda7a63b8f5ad2c40455300465a3c5b169e14f4ac7390742a172db30ba750a`.
The generated artifact retains the complete original local commit object; its Git
object ID and identical tree are verified. This preserves the local freeze's
inspectable contents, without claiming externally attested local chronology.
The implementation descends from the published preregistration commit. Current
bytes, its baseline parent and intervening edit/restore history are checked.

## Source evidence and interpretation

Publication: Q. Li et al., [Nature 560, 582-588 (2018)](https://www.nature.com/articles/s41586-018-0431-5),
DOI `10.1038/s41586-018-0431-5`.
The official supplementary PDF was recovered again and matched the pre-existing
2,711,453-byte SHA-256 pin
`5b61d5c831be98c46e47fcc32f1ade0a680b4af6354d2bc34859d94b22279ffb`.
Printed pages 12-13 are PDF pages 13-14 because of the publisher cover.
The equations were inspected visually, alongside text extraction.

| Required evidence | Source and disposition |
| --- | --- |
| Three individual determinations | Supplementary Table 3, printed p. 20; Section 6 AAF paragraph, printed p. 13; reuse the pinned individual reconstructions. |
| Component inventory and units | Official Nature Table 1, p. 584, 21 applicable AAF rows per run; reuse the existing depth-2b authorization. |
| Statistical classification | Section 6, p. 13, AAF paragraph: angular-acceleration statistical uncertainty is independent across runs. |
| Cross-run covariance | The same paragraph treats each shared non-statistical item as fully correlated; the preceding simplified uncertainty equation sums itemwise squares. |
| Estimator and normalization | Section 6, p. 12 explicitly normalizes inverse total variances twice, first for two runs and then for four fibre determinations. The final AAF sentence on p. 13 incorporates that same method for three runs. |
| Singular-matrix procedure | No matrix inverse appears in these source equations. All individual variances are positive; no extra prescription is needed. |
| Numerical sufficiency | The three reconstructed central values and 63 component entries supply every operand. |

The exact short excerpts and locators are recorded in the generated JSON. The
AAF paragraph's explicit backward reference is the basis for applying the
preceding equations. Translating them to three AAF runs is a mathematical
deduction; it is not a separately printed AAF formula. Both earlier weight
equations use the same inverse marginal-variance normalization, so their different
run counts leave no choice of weighting convention. TOS-specific intermediate
fibre and background terms are not imported into AAF.

Let `u_ki = abs(G_i) * ppm_ki * 1e-6`. For each non-statistical item, the off-diagonal
correlation is 1; for the statistical angular-acceleration item it is 0. The
diagonal correlation is always 1. Within this published itemwise budget,

```text
C_ij = sum_k(rho_k(i,j) * u_ki * u_kj)
p_i = (1 / C_ii) / sum_j(1 / C_jj)
G_AAF = sum_i(p_i * G_i)
u_AAF^2 = sum_nonstat_k(sum_i(p_i * u_ki)^2)
          + sum_i((p_i * u_stat_i)^2)
        = p^T C p
```

These are marginal inverse-variance weights followed by correlated propagation.
They do not use an inverse covariance matrix. The source's same-item correlation
assumption is not a claim that all physical systematic effects are independent
or completely described.

## Result

Authoritative calculations use precision-50 Decimal, with numbers serialized as
strings. The following are presentation approximations:

| Quantity | Reconstruction |
| --- | --- |
| AAF-I weight | 0.306493653370 |
| AAF-II weight | 0.315444891277 |
| AAF-III weight | 0.378061455353 |
| Combined G, m^3 kg^-1 s^-2 | 6.6744840065457963e-11 |
| Combined standard uncertainty, m^3 kg^-1 s^-2 | 7.7532046181704313e-16 |
| Relative standard uncertainty | 11.6161857764 ppm |

All seven principal minors of the serialized 3-by-3 covariance matrix are positive
under an exact rational sign check. The matrix is therefore positive definite and
invertible, although its inverse is not used. Its diagonal reproduces the three
component-derived variances. Independent RSS reconstruction preserves each
historical individual uncertainty. The componentwise and quadratic-form combined
variances differ relatively by about `1.66e-50`, below the frozen `1e-47`
arithmetic bound.

Only after reconstruction, the terminal comparison records the published
`6.674484e-11`, `7.8e-16` absolute uncertainty, and `11.61 ppm` relative uncertainty.
The central-value difference is approximately `6.55e-20`; the relative-uncertainty
difference is approximately `0.00618578 ppm`. These differences remain visible.
The nominal rounded component inputs do not reproduce every final displayed ppm
digit. No weight, coefficient or correlation is tuned to remove that difference.
The extra calculation digits do not represent extra experimental precision.
Terminal agreement has no role in GO/NO-GO or test acceptance.

## Validation and preservation

The focused module exercises 39 tests, including an independent exact-rational
calculation from the source strings, changes/deletion of terminal comparisons,
target and weight injections, all required inventory/covariance attacks, absent
or ambiguous evidence, and real disposable Git histories for ancestry and
edit/restore attacks. Existing HUST regressions were also run. The full Python
suite and permanent freshness guards run at the final implementation head;
exact-head GitHub Actions supplies the Python and Lean verification evidence.

The preregistration lists baseline hashes for every existing HUST experimental
artifact and Lean source/configuration. Every hash remains unchanged. Existing
central values, RSS uncertainties, 21-component records, source pins,
authorizations, historical v1/v2 artifacts and the PR #36 mutation v3 record are
preserved. CI receives only the new feasibility freshness command.

No existing MeasurementModel, replication status, apparatus-validation claim,
physical-bridge schema, Lean source, or milestone tag changes. This audit makes
no new measurement, physical prediction, TOS authorization, physical-independence
claim, or claim that unknown systematic effects are exhausted.

## Independent audit focus

Challenge the interpretation of Section 6's AAF backward reference, absolute
versus relative marginal variances, same-item covariance mapping, target isolation,
and the freeze/publication chronology. Reject GO if any material source choice
remains discretionary. A successful arithmetic comparison is insufficient.

Historical PR #36 assurance housekeeping remains outside this PR. No new
non-blocking maintenance defect was consciously deferred during this implementation.
Merge only after independent audit, using **Create a merge commit**; do not squash,
rebase, or create a milestone tag.
