open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f = 2 the declared flux f³/3 has derivative 4 but the declared Jacobian is 2. -/
theorem refute_B5 : ¬ JacobianIsDerivative := by
  intro h
  have h1 := h ⟨0⟩ ⟨⟩ ⟨2⟩
  have h2 : HasDerivAt (fun s : ℝ => (xFluxExprs ⟨0⟩ ⟨⟩ ⟨s⟩).flux_f) 4 2 := by
    have := (((hasDerivAt_id (2 : ℝ)).const_mul (1 / 3 : ℝ)).mul
      (hasDerivAt_id (2 : ℝ))).mul (hasDerivAt_id (2 : ℝ))
    simp only [xFluxExprs, id] at this ⊢
    convert this using 1
    norm_num
  have := h1.unique h2
  simp [jac, xFluxJacobianExprs] at this
  norm_num at this
