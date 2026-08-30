import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring

/-!
# Conditional inverse-square estimator certification

This module checks the algebraic rearrangement used by the physical-bridge estimator.
It is independent of any particular derivation of the inverse-square relation: that
relation remains an explicit hypothesis.

The theorems do not establish that an apparatus obeys the relation, that any input was
observed or calibrated, that an uncertainty model is complete, or that an estimate of
Newton's gravitational constant has been produced. They certify only the implication
from the stated real-number equalities and nonzero denominator conditions.
-/

namespace TheNumberProject.FormalPhysics

/--
If an inverse-square scalar relation holds and both masses and the separation are
nonzero, its standard estimator expression equals the supplied gravitational constant.

No nonzero hypothesis on the gravitational constant or force is needed. This is a
conditional field rearrangement, not an empirical measurement or validation of the
inverse-square model.
-/
theorem force_mul_radius_sq_div_masses_eq_gravitationalConstant
    (gravitationalConstant force massOne massTwo radius : ℝ)
    (hMassOne : massOne ≠ 0)
    (hMassTwo : massTwo ≠ 0)
    (hRadius : radius ≠ 0)
    (hInverseSquare :
      force = gravitationalConstant * massOne * massTwo / radius ^ 2) :
    force * radius ^ 2 / (massOne * massTwo) = gravitationalConstant := by
  have hInverseSquareBalance :
      force * radius ^ 2 = gravitationalConstant * massOne * massTwo :=
    (eq_div_iff (pow_ne_zero 2 hRadius)).mp hInverseSquare
  symm
  apply (eq_div_iff (mul_ne_zero hMassOne hMassTwo)).2
  calc
    gravitationalConstant * (massOne * massTwo) =
        gravitationalConstant * massOne * massTwo := by ring
    _ = force * radius ^ 2 := hInverseSquareBalance.symm

/--
If `gravitationalConstantEstimate` is defined by the inverse-square estimator and the
corresponding inverse-square relation holds for nonzero masses and separation, then the
estimate equals the supplied gravitational constant.

The estimator definition and physical relation are separate named hypotheses so the
theorem cannot hide either premise inside a definition.
-/
theorem inverseSquareEstimator_eq_gravitationalConstant
    (gravitationalConstant gravitationalConstantEstimate force massOne massTwo radius : ℝ)
    (hMassOne : massOne ≠ 0)
    (hMassTwo : massTwo ≠ 0)
    (hRadius : radius ≠ 0)
    (hInverseSquare :
      force = gravitationalConstant * massOne * massTwo / radius ^ 2)
    (hEstimatorDefinition :
      gravitationalConstantEstimate =
        force * radius ^ 2 / (massOne * massTwo)) :
    gravitationalConstantEstimate = gravitationalConstant := by
  calc
    gravitationalConstantEstimate =
        force * radius ^ 2 / (massOne * massTwo) := hEstimatorDefinition
    _ = gravitationalConstant :=
      force_mul_radius_sq_div_masses_eq_gravitationalConstant
        gravitationalConstant force massOne massTwo radius
        hMassOne hMassTwo hRadius hInverseSquare

end TheNumberProject.FormalPhysics
