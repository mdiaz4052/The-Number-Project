# HUST 2018 pre-MeasurementModel micro-cleanup

This bounded cleanup closes Claude's PR #27 follow-ups F1-F4 before the HUST AAF MeasurementModel milestone.

- F1: write-capable GitHub Actions permissions are detected across `write-all`, whitespace variants, quoted `write`, workflow-level permissions, and job-level permissions.
- F2: correctly guarded folded/multiline job-level `if:` expressions are accepted.
- F3: the policy is explicitly job-level; a step-level guard does not protect a write-capable job.
- F4: the nine direct HUST AAF source locators are independently pinned so a wrong AAF column locator cannot remain green while the numeric transcription stays unchanged.

No HUST estimator, MeasurementModel, uncertainty policy, source-audit decision, physical-bridge schema, or scientific claim changes in this cleanup.

The next milestone should preregister depth-2a reconstructed `G` with no reconstructed combined standard uncertainty (`standard_uncertainty = None`) and implement AAF-I, AAF-II, and AAF-III separately, with no combined estimator while the source audit withholds combined reconstruction authorization.
