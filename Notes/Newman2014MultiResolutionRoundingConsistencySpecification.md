# The Number Project — Newman 2014 Multi-Resolution Terminal-Constraint Specification

## Objective

Implement one bounded scientific capability PR that formalizes **multi-resolution terminal constraints** for the already-established Newman et al. 2014 Table 11 uncertainty reconstruction.

The question is:

> If the same underlying fibre uncertainty is printed at two resolutions in the same publication — once as the one-decimal Table 11 quadrature sum and again as an integer-ppm conclusion statement — what exact representation interval follows from requiring one underlying value to be consistent with both printed statements, and does the already-frozen Newman component model remain representable inside that joint interval?

This PR sharpens an existing published-measurement certificate. It is not a fourth measurement reconstruction and is not a new outcome-blind falsification attempt.

## Known prior information

The PR #42 audit already reported that combining the one-decimal and integer statements would leave all three Newman fibre verdicts `compatible` and would narrow the effective terminal interval for fibre 1. That information predates this preregistration.

Accordingly, this freeze does **not** claim blindness to the real-data outcome. Its purpose is to freeze the mathematical semantics, provenance boundary, terminal-intersection rules, schedule reuse, failure states, and evidence classification before implementation.

No implementation result may be advertised as a newly discovered empirical outcome.

## Intended base

`1fd38d8f009c2b23b6d419f7817acc730cc57812`, the true merge commit of PR #42.

## Source authority

The same peer-reviewed publication already frozen for PR #42:

Riley Newman, Michael Bantel, Eric Berg, William Cross, “A measurement of G with a cryogenic torsion pendulum,” *Philosophical Transactions of the Royal Society A* 372:20140025 (2014), DOI `10.1098/rsta.2014.0025`.

Two publication surfaces are authoritative for this PR:

1. Table 11, printed/PDF page 22: one-decimal `quadrature sum` cells 14.5, 22.2, and 19.6 ppm for fibres 1–3.
2. §7 Conclusion, printed/PDF page 24: corresponding integer uncertainty statements 14, 22, and 20 ppm.

The prior Newman source attestation remains immutable and supplies the component projection and Table 11 transcription. A new terminal attestation freezes the conclusion integers and the exact relationship between the two publication surfaces. CI performs no live network access.

## Reporting model

Each printed terminal representation contributes a **closed conservative rounding-consistency bin**:

- one-decimal value `v`: `[v - 0.05, v + 0.05]` ppm;
- integer value `n`: `[n - 0.5, n + 0.5]` ppm.

Closed endpoints are intentional. They avoid assuming an undocumented tie-breaking convention. No claim is made that the authors necessarily used nearest rounding; the bins encode only the declared consistency model.

For each fibre, the **joint terminal interval** is the exact intersection of all declared terminal bins.

The implementation must retain every constituent interval and the exact joint interval in the artifact.

## Candidate generation

The component model and schedule are unchanged from PR #42:

`R^2 = x_statistical^2 + x_systematic^2 + x_analysis_method^2`.

Each one-decimal component retains its ±0.05 ppm closed component box. The independently frozen tensor parameters are

`0, ±1/8, ±2/8, ±3/8, ±4/8, ±5/8, ±6/8, ±7/8`

for each of three component coordinates, yielding `15^3 = 3375` candidates per fibre and 10,125 candidates total.

Candidate generation must receive only:

- the component projection;
- the explicit component half-width;
- the frozen schedule.

No terminal value, terminal half-width, terminal representation list, or joint interval may enter candidate generation. This is the structural pattern required by the DM-057/FH-3 concern on the new surface.

All candidates for all three fibres must exist before terminal representations are interpreted.

## Classification

For each fibre:

1. Build every constituent terminal bin and their exact closed intersection.
2. If the terminal bins are mutually disjoint, verdict = `incompatible` with reason `terminal_constraints_disjoint`.
3. Otherwise square the non-empty joint interval exactly.
4. If the guaranteed component-box squared enclosure is disjoint from that squared interval, verdict = `incompatible` with reason `component_box_disjoint_from_joint_terminal`.
5. Otherwise, a scheduled candidate is `compatible` only when:
   - all component values are strictly interior to their nondegenerate component bins; and
   - its exact `R^2` is strictly interior to the **nondegenerate joint terminal squared interval**.
6. If the intersection is degenerate, or enclosure overlaps but no scheduled strict-interior witness exists, verdict = `unresolved`.

