import Mathlib

set_option linter.unusedVariables false
set_option linter.unusedTactic false
set_option maxHeartbeats 1000000

namespace maxwell_1d

structure Coordinates where
  x : Real

structure State where
  Ex : Real
  Ey : Real
  Ez : Real
  Bx : Real
  By : Real
  Bz : Real

structure Parameters where
  c : Real

structure Flux where
  flux_Ex : Real
  flux_Ey : Real
  flux_Ez : Real
  flux_Bx : Real
  flux_By : Real
  flux_Bz : Real

structure Fluxes1D where
  xFlux : Flux

noncomputable def xFluxExprs (C : Coordinates) (P : Parameters) (U : State) : Flux :=
  let x := C.x
  let c := P.c
  let Ex := U.Ex
  let Ey := U.Ey
  let Ez := U.Ez
  let Bx := U.Bx
  let By := U.By
  let Bz := U.Bz
  {
    flux_Ex := 0.0
    flux_Ey := ((c * c) * Bz)
    flux_Ez := -(((c * c) * By))
    flux_Bx := 0.0
    flux_By := -(Ez)
    flux_Bz := Ey
  }

noncomputable def fluxes (C : Coordinates) (P : Parameters) (U : State) : Fluxes1D :=
  {
    xFlux := xFluxExprs C P U
  }

structure WaveSpeed where
  mu1 : Real
  mu2 : Real
  mu3 : Real
  mu4 : Real
  mu5 : Real
  mu6 : Real

structure WaveSpeedEstimate1D where
  xWaveSpeed : WaveSpeed

noncomputable def xWaveSpeedExprs (C : Coordinates) (P : Parameters) (U : State) : WaveSpeed :=
  let x := C.x
  let c := P.c
  let Ex := U.Ex
  let Ey := U.Ey
  let Ez := U.Ez
  let Bx := U.Bx
  let By := U.By
  let Bz := U.Bz
  {
    mu1 := -(c)
    mu2 := -(c)
    mu3 := c
    mu4 := c
    mu5 := 0.0
    mu6 := 0.0
  }

noncomputable def wavespeeds (C : Coordinates) (P : Parameters) (U : State) : WaveSpeedEstimate1D :=
  {
    xWaveSpeed := xWaveSpeedExprs C P U
  }

structure StateGradient where
  d_Ex : Real
  d_Ey : Real
  d_Ez : Real
  d_Bx : Real
  d_By : Real
  d_Bz : Real

structure FluxJacobian where
  flux_Ex : StateGradient
  flux_Ey : StateGradient
  flux_Ez : StateGradient
  flux_Bx : StateGradient
  flux_By : StateGradient
  flux_Bz : StateGradient

structure FluxJacobians1D where
  xFluxJacobian : FluxJacobian

noncomputable def xFluxJacobianExprs (C : Coordinates) (P : Parameters) (U : State) : FluxJacobian :=
  let x := C.x
  let c := P.c
  let Ex := U.Ex
  let Ey := U.Ey
  let Ez := U.Ez
  let Bx := U.Bx
  let By := U.By
  let Bz := U.Bz
  {
    flux_Ex :=
      {
        d_Ex := 0.0
        d_Ey := 0.0
        d_Ez := 0.0
        d_Bx := 0.0
        d_By := 0.0
        d_Bz := 0.0
      }
    flux_Ey :=
      {
        d_Ex := 0.0
        d_Ey := 0.0
        d_Ez := 0.0
        d_Bx := 0.0
        d_By := 0.0
        d_Bz := (c * c)
      }
    flux_Ez :=
      {
        d_Ex := -(0.0)
        d_Ey := -(0.0)
        d_Ez := -(0.0)
        d_Bx := -(0.0)
        d_By := -((c * c))
        d_Bz := -(0.0)
      }
    flux_Bx :=
      {
        d_Ex := 0.0
        d_Ey := 0.0
        d_Ez := 0.0
        d_Bx := 0.0
        d_By := 0.0
        d_Bz := 0.0
      }
    flux_By :=
      {
        d_Ex := -(0.0)
        d_Ey := -(0.0)
        d_Ez := -(1)
        d_Bx := -(0.0)
        d_By := -(0.0)
        d_Bz := -(0.0)
      }
    flux_Bz :=
      {
        d_Ex := 0.0
        d_Ey := 1
        d_Ez := 0.0
        d_Bx := 0.0
        d_By := 0.0
        d_Bz := 0.0
      }
  }

