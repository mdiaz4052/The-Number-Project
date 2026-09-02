# Milestone 6A — PyDimension differential comparison

This directory records a methodological comparison between The Number Project's exact dimensional linear algebra and one pinned external implementation path in PyDimension.

## Question

Does an independently maintained implementation recover the same nullspace for the project's ten-generator dimensional matrix?

This is a test of a computation, not a test of gravity. Agreement is methodological corroboration only.

## Frozen comparison

The preregistration was committed before the target matrix was run through the external comparator. It pins:

- The Number Project baseline: `6376ee9c74a1f5bff0045b121a7202ec79a9b667` (merged Milestone 6C);
- result-driving project source anchor: `9abf4de2ffc045d2ca7d6613e02a2eb5b731d281`;
- PyDimension repository: `xiaoyuxie-vico/PyDimension`;
- PyDimension commit: `a899cd41e327a8ad185b139537272eecb6a9adb4`;
- inspected exact helper: `pydimension/data_generation/generator.py::DataGenerator._simplify_basis_vectors`;
- exact helper blob: `5ffcabd41dd011f5b42b65b16c0fa74d61b0a2ae`;
- MIT license blob: `5953bba9f50e93b0a692c40f2b6f4fc10a8222bd`;
- Python/package versions and matrix ordering.

The inspected helper recomputes `Matrix(self.dimension_matrix).nullspace()` with SymPy, clears denominators and reduces each vector to a primitive integer representative. The surrounding PyDimension method first computes a floating SciPy/SVD nullspace; 6A records that only as a diagnostic and does not use it for the exact verdict.

PyDimension supplies the primitive kernel vectors through that pinned helper. The external runner also uses the same frozen SymPy environment to record exact matrix rank/nullity and to reject any returned primitive vector with nonzero exact residual. Those auxiliary checks should not be mistaken for a separate independent rank algorithm.

## Comparison rule

Raw nullspace bases are not compared for textual equality because a vector space has many valid bases.

Both bases are converted to exact rational row spans and reduced to canonical RREF. `AGREEMENT` requires:

1. rank/nullity metadata agrees with the project's exact result;
2. every external primitive vector has exact zero residual;
3. the canonical nullspace spans are exactly equal;
4. the project's exact particular solution satisfies the target dimension of `G`;
5. translating that particular solution by every external kernel vector remains in the same affine solution set.

PyDimension is **not** credited with independently deriving the affine particular solution, definitional dependency, or the ten definitional-equivalence groups.

## Result

Outcome: **Methodological result — `AGREEMENT`.**

For the preregistered matrix:

- The Number Project: rank 4, nullity 6;
- external exact comparison: rank 4, nullity 6;
- the two raw bases differ in sign/orientation in several vectors;
- their canonical exact row spans are identical;
- all external primitive-vector residuals are exactly zero;
- the external kernel preserves the project's affine `G`-dimension solution.

The SciPy diagnostic residual is approximately `7.22e-16`. It is recorded to make the exact-vs-floating distinction visible, not as evidence controlling the outcome.

## Planted mismatch control

The preregistration copies the matrix and changes the mass exponent of `c` from 0 to 1. The external comparator still obtains rank 4/nullity 6, but the exact nullspace span changes.

Required control outcome: `DISAGREEMENT`.

Observed control outcome: **`DISAGREEMENT`**.

Thus the differential harness is capable of reporting a real mismatch instead of mechanically returning agreement.

## Provenance and reproducibility

The external run used a disposable GitHub Actions runner with `contents: read`. It cloned the pinned PyDimension commit, verified the code and license Git blobs, executed the frozen environment, and uploaded evidence without repository write permission. The temporary workflow was removed after the raw and normalized artifacts were reviewed and committed.

Successful canonical external run: `33661571456`.

A preceding infrastructure attempt failed only because the temporary inline runner used a lowercase JSON-style `false` inside Python metadata. It failed before serializing an external result. The typo was corrected without changing the preregistration or result-driving project source anchor.

Committed raw external SHA-256:

`e6d7760add5a1ad974377a685c503365333487751b3d71a618fd23e63eb6175e`

Committed normalized result SHA-256 at initial commit time:

`bfdfc8baad67433cd4df00e384d2311804ef9b1ea0349abf757fab47143e1ef6`

Normal CI does not install or rerun PyDimension. `python -m Discovery.pydimension_comparison --check` hashes the committed external bytes, recomputes all project-side exact classifications and span comparisons, verifies the planted-control result, and checks that result-driving project source has not changed since its recorded anchor.

## Nonclaims

This experiment does not establish a value of `G`, evidence for a physical mechanism, correctness of either software system generally, or independent confirmation of the project's definitional-dependency analysis. It is a bounded differential check of one exact dimensional nullspace computation.
