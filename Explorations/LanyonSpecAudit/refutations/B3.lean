open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f = 2 the flux f²/2 has derivative 2 but the declared Jacobian is 4. -/
theorem refute_B3 : ¬ JacobianIsDerivative := by
  intro h
  have h1 := h ⟨0⟩ ⟨⟩ ⟨2⟩
  have hf : (fun s : ℝ => (xFluxExprs ⟨0⟩ ⟨⟩ ⟨s⟩).flux_f) = fun s => (1 / 2 : ℝ) * s * s := rfl
  have h2 : HasDerivAt (fun s : ℝ => (xFluxExprs ⟨0⟩ ⟨⟩ ⟨s⟩).flux_f) 2 2 := by
    rw [hf]
    exact (((hasDerivAt_id (2 : ℝ)).const_mul (1 / 2 : ℝ)).mul (hasDerivAt_id (2 : ℝ))).congr_deriv
      (by simp only [id]; norm_num)
  have := h1.unique h2
  set_option simprocs false in
    simp only [jac, Matrix.of_apply, xFluxJacobianExprs] at this
  norm_num at this
