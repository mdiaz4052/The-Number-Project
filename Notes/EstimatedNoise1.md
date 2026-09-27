# Estimated noise and missed curvature — NP-ESTIMATED-NOISE-01 r1

**ESTIMATED_NOISE_1_COMPLETE · evidence_integrity=PASS · 96/96 interpretable. PROVISIONAL — INDEPENDENT AUDIT PENDING.** Completion means complete, integrity-valid evidence; it does not mean successful detection. This is one fixed synthetic epoch, not an empirical discovery or a population performance estimate.

The question was whether independently estimating uniform log-noise scale changes family rejection, and how additional paired calibration affects that change. The primary upper-95%-bound method with 64 pairs missed more curvature than the point estimate or known-noise reference at the middle noise level. Increasing the calibration budget narrowed the upper scale estimates, but neither detection nor coverage improved monotonically across individual blocks. Every adverse outcome is retained.

Sixteen independent blocks use exponents −2, −1, 1, 2 four times each. Each block has two laws and three noise half-widths, giving 96 datasets. The laws are k·x·t⁻²·zᵖ and that law times exp(0.01·(log z)²). Each dataset has 64 training, 48 validation and 64 held-out observations, plus 256 independent paired repeats. The first 16, 64 and 256 pairs form nested calibration budgets. There are 16,896 discovery observations and 49,152 calibration response values. Conditions share normalized banks within blocks; methods reuse the same complete five-class ranking. The 672 assessments are dependent and do not increase the independent sample size beyond 16.

Each pair supplies d=log(y₁)−log(y₂). The point estimate is sqrt(1.5·fsum(d²)/m). With α=0.05 and q=1−sqrt(−expm1(log(α)/m)), the operational upper scale is (max|d|+10⁻¹²)/(2q); the ideal unpadded bound is retained separately. Every decision uses T=2·scale+10⁻⁹. Equality is accepted. No threshold, seed, sample count, budget, penalty or sealed decision changed after outcomes.

**Primary comparisons (64 pairs).** Counts are curved-family rejections / 16 independent blocks; parentheses give misses / 16. The known-noise reference uses the same sealed fits and is computed only after selection.

| Uniform half-width ε | Upper95/64 | Point/64 | Known noise |
|---|---:|---:|---:|
| 0.0001 | 16/16 (0/16) | 16/16 (0/16) | 16/16 (0/16) |
| 0.0016 | 3/16 (13/16) | 9/16 (7/16) | 6/16 (10/16) |
| 0.005 | 0/16 (16/16) | 0/16 (16/16) | 0/16 (16/16) |

All adequate-law cells had 0/16 family rejections and 0/16 rank-1 abstentions under every method and budget. Family and rank-1 decisions happened to coincide across all 672 assessments, but are separately computed and retained. Every rank-1 base signature matched its generating monomial (96/96), and all rank-1 held-out errors were below the fixed approximation cutoff 0.04. Curved truths received **zero exact structural credit**, including stable selections that recovered the base exponents but omitted curvature. The 48 adequate datasets received controlled synthetic structural credit under each rule. Held-out results did not rescue pre-reveal decisions.

At ε=0.0016, moving from upper95/64 to point/64 changed 6 blocks from nonrejection to rejection and 0 in the reverse direction. Moving from upper95/64 to known noise changed 4 from nonrejection to rejection **and 1 from rejection to nonrejection**. Point/64 to known noise changed 3 from rejection to nonrejection and 0 in reverse. Every paired denominator is 16. Both directions were zero for the other two noise levels and for adequate controls.

**Prespecified secondary budgets.** The following counts are curved-family rejections at ε=0.0016. Every method/budget rejected all 16 curved families at ε=0.0001 and none at ε=0.005.

| Pairs | Upper95 rejections | Point rejections | Known-noise rejections | Upper bound covers ε, distinct matched blocks |
|---:|---:|---:|---:|---:|
| 16 | 1/16 | 8/16 | 6/16 | 15/16 |
| 64 | 3/16 | 9/16 | 6/16 | 14/16 |
| 256 | 3/16 | 7/16 | 6/16 | 15/16 |

Coverage was 15/16, 14/16 and 15/16 at 16, 64 and 256 pairs; all six matched condition copies agreed within each block, with no rounding-induced coverage disagreement. These are sixteen distinct block vectors, not 96 independent coverage trials. The observed counts do not estimate a 5% tail accurately and are not evidence that coverage was empirically 95%. Ideal and padded coverage agreed in this epoch.

For the upper-bound method, moving 16→64 pairs lost one curvature rejection and gained three; 64→256 lost one and gained one. For the point method, 16→64 lost two and gained three; 64→256 lost two and gained none. Thus a larger budget did not monotonically improve individual-block detection. All paired directions, including 16→256 and method/reference comparisons at every budget, remain in summary.json.

