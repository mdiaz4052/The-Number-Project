import Mathlib.Data.Real.Basic

/-!
# Scalar constants used by the entropic-gravity models

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

/--
The scalar constants used by the spherical-screen inverse-square model.

This extends `EntropicConstants` so the shared `k_B`, `c`, and `hbar` vocabulary is not
duplicated. The added field is only a real-valued scalar: equations (3.10)--(3.13),
nonzeroness, measured values, and physical interpretations remain explicit theorem inputs.
-/
structure InverseSquareConstants extends EntropicConstants where
  /-- The proportionality constant `G` introduced in Verlinde's equation (3.10). -/
  gravitationalConstant : ℝ

end TheNumberProject.FormalPhysics
