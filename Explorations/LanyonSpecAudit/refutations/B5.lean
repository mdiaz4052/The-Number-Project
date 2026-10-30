open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- At f = 2 the declared flux f³/3 has derivative 4 but the declared Jacobian is 2. -/
theorem refute_B5 : ¬ JacobianIsDerivative := by
  intro h
  have h1 := h ⟨0⟩ ⟨⟩ ⟨2⟩
  have hf : (fun s : ℝ => (xFluxExprs ⟨0⟩ ⟨⟩ ⟨s⟩).flux_f) = fun s => (1 / 3 : ℝ) * s * s * s := rfl
  have h2 : HasDerivAt (fun s : ℝ => (xFluxExprs ⟨0⟩ ⟨⟩ ⟨s⟩).flux_f) 4 2 := by
    rw [hf]
    exact ((((hasDerivAt_id (2 : ℝ)).const_mul (1 / 3 : ℝ)).mul (hasDerivAt_id (2 : ℝ))).mul
      (hasDerivAt_id (2 : ℝ))).congr_deriv (by simp only [id]; norm_num)
  have := h1.unique h2
  set_option simprocs false in
    simp only [jac, Matrix.of_apply, xFluxJacobianExprs, zero_lit] at this
  norm_num at this
