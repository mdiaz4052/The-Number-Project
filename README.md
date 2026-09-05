# The Number Project

The Number Project is a persistent laboratory for formal mathematics, mathematical
physics, symbolic computation, and eventually machine-assisted mathematical discovery.
Milestone 1 established two small, machine-verifiable experiments:

1. a Lean 4 proof that `F = m * a` follows algebraically from explicitly stated
   Verlinde-style assumptions; and
2. a Python search that treats dimensional consistency as a hard constraint while
   looking for expressions with the dimensions of Newton's gravitational constant `G`.

Milestone 2 builds on that foundation with:

1. a Lean-checked conditional derivation of `F = G * M * m / R^2` from the explicit
   spherical-screen equations in §3.2 of Verlinde's paper; and
2. an exact rational constraint solver that explains which monomial exponents follow
   from dimensions alone and which require an added scaling assumption.

Milestone 2.1 hardens and translates those results by:

1. certifying four Planck-unit controls symbolically in Lean, without equating rounded
   CODATA decimals;
2. replacing Python's anonymous signature set with a validated, traceable identity
   catalog;
3. recording paired Lean/Python dimension-vector contracts; and
4. adding a learner-facing inverse-square exponent walkthrough.

Milestone 3 adds exact dependency-aware candidate analysis by:

1. expanding registered Planck definitions over a declared atomic basis with rational
   exponents;
2. separating dependency status from Lean certification and numerical proximity;
3. grouping 21 surface candidates into 10 exact definitional-equivalence classes; and
4. reporting the full generator system's rank-4/nullity-6 dimensional ambiguity.

Milestone 4 defines a non-circular physical bridge contract by:

1. separating algebraic dependency from metrological provenance;
2. rejecting direct, inherited, calibrated, or corrected target leakage;
3. validating an unpopulated inverse-square measurement-model skeleton;
4. requiring uncertainty, covariance, traceability, and isolated comparison records; and
5. reporting separate evidence axes instead of an aggregate success score.

Milestone 4.1 hardens that bridge with byte-exact freshness checks for every generated
artifact, a named 34-case leakage corpus, and a separate schema/validation/facade module
boundary.

Milestone 5A closes the formal estimator gap by proving that the inverse-square estimator
equals `G` when the inverse-square relation, estimator definition, and nonzero denominator
conditions are supplied explicitly. It does not populate the bridge or claim a measurement.

Milestone 5B-core makes selected methodological failure modes measurable by adding a
machine-verifiable preregistration, provenance-stratified numerical nulls with an
independent geometric oracle, planted-target recovery controls, and ephemeral mutation
testing. These are methodological results about the project machinery, not evidence about
gravity or a measurement of `G`.

The practical-evidence pilot preregisters and audits a published-data reproduction of the
University of Washington 2000 torsion-balance result. The audit reaches
`NO-GO (INCOMPLETE_REPRODUCTION)`: the public record does not expose two indispensable
numerical inputs, and the proposed 2002 PRD companion is unrelated. A 1999 prototype
coupling, proposed budget, and design geometry are explicitly excluded from the 2000
input set. The repository records the missing evidence rather than back-solving it from
the published value. No empirical result or replication claim is created.

Milestone 6B uses a pinned PySR 2.2.0 run on preregistered synthetic controls to test a
specific provenance boundary. Its primary methodological result is `BOUNDARY_CONFIRMED`:
a candidate can be dimensionally valid and have no registered algebraic path to `G` while
still carrying known target information through the data-generation path. All 26 PySR
outputs are permanently `target_exposed_candidate` and promotion-ineligible; 17 also fail
the project's independent dimensional check. This is a software/methodology result, not
evidence about gravity or a measurement of `G`.

Milestone 7B adds three separately preregistered HUST 2018 AAF published-data
reconstructions at depth 2b. Nature's official Table 1 page is metadata-and-hash pinned;
each unchanged depth-2a central value receives 21 direct relative ppm contributions and a
precision-50 RSS-derived standard uncertainty. The combined AAF result, raw replication,
apparatus validation, and physical-independence claims remain unauthorized.

