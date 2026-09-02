from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from Discovery.pydimension_comparison import (
    EXTERNAL_OUTPUT_PATH,
    PREREGISTRATION_PATH,
    RESULT_OUTPUT_PATH,
    _control_matrix,
    build_result,
    canonical_row_span,
    internal_affine_solution,
    internal_kernel_solution,
    load_preregistration,
    validate_committed_result,
    validate_preregistered_input,
)


class PyDimensionComparisonTests(unittest.TestCase):
    def test_preregistered_matrix_is_current_project_matrix(self) -> None:
        prereg, _ = load_preregistration()
        validate_preregistered_input(prereg)
        self.assertEqual(prereg["project"]["baseline_commit_sha"], "6376ee9c74a1f5bff0045b121a7202ec79a9b667")
        self.assertEqual(prereg["external_comparator"]["commit_sha"], "a899cd41e327a8ad185b139537272eecb6a9adb4")

    def test_internal_baseline_is_affine_rank_four_nullity_six(self) -> None:
        kernel = internal_kernel_solution()
        affine = internal_affine_solution()
        self.assertEqual(kernel.rank, 4)
        self.assertEqual(kernel.nullity, 6)
        self.assertEqual(affine.status, "affine")
        self.assertEqual(affine.rank, 4)
        self.assertEqual(affine.nullity, 6)

    def test_canonical_row_span_compares_spaces_not_literal_bases(self) -> None:
        basis = internal_kernel_solution().nullspace_basis
        width = len(basis[0])
        changed_first = tuple(a + b for a, b in zip(basis[0], basis[1]))
        alternate = (
            tuple(Fraction(3) * value for value in basis[-1]),
            *reversed(basis[2:-1]),
            changed_first,
            basis[1],
        )
        self.assertEqual(len(alternate), len(basis))
        self.assertNotEqual(alternate, basis)
        self.assertEqual(
            canonical_row_span(alternate, width=width),
            canonical_row_span(basis, width=width),
        )

    def test_preregistered_planted_control_changes_the_kernel(self) -> None:
        prereg, _ = load_preregistration()
        baseline = internal_kernel_solution().nullspace_basis
        width = len(prereg["input"]["generator_order"])
        matrix = _control_matrix(prereg)
        # Solve the planted matrix with the same exact project solver only as a
        # local harness sanity check.  The committed 6A control outcome uses
        # PyDimension's independently produced exact basis.
        from Discovery.monomial_constraints import NamedFactor, solve_monomial_constraints

        factors = tuple(
            NamedFactor(key, tuple(row[column] for row in matrix))
            for column, key in enumerate(prereg["input"]["generator_order"])
        )
        control = solve_monomial_constraints(factors, [0] * len(matrix))
        self.assertNotEqual(
            canonical_row_span(control.nullspace_basis, width=width),
            canonical_row_span(baseline, width=width),
        )

    def test_committed_result_is_current_and_control_disagrees(self) -> None:
        validate_committed_result()
        result = json.loads(RESULT_OUTPUT_PATH.read_text(encoding="utf-8"))
        self.assertIn(
            result["methodological_result_status"],
            {"AGREEMENT", "DISAGREEMENT"},
        )
        self.assertEqual(result["planted_control"]["outcome"], "DISAGREEMENT")
        self.assertFalse(result["planted_control"]["equal_to_unperturbed_internal_span"])

    def test_float_diagnostic_does_not_control_exact_verdict(self) -> None:
        original = json.loads(EXTERNAL_OUTPUT_PATH.read_text(encoding="utf-8"))
        baseline = build_result()
        altered = json.loads(json.dumps(original))
        altered["baseline"]["float_scipy_diagnostic"] = {
            "basis_shape": [999, 999],
            "max_abs_residual": "not-used-for-exact-verdict",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "external.json"
            path.write_text(json.dumps(altered, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            repeated = build_result(external_path=path)
        self.assertEqual(
            repeated["methodological_result_status"],
            baseline["methodological_result_status"],
        )
        self.assertEqual(
            repeated["comparison"]["exact_nullspace_span_equal"],
            baseline["comparison"]["exact_nullspace_span_equal"],
        )


if __name__ == "__main__":
    unittest.main()