noncomputable def fluxJacobians (C : Coordinates) (P : Parameters) (U : State) : FluxJacobians1D :=
  {
    xFluxJacobian := xFluxJacobianExprs C P U
  }

structure FluxJacobianEigen where
  lambda1 : Real
  lambda2 : Real
  lambda3 : Real
  lambda4 : Real
  lambda5 : Real
  lambda6 : Real

structure FluxJacobianEigendecomposition1D where
  xFluxJacobianEigen : FluxJacobianEigen

noncomputable def xFluxJacobianEigenExprs (C : Coordinates) (P : Parameters) (U : State) : FluxJacobianEigen :=
  let x := C.x
  let c := P.c
  let Ex := U.Ex
  let Ey := U.Ey
  let Ez := U.Ez
  let Bx := U.Bx
  let By := U.By
  let Bz := U.Bz
  {
    lambda1 := -(c)
    lambda2 := -(c)
    lambda3 := c
    lambda4 := c
    lambda5 := 0.0
    lambda6 := 0.0
  }

noncomputable def fluxJacobianEigenvalues (C : Coordinates) (P : Parameters) (U : State) : FluxJacobianEigendecomposition1D :=
  {
    xFluxJacobianEigen := xFluxJacobianEigenExprs C P U
  }

theorem xHyperbolicity (C : Coordinates) (P : Parameters) (U : State) :
    (∃ r1 : Real, r1 = (xFluxJacobianEigenExprs C P U).lambda1) ∧
    (∃ r2 : Real, r2 = (xFluxJacobianEigenExprs C P U).lambda2) ∧
    (∃ r3 : Real, r3 = (xFluxJacobianEigenExprs C P U).lambda3) ∧
    (∃ r4 : Real, r4 = (xFluxJacobianEigenExprs C P U).lambda4) ∧
    (∃ r5 : Real, r5 = (xFluxJacobianEigenExprs C P U).lambda5) ∧
    (∃ r6 : Real, r6 = (xFluxJacobianEigenExprs C P U).lambda6) := by
  constructor
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda1, rfl⟩
  constructor
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda2, rfl⟩
  constructor
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda3, rfl⟩
  constructor
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda4, rfl⟩
  constructor
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda5, rfl⟩
  . refine ⟨(xFluxJacobianEigenExprs C P U).lambda6, rfl⟩

theorem xWaveStability (C : Coordinates) (P : Parameters) (U : State) :
    ((abs (xWaveSpeedExprs C P U).mu1) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda1)) ∧
    ((abs (xWaveSpeedExprs C P U).mu2) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda2)) ∧
    ((abs (xWaveSpeedExprs C P U).mu3) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda3)) ∧
    ((abs (xWaveSpeedExprs C P U).mu4) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda4)) ∧
    ((abs (xWaveSpeedExprs C P U).mu5) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda5)) ∧
    ((abs (xWaveSpeedExprs C P U).mu6) ≥ (abs (xFluxJacobianEigenExprs C P U).lambda6)) := by
  constructor
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]
  constructor
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]
  constructor
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]
  constructor
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]
  constructor
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]
  . simp [xWaveSpeedExprs, xFluxJacobianEigenExprs]

structure SpatialGradient where
  Ex_x : Real
  Ey_x : Real
  Ez_x : Real
  Bx_x : Real
  By_x : Real
  Bz_x : Real

structure DiffusiveFlux where
  diffusive_flux_Ex : Real
  diffusive_flux_Ey : Real
  diffusive_flux_Ez : Real
  diffusive_flux_Bx : Real
  diffusive_flux_By : Real
  diffusive_flux_Bz : Real

structure DiffusiveFluxes1D where
  xDiffusiveFlux : DiffusiveFlux

noncomputable def xDiffusiveFluxExprs (C : Coordinates) (P : Parameters) (U : State) (DU : SpatialGradient) : DiffusiveFlux :=
  let x := C.x
  let c := P.c
  let Ex := U.Ex
  let Ey := U.Ey
  let Ez := U.Ez
  let Bx := U.Bx
  let By := U.By
  let Bz := U.Bz
  let Ex_x := DU.Ex_x
  let Ey_x := DU.Ey_x
  let Ez_x := DU.Ez_x
  let Bx_x := DU.Bx_x
  let By_x := DU.By_x
  let Bz_x := DU.Bz_x
  {
    diffusive_flux_Ex := 0.0
    diffusive_flux_Ey := 0.0
    diffusive_flux_Ez := 0.0
    diffusive_flux_Bx := 0.0
    diffusive_flux_By := 0.0
    diffusive_flux_Bz := 0.0
  }

