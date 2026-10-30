import Mathlib

set_option linter.unusedVariables false
set_option linter.unusedTactic false
set_option maxHeartbeats 1000000

namespace inviscid_burgers_1d

structure Coordinates where
  x : Real

structure State where
  f : Real

structure Parameters where


structure Flux where
  flux_f : Real

structure Fluxes1D where
  xFlux : Flux

noncomputable def xFluxExprs (C : Coordinates) (P : Parameters) (U : State) : Flux :=
  let x := C.x

  let f := U.f
  {
    flux_f := ((1 / 2 : Real) * f * f)
  }

noncomputable def fluxes (C : Coordinates) (P : Parameters) (U : State) : Fluxes1D :=
  {
    xFlux := xFluxExprs C P U
  }

structure WaveSpeed where
  mu1 : Real

structure WaveSpeedEstimate1D where
  xWaveSpeed : WaveSpeed

noncomputable def xWaveSpeedExprs (C : Coordinates) (P : Parameters) (U : State) : WaveSpeed :=
  let x := C.x

  let f := U.f
  {
    mu1 := f
  }

noncomputable def wavespeeds (C : Coordinates) (P : Parameters) (U : State) : WaveSpeedEstimate1D :=
  {
    xWaveSpeed := xWaveSpeedExprs C P U
  }

structure StateGradient where
  d_f : Real

structure FluxJacobian where
  flux_f : StateGradient

structure FluxJacobians1D where
  xFluxJacobian : FluxJacobian

noncomputable def xFluxJacobianExprs (C : Coordinates) (P : Parameters) (U : State) : FluxJacobian :=
  let x := C.x

  let f := U.f
  {
    flux_f :=
      {
        d_f := ((0.0 * f * f) + ((1 / 2 : Real) * 1 * f) + ((1 / 2 : Real) * f * 1))
      }
  }

noncomputable def fluxJacobians (C : Coordinates) (P : Parameters) (U : State) : FluxJacobians1D :=
  {
    xFluxJacobian := xFluxJacobianExprs C P U
  }

structure FluxJacobianEigen where
  lambda1 : Real

structure FluxJacobianEigendecomposition1D where
  xFluxJacobianEigen : FluxJacobianEigen

noncomputable def xFluxJacobianEigenExprs (C : Coordinates) (P : Parameters) (U : State) : FluxJacobianEigen :=
  let x := C.x

  let f := U.f
  {
    lambda1 := f
  }

noncomputable def fluxJacobianEigenvalues (C : Coordinates) (P : Parameters) (U : State) : FluxJacobianEigendecomposition1D :=
  {
    xFluxJacobianEigen := xFluxJacobianEigenExprs C P U
  }

theorem xHyperbolicity (C : Coordinates) (P : Parameters) (U : State) :
    (∃ r1 : Real, r1 = (xFluxJacobianEigenExprs C P U).lambda1) := by
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda1, rfl⟩

theorem xWaveStability (C : Coordinates) (P : Parameters) (U : State) :
    ((abs (xWaveSpeedExprs C P U).mu1) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda1)) := by
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]

structure SpatialGradient where
  f_x : Real

structure DiffusiveFlux where
  diffusive_flux_f : Real

structure DiffusiveFluxes1D where
  xDiffusiveFlux : DiffusiveFlux

noncomputable def xDiffusiveFluxExprs (C : Coordinates) (P : Parameters) (U : State) (DU : SpatialGradient) : DiffusiveFlux :=
  let x := C.x

  let f := U.f
  let f_x := DU.f_x
  {
    diffusive_flux_f := 0.0
  }

noncomputable def diffusiveFluxes (C : Coordinates) (P : Parameters) (U : State) (DU : SpatialGradient) : DiffusiveFluxes1D :=
  {
    xDiffusiveFlux := xDiffusiveFluxExprs C P U DU
  }

theorem xDiffusiveFluxConsistency (C : Coordinates) (U : State) (P : Parameters) :
    let DU : SpatialGradient :=
      {
        f_x := 0
      }
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_f) = 0 := by
  . simp only [xDiffusiveFluxExprs]
    norm_num

