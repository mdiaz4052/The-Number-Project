# NIST campaign paired-torque uncertainty feasibility

**PROVISIONAL — INDEPENDENT AUDIT PENDING**

This implements the supplied September 10, 2026 specification on base
`6f722e92a09bc598aa06920e89ba02059bf1e7a4`, the true merge of PR #50.
The sole-file freeze is `5e104cd4a070167e2354619d473043f2528f169b`;
GitHub created draft PR #51 at **2026-09-10T13:31:25Z** with that head.
The local preparatory commit `6412bbf2b9dfbd4e6f672f4e95a9d356986fa117`
was not pushed because shell Git had no write credential. The authenticated
GitHub connector published the same sole-file bytes under the actual freeze SHA.
That unpublished local commit is not PR ancestry or the chronology anchor.
No evaluator, implementation attestation, result note or feasibility calculation
preceded the published freeze and draft anchor. `outcome_blind=false`: the visible
Table 15 values, published offsets and previous project results were already known.

The deterministic disposition is **NO_GO_CONTRAST_UNCERTAINTY**, bounded to the
reviewed article and accessible discovery material. The paired recovered-signal
comparison is described in the source. Its correction-stage completion and
combined uncertainty for the three equality contrasts are not established by this
corpus. This is a source-sufficiency result, not a rejection of a common torque
shift and not a finding that a required uncertainty object cannot exist.

| Axis | Finding |
|---|---|
| Comparison | Source describes both methods recovering the campaign torque difference; no demonstrated signal mismatch asserted |
| Type A | Eight standard-uncertainty marginals; within-pair and cross-campaign dependence unresolved |
| Combined contrast uncertainty | Unidentified; **C remains null**; partial Type A information is retained only for the as-published entries |
| Mean correction | Exact Table 15 correction convention remains unresolved for several effects |
| Meaning | Type A marginals and later conservative/noncentered assignments do not specify a centered campaign covariance |
| Precision | Exact arithmetic on reported decimal quantities, without recovering undisplayed precision |
| Sampling calibration | Not established for a future campaign-contrast test |
| Source access | No specific essential supplement identified; publisher associated-material index not fully reviewed |

## The restricted question

Use the eight summaries in this exact order:

```text
copper_0_servo, copper_0_free, copper_120_servo, copper_120_free,
copper_240_servo, copper_240_free, sapphire_servo, sapphire_free
```

Each entry is already a difference between source-mass positions. The proposed
between-method subtraction is a distinct operation, with no new amplitude factor.
The canonical-to-paper row-major permutation is `[3,2,5,4,7,6,1,0]`.
Clocking labels identify campaigns. Pairing does not establish simultaneous samples,
independence, or shared absolute error loadings.

In the stated working mean model, `E[y_star] = E t + b tau`, the four campaign
signals `t` are unconstrained. Free deflection is not assumed to be unbiased.
`B` subtracts free from servo within each pair; `R` subtracts the sapphire pair
from each copper pair. Thus

```text
A = R B =
[ 1,-1, 0, 0, 0, 0,-1, 1 ]
[ 0, 0, 1,-1, 0, 0,-1, 1 ]
[ 0, 0, 0, 0, 1,-1,-1, 1 ]
```

The exact certificate verifies `B E=0`, `B b=1`, `R 1=0`, `A E=A b=0`,
`rank(B)=4`, `rank(R)=rank(A)=3`, `rank([E,b])=5`, and
`ker(A)=col([E,b])`. The kernel result follows from exact inclusion and equal
dimensions. An invertible change of contrast coordinates preserves this restriction.
No observed `B y_star` or `A y_star` is evaluated.

Only `C=A V_y A^T` is required. A directly authorized C suffices without identifying
all of `V_y`, all four differences' covariance, or a common offset's uncertainty.
The implementation supports direct C, projected `V_d`, projected `V_y`, and a
single finite signed joint sensitivity/input model `A J U J^T A^T`. It preserves
cross terms and uses squared unit conversions, exact symmetry/PSD tests and rank.
No nearest-PSD adjustment, jitter, pseudoinverse outcome calculation or numerical
response differentiation is present.

## What is known and what is missing

The artifact records the Type A marginal contribution as a **partial matrix
expression**, together with all 28 explicitly unknown covariance terms and their
exact coefficient matrices. This expression belongs to as-published Table 15 y. Its transfer to a corrected
y_star is unresolved; it is not licensed as a component of the requested combined
C without the stage/correction map. The diagonal contribution is not a covariance
completion and must not be used as an independence covariance. For example,
`Cov_A(y_0,y_1)` has coefficient `-2` in the first contrast variance. Within-pair
dependence therefore survives this restriction. Cross-campaign terms also survive.
No missing entry is assigned zero.

Table 15 reference torques are frozen as transcription context. They are not used
as linearization anchors because no authorized source uncertainty conversion needs
them in this implementation. Changing those references or excluded final-G,
dark-uncertainty and published-offset context leaves the computed uncertainty and
authorization unchanged in behavioral tests, beyond file-digest rejection.