noncomputable def diffusiveFluxes (C : Coordinates) (P : Parameters) (U : State) (DU : SpatialGradient) : DiffusiveFluxes1D :=
  {
    xDiffusiveFlux := xDiffusiveFluxExprs C P U DU
  }

theorem xDiffusiveFluxConsistency (C : Coordinates) (U : State) (P : Parameters) :
    let DU : SpatialGradient :=
      {
        Ex_x := 0
        Ey_x := 0
        Ez_x := 0
        Bx_x := 0
        By_x := 0
        Bz_x := 0
      }
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_Ex) = 0 ∧
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_Ey) = 0 ∧
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_Ez) = 0 ∧
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_Bx) = 0 ∧
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_By) = 0 ∧
    ((xDiffusiveFluxExprs C P U DU).diffusive_flux_Bz) = 0 := by
  constructor
  . simp only [xDiffusiveFluxExprs]
    norm_num
  constructor
  . simp only [xDiffusiveFluxExprs]
    norm_num
  constructor
  . simp only [xDiffusiveFluxExprs]
    norm_num
  constructor
  . simp only [xDiffusiveFluxExprs]
    norm_num
  constructor
  . simp only [xDiffusiveFluxExprs]
    norm_num
  . simp only [xDiffusiveFluxExprs]
    norm_num

end maxwell_1d

namespace maxwell_1d_lax_friedrichs

open maxwell_1d

structure Wave where
  wave_Ex : Real
  wave_Ey : Real
  wave_Ez : Real
  wave_Bx : Real
  wave_By : Real
  wave_Bz : Real

structure WaveFamily where
  wave1 : Wave
  wave2 : Wave

structure Waves1D where
  xWaveFamily : WaveFamily

noncomputable def xWaveFamilyExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveFamily :=
  let x_L := CL.x
  let x_R := CR.x
  let Ex_L := UL.Ex
  let Ex_R := UR.Ex
  let Ey_L := UL.Ey
  let Ey_R := UR.Ey
  let Ez_L := UL.Ez
  let Ez_R := UR.Ez
  let Bx_L := UL.Bx
  let Bx_R := UR.Bx
  let By_L := UL.By
  let By_R := UR.By
  let Bz_L := UL.Bz
  let Bz_R := UR.Bz
  let c := P.c
  {
    wave1 :=
      {
        wave_Ex := ((1 / 2 : Real) * ((Ex_R - Ex_L) - ((0.0 - 0.0) / (abs c))))
        wave_Ey := ((1 / 2 : Real) * ((Ey_R - Ey_L) - ((((c * c) * Bz_R) - ((c * c) * Bz_L)) / (abs c))))
        wave_Ez := ((1 / 2 : Real) * ((Ez_R - Ez_L) - ((-(((c * c) * By_R)) - -(((c * c) * By_L))) / (abs c))))
        wave_Bx := ((1 / 2 : Real) * ((Bx_R - Bx_L) - ((0.0 - 0.0) / (abs c))))
        wave_By := ((1 / 2 : Real) * ((By_R - By_L) - ((-(Ez_R) - -(Ez_L)) / (abs c))))
        wave_Bz := ((1 / 2 : Real) * ((Bz_R - Bz_L) - ((Ey_R - Ey_L) / (abs c))))
      }
    wave2 :=
      {
        wave_Ex := ((1 / 2 : Real) * ((Ex_R - Ex_L) + ((0.0 - 0.0) / (abs c))))
        wave_Ey := ((1 / 2 : Real) * ((Ey_R - Ey_L) + ((((c * c) * Bz_R) - ((c * c) * Bz_L)) / (abs c))))
        wave_Ez := ((1 / 2 : Real) * ((Ez_R - Ez_L) + ((-(((c * c) * By_R)) - -(((c * c) * By_L))) / (abs c))))
        wave_Bx := ((1 / 2 : Real) * ((Bx_R - Bx_L) + ((0.0 - 0.0) / (abs c))))
        wave_By := ((1 / 2 : Real) * ((By_R - By_L) + ((-(Ez_R) - -(Ez_L)) / (abs c))))
        wave_Bz := ((1 / 2 : Real) * ((Bz_R - Bz_L) + ((Ey_R - Ey_L) / (abs c))))
      }
  }

