from __future__ import annotations

from dataclasses import replace
import unittest

from Discovery.dimensions import DIMENSIONLESS
from Discovery.physical_bridge_schema import (
    DECLARED_LOCAL_ATOM,
    DOCUMENTED,
    INCOMPLETE,
    MODEL_PARAMETER,
    SATISFIED,
    STRUCTURAL_PLACEHOLDER,
    ProvenanceEdge,
    QuantityRecord,
)
from Discovery.physical_bridge_validation import evaluate_measurement_model
from tests.test_physical_bridge import build_direct_budget_model


class HUST2018AAFDepth2BBridgeClosureTests(unittest.TestCase):
    def test_component_ancestry_contributes_to_metrological_evidence_axis(self) -> None:
        model = build_direct_budget_model()
        estimator_upstream = set(
            evaluate_measurement_model(model).estimator_upstream_ids
        )
        documented_model = replace(
            model,
            quantities=tuple(
                replace(quantity, provenance_evidence=DOCUMENTED)
                if quantity.identifier in estimator_upstream
                else quantity
                for quantity in model.quantities
            ),
        )
        self.assertEqual(
            evaluate_measurement_model(documented_model).metrological_provenance_status,
            SATISFIED,
        )

        component_ancestor = QuantityRecord(
            "component_source_placeholder",
            "u_component_source_placeholder",
            MODEL_PARAMETER,
            DIMENSIONLESS,
            "ppm",
            DECLARED_LOCAL_ATOM,
            None,
            STRUCTURAL_PLACEHOLDER,
            "Unresolved source ancestor planted to discriminate the evidence union.",
        )
        changed = replace(
            documented_model,
            quantities=(*documented_model.quantities, component_ancestor),
            metrological_edges=(
                *documented_model.metrological_edges,
                ProvenanceEdge(
                    "relative_component_a",
                    component_ancestor.identifier,
                    "observation_derivation",
                    "The direct contribution depends on the planted source ancestor.",
                ),
            ),
        )
        evaluation = evaluate_measurement_model(changed)
        self.assertIn(
            component_ancestor.identifier,
            evaluation.uncertainty_component_upstream_ids,
        )
        self.assertEqual(evaluation.metrological_provenance_status, INCOMPLETE)


if __name__ == "__main__":
    unittest.main()