The finite inventory has ten rows. The free-mode frequency/inertia/anelasticity
items are grouped because they belong to the same mechanical extraction path.
Background and empty-disk uncertainty are routed together for stage review, with
an explicit requirement to distinguish a torque residual from a conversion-only
mass-integration validation. Autocollimator scale and nonlinearity stay separate.
The frozen JSON gives positive locators, supplied information, correction status,
coordinates, evaluation method, missing loadings/dependence and smallest repairs.

Priority repairs are:

1. Clarify the transformations already reflected in Table 15, including pressure
   extrapolation and free-mode corrections, and confirm the intended campaign
   signal under seating/drift and calibration changes. The finite servo-gain
   correction is described as added at the torque stage and must not be reapplied.
2. Supply the combined uncertainty for `A y_star`, or an equivalent sufficient
   joint object with signed loading, correction, linearization and interpretation
   declarations. Type A dependence alone already prevents identifying its complete
   projected contribution from the present marginals.
3. If direct C is unavailable, supply the surviving campaign-level autocollimator,
   electrical, mechanical, background and extrapolation uncertainty/cross terms.
   Unknown shared apparatus loadings are not certified as equal absolute loadings.

A common relative-method loading `b` survives B but is annihilated by A. Its
unknown variance and cross-covariance are irrelevant to this equality restriction,
although they matter to estimating the common magnitude. Effects in `col(E)`
cancel even earlier. Neither shared calibration nor full correlation alone proves
these loading identities.

## Source and interpretation boundary

The controlling publication is Schlamminger et al., *Redetermination of the
gravitational constant with the BIPM torsion balance at NIST*, *Metrologia* 63
(2026) 025012, [DOI](https://doi.org/10.1088/1681-7575/ae570f),
[NIST journal PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075),
CC BY 4.0. The supplied specification provides the detailed bounded locator map
and prior visual transcription. This run read parsed primary-source passages in
sections 3, 7.7, 8 and 9, the article's end matter, publication download links and
one targeted associated-material search. No linked campaign covariance resource
was identified. Direct DOI/publisher requests returned access errors; the index
was not fully inspected. No essential named supplement was shown inaccessible.
The prior PDF hash is explicitly attributed to PR #50, not newly measured here.
Hashes bind bytes; they do not independently validate transcription or absence.

Table 14 concerns relative G shifts and marginal assignments. The nearby
full-correlation instruction concerns four final results, not eight torque
summaries. Tables 17–18 cannot be transferred or inverted to obtain campaign
covariance. A nonzero systematic shift combined in quadrature with spread is not
silently relabeled centered sampling covariance. General
[JCGM 100 guidance, section 3](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/03_e.html)
and [section 5](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/05_e.html)
explain uncertainty evaluation and covariance propagation; they supply none of
this experiment's missing dependence.

PR #50 supplies motivation and the protected final-summary interpretation boundary.
This campaign route does not reconstruct copper aggregation or supersede its
`NO_GO_IDENTIFIABILITY`. Neither #50 nor #47–49 builders/result artifacts are
scientific inputs. Shared history helpers are code dependencies. E-001 remains
outside file/import, numerical and claim boundaries. Claude Current and routed
patterns were inspected; targeted searches/Deferred listing did not retrieve the
specified overlapping detail files. No Claude-owned ID is assigned or closed.

## Verification and limits

Exact synthetic controls exercise all four uncertainty routes, same marginals
with different C, entire irrelevant unknown loading spans, noncanceling shared
loadings, larger differential calibration sensitivity, singular covariance,
stage/type-A/meaning boundaries, missing corrections and all six dispositions.
They are not fitted NIST covariances or proof about every possible source completion.
Eight frozen production mutations must fail only their designated behavioral
assertions; baseline and equivalent controls survive and a faulty calibration fails.
Import/syntax/runtime/skip/provenance failures receive no semantic kill credit.

Sources are committed before deterministic artifact emission. The strict freeze
verifier and full-history introduction checks bind the GitHub anchor. The scoped
source selector skips a merge inheriting the full relevant state from a parent,
but identifies a changed conflict resolution as a new source snapshot. Both CLI
`--check` paths are offline/read-only and do not rerun the mutation family. Tests
observe actual file/Git reads and repository imports, including runner evidence.
Exact-head CI and the final validation report provide the automated gate; this
note does not impersonate an independent audit or predeclare passing runs.

No observed paired differences, residual contrasts, common torque fit, real-data
statistic, p-value, confidence interval, corrected torque or G value is produced.
No campaign is discarded and no physical mechanism is chosen. Even a future GO
would authorize only a separate statistical specification. The source-request
companion is a reviewable document only; no correspondence was sent.

**Integration:** leave PR #51 unmerged for Miguel; eventual **Create a merge
commit**, never squash or rebase. Independent scientific audit remains pending.