noncomputable def waves (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Waves1D :=
  {
    xWaveFamily := xWaveFamilyExprs CL CR UL UR P
  }

theorem xWaveConsistency (C : Coordinates) (U : State) (P : Parameters) :
    ((xWaveFamilyExprs C C U U P).wave1.wave_Ex) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_Ex) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave1.wave_Ey) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_Ey) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave1.wave_Ez) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_Ez) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave1.wave_Bx) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_Bx) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave1.wave_By) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_By) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave1.wave_Bz) = 0.0 ∧
    ((xWaveFamilyExprs C C U U P).wave2.wave_Bz) = 0.0 := by
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp
  . simp [xWaveFamilyExprs]
    ring_nf
    field_simp

structure StateJump where
  jump_Ex : Real
  jump_Ey : Real
  jump_Ez : Real
  jump_Bx : Real
  jump_By : Real
  jump_Bz : Real

structure StateJumps1D where
  xStateJump : StateJump

noncomputable def xStateJumpExprs (UL : State) (UR : State) : StateJump :=
  let Ex_L := UL.Ex
  let Ex_R := UR.Ex
  let Ey_L := UL.Ey
  let Ey_R := UR.Ey
  let Ez_L := UL.Ez
  let Ez_R := UR.Ez
  let Bx_L := UL.Bx
  let Bx_R := UR.Bx
  let By_L := UL.By
  let By_R := UR.By
  let Bz_L := UL.Bz
  let Bz_R := UR.Bz
  {
    jump_Ex := Ex_R - Ex_L
    jump_Ey := Ey_R - Ey_L
    jump_Ez := Ez_R - Ez_L
    jump_Bx := Bx_R - Bx_L
    jump_By := By_R - By_L
    jump_Bz := Bz_R - Bz_L
  }

noncomputable def stateJumps (UL : State) (UR : State) : StateJumps1D :=
  {
    xStateJump := xStateJumpExprs UL UR
  }

structure WaveSum where
  wave_sum_Ex : Real
  wave_sum_Ey : Real
  wave_sum_Ez : Real
  wave_sum_Bx : Real
  wave_sum_By : Real
  wave_sum_Bz : Real

structure WaveSums1D where
  xWaveSum : WaveSum

noncomputable def xWaveSumExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveSum :=
  {
    wave_sum_Ex := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ex + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ex
    wave_sum_Ey := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ey + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ey
    wave_sum_Ez := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ez + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ez
    wave_sum_Bx := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_Bx + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_Bx
    wave_sum_By := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_By + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_By
    wave_sum_Bz := (xWaveFamilyExprs CL CR UL UR P).wave1.wave_Bz + (xWaveFamilyExprs CL CR UL UR P).wave2.wave_Bz
  }

noncomputable def waveSums (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : WaveSums1D :=
  {
    xWaveSum := xWaveSumExprs CL CR UL UR P
  }

theorem xWaveJumpCondition (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) :
    ((xStateJumpExprs UL UR).jump_Ex = (xWaveSumExprs CL CR UL UR P).wave_sum_Ex) ∧
    ((xStateJumpExprs UL UR).jump_Ey = (xWaveSumExprs CL CR UL UR P).wave_sum_Ey) ∧
    ((xStateJumpExprs UL UR).jump_Ez = (xWaveSumExprs CL CR UL UR P).wave_sum_Ez) ∧
    ((xStateJumpExprs UL UR).jump_Bx = (xWaveSumExprs CL CR UL UR P).wave_sum_Bx) ∧
    ((xStateJumpExprs UL UR).jump_By = (xWaveSumExprs CL CR UL UR P).wave_sum_By) ∧
    ((xStateJumpExprs UL UR).jump_Bz = (xWaveSumExprs CL CR UL UR P).wave_sum_Bz) := by
  constructor
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs]
    ring_nf
  constructor
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs]
    ring_nf
  constructor
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs]
    ring_nf
  constructor
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs]
    ring_nf
  constructor
  . simp [xStateJumpExprs, xWaveSumExprs, xWaveFamilyExprs]
    ring_nf
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
  let Ex_L := UL.Ex
  let Ex_R := UR.Ex
  let Ey_L := UL.Ey
  let Ey_R := UR.Ey
  let Ez_L := UL.Ez
  let Ez_R := UR.Ez
  let Bx_L := UL.Bx
  let Bx_R := UR.Bx
  let By_L := UL.By
  let By_R := UR.By
  let Bz_L := UL.Bz
  let Bz_R := UR.Bz
  let c := P.c
  {
    speed1 := -((abs c))
    speed2 := (abs c)
  }

