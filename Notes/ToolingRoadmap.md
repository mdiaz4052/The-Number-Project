# Tooling roadmap

Milestone 1 deliberately keeps the critical path small: Lean, mathlib, Lake, and the
Python standard library.

## LeanDojo v2

[LeanDojo v2](https://github.com/lean-dojo/LeanDojo-v2) is relevant to the longer-term
goal. It provides infrastructure around theorem-proving agents, traced Lean data,
retrieval, evaluation, and training. Its documented stack includes PyTorch,
Transformers, DeepSpeed, Ray, and Pantograph, and typical training expects a CUDA-capable
GPU. Those are valuable capabilities once this repository has a meaningful theorem
corpus and benchmark, but they would add substantial installation and compute costs to
the two elementary Milestone 1 experiments.

The intended integration point is later and explicit:

1. build a curated set of small, human-reviewed Lean statements;
2. trace it for retrieval or proof-search experiments;
3. keep generated proofs subject to ordinary Lean kernel checking and the same CI audit;
4. record whether a result is a theorem, conjecture, failed search, or numerical
   observation.

LeanDojo would assist proof search; it would not change the epistemic status of a physical
premise or make dimensional coincidences into evidence.

