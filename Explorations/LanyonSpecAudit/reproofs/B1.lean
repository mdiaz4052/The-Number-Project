open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- Lanyon's xWaveStability statement is true for B1 (|f| ≥ |f/2|); its proof script fails. -/
theorem reprove_B1_xWaveStability (C : Coordinates) (P : Parameters) (U : State) :
    ((abs (xWaveSpeedExprs C P U).mu1) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda1)) := by
  simp only [xWaveSpeedExprs, xFluxJacobianEigenExprs, abs_mul]
  have := abs_nonneg U.f
  norm_num
  linarith

/-- S3 is also true for B1; only its proof script fails. -/
theorem reprove_B1_dissipationBound : DissipationBound := by
  intro CL CR UL UR P i
  simp only [eig, xFluxJacobianEigenExprs, xSpeedFamilyExprs, abs_mul]
  have a := abs_nonneg UL.f
  have b := abs_nonneg UR.f
  norm_num
  constructor
  · exact le_trans (by linarith) (le_max_left |UL.f| |UR.f|)
  · exact le_trans (by linarith) (le_max_right |UL.f| |UR.f|)
