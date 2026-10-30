open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- At c = 2 the flux component c²·Bz has dBz-derivative 4 but the declared entry is 2. -/
theorem refute_M2 : ¬ JacobianIsDerivative := by
  intro h
  have h1 := h ⟨0⟩ ⟨2⟩ ⟨0, 0, 0, 0, 0, 0⟩ 1 5
  have h2 : HasDerivAt (fun s : ℝ => fluxVec ⟨0⟩ ⟨2⟩ (ofVec (Function.update (toVec ⟨0, 0, 0, 0, 0, 0⟩) 5 s)) 1)
      4 (toVec ⟨0, 0, 0, 0, 0, 0⟩ 5) := by
    have := (hasDerivAt_id (toVec ⟨0, 0, 0, 0, 0, 0⟩ 5)).const_mul ((2 : ℝ) * 2)
    simp only [fluxVec, ofVec, toVec, xFluxExprs, id] at this ⊢
    convert this using 1
    · funext s
      simp [Function.update_apply]
    · norm_num
  have := h1.unique h2
  simp [jac, gradVec, xFluxJacobianExprs] at this
  norm_num at this
