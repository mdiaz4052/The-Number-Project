# NIST 2026 Estimator Feasibility — Bounded Specification

## Objective

Audit the reconstructability of the 2026 NIST redetermination of the gravitational constant using the BIPM torsion balance, DOI `10.1088/1681-7575/ae570f`.

The PR answers two separate questions and must not conflate them:

1. **Experimental covariance layer:** do the four published determinations and Table 18 uncertainty/correlation summary uniquely determine a valid four-dimensional experimental covariance object suitable for deterministic correlated-estimator work?
2. **Published consensus layer:** does the paper specify a unique deterministic procedure sufficient to reproduce the Bayesian hierarchical consensus in equation (64), including its uncertainty, without inventing unstated statistical or computational choices?

This PR does **not** compare NIST-26 numerically with BIPM-14 and does not claim a common-constant verdict.

## Intended base and chronology

Base: `151b9c920cadb90a9fd02766cc8def7ba9348f61`, the true merge of PR #44.

Valid freeze: `a4451482ab211df4f5c9ede0e339db9ca25a97cd`.

Draft PR #46 is the external anchor. The freeze must remain the first branch commit, with the base as sole parent and only the preregistration added. Implementation must postdate that GitHub anchor.

Draft PR #45 is explicitly abandoned historical evidence: its frozen preregistration contained malformed JSON and failed closed before scientific calculation. No scientific verdict or result artifact from PR #45 is accepted, and its frozen bytes were not amended. PR #46 restarts from merged main with a valid freeze.

## Source authority

The controlling numerical/scientific source is the journal article PDF available from NIST's local-download endpoint and identified by the DOI above. The NIST landing page is bibliographic/availability evidence only because its displayed abstract contains numerical values that disagree with the published article PDF.

The source PDF is open access under CC BY 4.0. Raw PDF bytes are not committed in this PR; the attestation records the stable NIST URL, page count, access date, exact table/equation locators, and a reviewed transcription.

## Experimental covariance layer

Input order is fixed as:

1. copper-servo;
2. copper-free;
3. sapphire-servo;
4. sapphire-free.

Table 16 supplies the four central values. Table 18 is the controlling source for covariance geometry because its diagonal entries provide the more precise relative standard uncertainties `23.2, 30.3, 37.5, 93.9` ppm and its six off-diagonal entries provide the correlation coefficients.

The relative covariance matrix is

`C_ij = rho_ij * sigma_i * sigma_j`

in ppm², with exact decimal-to-rational parsing. Feasibility requires symmetry, unit correlation diagonal, all declared standard uncertainties positive, and positive definiteness of the resulting covariance matrix. The audit reports exact leading principal minors.

No BIPM value, CODATA value, NIST equation (64), dark uncertainty, or terminal comparison may enter this construction.

## Bayesian consensus layer

The audit inventories what the paper explicitly specifies for equation (63):

- `G_j = mu + lambda_j + epsilon_j`;
- `lambda ~ N(0, Sigma)` and `Sigma_ij = tau_i tau_j R_ij`;
- Gaussian prior center and standard deviation for `mu`;
- independent half-Cauchy prior family for the four `tau_j` with ranked median scales;
- Huber's M and `Qn` as posterior-sample summaries;
- Table 19 posterior summaries and equation (64) final result.

A deterministic GO requires a unique result-driving likelihood and a uniquely specified posterior-computation/summary procedure. Missing sampler size, seed, burn-in/thinning/convergence choices, an unstated likelihood distribution for `epsilon_j`, or any other materially result-driving ambiguity produces **NO-GO** rather than an assumed convention.

The audit must not substitute a generalized least-squares estimate for the Bayesian consensus and call it a reproduction of equation (64).

## Source discrepancy handling

Record, but do not numerically reconcile, the discrepancy between the NIST landing-page abstract and the journal PDF. The peer-reviewed article PDF controls the scientific transcription.

Also distinguish Table 16's rounded whole-ppm uncertainty display from Table 18's more precise diagonal values. Table 18 controls covariance construction.

## Outputs

New files:

- `Experiments/GMeasurements/nist_2026_estimator_feasibility_preregistration_v1.json`
- `Experiments/GMeasurements/nist_2026_estimator_source_attestation_v1.json`
- `Discovery/nist_2026_estimator_feasibility.py`
- `tests/test_nist_2026_estimator_feasibility.py`
- `Experiments/GMeasurements/nist_2026_estimator_feasibility_v1.json`
- `Notes/NIST2026EstimatorFeasibility.md`
- this specification.

Modify only `.github/workflows/verify.yml` to add one read-only `--check` guard.

## Focused tests

Tests must pin:

- exact source projection and input order;
- Table 18 precision dominance over rounded Table 16 uncertainty labels;
- exact symmetric relative covariance matrix;
- exact positive principal minors;
- central/terminal/CODATA/BIPM independence of experimental covariance feasibility;
- explicit Bayesian specified/missing inventory;
- fail-closed NO-GO when a required deterministic consensus ingredient is missing;
- source-authority resolution of the landing-page/PDF numerical conflict;
- preregistration chronology, source snapshot freshness, and E-001 isolation;
- committed artifact byte rebuild.

## Acceptance

Run focused tests, one complete Python suite, the new guard, relevant existing guards through exact-head CI, and `git diff --check`. No Lean-linked source changes are planned. Merge must use a true merge commit.
