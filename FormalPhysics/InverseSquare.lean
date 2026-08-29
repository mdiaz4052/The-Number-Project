import FormalPhysics.Verlinde
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.Ring

/-!
# Conditional inverse-square derivation

This module formalizes the scalar algebra in §3.2 of Erik Verlinde,
*On the Origin of Gravity and the Laws of Newton*, arXiv:1001.0785v1.

Every physical relation remains a named hypothesis. In particular, equation (3.10)
introduces `G` as the area-to-information proportionality constant before the paper
identifies it with Newton's gravitational constant. Lean checks the implication between
the equations; it does not establish the holographic-screen model, equipartition,
mass-energy equivalence, the entropy postulate, or the physical interpretation of `G`.

Unlike the Milestone 1 argument for `F = m * a`, this derivation deliberately does not use
the Unruh-temperature relation: the original paper explicitly sets it aside in §3.2.
-/

namespace TheNumberProject.EntropicGravity

open TheNumberProject.FormalPhysics

/--
Equations (3.6), (3.7), and (3.10)--(3.12), together with spherical area, imply the
inverse-square scalar relation.

The nonzero side conditions are limited to quantities cancelled by the proof or used as
denominators: `deltaX`, `c`, `hbar`, `G`, and `radius`. No nonzero premise is placed on
either mass, force, entropy change, temperature, bit count, area, or energy. Boltzmann's
constant also need not be cancelled: it remains on both sides of an intermediate
cross-multiplied equality.
-/
theorem force_eq_gravitationalConstant_mul_masses_div_radius_sq
    (constants : InverseSquareConstants)
    (force deltaX deltaS temperature bitCount area energy radius sourceMass testMass : ℝ)
    (hDeltaX : deltaX ≠ 0)
    (hLightSpeed : constants.speedOfLight ≠ 0)
    (hReducedPlanck : constants.reducedPlanckConstant ≠ 0)
    (hGravitationalConstant : constants.gravitationalConstant ≠ 0)
    (hRadius : radius ≠ 0)
    (hEntropyDisplacement :
      deltaS =
        (2 * Real.pi * constants.boltzmannConstant * testMass * constants.speedOfLight /
          constants.reducedPlanckConstant) * deltaX)
    (hEntropicWork : force * deltaX = temperature * deltaS)
    (hBitCount :
      bitCount =
        area * constants.speedOfLight ^ 3 /
          (constants.gravitationalConstant * constants.reducedPlanckConstant))
    (hEquipartition :
      energy = (1 / 2 : ℝ) * bitCount * constants.boltzmannConstant * temperature)
    (hMassEnergy : energy = sourceMass * constants.speedOfLight ^ 2)
    (hSphericalArea : area = 4 * Real.pi * radius ^ 2) :
    force = constants.gravitationalConstant * sourceMass * testMass / radius ^ 2 := by
  have hForceFromTemperature :
      force =
        temperature *
          (2 * Real.pi * constants.boltzmannConstant * testMass *
            constants.speedOfLight / constants.reducedPlanckConstant) := by
    apply mul_right_cancel₀ hDeltaX
    calc
      force * deltaX = temperature * deltaS := hEntropicWork
      _ =
          temperature *
            ((2 * Real.pi * constants.boltzmannConstant * testMass *
                constants.speedOfLight / constants.reducedPlanckConstant) * deltaX) := by
            rw [hEntropyDisplacement]
      _ =
          (temperature *
              (2 * Real.pi * constants.boltzmannConstant * testMass *
                constants.speedOfLight / constants.reducedPlanckConstant)) * deltaX := by
            ring

  have hEquipartitionExpanded := hEquipartition
  rw [hMassEnergy, hBitCount, hSphericalArea] at hEquipartitionExpanded
  field_simp [hGravitationalConstant, hReducedPlanck] at hEquipartitionExpanded

  have hScreenTemperatureBalance :
      2 * Real.pi * radius ^ 2 * constants.speedOfLight *
          constants.boltzmannConstant * temperature =
        constants.gravitationalConstant * constants.reducedPlanckConstant * sourceMass := by
    apply mul_right_cancel₀ (pow_ne_zero 2 hLightSpeed)
    nlinarith [hEquipartitionExpanded]

  rw [hForceFromTemperature]
  field_simp [hReducedPlanck, hRadius]
  linear_combination testMass * hScreenTemperatureBalance

/--
If the already established `F = m * a` relation and the inverse-square force relation
hold for the same nonzero test mass, cancelling that mass yields the acceleration law.
This is only a composition of two explicit algebraic inputs and does not independently
validate either one.
-/
theorem acceleration_eq_gravitationalConstant_mul_sourceMass_div_radius_sq
    (gravitationalConstant force sourceMass testMass radius acceleration : ℝ)
    (hTestMass : testMass ≠ 0)
    (hForceMassAcceleration : force = testMass * acceleration)
    (hInverseSquare :
      force = gravitationalConstant * sourceMass * testMass / radius ^ 2) :
    acceleration = gravitationalConstant * sourceMass / radius ^ 2 := by
  apply mul_left_cancel₀ hTestMass
  calc
    testMass * acceleration = force := hForceMassAcceleration.symm
    _ = gravitationalConstant * sourceMass * testMass / radius ^ 2 := hInverseSquare
    _ = testMass * (gravitationalConstant * sourceMass / radius ^ 2) := by ring

/--
Within the selected monomial `G^alpha * M^beta * m^gamma * R^delta`, matching the mass,
length, and time exponents of force fixes `alpha = 1`, `delta = -2`, and only the sum
`beta + gamma = 2`. This is an exact statement about that model and generator set, not a
claim that dimensional analysis forces nature to obey Newtonian gravity.
-/
theorem force_dimension_exponent_constraints
    (alpha beta gamma delta : ℚ)
    (hMassExponent : -alpha + beta + gamma = 1)
    (hLengthExponent : 3 * alpha + delta = 1)
    (hTimeExponent : -2 * alpha = -2) :
    alpha = 1 ∧ delta = -2 ∧ beta + gamma = 2 := by
  constructor
  · linarith
  constructor <;> linarith

/--
Adding the independent scaling premise `gamma = 1` (linearity in the test mass) selects
the unique exponent tuple `(1, 1, 1, -2)` within the same four-factor monomial model.
The scaling premise is not a consequence of dimensional analysis.
-/
theorem force_dimension_exponents_unique_of_testMass_linear
    (alpha beta gamma delta : ℚ)
    (hMassExponent : -alpha + beta + gamma = 1)
    (hLengthExponent : 3 * alpha + delta = 1)
    (hTimeExponent : -2 * alpha = -2)
    (hTestMassLinear : gamma = 1) :
    (alpha, beta, gamma, delta) = (1, 1, 1, -2) := by
  rcases force_dimension_exponent_constraints alpha beta gamma delta hMassExponent
      hLengthExponent hTimeExponent with ⟨hAlpha, hDelta, hMassSum⟩
  have hBeta : beta = 1 := by linarith
  simp [hAlpha, hBeta, hTestMassLinear, hDelta]

end TheNumberProject.EntropicGravity
