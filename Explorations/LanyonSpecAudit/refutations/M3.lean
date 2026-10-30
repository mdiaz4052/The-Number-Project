open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- The sign-flipped system has J² with trace 0 at c = 1 (eigenvalues ±i), while the
declared real eigenvalues give Σ λ² = 4. -/
theorem refute_M3 : ¬ RealEigenbasis := by
  intro h
  obtain ⟨R, L, hLR, hJ⟩ := h ⟨0⟩ ⟨1⟩ ⟨0, 0, 0, 0, 0, 0⟩ one_pos
  have := trace_sq_eq_of_eigenbasis hLR hJ
  simp [jac, eig, gradVec, xFluxJacobianExprs, xFluxJacobianEigenExprs, Matrix.trace,
    Matrix.mul_apply, Fin.sum_univ_succ] at this
  norm_num at this
