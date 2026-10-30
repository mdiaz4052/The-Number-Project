/-!
# LSA-1 strengthened statements for `inviscid_burgers_1d`

Appended by `audit.py` to the pinned (possibly mutated) upstream file; not standalone.
The statements refer only to what the spec declares, so a mutated spec is judged by the
same propositions. Proofs first rewrite the scientific literal `0.0` to `0` with simprocs
disabled (see README, "Numeral hazard").
-/

namespace lsa_inviscid_burgers_1d

open inviscid_burgers_1d inviscid_burgers_1d_lax_friedrichs

noncomputable def jac (C : Coordinates) (P : Parameters) (U : State) : Matrix (Fin 1) (Fin 1) ℝ :=
  Matrix.of fun _ _ => (xFluxJacobianExprs C P U).flux_f.d_f

noncomputable def eig (C : Coordinates) (P : Parameters) (U : State) : Fin 1 → ℝ :=
  fun _ => (xFluxJacobianEigenExprs C P U).lambda1

/-- S1: the declared Jacobian is the derivative of the declared flux. -/
def JacobianIsDerivative : Prop :=
  ∀ (C : Coordinates) (P : Parameters) (U : State),
    HasDerivAt (fun s : ℝ => (xFluxExprs C P ⟨s⟩).flux_f) (jac C P U 0 0) U.f

/-- S2: the declared eigenvalues diagonalize the declared Jacobian over the reals. -/
def RealEigenbasis : Prop :=
  ∀ (C : Coordinates) (P : Parameters) (U : State),
    ∃ R L : Matrix (Fin 1) (Fin 1) ℝ, L * R = 1 ∧ R * L = 1 ∧
      jac C P U * R = R * Matrix.diagonal (eig C P U)

/-- S3: the Lax-Friedrichs dissipation speed dominates the declared eigenvalues at both states. -/
def DissipationBound : Prop :=
  ∀ (CL CR : Coordinates) (UL UR : State) (P : Parameters) (i : Fin 1),
    |eig CL P UL i| ≤ (xSpeedFamilyExprs CL CR UL UR P).speed2 ∧
    |eig CR P UR i| ≤ (xSpeedFamilyExprs CL CR UL UR P).speed2

theorem zero_lit : (0.0 : ℝ) = 0 := by norm_num

theorem jacobianIsDerivative : JacobianIsDerivative := by
  intro C P U
  have hj : jac C P U 0 0 = U.f := by
    set_option simprocs false in
      simp only [jac, Matrix.of_apply, xFluxJacobianExprs, zero_lit]
    ring
  have hf : (fun s : ℝ => (xFluxExprs C P ⟨s⟩).flux_f) = fun s => (1 / 2 : ℝ) * s * s := rfl
  rw [hf, hj]
  have h := ((hasDerivAt_id U.f).const_mul (1 / 2 : ℝ)).mul (hasDerivAt_id U.f)
  exact h.congr_deriv (by simp only [id]; ring)

theorem realEigenbasis : RealEigenbasis := by
  intro C P U
  refine ⟨1, 1, Matrix.one_mul 1, Matrix.one_mul 1, ?_⟩
  rw [Matrix.mul_one, Matrix.one_mul]
  ext i j
  fin_cases i
  fin_cases j
  set_option simprocs false in
    simp only [jac, eig, Matrix.of_apply, xFluxJacobianExprs, xFluxJacobianEigenExprs, zero_lit]
  simp [Matrix.diagonal, eig, xFluxJacobianEigenExprs]
  all_goals ring

theorem dissipationBound : DissipationBound := by
  intro CL CR UL UR P i
  simp [eig, xFluxJacobianEigenExprs, xSpeedFamilyExprs]

/-! Similarity invariants used by the refutations: a real eigenbasis forces
`trace J = Σ λ` and `trace (J * J) = Σ λ²`. -/

theorem trace_eq_of_eigenbasis {n : Type*} [Fintype n] [DecidableEq n]
    {J R L D : Matrix n n ℝ}
    (hLR : L * R = 1) (hRL : R * L = 1) (hJ : J * R = R * D) : J.trace = D.trace := by
  have : J = R * D * L := by
    calc J = J * (R * L) := by rw [hRL, Matrix.mul_one]
      _ = R * D * L := by rw [← Matrix.mul_assoc, hJ]
  rw [this, Matrix.trace_mul_comm, ← Matrix.mul_assoc, hLR, Matrix.one_mul]

theorem trace_sq_eq_of_eigenbasis {n : Type*} [Fintype n] [DecidableEq n]
    {J R L D : Matrix n n ℝ}
    (hLR : L * R = 1) (hRL : R * L = 1) (hJ : J * R = R * D) :
    (J * J).trace = (D * D).trace := by
  have hJJ : (J * J) * R = R * (D * D) := by
    rw [Matrix.mul_assoc, hJ, ← Matrix.mul_assoc, hJ, Matrix.mul_assoc]
  exact trace_eq_of_eigenbasis hLR hRL hJJ

end lsa_inviscid_burgers_1d
