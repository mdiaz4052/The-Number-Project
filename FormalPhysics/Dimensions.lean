import Mathlib.Data.Int.Basic
import Mathlib.Tactic.NormNum

/-!
# SI dimension vectors

Mathlib v4.33.1 contains the algebra needed below but no general physical-units or SI
dimension system. We therefore use the conventional seven-dimensional SI exponent vector.
The vector is a function into `ℤ`, so addition and subtraction are mathlib's pointwise
function operations rather than a reimplemented algebraic hierarchy.
-/

namespace TheNumberProject.FormalPhysics

/-- The seven conventional SI base dimensions. -/
inductive SIBaseDimension
  | mass
  | length
  | time
  | electricCurrent
  | temperature
  | amountOfSubstance
  | luminousIntensity
  deriving DecidableEq, Repr

/-- A physical dimension is an integer exponent for each SI base dimension. -/
abbrev Dimension := SIBaseDimension → ℤ

namespace Dimension

/-- Construct an SI dimension vector in `M, L, T, I, Theta, N, J` order. -/
def ofExponents (M L T I temperature amount luminousIntensity : ℤ) : Dimension
  | .mass => M
  | .length => L
  | .time => T
  | .electricCurrent => I
  | .temperature => temperature
  | .amountOfSubstance => amount
  | .luminousIntensity => luminousIntensity

def dimensionless : Dimension := ofExponents 0 0 0 0 0 0 0
def mass : Dimension := ofExponents 1 0 0 0 0 0 0
def length : Dimension := ofExponents 0 1 0 0 0 0 0
def time : Dimension := ofExponents 0 0 1 0 0 0 0
def temperature : Dimension := ofExponents 0 0 0 0 1 0 0

def velocity : Dimension := length - time
def acceleration : Dimension := length - 2 • time
def force : Dimension := mass + acceleration
def energy : Dimension := force + length
def entropy : Dimension := energy - temperature

def boltzmannConstant : Dimension := energy - temperature
def speedOfLight : Dimension := velocity
def reducedPlanckConstant : Dimension := energy + time
def gravitationalConstant : Dimension := ofExponents (-1) 3 (-2) 0 0 0 0

/-- `F * delta_x = temperature * delta_S` is dimensionally homogeneous. -/
theorem entropicWork_dimensionally_consistent :
    force + length = temperature + entropy := by
  funext d
  cases d <;>
    norm_num [force, acceleration, energy, entropy, mass, length, time, temperature,
      ofExponents]

/--
The entropy-displacement postulate is dimensionally homogeneous. Dimensionless factors
such as `2 * pi` do not appear in the exponent equation.
-/
theorem entropyDisplacement_dimensionally_consistent :
    entropy =
      (boltzmannConstant + mass + speedOfLight - reducedPlanckConstant) + length := by
  funext d
  cases d <;>
    norm_num [entropy, energy, force, acceleration, boltzmannConstant, mass, speedOfLight,
      velocity, reducedPlanckConstant, length, time, temperature, ofExponents]

/-- The adopted Unruh-temperature relation is dimensionally homogeneous. -/
theorem unruhTemperature_dimensionally_consistent :
    temperature =
      reducedPlanckConstant + acceleration - boltzmannConstant - speedOfLight := by
  funext d
  cases d <;>
    norm_num [reducedPlanckConstant, energy, force, acceleration, boltzmannConstant,
      speedOfLight, velocity, mass, length, time, temperature, ofExponents]

end Dimension
end TheNumberProject.FormalPhysics

