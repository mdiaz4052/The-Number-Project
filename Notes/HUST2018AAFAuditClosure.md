# HUST 2018 AAF post-audit closure record

Base: `56b1144990f2482f1b791289945fde5ee047aa5d` (merged PR #26).

Purpose: close Claude's N1-N8 findings from the HUST 2018 AAF source-availability audit without implementing a `MeasurementModel` or changing the production physical-bridge schema.

## Closure map

- **N1:** classifier prose and behavior now distinguish an affected experiment from the global decision. A contaminated path removes that experiment; `PARTIAL` occurs only when no AAF determination retains a clean depth-2a path.
- **N2:** the magnetic-damper correction direction is machine-readable and pinned as `multiply_by_1_plus_delta`, with its source locator and displayed equation fragment recorded separately from the correction magnitude.
- **N3:** each direct summary input carries reviewed source-scope tokens and a pinned direct transcription. Numeric column substitution and scope-token swaps are rejected.
- **N4:** current output uses `maximum_assessed_replication_depth`; the frozen preregistration's older `maximum_supported_replication_depth` wording is preserved but explicitly superseded by a pinned post-audit clarification. Depths above 2a are `not_assessed` because four listed Source Data files were not successfully retrieved.
- **N5:** the current headline includes the authorization count: `GO / 2a (3 of 3 AAF determinations authorized)`.
- **N6:** a byte-pinned second-reader semantic-source record confirms the `P_g,l,m` target-dependency boundary, magnetic-damper direction, and Table-3 scope/air-density statement. It is explicitly human semantic verification, not automatic PDF comprehension.
- **N7:** a permanent workflow test requires every future `contents: write` workflow to carry both a bot-loop guard and an exact branch/head-ref guard.
- **N8:** printed values and one-standard-deviation uncertainties for the public `P_g` sum, corrected angular acceleration, and magnetic-damper inputs are now machine-readable and checked against the printed notation.

## Staging record

A one-shot finalizer workflow was used to regenerate the deterministic audit manifest. It was restricted to the exact branch `codex/hust-2018-aaf-audit-closure`; the new workflow-safety test inspected and passed that workflow while it still existed. The finalizer then removed itself before committing the regenerated manifest, ran the full Python suite from a clean committed tree, and pushed only after success.

Finalizer run: `33760301098` — success.

The temporary workflow is absent from the final branch tree.

## Scientific boundary

The scientific conclusion is unchanged: the retrieved public record supports the assessed depth-2a central-value reconstruction for AAF-I, AAF-II, and AAF-III. Depth 2b remains withheld, the combined AAF estimator remains unauthorized, and depths above 2a are not assessed rather than declared unsupported.
