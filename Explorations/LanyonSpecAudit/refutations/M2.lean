open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- At c = 2 the flux component c²·Bz has dBz-derivative 4 but the declared entry is 2. -/
theorem refute_M2 : ¬ JacobianIsDerivative := by
  intro h
  have h1 := h ⟨0⟩ ⟨2⟩ ⟨0, 0, 0, 0, 0, 0⟩ 1 5
  have h2 : HasDerivAt (fun s : ℝ => fluxVec ⟨0⟩ ⟨2⟩ (ofVec (Function.update (toVec ⟨0, 0, 0, 0, 0, 0⟩) 5 s)) 1)
      4 (toVec ⟨0, 0, 0, 0, 0, 0⟩ 5) := by
    apply hasDerivAt_of_affine
    intro s
    set_option simprocs false in
      simp only [fluxVec, xFluxExprs, zero_lit]
    simp [ofVec, toVec, Function.update_apply]
    all_goals first | (simp; done) | (norm_num; done) | (ring_nf; done)
  have := h1.unique h2
  set_option simprocs false in
    simp only [jac, gradVec, xFluxJacobianExprs, zero_lit] at this
  try simp at this
  all_goals norm_num at this
