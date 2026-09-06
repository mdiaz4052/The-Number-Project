# HUST 2018: combined uncertainty-qualified AAF MeasurementModel

PR #37 established that Supplement Section 6 prescribes a complete combination
procedure. It computed a feasibility result without adding a MeasurementModel.
The existing bridge described products of powers of inputs; that representation
could not express an additive weighted sum. This extension adds immutable Decimal
weighted terms and a mutually exclusive normalized inverse-marginal-variance
variant. Existing monomial records keep their schema and serialization unchanged;
the additive bridge record identifies itself as schema version 2.

The inputs are the frozen v2 depth-2b AAF-I, AAF-II and AAF-III reconstructions,
including each central value and total standard uncertainty. Their published
comparison values and deltas are discarded by an explicit validated projection.
Each former target becomes a derived empirical input whose source identity points
to the immutable individual artifact. All 18 central-input ancestry nodes remain
in the combined bridge's provenance and registered-target-path audits.

For each individual total standard uncertainty, compute
`v_i = u_i^2`, then `p_i = (1/v_i) / sum_j(1/v_j)` and
`G_combined = sum_i(p_i G_i)`. The shared validator independently recomputes these
coefficients. All authoritative arithmetic uses Decimal precision 50,
`ROUND_HALF_EVEN`, canonical input-ID order, and a `1e-47` absolute normalization
bound. The final coefficient is not adjusted to a residual. No inverse covariance
matrix, GLS estimator or statistical-only weighting is used.

The diagonal covariance is each individual total variance. Off-diagonal entries
sum products of absolute contributions for the same 20 non-statistical items
across runs. The statistical angular-acceleration contribution has zero
cross-run covariance. Canonical component IDs are checked along with values;
different error items never receive invented covariance. All seven principal
minors are evaluated with exact rational arithmetic on the serialized matrix.
The combined standard uncertainty is `sqrt(p^T C p)` under the bridge's
`estimator_input_propagation` basis.

| Reconstructed quantity | Value |
|---|---:|
| AAF-I weight | 0.3064936533700692456… |
| AAF-II weight | 0.3154448912771689128… |
| AAF-III weight | 0.3780614553527618416… |
| Combined G | 6.67448400654579634446… × 10⁻¹¹ m³ kg⁻¹ s⁻² |
| Standard uncertainty | 7.75320461817043125243… × 10⁻¹⁶ m³ kg⁻¹ s⁻² |
| Relative standard uncertainty | 11.616185776408652… ppm |
| Difference from displayed 11.61 ppm | +0.006185776408652… ppm |

These values are consequences of rounded upstream evidence and the reviewed
rules. Agreement with a terminal publication value is not a validation criterion.
The estimator never reads the feasibility output: it uses only the
target-independent source-rule projection frozen in the new preregistration.
Terminal comparison mutation or deletion leaves every production field unchanged.
An independent test oracle uses exact rational arithmetic for weights, covariance,
central value and variance, followed by an 85-digit Decimal square root.

The stochastic inputs are the three individual G determinations. Weights condition
on frozen uncertainty summaries; uncertainty in the estimated weights is outside
this model. Existing corrections are already incorporated into those individual
determinations. Two missing upstream provenance summaries are populated by exact
affine uncertainty transforms from their documented parents (`1e-9` for angular
acceleration and `1e-6` for the damper correction); they are not extra independent
stochastic inputs. Uncertainty-component roles are now excluded from central
ancestry under either uncertainty basis, resolving the touched DM-011 boundary.

The preregistration-only commit is
`39f3a9f4a3b3720889ac35cbe1cebfe198ac50f6`, based on
`0232b775cb34100c0ae1d15cff65459819682001`. Its SHA-256 is
`284957ec010d25bc7d5e0e64696df11b8d9c1af5358670c3a7bb7d7c2cf8961f`.
[Draft PR #38](https://github.com/mdiaz4052/The-Number-Project/pull/38) was created
at `2026-09-06T14:11:36Z`, before implementation. The PR #37 numerical result was
already known: this timestamp establishes the freezing of implementation rules,
not epistemic blindness to the answer. Preserve the preregistration commit by
merging with a merge commit.

The dimensional, algebraic-model, empirical-population, metrological-provenance
and uncertainty axes are satisfied within the declared evidence contract. The
registered-target-path result remains `no_registered_target_path`, and replication
remains `incomplete`. This is a reconstruction of published summary evidence, with
no new laboratory measurement, raw/run-level replication, independent apparatus
validation, proof of physical independence, completeness claim about nature's
error mechanisms, Lean proof of the estimator, or novel physical prediction.
