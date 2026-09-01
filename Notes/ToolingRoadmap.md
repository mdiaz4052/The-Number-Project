# Tooling roadmap

The first two milestones deliberately keep the critical path small: Lean, mathlib, Lake,
and the Python standard library.

## Exact symbolic constraints before symbolic regression

Milestone 2 adds a reusable exact linear-constraint layer for monomial exponents. It
reports rank, nullity, affine solution families, unique solutions, and inconsistency
using rational arithmetic. This is useful groundwork for later symbolic regression or
AI-guided conjecture generation because it can enforce structural constraints and expose
underdetermination before any numerical ranking begins.

A later search system can use this layer to reject dimensionally impossible expressions,
record free dimensionless directions, and pass precise candidate statements to Lean.
That future system must still distinguish definitions, physical assumptions, conjectures,
formal theorems, and numerical observations.

## LeanDojo v2

[LeanDojo v2](https://github.com/lean-dojo/LeanDojo-v2) is relevant to the longer-term
goal. It provides infrastructure around theorem-proving agents, traced Lean data,
retrieval, evaluation, and training. Its documented stack includes PyTorch,
Transformers, DeepSpeed, Ray, and Pantograph, and typical training expects a CUDA-capable
GPU. Those are valuable capabilities once this repository has a meaningful theorem
corpus and benchmark, but they would add substantial installation and compute costs to
the current elementary experiments.

The intended integration point is later and explicit:

1. build a curated set of small, human-reviewed Lean statements;
2. trace it for retrieval or proof-search experiments;
3. keep generated proofs subject to ordinary Lean kernel checking and the same CI audit;
4. record whether a result is a theorem, conjecture, failed search, or numerical
   observation.

LeanDojo would assist proof search; it would not change the epistemic status of a physical
premise or make dimensional coincidences into evidence.

## Published-data reproduction queue

The UW 2000 source audit is an explicit `NO-GO`: the public record does not expose the
main fitted acceleration amplitude or complete numerical multipole coupling, and its
purported 2002 PRD companion is unrelated. This finding should not trigger a broader
schema or hardening milestone.

The next audit should start with the HUST 2018 angular-acceleration-feedback method. Its
official supplement reports an aggregate multipole coupling, average angular
acceleration, magnetic-damper parameters, standard uncertainties, and a correlation rule
for combining runs. Treating the reported aggregate coupling as one source-backed model
input appears compatible with the current monomial estimator schema, but that is a
screening observation rather than a `GO` decision.

If a complete HUST transcription requires unpublished inputs or a sum-of-monomials
estimator, stop and review that representational change separately. The detailed 2014
BIPM torsion-balance publication is the next source-completeness candidate. Candidate
selection must remain based on public input completeness, not agreement with a preferred
value of `G`.
