from __future__ import annotations

from copy import deepcopy
import unittest

from Discovery import hust_2018_aaf_source_audit as audit


EXPECTED_DIRECT_LOCATORS = {
    "AAF-I:p_sum": (
        "Supplementary Table 3, p. 20, |sum_{l=2}^{10} P_g,l,2| row, "
        "AAF-I column"
    ),
    "AAF-I:alpha_corrected": (
        "Supplementary Table 3, p. 20, <alpha_t(2omega_d)> row, AAF-I "
        "column; table states this value is air-density corrected"
    ),
    "AAF-I:magnetic_damper_ppm": (
        "Supplementary Table 1, p. 18, AAF-I and II magnetic-damper "
        "DeltaG/G row"
    ),
    "AAF-II:p_sum": (
        "Supplementary Table 3, p. 20, |sum_{l=2}^{10} P_g,l,2| row, "
        "AAF-II column"
    ),
    "AAF-II:alpha_corrected": (
        "Supplementary Table 3, p. 20, <alpha_t(2omega_d)> row, AAF-II "
        "column; table states this value is air-density corrected"
    ),
    "AAF-II:magnetic_damper_ppm": (
        "Supplementary Table 1, p. 18, AAF-I and II magnetic-damper "
        "DeltaG/G row"
    ),
    "AAF-III:p_sum": (
        "Supplementary Table 3, p. 20, |sum_{l=2}^{10} P_g,l,2| row, "
        "AAF-III column"
    ),
    "AAF-III:alpha_corrected": (
        "Supplementary Table 3, p. 20, <alpha_t(2omega_d)> row, AAF-III "
        "column; table states this value is air-density corrected"
    ),
    "AAF-III:magnetic_damper_ppm": (
        "Supplementary Table 1, pp. 18-19, AAF-III magnetic-damper "
        "DeltaG/G row"
    ),
}


def _direct_locator_violations(graph: dict) -> list[str]:
    nodes, _ = audit._flatten_nodes(graph)
    violations: list[str] = []
    for node_id, expected_locator in EXPECTED_DIRECT_LOCATORS.items():
        node = nodes[node_id]
        locator = node.get("locator")
        if locator != expected_locator:
            violations.append(f"{node_id} locator changed")
    return violations


class Hust2018AafLocatorPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.graph = audit.load_required_inputs()

    def test_all_direct_input_locators_match_reviewed_transcription(self) -> None:
        self.assertEqual(_direct_locator_violations(self.graph), [])

    def test_wrong_aaf_column_locator_fails_closed(self) -> None:
        graph = deepcopy(self.graph)
        for node in graph["experiments"][0]["nodes"]:
            if node["node_id"] == "AAF-I:p_sum":
                node["locator"] = node["locator"].replace(
                    "AAF-I column", "AAF-II column"
                )
                break
        self.assertEqual(
            _direct_locator_violations(graph),
            ["AAF-I:p_sum locator changed"],
        )


if __name__ == "__main__":
    unittest.main()