end inviscid_burgers_1d

namespace inviscid_burgers_1d_lax_friedrichs

open inviscid_burgers_1d

structure Wave where
  wave_f : Real

structure WaveFamily where
  wave1 : Wave
  wave2 : Wave

structure Waves1D where
  xWaveFamily : WaveFamily

noncomputable def xWaveFamilyExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveFamily :=
  let x_L := CL.x
  let x_R := CR.x
  let f_L := UL.f
  let f_R := UR.f

  {
    wave1 :=
      {
        wave_f := ((1 / 2 : Real) * ((f_R - f_L) - ((((1 / 2 : Real) * (f_R * f_R)) - ((1 / 2 : Real) * (f_L * f_L))) /
          (max (abs f_L) (abs f_R)))))
      }
    wave2 :=
      {
        wave_f := ((1 / 2 : Real) * ((f_R - f_L) + ((((1 / 2 : Real) * (f_R * f_R)) - ((1 / 2 : Real) * (f_L * f_L))) /
          (max (abs f_L) (abs f_R)))))
      }
  }

noncomputable def waves (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Waves1D :=
  {
    xWaveFamily := xWaveFamilyExprs CL CR UL UR P
  }

theorem xWaveConsistency (C : Coordinates) (U : State) (P : Parameters) :
    ((xWaveFamilyExprs C C U U P).wave1.wave_f) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_f) = 0.0 := by
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp

structure StateJump where
  jump_f : Real

structure StateJumps1D where
  xStateJump : StateJump

noncomputable def xStateJumpExprs (UL : State) (UR : State) : StateJump :=
  let f_L := UL.f
  let f_R := UR.f
  {
    jump_f := f_R - f_L
  }

noncomputable def stateJumps (UL : State) (UR : State) : StateJumps1D :=
  {
    xStateJump := xStateJumpExprs UL UR
  }

structure WaveSum where
  wave_sum_f : Real

structure WaveSums1D where
  xWaveSum : WaveSum

noncomputable def xWaveSumExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveSum :=
  {
    wave_sum_f := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_f + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_f
  }

noncomputable def waveSums (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveSums1D :=
  {
    xWaveSum := xWaveSumExprs CL CR UL UR P
  }

theorem xWaveJumpCondition (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) :
    ((xStateJumpExprs UL UR).jump_f = (xWaveSumExprs CL CR UL UR P).wave_sum_f) := by
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs]
    ring_nf

structure SpeedFamily where
  speed1 : Real
  speed2 : Real

structure Speeds1D where
  xSpeedFamily : SpeedFamily

noncomputable def xSpeedFamilyExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : SpeedFamily :=
  let x_L := CL.x
  let x_R := CR.x
  let f_L := UL.f
  let f_R := UR.f

  {
    speed1 := -((max (abs f_L) (abs f_R)))
    speed2 := (max (abs f_L) (abs f_R))
  }

noncomputable def speeds (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Speeds1D :=
  {
    xSpeedFamily := xSpeedFamilyExprs CL CR UL UR P
  }

structure Fluctuation where
  fluctuation_f : Real

structure Fluctuations1D where
  xFluctuation : Fluctuation

noncomputable def xLeftFluctuationExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuation :=
  {
    fluctuation_f := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_f * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_f * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))
  }

noncomputable def xRightFluctuationExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuation :=
  {
    fluctuation_f := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_f * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_f * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))
  }

noncomputable def leftFluctuations (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuations1D :=
  {
    xFluctuation := xLeftFluctuationExprs CL CR UL UR P
  }

noncomputable def rightFluctuations (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuations1D :=
  {
    xFluctuation := xRightFluctuationExprs CL CR UL UR P
  }

theorem xLeftFluctuationsConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xLeftFluctuationExprs C C U U P).fluctuation_f) = 0.0 := by
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp

theorem xRightFluctuationsConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xRightFluctuationExprs C C U U P).fluctuation_f) = 0.0 := by
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp

