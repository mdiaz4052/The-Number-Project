open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- Positive control: the published conservation theorem fails at f_L = 0, f_R = 1,
where both of its nondegeneracy hypotheses hold (jump 1/3, fluctuation sum 1/2). -/
theorem refute_B4 :
    ∃ (CL CR : Coordinates) (UL UR : State) (P : Parameters),
      -(max |UL.f| |UR.f|) ≠ 0 ∧ max |UL.f| |UR.f| ≠ 0 ∧
      (xFluxJumpExprs CL CR UL UR P).flux_jump_f ≠
        (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_f := by
  refine ⟨⟨0⟩, ⟨0⟩, ⟨0⟩, ⟨1⟩, ⟨⟩, ?_, ?_, ?_⟩
  · norm_num
  · norm_num
  · simp [xFluxJumpExprs, xFluctuationSumExprs, xFluxExprs, xLeftFluctuationExprs,
      xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    norm_num
