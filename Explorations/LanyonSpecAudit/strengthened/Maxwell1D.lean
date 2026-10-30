/-!
# LSA-1 strengthened statements for `maxwell_1d`

Appended by `audit.py` to the pinned (possibly mutated) upstream file; not standalone.
State and flux components are ordered `Ex, Ey, Ez, Bx, By, Bz`.
-/

namespace lsa_maxwell_1d

open maxwell_1d maxwell_1d_lax_friedrichs

def toVec (U : State) : Fin 6 → ℝ := ![U.Ex, U.Ey, U.Ez, U.Bx, U.By, U.Bz]

def ofVec (v : Fin 6 → ℝ) : State := ⟨v 0, v 1, v 2, v 3, v 4, v 5⟩

noncomputable def fluxVec (C : Coordinates) (P : Parameters) (U : State) : Fin 6 → ℝ :=
  let F := xFluxExprs C P U
  ![F.flux_Ex, F.flux_Ey, F.flux_Ez, F.flux_Bx, F.flux_By, F.flux_Bz]

def gradVec (g : StateGradient) : Fin 6 → ℝ := ![g.d_Ex, g.d_Ey, g.d_Ez, g.d_Bx, g.d_By, g.d_Bz]

noncomputable def jac (C : Coordinates) (P : Parameters) (U : State) : Matrix (Fin 6) (Fin 6) ℝ :=
  let J := xFluxJacobianExprs C P U
  Matrix.of ![gradVec J.flux_Ex, gradVec J.flux_Ey, gradVec J.flux_Ez,
    gradVec J.flux_Bx, gradVec J.flux_By, gradVec J.flux_Bz]

noncomputable def eig (C : Coordinates) (P : Parameters) (U : State) : Fin 6 → ℝ :=
  let E := xFluxJacobianEigenExprs C P U
  ![E.lambda1, E.lambda2, E.lambda3, E.lambda4, E.lambda5, E.lambda6]

/-- S1: every declared Jacobian entry is the partial derivative of the declared flux. -/
def JacobianIsDerivative : Prop :=
  ∀ (C : Coordinates) (P : Parameters) (U : State) (i j : Fin 6),
    HasDerivAt (fun s : ℝ => fluxVec C P (ofVec (Function.update (toVec U) j s)) i)
      (jac C P U i j) (toVec U j)

/-- S2: under the spec's own assumption `c > 0`, the declared eigenvalues diagonalize the
declared Jacobian with a real invertible eigenbasis (strong hyperbolicity). -/
def RealEigenbasis : Prop :=
  ∀ (C : Coordinates) (P : Parameters) (U : State), 0 < P.c →
    ∃ R L : Matrix (Fin 6) (Fin 6) ℝ, L * R = 1 ∧ jac C P U * R = R * Matrix.diagonal (eig C P U)

/-- S3: the Lax-Friedrichs dissipation speed dominates the declared eigenvalues at both states. -/
def DissipationBound : Prop :=
  ∀ (CL CR : Coordinates) (UL UR : State) (P : Parameters) (i : Fin 6),
    |eig CL P UL i| ≤ (xSpeedFamilyExprs CL CR UL UR P).speed2 ∧
    |eig CR P UR i| ≤ (xSpeedFamilyExprs CL CR UL UR P).speed2

theorem jacobianIsDerivative : JacobianIsDerivative := by
  intro C P U i j
  fin_cases i <;> fin_cases j <;>
    simp [fluxVec, ofVec, toVec, jac, gradVec, xFluxExprs, xFluxJacobianExprs,
      Function.update_apply] <;>
    first
      | exact hasDerivAt_const _ _
      | exact hasDerivAt_id _
      | exact (hasDerivAt_id _).neg
      | exact hasDerivAt_mul_const _
      | exact (hasDerivAt_mul_const _).neg
      | exact ((hasDerivAt_id _).const_mul _).congr_deriv (by ring)
      | exact (((hasDerivAt_id _).const_mul _).neg).congr_deriv (by ring)

/-- Explicit eigenvectors (columns of `R`) and their dual basis (rows of `L`). -/
noncomputable def eigvecs (c : ℝ) : Matrix (Fin 6) (Fin 6) ℝ :=
  !![0, 0, 0, 0, 1, 0;
     -c, 0, c, 0, 0, 0;
     0, c, 0, c, 0, 0;
     0, 0, 0, 0, 0, 1;
     0, 1, 0, -1, 0, 0;
     1, 0, 1, 0, 0, 0]

noncomputable def eigvecsInv (c : ℝ) : Matrix (Fin 6) (Fin 6) ℝ :=
  !![0, -1 / (2 * c), 0, 0, 0, 1 / 2;
     0, 0, 1 / (2 * c), 0, 1 / 2, 0;
     0, 1 / (2 * c), 0, 0, 0, 1 / 2;
     0, 0, 1 / (2 * c), 0, -1 / 2, 0;
     1, 0, 0, 0, 0, 0;
     0, 0, 0, 1, 0, 0]

theorem realEigenbasis : RealEigenbasis := by
  intro C P U hc
  have hc0 : P.c ≠ 0 := hc.ne'
  refine ⟨eigvecs P.c, eigvecsInv P.c, ?_, ?_⟩
  · ext i j
    fin_cases i <;> fin_cases j <;>
      simp [eigvecs, eigvecsInv, Matrix.mul_apply, Fin.sum_univ_succ] <;> field_simp <;> ring
  · ext i j
    fin_cases i <;> fin_cases j <;>
      simp [eigvecs, jac, eig, gradVec, xFluxJacobianExprs, xFluxJacobianEigenExprs,
        Matrix.mul_apply, Fin.sum_univ_succ] <;> ring

theorem dissipationBound : DissipationBound := by
  intro CL CR UL UR P i
  fin_cases i <;> simp [eig, xFluxJacobianEigenExprs, xSpeedFamilyExprs]

/-! Similarity invariants used by the refutations: a real eigenbasis forces
`trace J = Σ λ` and `trace (J * J) = Σ λ²`. -/

theorem trace_eq_of_eigenbasis {n : Type*} [Fintype n] [DecidableEq n]
    {J R L D : Matrix n n ℝ}
    (hLR : L * R = 1) (hJ : J * R = R * D) : J.trace = D.trace := by
  have hRL : R * L = 1 := Matrix.mul_eq_one_comm.mp hLR
  have : J = R * D * L := by
    calc J = J * (R * L) := by rw [hRL, Matrix.mul_one]
      _ = R * D * L := by rw [← Matrix.mul_assoc, hJ]
  rw [this, Matrix.trace_mul_comm, ← Matrix.mul_assoc, hLR, Matrix.one_mul]

theorem trace_sq_eq_of_eigenbasis {n : Type*} [Fintype n] [DecidableEq n]
    {J R L D : Matrix n n ℝ}
    (hLR : L * R = 1) (hJ : J * R = R * D) : (J * J).trace = (D * D).trace := by
  have hJJ : (J * J) * R = R * (D * D) := by
    rw [Matrix.mul_assoc, hJ, ← Matrix.mul_assoc, hJ, Matrix.mul_assoc]
  exact trace_eq_of_eigenbasis hLR hJJ

end lsa_maxwell_1d
