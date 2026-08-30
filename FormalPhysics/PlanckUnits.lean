import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Ring.Commute
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

/-!
# Symbolic Planck-unit controls

This module certifies four algebraic rearrangements used as positive controls by the
Python dimensional search. The inputs are the conventional squared definitions

* `planckLength ^ 2 = hbar * G / c ^ 3`,
* `planckMass ^ 2 = hbar * c / G`, and
* `planckTime ^ 2 = hbar * G / c ^ 5`.

Squaring records the usual positive-root Planck definitions without introducing
`Real.sqrt` proof machinery. Positivity hypotheses select the physical branch when a
proof compares two squares; otherwise they supply only the nonzero denominators that the
algebra cancels.

No measured or rounded decimal value occurs here. These theorems certify definitional
dependence: because the Planck-unit inputs already depend on `G`, recovering `G` from
them is a consistency control rather than an independent determination of `G`.
-/

namespace TheNumberProject.FormalPhysics

/--
From the squared definitions of Planck length and Planck mass, positive `G`, `c`,
`planckLength`, and `planckMass` imply `G = c^2 * planckLength / planckMass`.

The positivity assumptions select the positive solution after the proof equates two
squares. This is a dependent Planck-unit control, not an independent measurement or
derivation of the gravitational constant.
-/
theorem gravitationalConstant_eq_speedOfLight_sq_mul_planckLength_div_planckMass
    (gravitationalConstant speedOfLight reducedPlanckConstant planckLength planckMass : ℝ)
    (hGravitationalConstant : 0 < gravitationalConstant)
    (hSpeedOfLight : 0 < speedOfLight)
    (hPlanckLength : 0 < planckLength)
    (hPlanckMass : 0 < planckMass)
    (hPlanckLengthSquared :
      planckLength ^ 2 =
        reducedPlanckConstant * gravitationalConstant / speedOfLight ^ 3)
    (hPlanckMassSquared :
      planckMass ^ 2 =
        reducedPlanckConstant * speedOfLight / gravitationalConstant) :
    gravitationalConstant = speedOfLight ^ 2 * planckLength / planckMass := by
  have hPlanckLengthBalance :
      planckLength ^ 2 * speedOfLight ^ 3 =
        reducedPlanckConstant * gravitationalConstant := by
    calc
      planckLength ^ 2 * speedOfLight ^ 3 =
          (reducedPlanckConstant * gravitationalConstant / speedOfLight ^ 3) *
            speedOfLight ^ 3 := by rw [hPlanckLengthSquared]
      _ = reducedPlanckConstant * gravitationalConstant := by
        field_simp [pow_ne_zero 3 (ne_of_gt hSpeedOfLight)]
  have hPlanckMassBalance :
      planckMass ^ 2 * gravitationalConstant =
        reducedPlanckConstant * speedOfLight := by
    calc
      planckMass ^ 2 * gravitationalConstant =
          (reducedPlanckConstant * speedOfLight / gravitationalConstant) *
            gravitationalConstant := by rw [hPlanckMassSquared]
      _ = reducedPlanckConstant * speedOfLight := by
        field_simp [ne_of_gt hGravitationalConstant]
  have hSquares :
      (gravitationalConstant * planckMass) ^ 2 =
        (speedOfLight ^ 2 * planckLength) ^ 2 := by
    calc
      (gravitationalConstant * planckMass) ^ 2 =
          gravitationalConstant * (planckMass ^ 2 * gravitationalConstant) := by ring
      _ = gravitationalConstant * (reducedPlanckConstant * speedOfLight) := by
        rw [hPlanckMassBalance]
      _ = speedOfLight * (reducedPlanckConstant * gravitationalConstant) := by ring
      _ = speedOfLight * (planckLength ^ 2 * speedOfLight ^ 3) := by
        rw [← hPlanckLengthBalance]
      _ = (speedOfLight ^ 2 * planckLength) ^ 2 := by ring
  apply (eq_div_iff (ne_of_gt hPlanckMass)).2
  rcases (sq_eq_sq_iff_eq_or_eq_neg).mp hSquares with hPositive | hNegative
  · exact hPositive
  · nlinarith [mul_pos hGravitationalConstant hPlanckMass,
      mul_pos (pow_pos hSpeedOfLight 2) hPlanckLength]

/--
The squared Planck-mass definition `planckMass^2 = hbar * c / G`, together with positive
`G` and `planckMass`, rearranges to `G = hbar * c / planckMass^2`.

Positivity is used only to justify the two cancelled denominators. Since Planck mass was
defined using `G`, the result is an algebraic control and supplies no independent physical
evidence for the value of `G`.
-/
theorem gravitationalConstant_eq_reducedPlanckConstant_mul_speedOfLight_div_planckMass_sq
    (gravitationalConstant speedOfLight reducedPlanckConstant planckMass : ℝ)
    (hGravitationalConstant : 0 < gravitationalConstant)
    (hPlanckMass : 0 < planckMass)
    (hPlanckMassSquared :
      planckMass ^ 2 =
        reducedPlanckConstant * speedOfLight / gravitationalConstant) :
    gravitationalConstant =
      reducedPlanckConstant * speedOfLight / planckMass ^ 2 := by
  have hPlanckMassBalance :
      planckMass ^ 2 * gravitationalConstant =
        reducedPlanckConstant * speedOfLight := by
    calc
      planckMass ^ 2 * gravitationalConstant =
          (reducedPlanckConstant * speedOfLight / gravitationalConstant) *
            gravitationalConstant := by rw [hPlanckMassSquared]
      _ = reducedPlanckConstant * speedOfLight := by
        field_simp [ne_of_gt hGravitationalConstant]
  apply (eq_div_iff (pow_ne_zero 2 (ne_of_gt hPlanckMass))).2
  calc
    gravitationalConstant * planckMass ^ 2 =
        planckMass ^ 2 * gravitationalConstant := by ring
    _ = reducedPlanckConstant * speedOfLight := hPlanckMassBalance

