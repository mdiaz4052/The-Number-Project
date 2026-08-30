# Dependency-aware candidate analysis

Milestone 3 asks a more careful question than the original bounded search:

> After an expression has the right units for `G`, what exact definitions does it use,
> which other expressions are merely different spellings of the same algebra, and what
> kind of certification—if any—does it have?

The resulting pipeline is:

```text
dimensions -> candidates -> dependency expansion -> equivalence groups
           -> certification status -> cautious interpretation
```

Each arrow adds information. None turns a symbolic candidate into an experiment.

## 1. Matching units is only the first filter

Newton's gravitational constant has SI dimension

```text
[G] = M^-1 L^3 T^-2.
```

The bounded search keeps a monomial only when its seven-component SI exponent vector
matches this vector exactly. That rejects expressions with incompatible units, which is
useful. It does not show that every survivor has the same meaning, origin, or physical
role as `G`.

An analogy is that two boxes can have the same external dimensions while containing
different objects. Units describe the dimensional shape of a formula, not everything
inside it.

## 2. Four ledgers that must remain separate

| Ledger | Question answered | What it does not answer |
|---|---|---|
| SI dimensions | Do the units match `G`? | Is the expression algebraically or physically `G`? |
| Registered definitions | Which atomic symbols remain after exact substitution? | Are the catalog endpoints fundamentally independent? |
| Numerical values | How large is the tabulated decimal ratio to measured `G`? | Is there an exact identity or law? |
| Certification | Is a corresponding identity linked to a compiled Lean theorem? | Are the theorem's premises physically true? |

Floating-point closeness never controls dependency, equivalence, or certification.

## 3. The dependency catalog

The current model stops expansion at

```text
G, c, hbar, k_B, m_e, m_p, m_u.
```

These are called **atomic within this catalog**. Here, “atomic” means only “the catalog
does not replace this symbol with another formula.” It does not mean metaphysically
fundamental, causally primitive, or experimentally independent.

The four conventional Planck definitions are registered with exact rational exponents:

```math
\ell_P=\hbar^{1/2}G^{1/2}c^{-3/2},
```

```math
m_P=\hbar^{1/2}c^{1/2}G^{-1/2},
```

```math
t_P=\hbar^{1/2}G^{1/2}c^{-5/2},
```

```math
T_P=\hbar^{1/2}c^{5/2}G^{-1/2}k_B^{-1}.
```

The catalog validates each definition against the existing exact SI dimension vector.
It also rejects duplicate keys or factors, inexact exponents, zero-power clutter,
unknown references, cycles, missing generator coverage, and dimensionally inconsistent
definitions.

The symbolic definitions are exact within this model. The separately tabulated decimal
Planck values are rounded and play no role in the substitution.

## 4. Exact exponent substitution

A surface expression is stored as a map from factor names to rational powers. Expansion
multiplies each registered definition by the surface power, adds like-symbol exponents,
and deletes exact zeros.

For example,

```math
c^2\ell_Pm_P^{-1}
```

expands to

```math
c^2
(\hbar^{1/2}G^{1/2}c^{-3/2})
(\hbar^{-1/2}c^{-1/2}G^{1/2}).
```

The `c` and `hbar` powers cancel and the two half-powers of `G` add:

```text
c:     2 - 3/2 - 1/2 = 0
hbar:  1/2 - 1/2     = 0
G:     1/2 + 1/2     = 1
```

The expanded signature is therefore exactly `G^1`.

Changing `m_P` to proton mass `m_p` gives a different result:

```math
c^2\ell_Pm_p^{-1}
=G^{1/2}c^{1/2}\hbar^{1/2}m_p^{-1}.
```

It contains `G^(1/2)` plus other atoms. It inherits `G`; it does not reconstruct `G`.

By contrast,

```math
\hbar c m_p^{-2}
```

contains no registered `G` power at all. That is a catalog-relative algebraic fact, not
evidence that the expression independently measures or explains gravity.

