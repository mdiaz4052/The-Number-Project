# Lean/Python dimension contract

This note is the translation contract between the project's two deliberately small
dimension representations. It does **not** create a new units library, attach units to
numbers, or make either language parse the other. Its job is to make the shared meanings
visible enough that a future edit cannot silently change one side.

## Base dimensions and ordering

Every vector uses this conventional seven-position SI order:

| Position | Symbol | Meaning | Lean constructor |
|---:|---|---|---|
| 1 | `M` | mass | `SIBaseDimension.mass` |
| 2 | `L` | length | `SIBaseDimension.length` |
| 3 | `T` | time | `SIBaseDimension.time` |
| 4 | `I` | electric current | `SIBaseDimension.electricCurrent` |
| 5 | `Theta` | thermodynamic temperature | `SIBaseDimension.temperature` |
| 6 | `N` | amount of substance | `SIBaseDimension.amountOfSubstance` |
| 7 | `J` | luminous intensity | `SIBaseDimension.luminousIntensity` |

Here `J` names the conventional base-dimension slot for luminous intensity. It should
not be confused with the joule, whose energy vector appears below.

## The two representations

Lean's authoritative vocabulary is `FormalPhysics/Dimensions.lean`:

```text
Dimension := SIBaseDimension -> Int
```

In the source this is written with Lean's integer symbol `ℤ`. A named SI dimension such
as force has integer powers of the seven base dimensions. The function representation
lets mathlib supply pointwise addition, subtraction, and integer scalar multiplication.

Python's authoritative vocabulary is `Discovery/dimensions.py`:

```text
Dimension.exponents: tuple[Fraction, ...]
```

The tuple follows the same seven-position order, but its coefficients are exact rational
numbers. Python permits rational powers because a bounded search may try exponents such
as `1/2`. It uses `Fraction`, never floating-point numbers, for dimensional algebra.

The domains differ intentionally:

- Lean currently certifies the project's named SI vocabulary, whose base exponents are
  integers.
- Python also explores monomials with rational exponents, so its dimension components
  must be able to become rational after scalar multiplication.
- Every integer Lean vector embeds exactly into Python by replacing each integer with a
  `Fraction` having denominator one.

## Shared literal vectors

The following vectors are normative for names shared by the current project:

| Dimension | Vector in `M, L, T, I, Theta, N, J` order | Familiar form |
|---|---|---|
| dimensionless | `(0, 0, 0, 0, 0, 0, 0)` | `1` |
| mass | `(1, 0, 0, 0, 0, 0, 0)` | `M` |
| length | `(0, 1, 0, 0, 0, 0, 0)` | `L` |
| time | `(0, 0, 1, 0, 0, 0, 0)` | `T` |
| temperature | `(0, 0, 0, 0, 1, 0, 0)` | `Theta` |
| velocity | `(0, 1, -1, 0, 0, 0, 0)` | `L T^-1` |
| acceleration | `(0, 1, -2, 0, 0, 0, 0)` | `L T^-2` |
| area | `(0, 2, 0, 0, 0, 0, 0)` | `L^2` |
| force | `(1, 1, -2, 0, 0, 0, 0)` | `M L T^-2` |
| energy | `(1, 2, -2, 0, 0, 0, 0)` | `M L^2 T^-2` |
| gravitational constant | `(-1, 3, -2, 0, 0, 0, 0)` | `M^-1 L^3 T^-2` |

## Drift protection

The contract is guarded independently on both sides:

- Lean theorems `area_expands_to_SI_vector`, `force_expands_to_SI_vector`,
  `energy_expands_to_SI_vector`, and `gravitationalConstant_expands_to_SI_vector`
  compare the named dimensions with literal calls to `Dimension.ofExponents`. The Lean
  kernel checks them during `lake build`.
- `tests/test_dimensions.py` compares Python's `AREA`, `FORCE`, `ENERGY`, and
  `GRAVITATIONAL_CONSTANT` with literal `Dimension.from_mapping(...)` values using exact
  `Fraction` components.

These checks are intentionally paired rather than generated from one language into the
other. If a shared dimension is added or changed, update the Lean vocabulary, Python
vocabulary, this table, and literal tests together. A formula that only recomputes a
constant from itself is not an adequate drift check.
