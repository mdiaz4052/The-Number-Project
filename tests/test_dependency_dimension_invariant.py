from dataclasses import replace
from types import MappingProxyType
import unittest

from Discovery.dependency_analysis import analyze_candidates, analyze_default_candidates
from Discovery.dependency_definitions import DEFAULT_DEPENDENCY_CATALOG
from Discovery.dimensions import DIMENSIONLESS


class DependencyDimensionInvariantTests(unittest.TestCase):
    def test_dependency_classification_ignores_dimension_metadata_after_validation(self) -> None:
        baseline = analyze_default_candidates()
        altered_catalog = replace(
            DEFAULT_DEPENDENCY_CATALOG,
            dimensions=MappingProxyType(
                {
                    key: DIMENSIONLESS
                    for key in DEFAULT_DEPENDENCY_CATALOG.dimensions
                }
            ),
        )
        repeated = analyze_candidates(
            tuple(record.candidate for record in baseline),
            catalog=altered_catalog,
        )

        def classification_view(records):
            return [
                (
                    record.surface_signature,
                    record.expanded_dependency_signature,
                    record.unresolved_factors,
                    record.power_of_g,
                    record.dependency_status,
                    record.certification_status,
                    record.lean_theorem_name,
                    record.equivalence_group_identifier,
                    record.equivalence_group_size,
                )
                for record in records
            ]

        self.assertEqual(classification_view(repeated), classification_view(baseline))


if __name__ == "__main__":
    unittest.main()
