open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- At c = 1 the declared Jacobian has trace 0 but the declared eigenvalues sum to -4. -/
theorem refute_M1 : ¬ RealEigenbasis := by
  intro h
  obtain ⟨R, L, hLR, hRL, hJ⟩ := h ⟨0⟩ ⟨1⟩ ⟨0, 0, 0, 0, 0, 0⟩ one_pos
  have := trace_eq_of_eigenbasis hLR hRL hJ
  set_option simprocs false in
    simp only [jac, eig, gradVec, xFluxJacobianExprs, xFluxJacobianEigenExprs, Matrix.trace,
    Fin.sum_univ_succ, zero_lit] at this
  try simp at this
  all_goals norm_num at this
