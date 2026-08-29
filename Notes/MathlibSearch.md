# Mathlib search record: physical dimensions

Before adding the local dimension representation, mathlib `v4.33.1` was searched at
commit `0df444a360eaa60ab8c11dca51a86af692955474` for `Dimension`, `Unit`, `Quantity`,
`SI`, and related terms.

Mathlib has several mathematical uses of “dimension” and “unit” (for example vector-space
dimension and units of a monoid), but no general SI physical-quantity system suitable for
this experiment was found. `FormalPhysics/Dimensions.lean` therefore defines only the
minimal algebraic vocabulary needed here: seven SI base dimensions and integer exponent
vectors. It continues to use mathlib's existing integers, functions, and pointwise
algebra rather than rebuilding those foundations.

This note records a scoped search result, not a claim that no relevant library can ever
exist. The search should be repeated before substantially expanding the unit system.

