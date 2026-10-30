open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f = 1 the declared Jacobian is 1 but the declared eigenvalue is 1/2. -/
theorem refute_B1 : ¬ RealEigenbasis := by
  intro h
  obtain ⟨R, L, hLR, hJ⟩ := h ⟨0⟩ ⟨⟩ ⟨1⟩
  have := trace_eq_of_eigenbasis hLR hJ
  simp [jac, eig, xFluxJacobianExprs, xFluxJacobianEigenExprs, Matrix.trace] at this
  norm_num at this
