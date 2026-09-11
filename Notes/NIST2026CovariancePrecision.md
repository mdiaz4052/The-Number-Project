# NIST published-covariance precision robustness

PROVISIONAL — INDEPENDENT AUDIT PENDING

Under the project-declared nearest-rounding enclosure and fixed displayed-midpoint normalization:

| Model | Certified outer Q bounds | Cutoff | Disposition |
|---|---|---|---|
| M0 | [23.3092233138695813479491776177, 27.0454982044081695099318300247] | 7.814728 | FLAGGED_FOR_ALL_PRECISION_VALUES |
| M_method | [16.9717917816647934130813015912, 18.5354055326872425483690443112] | 5.991465 | FLAGGED_FOR_ALL_PRECISION_VALUES |
| M_material | [5.22635514518539226371399425139, 5.71211724655526003613117861569] | 5.991465 | NOT_FLAGGED_FOR_ALL_PRECISION_VALUES |
| M_additive | [1.00306245679330490735945114084, 1.05177271549114108490388186790] | 3.841459 | NOT_FLAGGED_FOR_ALL_PRECISION_VALUES |

A robust flag means every member of this declared precision family exceeds that model’s cutoff. A robust non-flag means none exceeds it; this is not model acceptance. Variation requires two checked admissible point witnesses on opposite sides. Straddling outer bounds alone are inconclusive.

The study used 0 of 255 shared binary splits and 1 evaluated nodes. Stop reason: `all_models_resolved`. Covariance validity: `POSITIVE_DEFINITE_FULL_BOX`.

The exact JSON contains the full partition, retained frontier, exact rational proof terms and witnesses. Decimals above round outward and are readability only. Bounds need not be attained extrema.

## Certificate argument

The correlation matrix is affine in six shared off-diagonal entries. The 64 corner matrices have their exact leading principal minors recorded. If all are positive, their convex hull is positive definite. Positive diagonal D and full-row-rank R then give positive-definite V and C throughout. This corner argument certifies matrix validity, not extrema of Q.

At each covariance subbox center, exact LDL gives Cc=L diag(d) Lᵀ and T=L⁻¹. With Z=TR, entrywise interval arithmetic provides |V−Vc|≤E. Thus |Z(V−Vc)Zᵀ|≤F=|Z|E|Z|ᵀ. Writing g as F’s row sums, symmetry and 2|vᵢvⱼ|≤vᵢ²+vⱼ² give |vᵀWv|≤Σgᵢvᵢ². Hence diag(d−g)≤TCTᵀ≤diag(d+g) in matrix order. Positive-definite inversion reverses order: conjugate by a square root to reduce to eigenvalues ≥1, whose reciprocals are ≤1. The identity Q=(TRx)ᵀ(TCTᵀ)⁻¹(TRx) therefore yields the recorded Hlower/Hupper. If any d−g is nonpositive, this upper method is unavailable; the real covariance can still be positive definite.

For x=a+δ, |δᵢ|≤hᵢ, expand xᵀHx=aᵀHa+2δᵀHa+δᵀHδ. PSD makes the last term nonnegative for the lower bound. The upper bound retains both B=2Σhᵢ|(Ha)ᵢ| and E=Σhᵢhⱼ|Hᵢⱼ|. The resulting full central-box interval is [max(0,q−B),q+B+E]. Parent bounds intersect child bounds; every retained leaf remains in the full cover. Zero covariance widths reproduce the #49 display enclosure exactly.

## Meaning and provenance

The 14-parameter box simultaneously encloses printed x, s and rho at half-widths 0.0000005 U, 0.05 ppm and 0.005. It is a deterministic conditional enclosure, not extra experimental uncertainty or a probability distribution. The source caption does not establish nearest rounding. D uses immutable a, never perturbed x; other normalization rules and hidden author values are not certified. All four restrictions use full marginal RVRᵀ, profiled nuisance means and the inherited strict Q>cutoff convention; equality is not flagged.

Miguel reported reading the NIST-served PDF on September 10, 2026 at 12:04 PM, timezone unspecified. His report arrived at 16:13:05Z and image at 16:15:53Z. GPT’s image comparison separately reconciled rho03=0.12 and rho12=0.23 against the transposed typed report; the original text is retained unchanged. Claude inspected the supplied crop in the September 10 supplemental audit and accepted the earlier #49 numerical/behavior layer. That is inherited coverage, not independent review of this PR.

The new attestation maps the unchanged receipt and PNG into the repository. Image hashes bind PNG bytes only. Document identity, URL and page are attributed; the crop does not show them. Table 16 central values remain inherited from the pinned records. No original-PDF authentication, independent retrieval, new human confirmation or Claude-owned finding closure is claimed.

No new/corrected G, covariance completion, model selection, p-value, confidence interval, posterior, causal explanation or universality inference is produced. The Gaussian/known-covariance interpretation is an inherited working assumption at each candidate. Omitted physical uncertainty and the parked torque-response/campaign-uncertainty NO-GOs remain outside this result. No outreach or correspondence.

Base: `13c6b7b3bcaedda9acb1318c8a96ae39e18f538f`. Freeze: `6496188c17c82410241d2d703121aa1e9d048c6a`. Actual GitHub draft creation: `2026-09-11T19:01:42Z`. Source snapshot: `1b96f629c1f8384ffc0d641a706b5625a14ed133`. `outcome_blind=false`.

Use a true merge commit; preserve freeze, source and artifact ancestry.