noncomputable def speeds (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Speeds1D :=
  {
    xSpeedFamily := xSpeedFamilyExprs CL CR UL UR P
  }

structure Fluctuation where
  fluctuation_Ex : Real
  fluctuation_Ey : Real
  fluctuation_Ez : Real
  fluctuation_Bx : Real
  fluctuation_By : Real
  fluctuation_Bz : Real

structure Fluctuations1D where
  xFluctuation : Fluctuation

noncomputable def xLeftFluctuationExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuation :=
  {
    fluctuation_Ex := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ex * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ex * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Ey := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ey * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ey * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Ez := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ez * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ez * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Bx := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Bx * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Bx * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_By := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_By * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_By * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Bz := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Bz * (min (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Bz * (min (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))
  }

noncomputable def xRightFluctuationExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : Fluctuation :=
  {
    fluctuation_Ex := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ex * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ex * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Ey := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ey * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ey * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Ez := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Ez * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Ez * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Bx := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Bx * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Bx * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_By := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_By * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_By * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))

    fluctuation_Bz := 
      ((xWaveFamilyExprs CL CR UL UR P).wave1.wave_Bz * (max (xSpeedFamilyExprs CL CR UL UR P).speed1 0.0)) + 
      ((xWaveFamilyExprs CL CR UL UR P).wave2.wave_Bz * (max (xSpeedFamilyExprs CL CR UL UR P).speed2 0.0))
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
    ((xLeftFluctuationExprs C C U U P).fluctuation_Ex) = 0.0 ∧
    ((xLeftFluctuationExprs C C U U P).fluctuation_Ey) = 0.0 ∧
    ((xLeftFluctuationExprs C C U U P).fluctuation_Ez) = 0.0 ∧
    ((xLeftFluctuationExprs C C U U P).fluctuation_Bx) = 0.0 ∧
    ((xLeftFluctuationExprs C C U U P).fluctuation_By) = 0.0 ∧
    ((xLeftFluctuationExprs C C U U P).fluctuation_Bz) = 0.0 := by
  constructor
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  . simp [xLeftFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp

theorem xRightFluctuationsConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xRightFluctuationExprs C C U U P).fluctuation_Ex) = 0.0 ∧
    ((xRightFluctuationExprs C C U U P).fluctuation_Ey) = 0.0 ∧
    ((xRightFluctuationExprs C C U U P).fluctuation_Ez) = 0.0 ∧
    ((xRightFluctuationExprs C C U U P).fluctuation_Bx) = 0.0 ∧
    ((xRightFluctuationExprs C C U U P).fluctuation_By) = 0.0 ∧
    ((xRightFluctuationExprs C C U U P).fluctuation_Bz) = 0.0 := by
  constructor
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  constructor
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp
  . simp [xRightFluctuationExprs, xWaveFamilyExprs, xSpeedFamilyExprs]
    ring_nf
    field_simp

structure FluxJump where
  flux_jump_Ex : Real
  flux_jump_Ey : Real
  flux_jump_Ez : Real
  flux_jump_Bx : Real
  flux_jump_By : Real
  flux_jump_Bz : Real

structure FluxJumps1D where
  xFluxJump : FluxJump

noncomputable def xFluxJumpExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluxJump :=
  {
    flux_jump_Ex := (xFluxExprs CR P UR).flux_Ex - (xFluxExprs CL P UL).flux_Ex
    flux_jump_Ey := (xFluxExprs CR P UR).flux_Ey - (xFluxExprs CL P UL).flux_Ey
    flux_jump_Ez := (xFluxExprs CR P UR).flux_Ez - (xFluxExprs CL P UL).flux_Ez
    flux_jump_Bx := (xFluxExprs CR P UR).flux_Bx - (xFluxExprs CL P UL).flux_Bx
    flux_jump_By := (xFluxExprs CR P UR).flux_By - (xFluxExprs CL P UL).flux_By
    flux_jump_Bz := (xFluxExprs CR P UR).flux_Bz - (xFluxExprs CL P UL).flux_Bz
  }

noncomputable def fluxJumps (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters): FluxJumps1D :=
  {
    xFluxJump := xFluxJumpExprs CL CR UL UR P
  }

structure FluctuationSum where
  fluctuation_sum_Ex : Real
  fluctuation_sum_Ey : Real
  fluctuation_sum_Ez : Real
  fluctuation_sum_Bx : Real
  fluctuation_sum_By : Real
  fluctuation_sum_Bz : Real

structure FluctuationSums1D where
  xFluctuationSum : FluctuationSum

noncomputable def xFluctuationSumExprs (CL : Coordinates) (CR : Coordinates)
    (UL : State) (UR : State) (P : Parameters) : FluctuationSum :=
  {
    fluctuation_sum_Ex := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_Ex + (xRightFluctuationExprs CL CR UL UR P).fluctuation_Ex
    fluctuation_sum_Ey := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_Ey + (xRightFluctuationExprs CL CR UL UR P).fluctuation_Ey
    fluctuation_sum_Ez := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_Ez + (xRightFluctuationExprs CL CR UL UR P).fluctuation_Ez
    fluctuation_sum_Bx := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_Bx + (xRightFluctuationExprs CL CR UL UR P).fluctuation_Bx
    fluctuation_sum_By := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_By + (xRightFluctuationExprs CL CR UL UR P).fluctuation_By
    fluctuation_sum_Bz := (xLeftFluctuationExprs CL CR UL UR P).fluctuation_Bz + (xRightFluctuationExprs CL CR UL UR P).fluctuation_Bz
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
      let Ex_L := UL.Ex
      let Ex_R := UR.Ex
      let Ey_L := UL.Ey
      let Ey_R := UR.Ey
      let Ez_L := UL.Ez
      let Ez_R := UR.Ez
      let Bx_L := UL.Bx
      let Bx_R := UR.Bx
      let By_L := UL.By
      let By_R := UR.By
      let Bz_L := UL.Bz
      let Bz_R := UR.Bz
      let c := P.c
      (-((abs c)) ≠ 0)))
    (Speed2Nondegenerate : (
      let x_L := CL.x
      let x_R := CR.x
      let Ex_L := UL.Ex
      let Ex_R := UR.Ex
      let Ey_L := UL.Ey
      let Ey_R := UR.Ey
      let Ez_L := UL.Ez
      let Ez_R := UR.Ez
      let Bx_L := UL.Bx
      let Bx_R := UR.Bx
      let By_L := UL.By
      let By_R := UR.By
      let Bz_L := UL.Bz
      let Bz_R := UR.Bz
      let c := P.c
      ((abs c) ≠ 0))) : 
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_Ex = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_Ex) ∧
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_Ey = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_Ey) ∧
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_Ez = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_Ez) ∧
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_Bx = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_Bx) ∧
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_By = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_By) ∧
    ((xFluxJumpExprs CL CR UL UR P).flux_jump_Bz = (xFluctuationSumExprs CL CR UL UR P).fluctuation_sum_Bz) := by
  constructor
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
  constructor
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    ring_nf
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
  constructor
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    ring_nf
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
  constructor
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
  constructor
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    ring_nf
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
  . simp [xFluxJumpExprs, xFluctuationSumExprs]
    simp [xFluxExprs, xLeftFluctuationExprs, xRightFluctuationExprs]
    ring_nf
    simp [xWaveFamilyExprs, xSpeedFamilyExprs]
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]
    ring_nf
    repeat field_simp [Speed1Nondegenerate, Speed2Nondegenerate]

