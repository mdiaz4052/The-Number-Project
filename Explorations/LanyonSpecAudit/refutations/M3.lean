open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- The sign-flipped system has J² with trace 0 at c = 1 (eigenvalues ±i), while the
declared real eigenvalues give Σ λ² = 4. -/
theorem refute_M3 : ¬ RealEigenbasis := by
  intro h
  obtain ⟨R, L, hLR, hRL, hJ⟩ := h ⟨0⟩ ⟨1⟩ ⟨0, 0, 0, 0, 0, 0⟩ one_pos
  have := trace_sq_eq_of_eigenbasis hLR hRL hJ
  set_option simprocs false in
    simp only [jac, eig, gradVec, xFluxJacobianExprs, xFluxJacobianEigenExprs, Matrix.trace,
    Matrix.mul_apply, Fin.sum_univ_succ, zero_lit] at this
  try simp at this
  all_goals norm_num at this