Scale ratios below show median [minimum, maximum], n=16, for the adequate ε=0.0016 cell. This display does not pool matched copies; all six condition-specific scale and threshold ratios and bound widths are retained in the machine summary.

| Pairs | Point / ε | Padded upper / ε | Point threshold / known threshold | Upper threshold / known threshold |
|---:|---:|---:|---:|---:|
| 16 | 0.962326 [0.786496, 1.247093] | 1.273323 [0.931483, 1.596870] | 0.962326 [0.786496, 1.247093] | 1.273323 [0.931483, 1.596870] |
| 64 | 0.970752 [0.827379, 1.061977] | 1.150506 [0.955039, 1.250183] | 0.970752 [0.827379, 1.061977] | 1.150506 [0.955039, 1.250183] |
| 256 | 0.995824 [0.946760, 1.079577] | 1.069633 [0.986811, 1.101664] | 0.995824 [0.946760, 1.079577] | 1.069633 [0.986811, 1.101664] |

The complete block pattern at ε=0.0016 follows (1=rejected, 0=not rejected; block IDs are zero-based). The other two curved noise levels have constant all-1 / all-0 patterns, and adequate controls are all 0. For each of the seven rules, summary.json contains all 16 block values and signed family/rank-1 margins for every law/noise cell, plus exponent-stratified counts with expected denominator 4. evaluation.json contains all candidate training/validation/held-out metrics, ratios, reference disagreements, structural matches and credits.

| Block | p | Upper/16 | Upper/64 | Upper/256 | Point/16 | Point/64 | Point/256 | Known |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | -2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | -1 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| 3 | 2 | 0 | 0 | 1 | 1 | 1 | 1 | 1 |
| 4 | -2 | 0 | 1 | 0 | 1 | 1 | 0 | 0 |
| 5 | -1 | 0 | 1 | 1 | 0 | 1 | 1 | 1 |
| 6 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| 7 | 2 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 8 | -2 | 0 | 0 | 0 | 1 | 1 | 1 | 1 |
| 9 | -1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 11 | 2 | 1 | 0 | 0 | 1 | 1 | 1 | 1 |
| 12 | -2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 13 | -1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 15 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Primary middle-noise exponent-stratified rejections for p=(−2,−1,1,2), each out of 4, were upper95/64=(1,1,1,0), point/64=(2,2,3,2), known noise=(1,1,2,2). The strata were fixed before generation.

**Conditional inference and limits.** Under independent centered uniform errors, F(t)=P(|e₁−e₂|/(2ε)≤t)=2t−t². The chosen q satisfies F(q)^m=α, giving ideal marginal upper coverage 1−α at each fixed budget. For the adequate law, a training-only intercept fit leaves each validation residual bounded by 2ε. Conditional on a sufficiently large upper scale, the complete family cannot be rejected. This yields the assumption-dependent marginal family-rejection bound, subject to the declared numerical qualification. It is neither a formal Lean proof nor a rank-1 correctness, simultaneous-coverage, posterior-probability or real-data guarantee. The finite hash-based PRNG is not an ideal continuous source. The point estimate has no coverage guarantee. Repeats cannot reveal shared drift that cancels; correlated/heteroscedastic errors, unknown distributions, feature errors, outliers and missing repeats are outside scope. Nonrejection does not establish truth.

**Custody and numerical evidence.** The work order and prepared preregistration were read and hash-verified. The science digest remained `19edaba69d1b2cd8b4d0235180d548eac6387b0b564863c0109a7fec6fb4c312`. CPython 3.12.14, its executable hash/platform, and the complete source closure are pinned in preflight.json. Calibration workers received anonymous pairs and fixed settings only; discovery workers received anonymous training/validation rows and the sealed upper95/64 threshold only. Accepted staged-runner receipts prove source reads, fresh missing caches and the declared dependency inventories under trusted-code isolation; no hostile-code sandbox or global blinding is claimed.

| Epoch | Commit |
|---|---|
| Actual launch base | `0b3d31269c7fde9a75e9d7045ff483e71b4b9f4f` |
| Consumed instruction snapshot | `5c362165d80f60ccd7232a15ac459cdbff33f179` |
| Sole-file preregistration freeze | `e7670b8218f7cfd129529dc8afb8bc8f96ad2e09` |
| Qualified source | `da9e8fcf746e418629e9b769f9e354c449562aa5` |
| Published sole-file seed commitment | `dc7a04482a58fda9f97421d62efd90f98a3ed149` |
| One fixed data bank | `cbdc511215c26709037a893bebceaa782230570c` |
| Calibration seal | `df5a9b733f441f739506595de80ca7c771274610` |
| All operational decisions sealed | `aeab31d9cc803b6b6932009d6ed70dc6f378317b` |
| Reveal and immutable raw result | `c4d43e48b36e88d78ddd1e4a1cd7c8e0d683eefe` |