The project is exploratory. A compiled implication is not experimental evidence for its
premises, and a dimensionally valid numerical coincidence is not evidence of a physical
law.

## Current machine-verifiable outputs

- `FormalPhysics/Verlinde.lean` contains
  `TheNumberProject.EntropicGravity.force_eq_mass_mul_acceleration`. Lean's kernel checks
  the proof from the stated hypotheses.
- `FormalPhysics/InverseSquare.lean` contains the principal inverse-square theorem, its
  acceleration corollary, and exact rational proofs of the exponent-selection result.
- `FormalPhysics/PlanckUnits.lean` proves four symbolic rearrangements of the conventional
  Planck length, mass, and time definitions as dependent controls.
- `FormalPhysics/Estimator.lean` proves the generic inverse-square estimator expression
  and a bridge-shaped `G_hat = G` correctness theorem from explicit hypotheses.
- `FormalPhysics/Dimensions.lean` checks the dimensions of both milestones' relations.
- `Discovery/dimensional_search.py` enumerates and ranks dimensionally valid candidates.
- `Discovery/planck_identities.py` gives each certified Python control a stable identity,
  dependency explanation, and corresponding Lean theorem name.
- `Discovery/dependency_definitions.py` provides an immutable, dimension-validated exact
  dependency catalog; `Discovery/dependency_analysis.py` expands and groups candidates.
- `Discovery/monomial_constraints.py` exposes exact row reduction and affine solutions;
  `Discovery/inverse_square_search.py` applies it to `(G, M, m, R)`.
- `Discovery/physical_bridge_schema.py` defines the immutable records and strict scalar
  boundary; `Discovery/physical_bridge_validation.py` contains the graph, target-leakage,
  validation, and evaluation gates; `Discovery/physical_bridge.py` remains the public
  artifact-building facade and command-line entry point.
- `Experiments/GCoincidences/dependency_analysis.json` records exact signatures,
  statuses, groups, certification links, rank, nullity, RREF, and limitations.
- `Experiments/GMeasurements/` records the general physical-bridge contract, an
  explicitly unpopulated inverse-square structural example as deterministic JSON, and
  the preregistered UW 2000 source audit with its explicit
  `NO-GO (INCOMPLETE_REPRODUCTION)` decision. It also records the official-source-pinned
  HUST AAF individual depth-2b authorization, three uncertainty-qualified published-data
  reconstructions, and their behavioral mutation results.
- `Experiments/Falsification/` records the immutable 5B-core preregistration, complete
  provenance-stratified null and planted-control result, and disposable-worktree mutation
  result with source and integrity metadata.
- `Experiments/EcosystemComparison/PySRLeakage/` records the frozen 6B preregistration,
  deterministic dataset manifest, raw pinned PySR output, independently normalized v2 audit,
  and two killed semantic mutations for target exposure and hidden-generation leakage.
- `Discovery/null_experiments.py` isolates numerical log-space sampling from exact
  symbolic provenance and implements an independent interval-union CDF oracle;
  `Discovery/mutation_harness.py` and `Discovery/mutation_test_runner.py` enforce
  ephemeral mutation and in-process import-path integrity.
- `tests/` checks the dimension algebra, Planck controls, dependency catalog and groups,
  constrained and unconstrained dimensional systems, and a named adversarial corpus for
  the fail-closed bridge rules.
- GitHub Actions builds Lean with the mathlib cache, audits the resulting declarations,
  and runs the Python tests.

## Epistemic labels

These labels are part of the project's design, not merely documentation style.