end maxwell_1d_lax_friedrichs

namespace maxwell_1d_minmod

open maxwell_1d

structure Reconstruction where
  reconstruction_Ex : Real
  reconstruction_Ey : Real
  reconstruction_Ez : Real
  reconstruction_Bx : Real
  reconstruction_By : Real
  reconstruction_Bz : Real

structure Reconstruction1D where
  xReconstruction : Reconstruction

noncomputable def xLeftReconstructionExprs (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction :=
  let x_L := CL.x
  let x := C.x
  let x_R := CR.x
  let Ex_L := UL.Ex
  let Ex := U.Ex
  let Ex_R := UR.Ex
  let Ey_L := UL.Ey
  let Ey := U.Ey
  let Ey_R := UR.Ey
  let Ez_L := UL.Ez
  let Ez := U.Ez
  let Ez_R := UR.Ez
  let Bx_L := UL.Bx
  let Bx := U.Bx
  let Bx_R := UR.Bx
  let By_L := UL.By
  let By := U.By
  let By_R := UR.By
  let Bz_L := UL.Bz
  let Bz := U.Bz
  let Bz_R := UR.Bz
  let c := P.c
  {
    reconstruction_Ex := (Ex - ((1 / 2 : Real) * ((max 0.0 (min (Ex - Ex_L) (Ex_R - Ex))) + (min 0.0 (max (Ex - Ex_L)
      (Ex_R - Ex))))))
    reconstruction_Ey := (Ey - ((1 / 2 : Real) * ((max 0.0 (min (Ey - Ey_L) (Ey_R - Ey))) + (min 0.0 (max (Ey - Ey_L)
      (Ey_R - Ey))))))
    reconstruction_Ez := (Ez - ((1 / 2 : Real) * ((max 0.0 (min (Ez - Ez_L) (Ez_R - Ez))) + (min 0.0 (max (Ez - Ez_L)
      (Ez_R - Ez))))))
    reconstruction_Bx := (Bx - ((1 / 2 : Real) * ((max 0.0 (min (Bx - Bx_L) (Bx_R - Bx))) + (min 0.0 (max (Bx - Bx_L)
      (Bx_R - Bx))))))
    reconstruction_By := (By - ((1 / 2 : Real) * ((max 0.0 (min (By - By_L) (By_R - By))) + (min 0.0 (max (By - By_L)
      (By_R - By))))))
    reconstruction_Bz := (Bz - ((1 / 2 : Real) * ((max 0.0 (min (Bz - Bz_L) (Bz_R - Bz))) + (min 0.0 (max (Bz - Bz_L)
      (Bz_R - Bz))))))
  }

noncomputable def xRightReconstructionExprs (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) : Reconstruction :=
  let x_L := CL.x
  let x := C.x
  let x_R := CR.x
  let Ex_L := UL.Ex
  let Ex := U.Ex
  let Ex_R := UR.Ex
  let Ey_L := UL.Ey
  let Ey := U.Ey
  let Ey_R := UR.Ey
  let Ez_L := UL.Ez
  let Ez := U.Ez
  let Ez_R := UR.Ez
  let Bx_L := UL.Bx
  let Bx := U.Bx
  let Bx_R := UR.Bx
  let By_L := UL.By
  let By := U.By
  let By_R := UR.By
  let Bz_L := UL.Bz
  let Bz := U.Bz
  let Bz_R := UR.Bz
  let c := P.c
  {
    reconstruction_Ex := (Ex + ((1 / 2 : Real) * ((max 0.0 (min (Ex - Ex_L) (Ex_R - Ex))) + (min 0.0 (max (Ex - Ex_L)
      (Ex_R - Ex))))))
    reconstruction_Ey := (Ey + ((1 / 2 : Real) * ((max 0.0 (min (Ey - Ey_L) (Ey_R - Ey))) + (min 0.0 (max (Ey - Ey_L)
      (Ey_R - Ey))))))
    reconstruction_Ez := (Ez + ((1 / 2 : Real) * ((max 0.0 (min (Ez - Ez_L) (Ez_R - Ez))) + (min 0.0 (max (Ez - Ez_L)
      (Ez_R - Ez))))))
    reconstruction_Bx := (Bx + ((1 / 2 : Real) * ((max 0.0 (min (Bx - Bx_L) (Bx_R - Bx))) + (min 0.0 (max (Bx - Bx_L)
      (Bx_R - Bx))))))
    reconstruction_By := (By + ((1 / 2 : Real) * ((max 0.0 (min (By - By_L) (By_R - By))) + (min 0.0 (max (By - By_L)
      (By_R - By))))))
    reconstruction_Bz := (Bz + ((1 / 2 : Real) * ((max 0.0 (min (Bz - Bz_L) (Bz_R - Bz))) + (min 0.0 (max (Bz - Bz_L)
      (Bz_R - Bz))))))
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
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_Ex) = U.Ex ∧
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_Ey) = U.Ey ∧
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_Ez) = U.Ez ∧
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_Bx) = U.Bx ∧
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_By) = U.By ∧
    ((xLeftReconstructionExprs C C C U U U P).reconstruction_Bz) = U.Bz := by
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp

