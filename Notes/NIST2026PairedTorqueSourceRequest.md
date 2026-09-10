# Draft technical source request: campaign torque contrast uncertainty

**DRAFT — NOT SENT. PROVISIONAL — INDEPENDENT AUDIT PENDING**

Prepared by GPT for Miguel Diaz / The Number Project, September 10, 2026.
This document concerns a narrow source-interpretation question; it alleges no
defect in the publication. No message, recipient contact, scheduling or monitoring
has been performed.

Reference: Schlamminger et al., “Redetermination of the gravitational constant
with the BIPM torsion balance at NIST,” *Metrologia* 63 (2026) 025012,
[DOI 10.1088/1681-7575/ae570f](https://doi.org/10.1088/1681-7575/ae570f),
[NIST journal PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=961075).

We are documenting whether Table 15 supports a later comparison of the expected
servo-minus-free torque difference across copper clockings 0°, 120°, 240° and
sapphire. We have **not tested a common offset, calculated observed paired
contrasts, fitted a torque magnitude, or produced corrected G values**.

Let y contain Table 15's eight recovered source-position torque differences in
this order, using N m internally:

```text
copper_0_servo, copper_0_free,
copper_120_servo, copper_120_free,
copper_240_servo, copper_240_free,
sapphire_servo, sapphire_free
```

Each pair uses servo minus free. Let `y_star` denote the same summaries under the
appropriate specified correction convention. We seek the uncertainty associated
with `A y_star`, where

```text
A = [ 1,-1, 0, 0, 0, 0,-1, 1 ]
    [ 0, 0, 1,-1, 0, 0,-1, 1 ]
    [ 0, 0, 0, 0, 1,-1,-1, 1 ].
```

These are three contrasts relative to sapphire. They retain all four campaigns;
choosing sapphire merely fixes coordinates. Pairing does not assume simultaneous
samples or designate either method as unbiased. The source-position difference
already inside each table entry is distinct from this method subtraction.

Could you clarify the following, in order?

1. **Correction and comparison stage.** Which corrections, averaging and
   extrapolation steps are already reflected in each Table 15 torque entry and
   its Type A uncertainty? In particular, does Table 15 already include the
   zero-pressure extrapolation described in section 7.7 and the free-mode
   anelastic correction discussed in section 8.1? We understand section 3.3 to
   add the finite-gain elastic torque to the applied servo torque; please clarify
   its residual uncertainty coverage. Do the two methods in each campaign
   represent the intended common signal after these treatments, including any
   relevant calibration, seating, geometry or drift changes?

2. **The minimum joint uncertainty object.** Is the combined 3×3 matrix
   `C = A V_y A^T` available for those corrected representations, with its units,
   coordinate order, correction convention, linearization assumptions and
   uncertainty/distributional interpretation? A direct C is sufficient. Equivalent
   alternatives are the four-pair covariance `V_d`, the eight-entry covariance
   `V_y`, or signed input sensitivities and joint uncertainty sufficient to derive
   C. Please distinguish centered covariance, conservative uncertainty assignment,
   nonzero-mean second moment, bounds or intervals where appropriate.

3. **If a direct object is unavailable, the surviving terms.** We have not found
   within-pair or cross-campaign dependence for the Table 15 Type A marginals.
   We also need any non-canceling campaign-level autocollimator scale/nonlinearity
   relationships, correction/extrapolation cross-covariances, electrical and
   free-mode mechanical residual contributions, and applicable background/drift
   terms. The nearest source descriptions are sections 3.2–3.4, 7.7, 8.1–8.5
   and Table 15. Please indicate any terms already included or absent at this
   stage so they are neither omitted nor counted twice. For the section 8.5
   systematic shifts, a mean correction rule plus residual projected uncertainty,
   or an explicitly interpreted conservative projected assignment, would resolve
   the ambiguity. We have not transferred the four-final-result correlation
   statement or Tables 17–18 to these eight torque summaries.

A common method offset cancels in A. Thus information needed only to estimate
its magnitude or uncertainty is unnecessary for this limited equality question.
Likewise, an effect with an established signed loading L satisfying `A L=0`
needs no variance or cross-covariance specification for this target. Marginal
standard uncertainties alone do not supply the joint object; shared apparatus or
full correlation alone does not establish identical absolute loadings.

We are not requesting raw time series, complete posterior samples, or the final
copper aggregation if a direct contrast-level answer is available. The Number
Project's separate PR #50 final-summary response request remains parked context;
resolving that aggregation is not a prerequisite for this campaign route.

The current feasibility limitation is bounded to the reviewed article and
accessible discovery material. It is not a claim that additional information
cannot exist. Any newly supplied material would be incorporated transparently
through a new source record/specification before a later statistical test.
