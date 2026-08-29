import Mathlib.Data.Real.Basic

/-!
# Scalar constants used by the first entropic-gravity model

This file supplies a mathematical representation, not physical laws. Grouping the three
constants into a structure keeps theorem signatures readable without placing any of the
model's equations inside a definition.
-/

namespace TheNumberProject.FormalPhysics

/--
The scalar constants appearing in the Milestone 1 algebraic model.

The fields are real-valued magnitudes in a mutually consistent unit system. The structure
does not assert their measured SI values, nonzeroness, or any physical relationship.
-/
structure EntropicConstants where
  /-- Boltzmann constant, conventionally written `k_B`. -/
  boltzmannConstant : ℝ
  /-- Speed of light in vacuum, conventionally written `c`. -/
  speedOfLight : ℝ
  /-- Reduced Planck constant, conventionally written `hbar`. -/
  reducedPlanckConstant : ℝ
  deriving Repr

end TheNumberProject.FormalPhysics