theorem xRightReconstructionConsistent (C : Coordinates) (U : State) (P : Parameters) :
    ((xRightReconstructionExprs C C C U U U P).reconstruction_Ex) = U.Ex ∧
    ((xRightReconstructionExprs C C C U U U P).reconstruction_Ey) = U.Ey ∧
    ((xRightReconstructionExprs C C C U U U P).reconstruction_Ez) = U.Ez ∧
    ((xRightReconstructionExprs C C C U U U P).reconstruction_Bx) = U.Bx ∧
    ((xRightReconstructionExprs C C C U U U P).reconstruction_By) = U.By ∧
    ((xRightReconstructionExprs C C C U U U P).reconstruction_Bz) = U.Bz := by
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  . simp [xRightReconstructionExprs]
    ring_nf
    simp

theorem xLeftReconstructionLinearityPreservation (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (U : State) (P : Parameters) (D : Real) :
    let UL : State :=
      {
        Ex := U.Ex - D
        Ey := U.Ey - D
        Ez := U.Ez - D
        Bx := U.Bx - D
        By := U.By - D
        Bz := U.Bz - D
      }
    let UR : State :=
      {
        Ex := U.Ex + D
        Ey := U.Ey + D
        Ez := U.Ez + D
        Bx := U.Bx + D
        By := U.By + D
        Bz := U.Bz + D
      }
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Ex) = U.Ex - ((1 / 2 : Real) * D) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Ey) = U.Ey - ((1 / 2 : Real) * D) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Ez) = U.Ez - ((1 / 2 : Real) * D) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Bx) = U.Bx - ((1 / 2 : Real) * D) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_By) = U.By - ((1 / 2 : Real) * D) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Bz) = U.Bz - ((1 / 2 : Real) * D) := by
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp
  . simp [xLeftReconstructionExprs]
    ring_nf
    simp

