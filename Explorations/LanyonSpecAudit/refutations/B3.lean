open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f = 2 the flux f²/2 has derivative 2 but the declared Jacobian is 4. -/
theorem refute_B3 : ¬ JacobianIsDerivative := by
  intro h
  have h1 := h ⟨0⟩ ⟨⟩ ⟨2⟩
  have h2 : HasDerivAt (fun s : ℝ => (xFluxExprs ⟨0⟩ ⟨⟩ ⟨s⟩).flux_f) 2 2 := by
    have := ((hasDerivAt_id (2 : ℝ)).const_mul (1 / 2 : ℝ)).mul (hasDerivAt_id (2 : ℝ))
    simp only [xFluxExprs, id] at this ⊢
    convert this using 1
    norm_num
  have := h1.unique h2
  simp [jac, xFluxJacobianExprs] at this
  norm_num at this