structure FluxJump where
  flux_jump_f : Real

structure FluxJumps1D where
  xFluxJump : FluxJump

noncomputable def xFluxJumpExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluxJump :=
  {
    flux_jump_f := (xFluxExprs CR P UR).flux_f - (xFluxExprs CL P UL).flux_f
  }

noncomputable def fluxJumps (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters): FluxJumps1D :=
  {
    xFluxJump := xFluxJumpExprs CL CR UL UR P
  }

structure FluctuationSum where
  fluctuation_sum_f : Real

structure FluctuationSums1D where
  xFluctuationSum : FluctuationSum

noncomputable def xFluctuationSumExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluctuationSum :=
  {
    fluctuation_sum_f := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_f + (xRightFluctuationExprs CL CR UL UR P).fluctuation_f
  }

noncomputable def fluctuationSums (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluctuationSums1D :=
  {
    xFluctuationSum := xFluctuationSumExprs CL CR UL UR P
  }

theorem xFluxConservative (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters)
    (Speed1Nondegenerate : (
      let x_L := CL.x
      let x_R := CR.x
      let f_L := UL.f
      let f_R := UR.f

      (-((max (abs f_L) (abs f_R))) ≠ 0)))
    (Speed2Nondegenerate : (
      let x_L := CL.x
      let x_R := CR.x
      let f_L := UL.f
      let f_R := UR.f

      ((max (abs f_L) (abs f_R)) ≠ 0))) : 
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_f = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_f) := by
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    ring_nf
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]

end inviscid_burgers_1d_lax_friedrichs

namespace inviscid_burgers_1d_minmod

open inviscid_burgers_1d

structure Reconstruction where
  reconstruction_f : Real

structure Reconstruction1D where
  xReconstruction : Reconstruction

noncomputable def xLeftReconstructionExprs (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction :=
  let x_L := CL.x
  let x := C.x
  let x_R := CR.x
  let f_L := UL.f
  let f := U.f
  let f_R := UR.f

  {
    reconstruction_f := (f - ((1 / 2 : Real) * ((max 0.0 (min (f - f_L) (f_R - f))) + (min 0.0 (max (f - f_L) (f_R -
      f))))))
  }

noncomputable def xRightReconstructionExprs (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction :=
  let x_L := CL.x
  let x := C.x
  let x_R := CR.x
  let f_L := UL.f
  let f := U.f
  let f_R := UR.f

  {
    reconstruction_f := (f + ((1 / 2 : Real) * ((max 0.0 (min (f - f_L) (f_R - f))) + (min 0.0 (max (f - f_L) (f_R -
      f))))))
  }

noncomputable def leftReconstruction (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction1D :=
  {
    xReconstruction := xLeftReconstructionExprs CL C CR UL U UR P
  }

noncomputable def rightReconstruction (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction1D :=
  {
    xReconstruction := xRightReconstructionExprs CL C CR UL U UR P
  }

theorem xLeftReconstructionConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_f) = U.f := by
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp

theorem xRightReconstructionConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xRightReconstructionExprs C C C U U U P).reconstruction_f) = U.f := by
  . simp [xRightReconstructionExprs]
    ring_nf
    simp

theorem xLeftReconstructionLinearityPreservation (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (U : State) (P : Parameters) (D : Real) :
    let UL : State :=
      {
        f := U.f - D
      }
    let UR : State :=
      {
        f := U.f + D
      }
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_f) = U.f - ((1 / 2 : Real) * D) := by
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp

theorem xRightReconstructionLinearityPreservation (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (U : State) (P : Parameters) (D : Real) :
    let UL : State :=
      {
        f := U.f - D
      }
    let UR : State :=
      {
        f := U.f + D
      }
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_f) = U.f + ((1 / 2 : Real) * D) := by
  . simp [xRightReconstructionExprs]
    ring_nf
    simp

theorem xReconstructionSymmetric (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) :
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_f) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_f) := by
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith

end inviscid_burgers_1d_minmod
                