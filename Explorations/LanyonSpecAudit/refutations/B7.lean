open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f_L = f_R = 1 the halved dissipation speed 1/2 is below the eigenvalue 1. -/
theorem refute_B7 : ¬ DissipationBound := by
  intro h
  have := (h ⟨0⟩ ⟨0⟩ ⟨1⟩ ⟨1⟩ ⟨⟩ 0).1
  simp [eig, xFluxJacobianEigenExprs, xSpeedFamilyExprs] at this
  norm_num at this
