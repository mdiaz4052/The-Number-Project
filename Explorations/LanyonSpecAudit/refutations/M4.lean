open maxwell_1d maxwell_1d_lax_friedrichs lsa_maxwell_1d

/-- Positive control: the published wave-stability theorem fails at c = 1 (|mu5| = 0 < 1 = |lambda5|). -/
theorem refute_M4 :
    ∃ (C : Coordinates) (P : Parameters) (U : State),
      ¬ ((abs (xWaveSpeedExprs C P U).mu5) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda5)) := by
  refine ⟨⟨0⟩, ⟨1⟩, ⟨0, 0, 0, 0, 0, 0⟩, ?_⟩
  set_option simprocs false in
    simp only [xWaveSpeedExprs, xFluxJacobianEigenExprs, zero_lit]
  norm_num
