open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs lsa_inviscid_burgers_1d

/-- Positive control: the published wave-stability theorem fails at f = 1. -/
theorem refute_B6 :
    ∃ (C : Coordinates) (P : Parameters) (U : State),
      ¬ ((abs (xWaveSpeedExprs C P U).mu1) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda1)) := by
  refine ⟨⟨0⟩, ⟨⟩, ⟨1⟩, ?_⟩
  simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]
  norm_num
