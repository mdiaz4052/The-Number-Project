open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- Lanyon's xFluxConservative statement is true for M5 (any nonzero dissipation speed
conserves); its proof script fails. Hypotheses restated in the equivalent form c ≠ 0. -/
theorem reprove_M5_xFluxConservative (CL CR : Coordinates) (UL UR : State) (P : Parameters)
    (hc : P.c ≠ 0) :
    let J := xFluxJumpExprs CL CR UL UR P
    let S := xFluctuationSumExprs CL CR UL UR P
    J.flux_jump_Ex = S.fluctuation_sum_Ex ∧ J.flux_jump_Ey = S.fluctuation_sum_Ey ∧
    J.flux_jump_Ez = S.fluctuation_sum_Ez ∧ J.flux_jump_Bx = S.fluctuation_sum_Bx ∧
    J.flux_jump_By = S.fluctuation_sum_By ∧ J.flux_jump_Bz = S.fluctuation_sum_Bz := by
  have hpos : 0 < |P.c| := abs_pos.mpr hc
  have h1 : -((1 / 2 : ℝ) * |P.c|) ≤ 0 := by linarith
  have h2 : (0 : ℝ) ≤ (1 / 2 : ℝ) * |P.c| := by linarith
  have hne : |P.c| ≠ 0 := hpos.ne'
  set_option simprocs false in
    simp only [xFluxJumpExprs, xFluctuationSumExprs, xFluxExprs, xLeftFluctuationExprs,
      xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs, zero_lit]
  rw [min_eq_left h1, min_eq_right h2, max_eq_right h1, max_eq_left h2]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;> field_simp <;> ring