/--
From the squared definitions of Planck time and Planck mass, positive `G`, `c`,
`planckTime`, and `planckMass` imply `G = c^3 * planckTime / planckMass`.

The positivity assumptions select the positive branch after comparing squares. Because
both Planck-unit definitions already contain `G`, this theorem checks their algebraic
compatibility rather than independently determining the gravitational constant.
-/
theorem gravitationalConstant_eq_speedOfLight_cubed_mul_planckTime_div_planckMass
    (gravitationalConstant speedOfLight reducedPlanckConstant planckTime planckMass : ℝ)
    (hGravitationalConstant : 0 < gravitationalConstant)
    (hSpeedOfLight : 0 < speedOfLight)
    (hPlanckTime : 0 < planckTime)
    (hPlanckMass : 0 < planckMass)
    (hPlanckTimeSquared :
      planckTime ^ 2 =
        reducedPlanckConstant * gravitationalConstant / speedOfLight ^ 5)
    (hPlanckMassSquared :
      planckMass ^ 2 =
        reducedPlanckConstant * speedOfLight / gravitationalConstant) :
    gravitationalConstant = speedOfLight ^ 3 * planckTime / planckMass := by
  have hPlanckTimeBalance :
      planckTime ^ 2 * speedOfLight ^ 5 =
        reducedPlanckConstant * gravitationalConstant := by
    calc
      planckTime ^ 2 * speedOfLight ^ 5 =
          (reducedPlanckConstant * gravitationalConstant / speedOfLight ^ 5) *
            speedOfLight ^ 5 := by rw [hPlanckTimeSquared]
      _ = reducedPlanckConstant * gravitationalConstant := by
        field_simp [pow_ne_zero 5 (ne_of_gt hSpeedOfLight)]
  have hPlanckMassBalance :
      planckMass ^ 2 * gravitationalConstant =
        reducedPlanckConstant * speedOfLight := by
    calc
      planckMass ^ 2 * gravitationalConstant =
          (reducedPlanckConstant * speedOfLight / gravitationalConstant) *
            gravitationalConstant := by rw [hPlanckMassSquared]
      _ = reducedPlanckConstant * speedOfLight := by
        field_simp [ne_of_gt hGravitationalConstant]
  have hSquares :
      (gravitationalConstant * planckMass) ^ 2 =
        (speedOfLight ^ 3 * planckTime) ^ 2 := by
    calc
      (gravitationalConstant * planckMass) ^ 2 =
          gravitationalConstant * (planckMass ^ 2 * gravitationalConstant) := by ring
      _ = gravitationalConstant * (reducedPlanckConstant * speedOfLight) := by
        rw [hPlanckMassBalance]
      _ = speedOfLight * (reducedPlanckConstant * gravitationalConstant) := by ring
      _ = speedOfLight * (planckTime ^ 2 * speedOfLight ^ 5) := by
        rw [← hPlanckTimeBalance]
      _ = (speedOfLight ^ 3 * planckTime) ^ 2 := by ring
  apply (eq_div_iff (ne_of_gt hPlanckMass)).2
  rcases (sq_eq_sq_iff_eq_or_eq_neg).mp hSquares with hPositive | hNegative
  · exact hPositive
  · nlinarith [mul_pos hGravitationalConstant hPlanckMass,
      mul_pos (pow_pos hSpeedOfLight 3) hPlanckTime]

/--
The squared Planck-length definition `planckLength^2 = hbar * G / c^3`, together with
positive `c` and `hbar`, rearranges to `G = c^3 * planckLength^2 / hbar`.

Only the nonzero denominators require positivity here; no square-root branch is selected
because the conclusion still contains `planckLength^2`. The identity remains a dependent
control because Planck length was defined using `G`.
-/
theorem gravitationalConstant_eq_speedOfLight_cubed_mul_planckLength_sq_div_reducedPlanckConstant
    (gravitationalConstant speedOfLight reducedPlanckConstant planckLength : ℝ)
    (hSpeedOfLight : 0 < speedOfLight)
    (hReducedPlanckConstant : 0 < reducedPlanckConstant)
    (hPlanckLengthSquared :
      planckLength ^ 2 =
        reducedPlanckConstant * gravitationalConstant / speedOfLight ^ 3) :
    gravitationalConstant =
      speedOfLight ^ 3 * planckLength ^ 2 / reducedPlanckConstant := by
  have hPlanckLengthBalance :
      planckLength ^ 2 * speedOfLight ^ 3 =
        reducedPlanckConstant * gravitationalConstant := by
    calc
      planckLength ^ 2 * speedOfLight ^ 3 =
          (reducedPlanckConstant * gravitationalConstant / speedOfLight ^ 3) *
            speedOfLight ^ 3 := by rw [hPlanckLengthSquared]
      _ = reducedPlanckConstant * gravitationalConstant := by
        field_simp [pow_ne_zero 3 (ne_of_gt hSpeedOfLight)]
  apply (eq_div_iff (ne_of_gt hReducedPlanckConstant)).2
  calc
    gravitationalConstant * reducedPlanckConstant =
        reducedPlanckConstant * gravitationalConstant := by ring
    _ = planckLength ^ 2 * speedOfLight ^ 3 := hPlanckLengthBalance.symm
    _ = speedOfLight ^ 3 * planckLength ^ 2 := by ring

end TheNumberProject.FormalPhysics
