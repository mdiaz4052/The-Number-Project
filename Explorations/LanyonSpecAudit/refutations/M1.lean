open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- At c = 1 the declared Jacobian has trace 0 but the declared eigenvalues sum to -4. -/
theorem refute_M1 : ¬ RealEigenbasis := by
  intro h
  obtain ⟨R, L, hLR, hJ⟩ := h ⟨0⟩ ⟨1⟩ ⟨0, 0, 0, 0, 0, 0⟩ one_pos
  have := trace_eq_of_eigenbasis hLR hJ
  simp [jac, eig, gradVec, xFluxJacobianExprs, xFluxJacobianEigenExprs, Matrix.trace,
    Fin.sum_univ_succ] at this
  norm_num at this