| Label | Meaning in this repository |
|---|---|
| **Definition** | A chosen mathematical representation or name. It makes no empirical claim. |
| **Assumption / hypothesis** | An input accepted temporarily inside a stated model or theorem. |
| **Theorem** | A proposition whose proof term is accepted by Lean's kernel from its hypotheses. |
| **Conjecture** | A precise proposed relationship for which no proof is currently supplied. |
| **Target-exposed candidate** | A candidate proposed or generated after the target or target-bearing data were available to the generating process. It may motivate a new target-clean preregistered path, but the original candidate is not promotion-eligible. |
| **Symbolic result** | Exact output of a declared computational model, including any free parameters. |
| **Numerical observation** | A computational pattern; dimensional validity and numerical proximity alone do not make it a law. |
| **Empirical observation** | Information supplied by an instrument or physical procedure; it is an external premise, not a theorem. |
| **Measurement result** | An estimate of a stated measurand together with its uncertainty and relevant metrological information. |
| **Methodological result** | A reproducible result concerning the behavior, reliability, sensitivity, specificity, robustness, or failure mode of the project's methods or software. |
| **Physical interpretation** | A cautious reading of a result; not an additional proof or measurement. |

## Track A: conditional Lean derivations

### Milestone 1: force and acceleration

The formal target follows equations (3.6)--(3.8) of Erik Verlinde's 2010 paper,
[On the Origin of Gravity and the Laws of Newton](https://arxiv.org/abs/1001.0785):

```text
F * delta_x = T * delta_S
delta_S = (2 * pi * k_B * m * c / hbar) * delta_x
T = hbar * a / (2 * pi * k_B * c)
```

The Lean theorem treats those equations as named hypotheses. It also requires the
displacement and the three cancelling constants to be nonzero. Nothing in the theorem
claims that the entropy-displacement postulate, the entropic-force interpretation, or the
application of the Unruh relation is physically correct. Lean proves the conditional
statement: **if these equations and side conditions hold over the real numbers, then
`F = m * a`.**

`FormalPhysics/Constants.lean` defines only a container for the three scalar constants.
It deliberately places no model equation inside the definition. `Dimensions.lean` uses
the seven SI base dimensions as an integer-exponent vector and separately checks that the
relations are dimensionally homogeneous.

### Milestone 2: the inverse-square relation

The new formal target uses equations (3.6), (3.7), and (3.10)--(3.12), plus the spherical
area relation, to derive equation (3.13) of
[§3.2 in the original paper](https://arxiv.org/html/1001.0785v1#S3.SS2):

```text
delta_S = (2 * pi * k_B * m * c / hbar) * delta_x
F * delta_x = T * delta_S
N = A * c^3 / (G * hbar)
E = (1/2) * N * k_B * T
E = M * c^2
A = 4 * pi * R^2
```

`TheNumberProject.EntropicGravity.force_eq_gravitationalConstant_mul_masses_div_radius_sq`
treats every displayed equation as a named hypothesis and concludes
`F = G * M * m / R^2`. Its only nonzero premises are `delta_x`, `c`, `hbar`, `G`, and
`R`: those are the quantities used as denominators or genuinely cancelled by the proof.
The masses, temperature, bit count, area, energy, entropy change, force, and even `k_B`
need no nonzero premise.

The Unruh-temperature relation from Milestone 1 is intentionally absent. Verlinde says
at the start of §3.2 that it is not needed for this argument. Equation (3.10) introduces
`G` as the proportionality constant connecting area and information count; only after the
algebra is completed is it identified with Newton's gravitational constant.

The theorem is therefore conditional. **Assumptions** include the spherical screen,
holographic bit count, equipartition, the adopted mass-energy relation, the entropy-
displacement postulate, and entropic work. The **theorem** is the real-number implication
from those assumptions. Lean does not prove that the model's premises are physically
correct or that the result empirically supports entropic gravity.

The file also composes an assumed `F = m * a` equality with the inverse-square equality:
for a nonzero test mass it obtains `a = G * M / R^2`. This corollary does not independently
validate either input relation.

### Milestone 2.1: symbolic Planck-unit controls

`FormalPhysics/PlanckUnits.lean` takes the conventional squared definitions

```text
l_P^2 = hbar * G / c^3
m_P^2 = hbar * c / G
t_P^2 = hbar * G / c^5
```

as explicit theorem hypotheses. Positivity selects the conventional positive-root branch
where two squared expressions must be compared and supplies the nonzero denominators used
by the algebra. Lean then certifies:

```text
G = c^2 * l_P / m_P
G = hbar * c / m_P^2
G = c^3 * t_P / m_P
G = c^3 * l_P^2 / hbar
```

These are **dependent controls**, not new determinations of `G`: Planck length, mass, and
time were defined using `G` in the first place. Lean proves the symbolic rearrangements;
it does not assert equality among rounded measured decimals. The Python ratios are close
to one rather than exactly one because the checked-in Planck-unit values have finite
precision and inherit uncertainty from measured `G`.

The exact cross-language base ordering and literal shared vectors are recorded in
[`Notes/DimensionContract.md`](Notes/DimensionContract.md).

### Milestone 5A: conditional estimator certification

`FormalPhysics/Estimator.lean` separates two claims that ordinary algebra often compresses.
First, for nonzero masses and separation, the inverse-square relation implies

```text
F * r^2 / (m_1 * m_2) = G.
```

Second, if `G_hat` is explicitly defined by that expression, then `G_hat = G`. The
inverse-square relation, estimator definition, and three nonzero denominator conditions
are named theorem hypotheses. Neither theorem assumes that an observation occurred or
that a force estimate, geometry model, calibration chain, correction, or uncertainty
budget is valid. The physical-bridge catalog therefore marks only the exact estimator
theorem as `estimator_rearrangement_certified: true`; the earlier relation-only theorem
remains `false`.

## Track B: exact dimensional computation

### Milestone 1: bounded search for the dimensions of G

The search represents a dimension as an exact seven-component vector over rational
exponents, ordered as mass, length, time, electric current, temperature, amount of
substance, and luminous intensity. Thus:

```text
[G] = M^-1 L^3 T^-2
```

The default search:

- excludes `G` itself from the generating constants;
- uses products of at most three distinct constants;
- uses nonzero integer powers from `-3` through `3`;
- rejects every expression whose dimension vector differs from `[G]` exactly; and
- records expression, exponents, SI magnitude, ratio to measured `G`, logarithmic
  magnitude difference, complexity, number of constants, and a cautious classification.

Planck length, mass, and time are included intentionally as controls. Expressions such as
`hbar * c * m_P^-2` should reconstruct `G` up to the rounding and measurement uncertainty
of the tabulated values. The structured catalog certifies exactly four selected controls
as `known Planck-unit identity`; other Planck-containing candidates retain the more
cautious `Planck-unit rearrangement` label. Neither label is a discovery claim.
Expressions such as `hbar * c * m_e^-2` are dimensionally valid comparisons but are not
thereby physical identities.

The constants are from the
[NIST 2022 CODATA complete listing](https://physics.nist.gov/cuu/Constants/Table/allascii.txt).
The exact SI defining constants are cross-checked against the
[BIPM SI defining constants](https://www.bipm.org/en/measurement-units/si-defining-constants).

Run the search from the repository root:

```bash
python -m Discovery.dimensional_search
```

It prints the leading candidates and regenerates
`Experiments/GCoincidences/candidates.csv`. Use `--help` to see bounded rational-power,
factor-count, and output options. The implementation uses only Python's standard library.

### Milestone 2: exact monomial constraints

For the explicitly chosen candidate form

```text
G^alpha * M^beta * m^gamma * R^delta,
```

matching the dimensions of force gives three independent equations:

```text
-alpha + beta + gamma = 1
3*alpha + delta = 1
-2*alpha = -2
```

Exact row reduction yields

```text
alpha = 1,  delta = -2,  beta + gamma = 2.
```

The particular solution `(1, 2, 0, -2)` plus nullspace direction `(0, -1, 1, 0)`
describes the whole family. That direction shifts a power between `M` and `m`, or
equivalently multiplies by a power of the dimensionless ratio `m/M`. Dimensional analysis
cannot distinguish the two masses because they have the same SI dimension.

The extra **assumption** `gamma = 1`—linearity in the test mass—selects the unique tuple
`(1, 1, 1, -2)` within this four-factor monomial model. Source-mass linearity selects the
same tuple. This uniqueness is not global: a dimensionless coefficient or function such
as `Phi(m/M)` remains possible, and the factor set and monomial form define the search
space rather than follow from dimensional analysis.

Regenerate or check the exact artifact with:

```bash
python -m Discovery.inverse_square_search
python -m Discovery.inverse_square_search --check
```

The machine-readable rank, nullity, RREF, affine family, constraints, exact tuple, and
limitations are recorded in `Experiments/InverseSquare/solutions.json`. There is no
numerical fitting or candidate ranking in this experiment. The same exponent implications
are separately proved over `ℚ` in Lean.

For a step-by-step explanation of monomials, exponent vectors, the affine solution line,
the nullspace direction, and the separate test-mass scaling premise, read
[`Notes/InverseSquareWalkthrough.md`](Notes/InverseSquareWalkthrough.md).

### Milestone 3: dependency-aware provenance

The original bounded search answers which monomials have exactly the dimensions of `G`.
Milestone 3 adds a second exact filter: it substitutes the registered Planck definitions
using `Fraction` exponents and records which atomic symbols remain. This distinguishes an
exact reconstruction of `G`, partial inherited dependence on `G`, no dependence found by
the current catalog, and unresolved provenance.

The default 21 candidates form 10 exact definitional-equivalence groups. Six expressions
reduce exactly to `G`; four have linked declarations in `FormalPhysics/PlanckUnits.lean`,
while two are deliberately labeled `exact_python_reduction_only`. All six remain
dependent controls because the Planck inputs already contain `G`.

The complete ten-generator dimension matrix has rank 4 and nullity 6. Its nullspace
directions are dimensionless transformations—including mass ratios—so dimensional
analysis cannot select a unique formula from this catalog. That is underdetermination by
the stated dimensional information, not a claim that nature itself is underdetermined.

Regenerate or check the deterministic artifact with:

```bash
python -m Discovery.dependency_analysis
python -m Discovery.dependency_analysis --check
```

The artifact preserves every legacy candidate search field and appends exact surface and
expanded signatures, target power, dependency and certification statuses, group identity,
group size, and a plain-language explanation. Decimal proximity never determines an
exact group or status.

For the learner-facing derivation and the exact boundary between this computation and a
physical determination or explanation of `G`, read
[`Notes/DependencyAnalysis.md`](Notes/DependencyAnalysis.md).

## Track C: physical evidence contracts

### Milestone 4: non-circular bridge to G

The physical bridge asks what would be required to move from a formal inverse-square
expression to a defensible empirical estimate. The educational skeleton declares

```text
F = G * m_1 * m_2 / r^2
G_hat = F_hat * r^2 / (m_1 * m_2),
```

then expands the provenance of `F_hat`, both masses, and the separation into structural
observation, calibration, and correction parents. Exact dimensional arithmetic verifies
that the estimator has the dimensions of `G`. No observation or estimated output is
populated.

The target-clean gate reuses Milestone 3's registered definitions. It rejects direct `G`,
Planck-unit inputs that inherit a nonzero power of `G`, target-dependent estimator or direct
uncertainty-component ancestors, and a reference value of `G` used anywhere upstream.
Unresolved ancestry remains `unresolved`. Direct-mode records expose their component
closure as a separate machine-readable assessment block. The status
`no_registered_target_path` is catalog-relative algebraic information, not a claim of
experimental independence.

The display-symbol namespace is a separate ambiguity guard. It removes invisible Unicode
format controls (category `Cf`), applies Unicode NFC normalization, and trims outer
whitespace before exact comparison. It rejects reuse of a registered catalog symbol and
duplicate normalized symbols across every provenance kind. It is deliberately not a
visual-confusables or homoglyph detector; stable identifiers and exact registered
dependency signatures remain the authoritative algebraic records.

CODATA 2022 appears only as an editioned, sourced, uncertainty-bearing
`external_comparison_reference` in a terminal post-estimation node. The example separately
reports dimensional, algebraic-model, registered-target-path, metrological-provenance,
uncertainty, empirical-population, and replication statuses. Its empirical and uncertainty
axes remain incomplete.

The existing Lean inverse-square theorem is linked by a small explicit catalog. It
kernel-checks a conditional force implication from stated hypotheses; it does not directly
certify the estimator rearrangement or establish observations, calibration, apparatus
behavior, or uncertainty completeness.

Regenerate or check both deterministic bridge artifacts with:

```bash
python3 -m Discovery.physical_bridge
python3 -m Discovery.physical_bridge --check
```

Milestone 7A extends this contract with a second, explicit uncertainty basis for published
budget entries that are already contributions to the final measurand. The original
`estimator_input_propagation` mode is unchanged. The new
`direct_measurand_contributions` mode keeps those entries out of the central estimator,
requires a source-documented and dimensionally homogeneous component inventory with its
full ancestry audited for registered target paths, and requires a resolved propagation and
correlation policy. A missing target standard uncertainty remains an explicit incomplete
gap; a populated one must use the target unit. This basis is eligible only when the pinned
publication reports final-measurand contributions. The generic bridge validates
representation only; mode selection does not establish eligibility, and scientific
completeness and arithmetic remain the responsibility of a source-specific validator. This
additive change does not populate a HUST depth-2b uncertainty or authorize a combined AAF
estimator.

The first practical pilot is an explicit UW 2000 source-audit
`NO-GO (INCOMPLETE_REPRODUCTION)`, not a project measurement. Its original
preregistration, review-time clarification about exact symbolic constants, and source
audit are SHA-256-pinned by a deterministic manifest. Check those bytes and canonical
decision fields with:

```bash
python3 -m Discovery.published_data_pilot --check
```

The manifest is tamper evidence, not an unforgeability claim. A populated empirical
record receives no source-provenance exemption merely because its generic `exact` flag is
set.

Read [`Notes/PhysicalBridgeContract.md`](Notes/PhysicalBridgeContract.md) for the
first-principles evidence boundary and
[`Notes/GMeasurementLiterature.md`](Notes/GMeasurementLiterature.md) for the experimental
and metrology foundation.

## Lean and mathlib setup

The repository pins the matching stable releases Lean `v4.33.1` and mathlib `v4.33.1`.
`lake-manifest.json` additionally fixes mathlib and its transitive dependencies to exact
commits. Mathlib's cache command downloads precompiled artifacts, avoiding a local rebuild
of the full library.

The repository's development-container configuration installs Elan and the official Lean
extension. Its first-run hook also runs `lake update`, which synchronizes the pinned
dependencies and invokes mathlib's precompiled-cache download.

To repeat that step manually, open the menu at the upper left, choose **Terminal -> New
Terminal**, and run:

```bash
lake update
```

Successful output normally shows repositories being cloned or updated, followed by a
cache download summary. Then verify the project with `lake build`.

Run the Python checks with:

```bash
python -m unittest discover -s tests -v
```

## Repository map

```text
FormalPhysics/                 Lean definitions and proofs
Discovery/                     Reusable Python search components
Experiments/GCoincidences/     Reproducible search output and interpretation
Experiments/InverseSquare/     Exact constraint artifact and interpretation
Experiments/GMeasurements/     Physical-bridge contract and structural example
Notes/                         Research decisions, literature, and tooling notes
tests/                         Python unit tests
.github/workflows/verify.yml   Lean, proof-audit, and Python CI
.devcontainer/                Reproducible Codespaces setup
```

Promising extensions belong in `Notes/ToolingRoadmap.md`; this milestone intentionally
stops before general relativity, empirical fitting, modified gravity, neural symbolic
regression, LeanDojo integration, or a general physical-units library. A candidate with
no registered dependence on `G` is not thereby an independent measurement or physical
explanation of `G`; it has only passed the current catalog's algebraic provenance check.
