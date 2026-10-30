open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- At c = 1 the halved dissipation speed 1/2 is below |lambda3| = 1. -/
theorem refute_M5 : ¬ DissipationBound := by
  intro h
  have := (h ⟨0⟩ ⟨0⟩ ⟨0, 0, 0, 0, 0, 0⟩ ⟨0, 0, 0, 0, 0, 0⟩ ⟨1⟩ 2).1
  set_option simprocs false in
    simp only [eig, xFluxJacobianEigenExprs, xSpeedFamilyExprs, zero_lit] at this
  try simp at this
  all_goals norm_num at this