theorem xRightReconstructionLinearityPreservation (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (U : State) (P : Parameters) (D : Real) :
    let UL : State :=
      {
        Ex := U.Ex - D
        Ey := U.Ey - D
        Ez := U.Ez - D
        Bx := U.Bx - D
        By := U.By - D
        Bz := U.Bz - D
      }
    let UR : State :=
      {
        Ex := U.Ex + D
        Ey := U.Ey + D
        Ez := U.Ez + D
        Bx := U.Bx + D
        By := U.By + D
        Bz := U.Bz + D
      }
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_Ex) = U.Ex + ((1 / 2 : Real) * D) ∧
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_Ey) = U.Ey + ((1 / 2 : Real) * D) ∧
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_Ez) = U.Ez + ((1 / 2 : Real) * D) ∧
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_Bx) = U.Bx + ((1 / 2 : Real) * D) ∧
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_By) = U.By + ((1 / 2 : Real) * D) ∧
    ((xRightReconstructionExprs CL C CR UL U UR P).reconstruction_Bz) = U.Bz + ((1 / 2 : Real) * D) := by
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  constructor
  . simp [xRightReconstructionExprs]
    ring_nf
    simp
  . simp [xRightReconstructionExprs]
    ring_nf
    simp

theorem xReconstructionSymmetric (CL : Coordinates) (C : Coordinates) (CR : Coordinates)
    (UL : State) (U : State) (UR : State) (P : Parameters) :
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Ex) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_Ex) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Ey) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_Ey) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Ez) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_Ez) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Bx) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_Bx) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_By) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_By) ∧
    ((xLeftReconstructionExprs CL C CR UL U UR P).reconstruction_Bz) = ((xRightReconstructionExprs CR C CL UR U UL P).reconstruction_Bz) := by
  constructor
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith
  constructor
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith
  constructor
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith
  constructor
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith
  constructor
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith
  . simp [xLeftReconstructionExprs, xRightReconstructionExprs]
    ring_nf
    field_simp
    simp only [min_def, max_def]
    split_ifs <;> linarith

end maxwell_1d_minmod
                