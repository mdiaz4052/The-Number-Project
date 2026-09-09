# BIPM–NIST bounded mutation validation

The eight production mutation IDs and their designated behavioral tests were
frozen before implementation in the new diagnostic preregistration. The
new harness adapts the prior isolated runner pattern without changing shared
infrastructure. No unrelated historical mutation family is rerun.

| Frozen requirement / production mutation | Behavioral oracle |
|---|---|
| covariance_off_diagonal | Hand-computed inverse of [[2,1],[1,2]] retains -1/3 off-diagonals |
| bipm_ppm_squared_scaling | b=3, r=25 gives 225/10^12 in absolute units squared |
| cross_covariance_sign | Marginal variances 1,4 and D²=9 give opposite cutoff dispositions at rho=-1,+1 |
| display_cell_collapse | A=I-J/4, x=(0,0,0,4), h=1/10 gives Q=12, L=6/5, E=3/50 |
| df_cutoff_mapping | Three degrees of freedom maps to 7.814728; one to 3.841459; equality is not flagged |
| omitted_mean_fitting | Direct residuals subtract the fitted mean from all four entries |
| forbidden_terminal_consumption | Actual selector remains invariant when comparison-only final G changes |
| unsupported_claim_promotion | Output remains explicitly conditional and independently unaudited |

The covariance and mean-fitting mutants are scored at their actual production
numerical primitives, so a later identity guard throwing an exception cannot
masquerade as a kill. The terminal-consumption mutant is scored at the actual
production projection selector. Full-consumer forbidden-field invariance and
observed read-closure tests are separately provided in the diagnostic tests.

A surviving unmodified baseline runs all designated tests. A faulty interval
endpoint control must be killed. An algebraically equivalent b² scaling control
must survive. Copies use Python -I -B and validated imports in a disposable
workspace, with a temporary tests package initializer. Production source byte
images and test identities are recorded. Syntax, import, runtime, skipped-test,
history, source-state, missing-evidence and infrastructure failures earn no
kill credit. The test suite includes actual invalid import/syntax executions.

Generation runs this bounded family once after source commit. The read-only
--check validates source pins, mapping, import records, counts, calibration,
byte images and the derived envelope without rerunning it. Rebuild is required
if a result-driving source in this family's bounded closure changes.