Status labels are explicitly model-relative:

- `compatible`: `representable_under_the_declared_multiresolution_reporting_model`
- `incompatible`: `not_representable_under_the_declared_multiresolution_reporting_model`
- `unresolved`: `undetermined_under_the_frozen_tensor_schedule_and_reporting_model`

Malformed or provenance-invalid evidence is invalid and never becomes a numerical verdict.

## Resolution-width reporting

The artifact must explicitly report, per fibre:

- every constituent terminal interval;
- joint terminal interval;
- original one-decimal width;
- joint width;
- exact width ratio relative to the Table 11 interval;
- whether the second representation narrows the domain.

The claim limits must state that `compatible` establishes existence within the declared reporting model, not correctness of a unique printed cell, hidden author values, or a historical rounding procedure.

This supplies the resolution-width caveat prospectively on the new artifact without rewriting frozen PR #41/#42 artifacts.

## Required implementation surfaces

Add only:

- `Experiments/GMeasurements/newman_2014_multiresolution_rounding_consistency_preregistration_v1.json`
- `Experiments/GMeasurements/newman_2014_multiresolution_terminal_attestation_v1.json`
- `Experiments/GMeasurements/newman_2014_multiresolution_rounding_consistency_v1.json`
- `Experiments/GMeasurements/newman_2014_multiresolution_mutations_v1.json`
- `Discovery/multiresolution_rounding.py`
- `Discovery/newman_2014_multiresolution_rounding_consistency.py`
- `Discovery/newman_2014_multiresolution_mutations.py`
- `tests/test_newman_2014_multiresolution_rounding_consistency.py`
- `tests/test_newman_2014_multiresolution_mutations.py`
- `Notes/Newman2014MultiResolutionRoundingConsistencySpecification.md`
- `Notes/Newman2014MultiResolutionRoundingConsistency.md`
- two read-only `--check` steps in `.github/workflows/verify.yml`.

Do not modify:

- `Discovery/rounding_consistency.py`;
- `Discovery/newman_2014_table11_rounding_consistency.py`;
- any PR #42 artifact or preregistration;
- the PR #41 joint-inference module or artifact;
- HUST or Schlamminger scientific artifacts;
- shared preregistration/history infrastructure;
- Lean sources.

## Provenance and chronology

The preregistration must be the only file in the first branch commit and its sole parent must be the intended base.

Push the freeze and create the draft PR before adding implementation files. Record the GitHub-created PR timestamp as an external chronology anchor.

Because the expected real-data verdict was already reported by Claude before this freeze, chronology proves implementation-after-freeze only. It must not be described as proof of outcome blindness.

The source attestation and bounded specification are prepared before the freeze and hash-pinned by it, but are committed only after the draft PR anchor to preserve the one-file first-commit rule.

## Verification

Focused tests must cover:

- exact source/terminal schema and frozen projections;
- three mandatory fibres and two terminal representations per fibre;
- exact closed-bin intersection;
- fibre 1 narrowing and unchanged/full-width cases;
- disjoint terminal constraints;
- degenerate intersection => `unresolved`;
- exact schedule order and 3375 candidates per scope;
- structural terminal-resolution isolation from candidate generation;
- strict-interior witness rule;
- real-data expected verdicts;
- central-value invariance;
- explicit effective-width reporting;
- model-relative status labels;
- E-001 isolation;
- source/provenance freshness;
- exact committed-artifact rebuild.

Because terminal-intersection semantics are a new epistemic boundary, add one bounded mutation family. It must challenge at least:

- widening an intersection by union/min-max logic;
- ignoring the coarse-resolution constraint;
- treating a disjoint terminal pair as non-falsifying;
- allowing a degenerate/boundary-only witness to become `compatible`;
- allowing terminal half-width into component candidate generation;
- erasing the model-relative negative qualifier;
- erasing effective-width/narrowing reporting.

Include a killable calibration and an executable-equivalent calibration. Infrastructure/import/syntax/source-state failures never count as kills.

Final validation on the final tree:

- focused tests;
- one complete Python test-suite pass;
- both new `--check` guards;
- the bounded mutation family;
- `git diff --check`.

No local Lean run is required because Lean-linked surfaces are unchanged. Exact-head GitHub CI remains the repository-wide final automated gate.

## Merge semantics

Merge by true merge commit only. Never squash, rebase, or rewrite the freeze/anchor chronology.
