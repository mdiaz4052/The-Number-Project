# NIST n=4: bounded mutation-validation completion

This additive implementation note completes the eight `mutation_requirements`
already frozen in PR #47 at `504200ae817a60b211decec4432b43be9087e9e3`.
It is not a new scientific experiment or a retrospective change to preregistration.
The existing estimator, result artifact, prior notes, source attestation and freeze
remain byte-identical to the previously green head `a1ad8f0d3d210218212641f3b4dcabe3ac25c2a8`.

## Additional validation surfaces

The frozen planned-file list did not enumerate the production-mutation machinery.
The additional surfaces are explicitly declared here rather than editing that list:

- `Discovery/nist_2026_n4_experimental_estimator_mutations.py`
- `tests/test_nist_2026_n4_experimental_estimator_mutations.py`
- this note
- `Experiments/GMeasurements/nist_2026_n4_experimental_estimator_mutations_v1.json`
- one additional read-only mutation `--check` in the existing Verify workflow.

The eight cases correspond in order to the frozen requirements: remove off-diagonal
correlations; round Table 18 uncertainties to whole-ppm labels; omit the absolute
covariance scaling; omit the fourth aggregate term; read the Bayesian comparison
value into the estimator; collapse display cells; ignore negative weight signs;
and omit unbiased normalization. All are actual edits of the production estimator
source in disposable directories, not edits of frozen input or expected answers.

An independently implemented determinant-by-permutations/Cramer's-rule oracle
checks the four-input weights and aggregate, rather than calling the production
Gaussian-elimination routine. A 16-corner enumeration verifies the linear image
of the real four-dimensional display box and a synthetic signed-weight box.

The unmutated baseline must survive all designated tests. A separate asymmetric-cell
calibration must fail its own oracle. An executable nested-Fraction equivalent
calibration must survive. Only designated assertion failures count as kills.
Collection, syntax, import, runtime, source-state, history, skip, and subprocess
failures are invalid evidence. The normalization test turns only the precise
numerical rejection of a valid input into an assertion failure. A forbidden
filesystem/subprocess access is itself an explicit target-independence assertion;
missing files are never counted as kills.

The parent harness verifies the unchanged preregistration, implementation chronology,
source bytes and Git ancestry before mutation execution. Behavioral sandbox tests
read a hash-checked frozen fixture and need no Git history; no production history
guard is monkeypatched or bypassed. Python `-I -B`, validated module paths before
and after execution, and an empty sandbox-local `tests/__init__.py` prevent imports
from another checkout. Every copied file, oracle and the shared runner are in the
mutation artifact's source snapshot.

The mutation `--check` only validates records, complete metadata, source identity,
source ancestry, calibration, and canonical serialization. It does not re-execute
a previously attested family. Counts and validity are derived from the complete
ordered records; recorded top-level counts cannot substitute for those records.
A new permanent test also observes the n=4 builder's file reads, including direct
open calls and Git blob reads, and checks its declared NIST-scoped closure.

## Primary-source transcription cross-check (2026-09-09 UTC)

Source: Schlamminger et al., *Metrologia* **63** (2026) 025012,
DOI `10.1088/1681-7575/ae570f`.
NIST-hosted peer-reviewed PDF:
`https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075`.

The implementer re-opened this PDF and visually inspected Table 18 on the page
labelled **26** (PDF sheet **27** counting the cover, screenshot index **26**).
Its four bold diagonal standard uncertainties are **23.2, 30.3, 37.5, 93.9 ppm**.
The upper-triangular correlations, in frozen input order, are
**0.42, 0.38, 0.12, 0.23, 0.23, 0.25**. Table 17's Combined row on the same page
agrees with the four uncertainties. This is direct source-reading evidence for
the transcriptions; positive definiteness alone would not establish them.
Table 16 is on the page labelled **25** (PDF sheet 26, screenshot index 25).
These explicit page conventions clarify the shorter locators in frozen records.
This cross-check is by the implementer, not an independent Claude attestation.
No raw PDF byte custody, stored PDF hash, or resolution of every part of DM-078
is claimed.

## Scientific boundary

No numerical estimator or covariance policy changes. The displayed covariance
summary is held fixed; its own rounding ambiguity is not propagated. The exact
linear image is solely publication-resolution ambiguity conditional on fixed
weights. It is neither a confidence interval nor an uncertainty budget.
The standard uncertainty remains conditional on experimental covariance only,
excluding NIST's configuration-specific dark uncertainty. Minimum variance and
unbiasedness refer to the declared fixed-covariance/common-mean linear model;
they do not establish that all physical biases in the observations are absent.

The result is not NIST's Bayesian equation (64), and no comparison with BIPM,
CODATA, or that equation is performed. An eventual common-constant test needs
its own error model and treatment of cross-experiment dependence; merely testing
intersection of narrow display-rounding cells cannot establish statistical
incompatibility of physical measurements. No outcome-blind claim is made.

True merge commit only. Preserve the original freeze and prerequisite ancestry.