## 5. Dependency statuses

| Status | Exact meaning |
|---|---|
| `target_reconstruction` | The complete expanded signature is exactly `G^1`. |
| `target_dependent` | A nonzero power of `G` remains, but the expression is not exactly `G`. |
| `no_registered_target_dependency` | Complete expansion leaves `G^0` under the current catalog. |
| `unresolved_provenance` | At least one factor cannot be fully expanded by the catalog. |

The longer phrase `no_registered_target_dependency` is intentional. Shortening it to
“independent” would claim more than the computation knows.

Certification is recorded separately:

| Status | Exact meaning |
|---|---|
| `lean_certified` | A linked theorem declaration checks the corresponding exact identity. |
| `exact_python_reduction_only` | Exact registered substitution reaches `G`, but no linked Lean theorem covers this surface signature. |
| `not_applicable` | The expression is not an exact target reconstruction requiring this identity certification. |

## 6. Six reconstructions, four Lean certificates

The default 21 candidates contain six exact target reconstructions:

```text
c^2 * l_P * m_P^-1
c * hbar * m_P^-2
c^3 * m_P^-1 * t_P
c^3 * hbar^-1 * l_P^2
l_P^3 * m_P^-1 * t_P^-2
hbar^2 * l_P^-1 * m_P^-3
```

The first four are linked to declarations in `FormalPhysics/PlanckUnits.lean`; they are
`lean_certified`. The last two are exact consequences of the same registered exponent
definitions but currently have `exact_python_reduction_only` status.

This distinction is not a ranking of physical truth. All six use Planck quantities whose
definitions already contain `G`. They are dependent consistency checks, not six
measurements or six noncircular derivations of `G`.

## 7. Definitional-equivalence groups

Two candidates are placed in the same group exactly when their fully expanded signatures
are identical. They are not grouped because their SI dimensions match—all 21 already
pass that weaker condition—or because their rounded decimal ratios happen to be close.

For example, these three proton expressions form one exact group:

```text
c^2 * l_P * m_p^-1
c^3 * t_P * m_p^-1
l_P^3 * t_P^-2 * m_p^-1
```

Each expands to

```math
G^{1/2}c^{1/2}\hbar^{1/2}m_p^{-1}.
```

Corresponding three-member groups occur for `m_e` and `m_u`. Across the full default
search, 21 surface expressions collapse into 10 exact definitional-equivalence groups.
The group identifiers are deterministic hashes of canonical exact signatures, so
regeneration does not depend on discovery order or decimal values.

## 8. Numerical proximity remains a separate observation

The original candidate record is retained in the new JSON artifact, including SI value,
ratio to measured `G`, logarithmic distance, ranking score, classification, and
assessment. Those fields keep their original navigation purpose.

The dependency layer never asks whether two floats are close. In particular, rounded
Planck values can produce a ratio near—but not exactly equal to—one while exact symbolic
substitution still produces an identity. Conversely, a striking numerical coincidence
would not create an identity if the exact signatures differ.

## 9. Rank, nullity, and dimensional ambiguity

The complete default generator order is

```text
c, hbar, k_B, m_e, m_p, m_u, l_P, m_P, t_P, T_P.
```

Solving their exact dimension matrix against `[G]` gives:

```text
status:  affine
rank:    4
nullity: 6
```

**Rank 4** means that these generator columns span four independent directions in the
seven-slot SI dimension space. **Nullity 6** means that six independent changes to the
ten exponents leave the total dimension unchanged.

Every nullspace direction therefore describes a dimensionless multiplier. The displayed
deterministic basis includes familiar mass swaps:

```text
m_p / m_e
m_u / m_e
m_P / m_e
```

Multiplying any solution by an arbitrary power of such a ratio cannot change its units.
That is why dimensional information cannot choose one unique formula from this catalog.

A nullspace **basis** is not unique: different sets of six independent directions can
span the same nullspace. The nullspace itself, for the fixed dimension matrix, is the
invariant fact.

