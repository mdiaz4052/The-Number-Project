import FormalPhysics.Constants
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Conditional algebraic core of a Verlinde-style argument

The hypotheses mirror equations (3.6), (3.7), and (3.8) in:

Erik P. Verlinde, *On the Origin of Gravity and the Laws of Newton*,
arXiv:1001.0785 (2010), https://arxiv.org/abs/1001.0785.

The result below is deliberately conditional. The entropy-displacement relation and the
entropic-force relation are model inputs. The Unruh temperature is a quantum-field-theory
relation whose use as the screen temperature is also an input to this model. Lean verifies
only that the stated real-number equations imply the conclusion.
-/

namespace TheNumberProject.EntropicGravity

open TheNumberProject.FormalPhysics

/--
Given the three stated Verlinde-style relations and the nonzero quantities needed for
cancellation, the scalar relation `F = m * a` follows.

The equations remain explicit hypotheses rather than fields hidden in a definition:

* `hEntropicWork`: `F * delta_x = temperature * delta_S`;
* `hEntropyDisplacement`:
  `delta_S = (2 * pi * k_B * m * c / hbar) * delta_x`;
* `hUnruhTemperature`: `temperature = hbar * a / (2 * pi * k_B * c)`.
-/
theorem force_eq_mass_mul_acceleration
    (constants : EntropicConstants)
    (F deltaX temperature deltaS mass acceleration : ℝ)
    (hDeltaX : deltaX ≠ 0)
    (hBoltzmann : constants.boltzmannConstant ≠ 0)
    (hLightSpeed : constants.speedOfLight ≠ 0)
    (hReducedPlanck : constants.reducedPlanckConstant ≠ 0)
    (hEntropicWork : F * deltaX = temperature * deltaS)
    (hEntropyDisplacement :
      deltaS =
        (2 * Real.pi * constants.boltzmannConstant * mass * constants.speedOfLight /
          constants.reducedPlanckConstant) * deltaX)
    (hUnruhTemperature :
      temperature =
        constants.reducedPlanckConstant * acceleration /
          (2 * Real.pi * constants.boltzmannConstant * constants.speedOfLight)) :
    F = mass * acceleration := by
  apply mul_right_cancel₀ hDeltaX
  calc
    F * deltaX = temperature * deltaS := hEntropicWork
    _ =
        (constants.reducedPlanckConstant * acceleration /
            (2 * Real.pi * constants.boltzmannConstant * constants.speedOfLight)) *
          ((2 * Real.pi * constants.boltzmannConstant * mass * constants.speedOfLight /
              constants.reducedPlanckConstant) * deltaX) := by
        rw [hUnruhTemperature, hEntropyDisplacement]
    _ = (mass * acceleration) * deltaX := by
        field_simp [hBoltzmann, hLightSpeed, hReducedPlanck, Real.pi_ne_zero] <;>
          ring

end TheNumberProject.EntropicGravity

