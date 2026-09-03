# Final post-audit closure

This note records the final bounded infrastructure closure before the next published-data source-availability audit.

- The post-P4 source-identifier behaviors identified by external audit are pinned by direct tests.
- The temporary `force_reference` certificate canonicalization shim has been retired.
- `Discovery/physical_bridge_schema.py` is now part of the Milestone 5B mutation-harness source-attestation boundary.
- The original mutation artifact remains historical; the current re-anchored artifact is `Experiments/Falsification/milestone_5b_core_v1.mutation_results_v2.json`.
- Because `Discovery/mutation_harness.py` is also source-pinned by the Milestone 6B and post-6B mutation checks, their original artifacts remain historical and new v2 artifacts are re-anchored after this intentional shared-infrastructure change. No PySR fit/search result is rerun.
- The source-identifier Unicode gate intentionally rejects format/combining-mark categories plus a bounded set of known visually blank filler characters. General Unicode homoglyph/confusable detection remains out of scope.
- Primary NIST verification corrects the UW/CODATA RMP locators to journal p. 45 for the magnetic-damper correction discussion and journal p. 102 for the `Gundlach and Merkowitz, 2002` private-communication bibliography entry. The manifest-pinned historical UW source audit is not rewritten.
- Temporary write-enabled staging jobs are absent from the final review tree; permanent `Verify` is restored to read-only repository permissions.

These are methodological and provenance controls. They do not establish empirical validity, source resolvability, or experimental independence.