This does not prove that nature is underdetermined. It proves that the answer is
underdetermined by the stated dimensional information.

## 10. What Milestone 3 has established

The milestone establishes, within its declared models:

- which bounded monomials exactly match the SI dimensions of `G`;
- the exact registered atomic signature of each candidate;
- which surface formulas are definitionally equivalent;
- which candidates reconstruct, depend on, or have no registered dependence on `G`;
- which four reconstruction identities have linked Lean certificates; and
- the exact rank, nullity, RREF, particular solution, and nullspace basis of the default
  dimensional system.

It has not established:

- a measured value of `G`;
- the physical truth of Newtonian, entropic-gravity, holographic, or equipartition
  premises;
- that any catalog atom is fundamentally or experimentally independent;
- a unique physical formula selected by nature; or
- a noncircular physical origin for the strength of gravity.

## 11. The remaining physical problem after Lean

“Physically establish `G`” can mean two different things, and they should not be blended.

### A. Determine `G` experimentally

An experimental determination needs more than a correct algebraic rearrangement:

1. **Operational model:** specify how measured positions, times, masses, forces, or other
   observables depend on `G` within a stated gravitational model.
2. **Independent observations:** collect data from physical apparatus rather than from
   quantities whose definitions already import the target value.
3. **Calibration and traceability:** connect every instrument and input quantity to
   documented measurement standards.
4. **Uncertainty model:** propagate statistical uncertainty, systematic effects,
   environmental influences, geometry corrections, and model approximations.
5. **Inference:** estimate `G` from the observations under the explicit model, without
   treating a `G`-derived Planck quantity as independent evidence.
6. **Reproducibility:** obtain compatible results across repeated runs and, more
   importantly, independent apparatus or measurement principles.

This would establish an empirical value of the model parameter in a specified unit
system and regime. It would not by itself explain why gravity has that strength.

### B. Explain or derive the gravitational coupling

A noncircular physical explanation has a stronger burden:

1. begin from premises and empirical inputs whose provenance does not already contain
   `G`, directly or through a derived quantity;
2. show how an effective gravitational coupling and the appropriate low-energy or
   large-distance behavior follow from that structure;
3. connect the result to operational observables and a declared unit convention;
4. produce falsifiable consequences that are not merely algebraic rewritings of the
   definitions; and
5. survive comparison with experiment.

Because the numerical value of a dimensionful constant changes when units change, a
deeper explanation must make clear which observable, unit convention, or dimensionless
comparison carries the physical content. Merely reconstructing the SI dimensions or
rewriting a Planck definition cannot meet that burden.

Lean could eventually certify a chain such as “given this measurement model, these
calibration bounds, and these observations, `G` lies in this interval,” or could verify
the mathematical consequences of a deeper theory. Lean still cannot generate the
observations, calibrate the apparatus, or prove that empirical premises describe nature.
That is the precise post-Lean boundary: formal proof can secure the inference; physical
work must secure the premises.

## 12. Code map and commands

| Purpose | Location |
|---|---|
| Immutable exact dependency catalog | `Discovery/dependency_definitions.py` |
| Expansion, statuses, grouping, and dimensional-system report | `Discovery/dependency_analysis.py` |
| Four linked Lean identity declarations | `FormalPhysics/PlanckUnits.lean` |
| Deterministic machine-readable result | `Experiments/GCoincidences/dependency_analysis.json` |
| Focused validation | `tests/test_dependency_definitions.py`, `tests/test_dependency_analysis.py` |

From the repository root:

```bash
python3 -m Discovery.dependency_analysis
python3 -m Discovery.dependency_analysis --check
python3 -m unittest discover -s tests -v
lake build --wfail
```

Python does not parse Lean source. The small Planck identity catalog supplies the four
fully qualified theorem names, while the Lean build remains authoritative for whether
those declarations compile and pass the proof audit.
