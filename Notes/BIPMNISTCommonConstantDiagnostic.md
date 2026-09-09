# BIPM–NIST common-constant diagnostic

**PROVISIONAL — INDEPENDENT AUDIT PENDING.** This result consumes PR #47
(implementation head `621f5ddc938bc62273eac42004e56d940ef376fa`, merge
`4e8acdebc5b03d03d5039c24a73bcc37e44711e2`). The retrieved independent acceptance
ends at PR #46. The freeze-time audit record is provenance, not a mutable input
or a claim that a later audit has occurred.

## What is computed

Two separate, nominally calibrated diagnostics use fixed summary covariance
matrices and zero-mean jointly Gaussian errors as working assumptions. One asks
whether the four NIST determinations fit one mean. The other compares the
existing project-defined BIPM and NIST aggregates over every admissible aggregate
correlation. Neither yields a combined estimate of G. Neither assigns a
probability that G is constant, identifies a bias or physical cause, or validates
the apparatus. They are not combined into a single test or independent evidence.

The exact operational cutoffs are 7.814728 (three degrees of freedom) and
3.841459 (one degree of freedom); equality is not flagged. Their independent,
data-free percentile check preceded freeze and is recorded in the protocol.
NIST's [chi-square reference](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3674.htm)
supports the upper-tail calibration. The six-decimal cutoffs are project choices,
upward-rounded from the 95th percentiles, rather than quotations of its table.
No p-values are computed. There is no joint 5% error-rate claim. Nominal
calibration under fixed, known summary covariances is not an experimental
error-rate guarantee for rounded, estimated uncertainty budgets.

## Input conventions and source limits

All G coordinates use U = 10^-11 m^3 kg^-1 s^-2. BIPM's exact reconstructed
midpoint b is held fixed as the common uncertainty reference. The new variance
is v_B = b² r_B / 10^12. Scaling its whole relative covariance matrix by the
same positive factor preserves its inherited minimum-variance weights. This
project convention does not recover hidden author covariance and does not
rescale the two component errors by their separate midpoints. The full BIPM
aggregate enclosure is used, without intersecting a published terminal cell.

