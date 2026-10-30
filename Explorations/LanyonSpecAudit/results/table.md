| id | family | mutation | predicted L / L+S | observed L / L+S | failing theorems | refuted | re-proved |
|---|---|---|---|---|---|---|---|
| B0 | curated | unmutated control | pass / pass | pass / pass | - | - | - |
| B1 | curated | eigenvalue halved: lambda1 := f/2 | pass / fail | fail / fail | xWaveStability, dissipationBound, realEigenbasis | refute_B1 | reprove_B1_xWaveStability, reprove_B1_dissipationBound |
| B2 | curated | eigenvalue sign-flipped: lambda1 := -f | pass / fail | pass / fail | realEigenbasis | refute_B2 | - |
| B3 | curated | Jacobian wrong: d_f := f*f (eigenvalue left as f) | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | refute_B3 | - |
| B4 | curated | flux changed to f^3/3 in the flux only (waves still use f^2/2) | fail / fail | fail / fail | xFluxConservative, jacobianIsDerivative | refute_B4 | - |
| B5 | curated | different PDE: flux f^3/3 in flux and Lax-Friedrichs waves; Jacobian, eigenvalue, wave speed left for f^2/2 | pass / fail | pass / fail | jacobianIsDerivative | refute_B5 | - |
| B6 | curated | wave-speed estimate halved: mu1 := f/2 | fail / fail | fail / fail | xWaveStability | refute_B6 | - |
| B7 | curated | Lax-Friedrichs dissipation speed halved consistently in waves, speeds and hypotheses | pass / fail | fail / fail | xFluxConservative, dissipationBound | refute_B7 | reprove_B7_xFluxConservative |
| M0 | curated | unmutated control | pass / pass | pass / pass | - | - | - |
| M1 | curated | eigenvalues lambda3, lambda4 := -c (spectrum all -c, -c, -c, -c, 0, 0) | pass / fail | pass / fail | realEigenbasis | refute_M1 | - |
| M2 | curated | Jacobian entry dFlux_Ey/dBz := c instead of c^2 | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | refute_M2 | - |
| M3 | curated | non-hyperbolic system: flux_Ey sign flipped consistently in flux, waves and Jacobian (spectrum becomes +-ic); listed eigenvalues unchanged | pass / fail | pass / fail | realEigenbasis | refute_M3 | - |
| M4 | curated | zero eigenvalue moved: lambda5 := c | fail / fail | fail / fail | xWaveStability, realEigenbasis | refute_M4 | - |
| M5 | curated | Lax-Friedrichs dissipation speed halved consistently in waves, speeds and hypotheses | pass / fail | fail / fail | xFluxConservative, dissipationBound | refute_M5 | reprove_M5_xFluxConservative |
| BS01 | systematic-flux | sign flip of xFluxExprs.flux_f | fail / fail | fail / fail | xFluxConservative, jacobianIsDerivative | - | - |
| BS02 | systematic-jacobian | sign flip of xFluxJacobianExprs.flux_f.d_f | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | - | - |
| BS03 | systematic-eigenvalue | sign flip of xFluxJacobianEigenExprs.lambda1 | pass / fail | pass / fail | realEigenbasis | - | - |
| BS04 | systematic-wavespeed | sign flip of xWaveSpeedExprs.mu1 | pass / pass | pass / pass | - | - | - |
| MS01 | systematic-flux | sign flip of xFluxExprs.flux_Ey | fail / fail | fail / fail | xFluxConservative, jacobianIsDerivative | - | - |
| MS02 | systematic-flux | sign flip of xFluxExprs.flux_Ez | fail / fail | fail / fail | xFluxConservative, jacobianIsDerivative | - | - |
| MS03 | systematic-flux | sign flip of xFluxExprs.flux_By | fail / fail | fail / fail | xFluxConservative, jacobianIsDerivative | - | - |
| MS04 | systematic-flux | sign flip of xFluxExprs.flux_Bz | fail / fail | fail / fail | xFluxConservative, jacobianIsDerivative | - | - |
| MS05 | systematic-jacobian | sign flip of xFluxJacobianExprs.flux_Ey.d_Bz | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | - | - |
| MS06 | systematic-jacobian | sign flip of xFluxJacobianExprs.flux_Ez.d_By | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | - | - |
| MS07 | systematic-jacobian | sign flip of xFluxJacobianExprs.flux_By.d_Ez | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | - | - |
| MS08 | systematic-jacobian | sign flip of xFluxJacobianExprs.flux_Bz.d_Ey | pass / fail | pass / fail | jacobianIsDerivative, realEigenbasis | - | - |
| MS09 | systematic-eigenvalue | sign flip of xFluxJacobianEigenExprs.lambda1 | pass / fail | pass / fail | realEigenbasis | - | - |
| MS10 | systematic-eigenvalue | sign flip of xFluxJacobianEigenExprs.lambda2 | pass / fail | pass / fail | realEigenbasis | - | - |
| MS11 | systematic-eigenvalue | sign flip of xFluxJacobianEigenExprs.lambda3 | pass / fail | pass / fail | realEigenbasis | - | - |
| MS12 | systematic-eigenvalue | sign flip of xFluxJacobianEigenExprs.lambda4 | pass / fail | pass / fail | realEigenbasis | - | - |
| MS13 | systematic-wavespeed | sign flip of xWaveSpeedExprs.mu1 | pass / pass | pass / pass | - | - | - |
| MS14 | systematic-wavespeed | sign flip of xWaveSpeedExprs.mu2 | pass / pass | pass / pass | - | - | - |
| MS15 | systematic-wavespeed | sign flip of xWaveSpeedExprs.mu3 | pass / pass | pass / pass | - | - | - |
| MS16 | systematic-wavespeed | sign flip of xWaveSpeedExprs.mu4 | pass / pass | pass / pass | - | - | - |
