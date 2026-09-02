"""Milestone 6A exact differential comparison against a pinned PyDimension checkout.

PyDimension is used only as an external, untrusted comparator.  The committed raw
external output is hash-pinned; normal CI never imports or installs PyDimension.
The verdict compares exact rational row spans, not textual basis vectors.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence

from Discovery.constants import DEFAULT_SEARCH_CONSTANTS, GRAVITATIONAL_CONSTANT_G
from Discovery.dimensions import BASE_DIMENSIONS, DIMENSIONLESS
from Discovery.monomial_constraints import (
    NamedFactor,
    reduced_row_echelon,
    solve_monomial_constraints,
)
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)


PREREGISTRATION_PATH = Path(
    "Experiments/EcosystemComparison/PyDimension/"
    "milestone_6a_pydimension_v1.preregistration.json"
)
EXTERNAL_OUTPUT_PATH = Path(
    "Experiments/EcosystemComparison/PyDimension/"
    "milestone_6a_pydimension_v1.external.json"
)
RESULT_OUTPUT_PATH = Path(
    "Experiments/EcosystemComparison/PyDimension/"
    "milestone_6a_pydimension_v1.result.json"
)
RESULT_SCHEMA_VERSION = 1
EXTERNAL_SCHEMA_VERSION = 1
SOURCE_PATHS = (
    "Discovery/pydimension_comparison.py",
    "Discovery/constants.py",
    "Discovery/dimensions.py",
    "Discovery/monomial_constraints.py",
    "Discovery/source_history.py",
    "tests/test_pydimension_comparison.py",
    str(PREREGISTRATION_PATH),
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _parse_fraction(value: object) -> Fraction:
    if isinstance(value, bool):
        raise ValueError("boolean is not an exact rational")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError(f"invalid rational string: {value!r}") from error
    raise ValueError(f"expected exact integer/rational string, got {type(value).__name__}")


def load_preregistration(
    path: Path = PREREGISTRATION_PATH,
) -> tuple[dict[str, Any], bytes]:
    content = path.read_bytes()
    prereg = json.loads(content)
    if prereg.get("schema_version") != 1:
        raise ValueError("stale 6A preregistration schema")
    return prereg, content


def _project_matrix() -> tuple[tuple[int, ...], ...]:
    rows = []
    for row_index in range(len(BASE_DIMENSIONS)):
        row = []
        for constant in DEFAULT_SEARCH_CONSTANTS:
            exponent = constant.dimension.exponents[row_index]
            if exponent.denominator != 1:
                raise ValueError(
                    "6A project matrix unexpectedly contains rational dimension exponents"
                )
            row.append(exponent.numerator)
        rows.append(tuple(row))
    return tuple(rows)


def _project_target() -> tuple[int, ...]:
    target = []
    for exponent in GRAVITATIONAL_CONSTANT_G.dimension.exponents:
        if exponent.denominator != 1:
            raise ValueError(
                "6A target unexpectedly contains rational dimension exponents"
            )
        target.append(exponent.numerator)
    return tuple(target)


def validate_preregistered_input(prereg: Mapping[str, Any]) -> None:
    input_record = prereg.get("input")
    if not isinstance(input_record, Mapping):
        raise ValueError("6A preregistration input is malformed")
    if input_record.get("base_dimension_order") != list(BASE_DIMENSIONS):
        raise ValueError(
            "6A preregistered base-dimension order no longer matches project"
        )
    if input_record.get("generator_order") != [
        constant.key for constant in DEFAULT_SEARCH_CONSTANTS
    ]:
        raise ValueError("6A preregistered generator order no longer matches project")
    expected_matrix = [list(row) for row in _project_matrix()]
    if input_record.get("dimension_matrix_rows") != expected_matrix:
        raise ValueError("6A preregistered dimensional matrix no longer matches project")
    if input_record.get("target_dimension") != list(_project_target()):
        raise ValueError("6A preregistered target dimension no longer matches project")


def _factors() -> tuple[NamedFactor, ...]:
    return tuple(
        NamedFactor(constant.key, constant.dimension.exponents)
        for constant in DEFAULT_SEARCH_CONSTANTS
    )


def internal_kernel_solution():
    return solve_monomial_constraints(
        _factors(),
        DIMENSIONLESS.exponents,
    )


def internal_affine_solution():
    return solve_monomial_constraints(
        _factors(),
        GRAVITATIONAL_CONSTANT_G.dimension.exponents,
    )


def canonical_row_span(
    basis: Sequence[Sequence[Fraction | int]],
    *,
    width: int,
) -> tuple[tuple[Fraction, ...], ...]:
    """Canonicalize a vector-space span by exact row RREF."""
    rows = [tuple(Fraction(value) for value in vector) for vector in basis]
    if any(len(row) != width for row in rows):
        raise ValueError("basis vector width mismatch")
    if not rows:
        return ()
    reduction = reduced_row_echelon(rows)
    return tuple(
        row for row in reduction.matrix if any(value != 0 for value in row)
    )


def _matrix_vector_product(
    matrix: Sequence[Sequence[int | Fraction]],
    vector: Sequence[int | Fraction],
) -> tuple[Fraction, ...]:
    width = len(vector)
    if any(len(row) != width for row in matrix):
        raise ValueError("matrix/vector shape mismatch")
    return tuple(
        sum(
            (
                Fraction(coefficient) * Fraction(value)
                for coefficient, value in zip(row, vector)
            ),
            Fraction(0),
        )
        for row in matrix
    )


def _vector_add(
    left: Sequence[int | Fraction],
    right: Sequence[int | Fraction],
) -> tuple[Fraction, ...]:
    if len(left) != len(right):
        raise ValueError("vector length mismatch")
    return tuple(Fraction(a) + Fraction(b) for a, b in zip(left, right))


def _serialize_basis(
    basis: Sequence[Sequence[int | Fraction]],
) -> list[list[str]]:
    return [[_fraction_text(Fraction(value)) for value in vector] for vector in basis]


def _external_basis(
    record: object,
    *,
    width: int,
) -> tuple[tuple[Fraction, ...], ...]:
    if not isinstance(record, list):
        raise ValueError("external basis is malformed")
    vectors: list[tuple[Fraction, ...]] = []
    for vector in record:
        if not isinstance(vector, list) or len(vector) != width:
            raise ValueError("external basis vector shape mismatch")
        parsed = tuple(_parse_fraction(value) for value in vector)
        vectors.append(parsed)
    return tuple(vectors)


def _control_matrix(prereg: Mapping[str, Any]) -> tuple[tuple[int, ...], ...]:
    baseline = [list(row) for row in prereg["input"]["dimension_matrix_rows"]]
    control = prereg["planted_control"]
    row_index = control["row_index"]
    column_index = control["column_index"]
    if baseline[row_index][column_index] != control["original"]:
        raise ValueError("6A planted-control original value mismatch")
    baseline[row_index][column_index] = control["replacement"]
    return tuple(tuple(int(value) for value in row) for row in baseline)


def _validate_external_metadata(
    external: Mapping[str, Any],
    prereg: Mapping[str, Any],
    prereg_bytes: bytes,
) -> None:
    if external.get("schema_version") != EXTERNAL_SCHEMA_VERSION:
        raise ValueError("stale 6A external-output schema")
    if external.get("experiment_identifier") != prereg["experiment_identifier"]:
        raise ValueError("6A external/preregistration experiment mismatch")
    integrity = external.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ValueError("6A external integrity metadata is missing")
    if integrity.get("preregistration_sha256") != _sha256(prereg_bytes):
        raise ValueError("6A external preregistration hash mismatch")
    if external.get("external_comparator") != prereg["external_comparator"]:
        raise ValueError("6A external comparator metadata mismatch")
    if external.get("environment") != prereg["environment"]:
        raise ValueError("6A external environment metadata mismatch")
    if external.get("generator_order") != prereg["input"]["generator_order"]:
        raise ValueError("6A external generator order mismatch")
    if external.get("base_dimension_order") != prereg["input"]["base_dimension_order"]:
        raise ValueError("6A external base-dimension order mismatch")
    if (
        external.get("baseline", {}).get("dimension_matrix_rows")
        != prereg["input"]["dimension_matrix_rows"]
    ):
        raise ValueError("6A external baseline matrix mismatch")
    expected_control = [list(row) for row in _control_matrix(prereg)]
    if external.get("control", {}).get("dimension_matrix_rows") != expected_control:
        raise ValueError("6A external planted-control matrix mismatch")
    source_anchor = integrity.get("project_source_commit_sha")
    if not isinstance(source_anchor, str) or re.fullmatch(
        r"[0-9a-f]{40}", source_anchor
    ) is None:
        raise ValueError("6A external project source commit is invalid")


def _git_log_sha(root: Path, path: Path) -> str:
    return subprocess.run(
        ("git", "log", "-1", "--format=%H", "--", str(path)),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_result(
    *,
    external_path: Path = EXTERNAL_OUTPUT_PATH,
    preregistration_path: Path = PREREGISTRATION_PATH,
) -> dict[str, Any]:
    prereg, prereg_bytes = load_preregistration(preregistration_path)
    validate_preregistered_input(prereg)
    external_bytes = external_path.read_bytes()
    external = json.loads(external_bytes)
    _validate_external_metadata(external, prereg, prereg_bytes)

    matrix = tuple(
        tuple(int(value) for value in row)
        for row in prereg["input"]["dimension_matrix_rows"]
    )
    target = tuple(int(value) for value in prereg["input"]["target_dimension"])
    width = len(prereg["input"]["generator_order"])

    kernel = internal_kernel_solution()
    affine = internal_affine_solution()
    if affine.particular_solution is None:
        raise ValueError(
            "6A internal affine system unexpectedly lacks a particular solution"
        )

    internal_basis = kernel.nullspace_basis
    internal_span = canonical_row_span(internal_basis, width=width)
    baseline_external_basis = _external_basis(
        external["baseline"]["exact_primitive_basis_vectors"],
        width=width,
    )
    external_span = canonical_row_span(baseline_external_basis, width=width)
    external_residuals = tuple(
        _matrix_vector_product(matrix, vector)
        for vector in baseline_external_basis
    )
    zero_residual = tuple(Fraction(0) for _ in matrix)
    residuals_zero = all(
        residual == zero_residual for residual in external_residuals
    )

    external_rank = external["baseline"].get("exact_rank")
    external_nullity = external["baseline"].get("exact_nullity")
    ranks_agree = external_rank == kernel.rank and external_nullity == kernel.nullity
    exact_span_equal = external_span == internal_span

    particular_residual = _matrix_vector_product(matrix, affine.particular_solution)
    particular_exact = particular_residual == tuple(Fraction(value) for value in target)
    translated_residuals = tuple(
        _matrix_vector_product(
            matrix,
            _vector_add(affine.particular_solution, vector),
        )
        for vector in baseline_external_basis
    )
    target_fraction = tuple(Fraction(value) for value in target)
    affine_consistent = particular_exact and all(
        residual == target_fraction for residual in translated_residuals
    )

    baseline_outcome = (
        "AGREEMENT"
        if ranks_agree and exact_span_equal and residuals_zero and affine_consistent
        else "DISAGREEMENT"
    )

    control_external_basis = _external_basis(
        external["control"]["exact_primitive_basis_vectors"],
        width=width,
    )
    control_span = canonical_row_span(control_external_basis, width=width)
    control_equal_to_baseline = control_span == internal_span
    control_outcome = "AGREEMENT" if control_equal_to_baseline else "DISAGREEMENT"
    if control_outcome != "DISAGREEMENT":
        raise ValueError("6A planted mismatch control failed to report disagreement")

    source_commit_sha = external["integrity"]["project_source_commit_sha"]
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment_identifier": prereg["experiment_identifier"],
        "methodological_result_status": baseline_outcome,
        "integrity": {
            "preregistration_path": str(preregistration_path),
            "preregistration_sha256": _sha256(prereg_bytes),
            "preregistration_commit_sha": _git_log_sha(
                repository_root(), preregistration_path
            ),
            "external_output_path": str(external_path),
            "external_output_sha256": _sha256(external_bytes),
            "project_source_commit_sha": source_commit_sha,
            "source_paths": list(SOURCE_PATHS),
        },
        "comparison": {
            "matrix": [list(row) for row in matrix],
            "generator_order": list(prereg["input"]["generator_order"]),
            "internal": {
                "status": affine.status,
                "rank": kernel.rank,
                "nullity": kernel.nullity,
                "particular_solution": [
                    _fraction_text(value) for value in affine.particular_solution
                ],
                "nullspace_basis_vectors": _serialize_basis(internal_basis),
                "canonical_nullspace_row_span": _serialize_basis(internal_span),
            },
            "external_exact": {
                "rank": external_rank,
                "nullity": external_nullity,
                "primitive_basis_vectors": _serialize_basis(
                    baseline_external_basis
                ),
                "canonical_nullspace_row_span": _serialize_basis(external_span),
                "residuals": _serialize_basis(external_residuals),
            },
            "float_scipy_diagnostic": external["baseline"][
                "float_scipy_diagnostic"
            ],
            "ranks_and_nullities_agree": ranks_agree,
            "exact_nullspace_span_equal": exact_span_equal,
            "external_exact_residuals_zero": residuals_zero,
            "internal_particular_solution_exact": particular_exact,
            "external_kernel_preserves_affine_solution": affine_consistent,
            "outcome": baseline_outcome,
        },
        "planted_control": {
            "construction": prereg["planted_control"]["construction"],
            "external_exact_rank": external["control"]["exact_rank"],
            "external_exact_nullity": external["control"]["exact_nullity"],
            "canonical_control_row_span": _serialize_basis(control_span),
            "equal_to_unperturbed_internal_span": control_equal_to_baseline,
            "required_outcome": "DISAGREEMENT",
            "outcome": control_outcome,
        },
        "external_execution": {
            "runner": external.get("runner"),
            "external_comparator": external["external_comparator"],
            "environment": external["environment"],
        },
        "nonclaims": list(prereg["nonclaims"]),
    }


def serialize_result(result: Mapping[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


def verify_source_state(root: Path, source_commit_sha: str) -> None:
    verify_committed_source_state(
        root,
        source_commit_sha,
        source_paths=SOURCE_PATHS,
        artifact_label="Milestone 6A PyDimension result",
    )


def validate_committed_result(
    *,
    result_path: Path = RESULT_OUTPUT_PATH,
    external_path: Path = EXTERNAL_OUTPUT_PATH,
    preregistration_path: Path = PREREGISTRATION_PATH,
) -> None:
    if not result_path.exists():
        raise ValueError(f"missing 6A result artifact: {result_path}")
    committed = result_path.read_text(encoding="utf-8")
    result = build_result(
        external_path=external_path,
        preregistration_path=preregistration_path,
    )
    rendered = serialize_result(result)
    if committed != rendered:
        raise ValueError("stale or tampered 6A result artifact")
    verify_source_state(
        repository_root(),
        result["integrity"]["project_source_commit_sha"],
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preregistration", type=Path, default=PREREGISTRATION_PATH)
    parser.add_argument("--external", type=Path, default=EXTERNAL_OUTPUT_PATH)
    parser.add_argument("--output", type=Path, default=RESULT_OUTPUT_PATH)
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.check:
            validate_committed_result(
                result_path=args.output,
                external_path=args.external,
                preregistration_path=args.preregistration,
            )
            result = json.loads(args.output.read_text(encoding="utf-8"))
            print(
                "Milestone 6A PyDimension differential result is current: "
                f"{result['methodological_result_status']}."
            )
            return

        result = build_result(
            external_path=args.external,
            preregistration_path=args.preregistration,
        )
        rendered = serialize_result(result)
        if args.output.exists():
            print(
                "refusing to overwrite an existing 6A result; remove it explicitly "
                "only when creating a new preregistered experiment version",
                file=sys.stderr,
            )
            raise SystemExit(1)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote Milestone 6A result to {args.output}.")
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as error:
        print(f"invalid Milestone 6A comparison: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
