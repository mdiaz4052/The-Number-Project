# NIST 2026 estimator feasibility result

## Scope

This note records a source/estimator **feasibility audit**, not a BIPM-14 versus NIST-26 comparison and not a reproduction of the paper's final Bayesian consensus.

The controlling source is Stephan Schlamminger et al., *Redetermination of the gravitational constant with the BIPM torsion balance at NIST*, Metrologia 63 (2026) 025012, DOI `10.1088/1681-7575/ae570f`.

The preregistration was deliberately not outcome-blind: the final NIST result, its discrepancy with BIPM-14, and the existence of the dark-uncertainty hierarchy were known before the freeze. The protected question is which reconstruction layers are actually authorized by the published source.

## A. Four-configuration experimental covariance — GO

The paper publishes four determinations of G in Table 16 and a complete four-dimensional correlation summary in Table 18.

Fixed input order:

1. copper-servo;
2. copper-free;
3. sapphire-servo;
4. sapphire-free.

Table 18 gives the more precise standard uncertainties

`(23.2, 30.3, 37.5, 93.9) ppm`

and all six pairwise correlations. The exact relative covariance rule is

`C_ij = rho_ij sigma_i sigma_j`.

The resulting matrix is symmetric and its exact leading principal minors are

- `13456/25`;
- `158978208771/390625`;
- `121558568110209/250000`;
- `4846543822981430177733/1250000000`.

All are positive. Therefore the source uniquely determines a positive-definite `4 x 4` experimental covariance object suitable for a later preregistered correlated-estimator certificate.

This GO requires no NIST final consensus value, CODATA value, BIPM-14 value, dark uncertainty, or common-constant assumption.

## B. Published Bayesian consensus, equation (64) — NO-GO for exact deterministic reproduction from the primary paper alone

The paper gives substantial model structure: equation (63), a Gaussian prior for the consensus `mu`, half-Cauchy priors for configuration-specific dark uncertainties, a multivariate-normal configuration-effect model, and Huber's M / Qn posterior summaries.

However, the primary paper does not uniquely specify every result-driving statistical/computational choice needed for a byte-deterministic reconstruction of equation (64). The audit records five explicit blockers:

1. the likelihood/distribution of the measurement-error term `epsilon_j` is not explicitly stated in the consensus-model section;
2. the paper-specific posterior sampler or integration algorithm is not specified;
3. sample count, seed, warmup/burn-in, thinning/chains, and convergence controls are not specified;
4. all implementation/tuning conventions for Huber's M and Qn on the posterior samples are not stated;
5. the `R` used in the dark-uncertainty covariance is contextually associated with the experimental correlations but is not explicitly identified as Table 18 in the equation paragraph.

The project therefore must not choose conventional defaults and then label the result a reproduction of equation (64). A generalized least-squares combination of Tables 16/18 would likewise be a different estimator, not the published consensus estimator.

## Source-authority discrepancy

The current NIST landing page displays a numerical final result different from the peer-reviewed article PDF. The journal PDF is treated as the controlling scientific source; landing-page numerical values are retained only as a provenance warning and are not reconciled or used in any feasibility decision.

Table 16 also displays whole-ppm uncertainties, whereas Table 18 supplies more precise diagonal uncertainty values. Table 18 controls covariance construction; the Table 16 values remain source-recorded rounded displays.

## Authorized next scientific step

The frozen decision rule for the observed `GO / NO-GO` split authorizes a new preregistered **NIST 2026 n=4 experimental covariance/correlated-estimator certificate** based only on the four published determinations and their experimental covariance object.

That later certificate must explicitly state that it does not reproduce equation (64). A BIPM-14 versus NIST-26 common-constant comparison remains a separate later experiment requiring its own preregistered cross-measurement model and evidence boundary.
