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
def informationCount : Dimension := dimensionless

def velocity : Dimension := length - time
def acceleration : Dimension := length - 2 • time
def area : Dimension := 2 • length
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

/-- `A = 4 * pi * R^2` is homogeneous; `4 * pi` is dimensionless. -/
theorem sphericalArea_dimensionally_consistent :
    area = 2 • length := by
  funext d
  cases d <;> norm_num [area, length, ofExponents]

/-- `N = A * c^3 / (G * hbar)` gives a dimensionless information count. -/
theorem holographicBitCount_dimensionally_consistent :
    informationCount =
      area + 3 • speedOfLight - gravitationalConstant - reducedPlanckConstant := by
  funext d
  cases d <;>
    norm_num [informationCount, dimensionless, area, speedOfLight, velocity,
      gravitationalConstant, reducedPlanckConstant, energy, force, acceleration, mass,
      length, time, ofExponents]

/-- `E = (1 / 2) * N * k_B * T` is homogeneous; `1 / 2` is dimensionless. -/
theorem equipartition_dimensionally_consistent :
    energy = informationCount + boltzmannConstant + temperature := by
  funext d
  cases d <;>
    norm_num [energy, force, acceleration, informationCount, dimensionless,
      boltzmannConstant, mass, length, time, temperature, ofExponents]

/-- The model input `E = M * c^2` is dimensionally homogeneous. -/
theorem massEnergy_dimensionally_consistent :
    energy = mass + 2 • speedOfLight := by
  funext d
  cases d <;>
    norm_num [energy, force, acceleration, mass, speedOfLight, velocity, length, time,
      temperature, ofExponents]

/-- `F = G * M * m / R^2` is dimensionally homogeneous. -/
theorem inverseSquareForce_dimensionally_consistent :
    force = gravitationalConstant + mass + mass - 2 • length := by
  funext d
  cases d <;>
    norm_num [force, acceleration, gravitationalConstant, mass, length, time, ofExponents]

end Dimension
end TheNumberProject.FormalPhysics