The [corrected BIPM treatment](https://doi.org/10.1098/rsta.2014.0032), section
11(d), describes correlated minimum-variance combination. The review could
inspect indexed publisher passages, but direct full publisher/PDF access failed.
The prior corrected source attestation is inherited; no new primary-PDF byte
verification is claimed. Its source access limitation remains explicit.

NIST's covariance remains V_ij = rho_ij (x_i s_i/10^6)(x_j s_j/10^6), using
Table 18's precise uncertainties and the frozen four-input order. In the
[NIST paper](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075),
pp.3–5 document the apparatus lineage and shared collaboration; pp.25–27
distinguish experimental correlations from the Bayesian/dark-uncertainty layer;
pp.27–28 discuss unresolved discrepancy. Table 18 describes within-NIST
correlations. These reviewed passages do not numerically identify the
cross-campaign covariance. This is bounded non-identification, not exhaustive
absence. Inaccessible BIPM evidence is distinguished from accessible NIST
material. The full rho interval [-1,1] is a mathematical covariance class, not a
measured uncertainty interval or a prior for rho.

The uncorrelated rho=0 reference is hypothetical. New personnel and location
do not establish statistical independence. Table 19, the Bayesian consensus,
CODATA, printed terminal values, rounded final errors and target-conditioned
intersections do not enter the numerical projection. Earlier NOT_EVALUATED,
NO_GO and NOT_AUTHORIZED states remain unchanged; this protocol authorizes its
own comparison.

## Derivations

Let z = V^-1 1 and w = z/(1^T z). The consumer verifies the inherited weights
through sum(w)=1 and Vw=v_N 1, rather than recalculating weights over cells.
With n=w^T x, the residual statistic is

Q_N = (x-n1)^T V^-1 (x-n1) = x^T A x,

A = V^-1 - zz^T/(1^T z).

To see the distribution and rank, whiten x by V^-1/2 and write
q = V^-1/2 1 / sqrt(1^T V^-1 1). Then A is the congruence of I-qq^T
by V^-1/2. The middle matrix is an orthogonal projection with rank three.
Under the common-mean Gaussian null, Q_N is the sum of squares of three
independent standard-normal residual coordinates. Thus the reference is
chi-square with three degrees of freedom. Exact arithmetic checks both Q
formulas, A1=0, determinant(A)=0 and a positive principal 3x3 minor.

For any display perturbation delta with |delta_i| <= h_i,

Q(x+delta) = Q(x) + 2 delta^T Ax + delta^T A delta.

The absolute linear term is at most L = 2 sum h_i |(Ax)_i|. Positive
semidefiniteness gives delta^T A delta >= 0; its absolute-entry bound is
E = sum h_i h_j |A_ij|. Therefore [max(0,Q-L), Q+L+E] is a certified outer
bound. It need not be the exact range. The fitted mean moves with the cell
values; covariance and weights remain fixed. No optimization or additional
random rounding error is introduced.

The aggregate contrast D=b-n has variance v_B+v_N-2 rho sqrt(v_B v_N).
Under its separate Gaussian common-mean null and positive variance,
D/sqrt(v_D) is a standard normal, so its square has one degree of freedom.
For rho in [-1,1], the variance extrema are (sqrt(v_B)±sqrt(v_N))².
For an interval of differences, let a_min and a_max be the extrema of |D|.
When v_B != v_N, the exact all-display, all-rho extrema are

a_min²/(sqrt(v_B)+sqrt(v_N))² and a_max²/(sqrt(v_B)-sqrt(v_N))².

Every endpoint is attainable within the specified aggregate class and display
intervals. Hence the mixed classification really means there are choices on
both sides of the strict threshold. There is no rho grid approximation. If the
marginal variances are equal, rho=1 is singular; the closed-family classification
is UNRESOLVED_SINGULAR_ENDPOINT, with rho=0 still separately available. No
regularization, division by zero, or silent endpoint exclusion occurs.

All comparisons use the exact sign of a+b sqrt(r). If a,b have the same sign,
that sign is immediate. If their signs differ, the sign is sign(a) times the
sign of a²-b²r; zero terms are handled first. Thus squaring never loses a sign
condition. The artifact serializes rational operands, radical denominators,
and exact comparison signs. Decimal readings are not certificates.

## Results under the declared model

These decimals are for readability; the JSON artifact contains the exact values.

| Diagnostic | Value or range | Operational cutoff | Disposition |
|---|---:|---:|---|
| NIST displayed-midpoint Q_N | 25.0383749520680043 | 7.814728 | FLAGGED_UNDER_DECLARED_MODEL |
| NIST display-cell conservative Q bound | [24.9984677125400346, 25.0783261791220178] | 7.814728 | FLAGGED_FOR_ALL_DISPLAY_VALUES |
| Aggregate T at rho=0, displayed midpoints | 78.5336863997741613 | 3.841459 | FLAGGED_UNDER_DECLARED_MODEL, hypothetical rho=0 |
| Aggregate exact all-rho/all-display range | [39.2548696181928982, 7291.09639575431611] | 3.841459 | FLAGGED_FOR_ALL_RHO_AND_DISPLAY_VALUES |

The signed midpoint difference is +0.00192040441441399320 U; its display
interval is [0.00191490441441399320, 0.00192590441441399320] U. The declared
model is flagged by both diagnostics under the stated uncertainty/dependence
assumptions. NIST's experimental-only common-mean model is already challenged
internally. The cross-campaign result remains conditional under that same
model; it is not independent confirmation and does not establish non-universality
of G. Neither variance inflation nor configuration removal has been applied.

## Chronology, provenance and verification

The source review, specification preparation, upstream validation and cutoff
check preceded the sole-file freeze `bf310acdbbef61100efa50fe411ae7873593db4c`.
GitHub created draft PR #48 at 2026-09-09T02:59:14Z. Diagnostic implementation,
this result-bearing note and source-attestation serialization followed the
anchor. Prior outcomes and source discussion were known: outcome_blind=false.
The final source snapshot is committed before artifact emission; artifacts
exclude themselves from source closure. A true merge commit is required.

The seven upstream files have full SHA-256 pins and exact field selectors.
Only selected fields reach typed numerical inputs. Behavioral invariance to
forbidden fields is tested independently of whole-file digest rejection.
Tests instrument actual file opens and Git reads, including helper-source
hashing and bounded history metadata. No HUST authorization or E-001 surface
is read. Existing scientific modules and shared infrastructure are unchanged.
The numerical oracle uses permutation/cofactor inversion, distinct from the
production elimination. Synthetic tests cover invariances, box corners,
threshold equality, correlation dependence and singular geometry. The separate
mutation record supplies eight production kills and calibrated execution;
only designated assertion failures score. CI supplies final Lean attestation.
