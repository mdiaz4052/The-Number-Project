open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- Lanyon's xFluxConservative statement is true for B7 (any nonzero dissipation speed
conserves); its proof script fails. Hypotheses restated in the equivalent form m ≠ 0. -/
theorem reprove_B7_xFluxConservative (CL CR : Coordinates) (UL UR : State) (P : Parameters)
    (hm : max |UL.f| |UR.f| ≠ 0) :
    (xFluxJumpExprs CL CR UL UR P).flux_jump_f =
      (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_f := by
  have hpos : 0 < max |UL.f| |UR.f| := lt_of_le_of_ne (le_max_of_le_left (abs_nonneg _)) (Ne.symm hm)
  have h1 : -((1 / 2 : ℝ) * max |UL.f| |UR.f|) ≤ 0 := by linarith
  have h2 : (0 : ℝ) ≤ (1 / 2 : ℝ) * max |UL.f| |UR.f| := by linarith
  set_option simprocs false in
    simp only [xFluxJumpExprs, xFluctuationSumExprs, xFluxExprs, xLeftFluctuationExprs,
      xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs, zero_lit]
  rw [min_eq_left h1, min_eq_right h2, max_eq_right h1, max_eq_left h2]
  field_simp
  ring
