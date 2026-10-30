open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f = 1 the declared Jacobian is 1 but the declared eigenvalue is -1. -/
theorem refute_B2 : ¬ RealEigenbasis := by
  intro h
  obtain ⟨R, L, hLR, hRL, hJ⟩ := h ⟨0⟩ ⟨⟩ ⟨1⟩
  have := trace_eq_of_eigenbasis hLR hRL hJ
  set_option simprocs false in
    simp only [jac, eig, xFluxJacobianExprs, xFluxJacobianEigenExprs, Matrix.trace, zero_lit] at this
  try simp at this
  all_goals norm_num at this