Draft PR #61 was created at 2026-09-25T14:51:20Z, strictly after the 14:51:04Z freeze. The actual remote seed head was read back before generation; the receipt is in commitment.json. All 288 budget estimates and 576 operational assessments were committed before the post-seal known-noise/held-out evaluation. There were 480 principal fits plus 96 inherited group diagnostic refits; secondary thresholds introduced no new fits.

Pre-seed qualification retained five attempts. Attempts 1, 2 and 4 failed (exponent serialization schema, chronology-test exception handling, and a generator group-label interpretation); 3 passed the then-current fixtures, and 5 passed the complete qualification. Every failed source snapshot and test log remains in preflight_attempts. A preserved whitespace check identified inherited final blank lines in two exact historical source copies; the archive-local attributes exempt only those copies while preserving their bytes. No existing shared source, workflow, dependency or historical artifact was changed. No scientific-stage failure, replacement seed, omitted dataset or rerun occurred.

Qualification included 640 calibration corners, 192 candidate-arithmetic corners, alternate alpha/budget policies, all ten designated semantic mutation kills, and surviving baseline/equivalent controls. Deterministic engineering seeds were explicitly separate from the prospective seed and supplied no study evidence. All actual records were checked again after reveal using independent 80-digit Decimal arithmetic. Maximum observed-log difference error was 2.124e−16, maximum error against intended paired differences 1.684e−15 (both below 1e−12), and maximum candidate metric discrepancy 4.052e−16 (below 1e−10). Adequate true-class residual bounds passed. No allowance was enlarged.

**Read-only validation and audit routing.** Run `python3.12 -B -m Discovery.estimated_noise1_portable_verifier check` and the focused `python3.12 -B -m unittest tests.test_estimated_noise1 tests.test_estimated_noise1_portable -v`. The verifier checks committed used-source epochs and receipts, never permanent equality of future shared working-tree modules; it does not generate observations or refit the scientific epoch. verification_routes.json explicitly distinguishes the raw result and retained pre-seed operational failures. The immutable raw result SHA-256 is `279324653fb9556fc8460dc4ff41b1d6cd5e049c438870a07f8bc81992a2fb03`. Final-head CI and the ready-to-use reviewer prompt are attested externally in PR #61 and the canonical GPT handoff, avoiding self-hashes.

Independent review must adjudicate DM-093 at this estimated-scale boundary, the coverage derivation and numeric allowance, calibration/target separation and matched dependence, complete inventory and training-only fits, both directions of paired changes, structural-credit limits, failure-aware dispositions, source pins and true-merge chronology. Existing DM-090/094/097/098/100 scopes remain with Claude; no global finding closure is asserted. No evidence-card API call was added. PR #60’s audit remains deferred. The independent audit has not been launched. Leave this PR unmerged for Miguel, using **Create a merge commit only** if subsequently authorized; never squash or rebase the evidence chain. No release or follow-on study is authorized.

A post-science push of head `5cf61eaa53c82195bd95eaa591741a7bb81c3c87` failed with an HTTP 400 / sideband disconnect. One authorized identical-object retry with a larger HTTP buffer succeeded, and the remote head was read back. Root cause is not established. The complete combined original tool output, separate retry streams, and before/after remote reads are retained in [the supplemental operational receipt](EstimatedNoise1/operational_failures/publication-01.json); [its explicit route](EstimatedNoise1/verification_routes.json) is separate from the already sealed scientific package. The initial failure did not have separately captured OS streams or an exact timestamp; that limitation is explicit. Scientific completion and independent-review status are unchanged.

Final-head CI at `543ace1d15c033e2d0190401675dd9837278ba3b` exposed a post-science verifier portability failure: 911 of 912 tests passed, but an exact comparison to Linux libm `exp` rejected feature provenance. Lean passed. The complete original job log and explicit retention limitation are in [the CI failure receipt](EstimatedNoise1/operational_failures/ci-344.json). The work order's permitted detached, source-pinned read-only correction is [recorded here](EstimatedNoise1/portable_verifier_manifest.json). It checks coefficient/feature exponentiation against 80-digit Decimal within one binary64 ULP, a faithful-rounding engineering criterion independent of the current platform's libm. Every other generation check is unchanged. The original verifier remains available, the original failure is not relabeled as a pass, and no scientific pad, score, decision, observation, source epoch, result or sealed artifact was altered. This post-outcome correction requires explicit independent review. The focused test's import now routes through the detached verifier; its pre-seed version remains pinned at the scientific source commit.

The preceding published report head `5cf61eaa53c82195bd95eaa591741a7bb81c3c87` also completed CI with the identical verifier failure in Verify #343; its separate full log and [failure receipt](EstimatedNoise1/operational_failures/ci-343.json) are retained. Both failed runs remain visible. Their copied logs preserve original whitespace through exact-file attributes only.
