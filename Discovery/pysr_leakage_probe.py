"""Milestone 6B: target-exposed symbolic-regression leakage probe.

This module keeps three axes separate:
1. candidate-generation exposure to the target,
2. registered algebraic target ancestry, and
3. known target ancestry in a preregistered synthetic generation graph.

PySR is never imported here. Its committed output is untrusted input to this checker.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from decimal import Decimal, getcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

from Discovery.dependency_definitions import (
    DEFAULT_DEPENDENCY_DEFINITIONS,
    DEFAULT_CONSTANT_DIMENSIONS,
    DependencyDefinition,
    build_dependency_catalog,
)
from Discovery.dimensions import DIMENSIONLESS, GRAVITATIONAL_CONSTANT, LENGTH, Dimension
from Discovery.planck_identities import normalize_exponent_signature
from Discovery.source_history import (
    SourceVerificationError,
    exit_for_source_verification_error,
    repository_root,
    verify_committed_source_state,
)

SCHEMA_VERSION = 1
EXPERIMENT_IDENTIFIER = "milestone_6b_pysr_leakage_v1"
BASELINE_SHA = "c446d39b7940219a7b2e58481375a8c70722f4cd"

TARGET_EXPOSED_CANDIDATE = "target_exposed_candidate"
PROMOTION_ELIGIBLE = False

NORMALIZED_MONOMIAL = "normalized_monomial"
REPRESENTATIONAL_GAP = "representational_gap"
PARSE_FAILURE = "parse_failure"

DIMENSIONALLY_VALID = "dimensionally_valid"
DIMENSIONALLY_INVALID = "dimensionally_invalid"
DIMENSION_UNRESOLVED = "dimension_unresolved"

TARGET_PATH_DETECTED = "target_path_detected"
NO_REGISTERED_TARGET_PATH = "no_registered_target_path"
UNRESOLVED_REGISTERED_PROVENANCE = "unresolved_registered_provenance"
NOT_APPLICABLE_REPRESENTATION_GAP = "not_applicable_representation_gap"

OUTPUT_DIR = Path("Experiments/EcosystemComparison/PySRLeakage")
PREREGISTRATION_PATH = OUTPUT_DIR / f"{EXPERIMENT_IDENTIFIER}.preregistration.json"
DATASETS_PATH = OUTPUT_DIR / f"{EXPERIMENT_IDENTIFIER}.datasets.json"
EXTERNAL_PATH = OUTPUT_DIR / f"{EXPERIMENT_IDENTIFIER}.external.json"
RESULT_PATH = OUTPUT_DIR / f"{EXPERIMENT_IDENTIFIER}.result.json"

TARGET_KEY = "G"
CHANNELS = ("A_clean", "B_registered_leak", "C_hidden_leak")
SEEDS = (0, 1, 2)

CHANNEL_PREDICTORS = {
    "A_clean": ("u_clean", "r_clean"),
    "B_registered_leak": ("hbar", "c", "m_P"),
    "C_hidden_leak": ("k_hidden", "s_hidden"),
}
CANONICAL_CONTROLS = {
    "A_clean": "u_clean / r_clean",
    "B_registered_leak": "hbar * c / (m_P * m_P)",
    "C_hidden_leak": "k_hidden / s_hidden",
}
GENERATION_PARENTS = {
    "A_clean": {
        "u_clean": (),
        "r_clean": (),
        "G": ("u_clean", "r_clean"),
    },
    "B_registered_leak": {
        "G": (),
        "hbar": (),
        "c": (),
        "m_P": ("G", "hbar", "c"),
    },
    "C_hidden_leak": {
        "G": (),
        "s_hidden": (),
        "k_hidden": ("G", "s_hidden"),
    },
}
CHANNEL_DIMENSIONS = {
    "A_clean": {
        "u_clean": GRAVITATIONAL_CONSTANT * LENGTH,
        "r_clean": LENGTH,
        "G": GRAVITATIONAL_CONSTANT,
    },
    "B_registered_leak": {
        "hbar": DEFAULT_CONSTANT_DIMENSIONS["hbar"],
        "c": DEFAULT_CONSTANT_DIMENSIONS["c"],
        "m_P": DEFAULT_CONSTANT_DIMENSIONS["m_P"],
        "G": GRAVITATIONAL_CONSTANT,
    },
    "C_hidden_leak": {
        "k_hidden": GRAVITATIONAL_CONSTANT,
        "s_hidden": DIMENSIONLESS,
        "G": GRAVITATIONAL_CONSTANT,
    },
}

SOURCE_PATHS = (
    "Discovery/pysr_leakage_probe.py",
    "Discovery/dependency_definitions.py",
    "Discovery/dimensions.py",
    "Discovery/source_history.py",
    "tests/test_pysr_leakage_probe.py",
    str(PREREGISTRATION_PATH),
    str(DATASETS_PATH),
)


class LeakageProbeError(ValueError):
    """Raised when committed 6B evidence violates the frozen contract."""


@dataclass(frozen=True, slots=True)
class ParsedExpression:
    tree: ast.Expression
    names: tuple[str, ...]


def canonical_json_bytes(record: object) -> bytes:
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def dimension_record(dimension: Dimension) -> list[str]:
    return [
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
        for value in dimension.exponents
    ]


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def build_datasets_record() -> dict[str, Any]:
    """Build three deterministic, zero-noise synthetic channels."""

    getcontext().prec = 50
    channels: dict[str, list[dict[str, str]]] = {channel: [] for channel in CHANNELS}
    for index in range(128):
        i = Decimal(index + 1)

        r_clean = Decimal(2) + i / Decimal(97)
        u_clean = Decimal(3) + (i * i + Decimal(7)) / Decimal(113)
        g_a = u_clean / r_clean
        channels["A_clean"].append(
            {
                "u_clean": _decimal_text(u_clean),
                "r_clean": _decimal_text(r_clean),
                "G": _decimal_text(g_a),
            }
        )

        g_b = Decimal(1) + i / Decimal(211)
        hbar = Decimal(2) + (i * Decimal(7) % Decimal(101)) / Decimal(131)
        c = Decimal(3) + (i * Decimal(11) % Decimal(103)) / Decimal(137)
        m_p = (hbar * c / g_b).sqrt()
        channels["B_registered_leak"].append(
            {
                "hbar": _decimal_text(hbar),
                "c": _decimal_text(c),
                "m_P": _decimal_text(m_p),
                "G": _decimal_text(g_b),
            }
        )

        g_c = Decimal(1) + i / Decimal(223)
        s_hidden = Decimal(1) + (i * Decimal(13) % Decimal(107)) / Decimal(149)
        k_hidden = g_c * s_hidden
        channels["C_hidden_leak"].append(
            {
                "k_hidden": _decimal_text(k_hidden),
                "s_hidden": _decimal_text(s_hidden),
                "G": _decimal_text(g_c),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "purpose": "Synthetic zero-noise fixtures for target-leakage methodology only.",
        "rows_per_channel": 128,
        "channels": channels,
    }


def dataset_hashes(record: Mapping[str, Any]) -> dict[str, str]:
    channels = record.get("channels")
    if not isinstance(channels, Mapping):
        raise LeakageProbeError("dataset channels must be a mapping")
    return {
        channel: sha256_bytes(canonical_json_bytes(channels[channel]))
        for channel in CHANNELS
    }


def _normalize_for_ast(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip():
        raise LeakageProbeError("candidate expression must be nonempty text")
    if len(expression) > 500:
        raise LeakageProbeError("candidate expression exceeds bounded parser length")
    return expression.replace("^", "**")


_ALLOWED_NODES = (
    ast.Expression,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.UnaryOp,
    ast.UAdd,
    ast.USub,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
)


def parse_expression(expression: str, allowed_names: Iterable[str]) -> ParsedExpression:
    normalized = _normalize_for_ast(expression)
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as error:
        raise LeakageProbeError(f"candidate expression is not parseable: {error.msg}") from error
    allowed = set(allowed_names)
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise LeakageProbeError(
                f"unsupported expression syntax: {type(node).__name__}"
            )
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise LeakageProbeError("numeric constants must be int or float literals")
        if isinstance(node, ast.Name):
            if node.id not in allowed:
                raise LeakageProbeError(f"unknown candidate variable: {node.id}")
            names.add(node.id)
    return ParsedExpression(tree=tree, names=tuple(sorted(names)))


def _numeric_fraction(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
        if isinstance(node.value, int):
            return Fraction(node.value)
        if isinstance(node.value, float):
            return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _numeric_fraction(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    raise LeakageProbeError("power exponent must be a numeric literal")


def _merge_exponents(
    left: Mapping[str, Fraction],
    right: Mapping[str, Fraction],
    multiplier: Fraction = Fraction(1),
) -> dict[str, Fraction]:
    result = dict(left)
    for name, exponent in right.items():
        result[name] = result.get(name, Fraction(0)) + multiplier * exponent
        if result[name] == 0:
            del result[name]
    return result


def normalize_monomial(parsed: ParsedExpression) -> tuple[Fraction, dict[str, Fraction]] | None:
    """Return coefficient and variable exponents, or None for non-monomial syntax."""

    def walk(node: ast.AST) -> tuple[Fraction, dict[str, Fraction]] | None:
        if isinstance(node, ast.Name):
            return Fraction(1), {node.id: Fraction(1)}
        if isinstance(node, ast.Constant):
            return _numeric_fraction(node), {}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            inner = walk(node.operand)
            if inner is None:
                return None
            coefficient, exponents = inner
            return (
                coefficient if isinstance(node.op, ast.UAdd) else -coefficient,
                exponents,
            )
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            left = walk(node.left)
            right = walk(node.right)
            if left is None or right is None:
                return None
            return left[0] * right[0], _merge_exponents(left[1], right[1])
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            left = walk(node.left)
            right = walk(node.right)
            if left is None or right is None or right[0] == 0:
                return None
            return left[0] / right[0], _merge_exponents(
                left[1], right[1], Fraction(-1)
            )
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base = walk(node.left)
            if base is None:
                return None
            exponent = _numeric_fraction(node.right)
            if exponent.denominator != 1:
                return None
            return base[0] ** exponent.numerator, {
                name: power * exponent for name, power in base[1].items()
            }
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            return None
        return None

    return walk(parsed.tree.body)


def evaluate_dimension(parsed: ParsedExpression, dimensions: Mapping[str, Dimension]) -> tuple[str, Dimension | None]:
    def walk(node: ast.AST) -> Dimension:
        if isinstance(node, ast.Name):
            if node.id not in dimensions:
                raise KeyError(node.id)
            return dimensions[node.id]
        if isinstance(node, ast.Constant):
            _numeric_fraction(node)
            return DIMENSIONLESS
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return walk(node.operand)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return walk(node.left) * walk(node.right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return walk(node.left) / walk(node.right)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exponent = _numeric_fraction(node.right)
            if exponent.denominator != 1:
                raise LeakageProbeError("only integer powers are supported")
            return walk(node.left) ** exponent
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
            left = walk(node.left)
            right = walk(node.right)
            if left != right:
                raise LeakageProbeError("additive operands have inconsistent dimensions")
            return left
        raise LeakageProbeError(f"unsupported dimension syntax: {type(node).__name__}")

    try:
        result = walk(parsed.tree.body)
    except KeyError:
        return DIMENSION_UNRESOLVED, None
    except LeakageProbeError:
        return DIMENSIONALLY_INVALID, None
    return (
        DIMENSIONALLY_VALID if result == GRAVITATIONAL_CONSTANT else DIMENSIONALLY_INVALID,
        result,
    )


def channel_dependency_catalog(channel: str):
    if channel == "B_registered_leak":
        return build_dependency_catalog(
            DEFAULT_DEPENDENCY_DEFINITIONS,
            DEFAULT_CONSTANT_DIMENSIONS,
            required_keys=DEFAULT_CONSTANT_DIMENSIONS,
        )

    definitions = list(DEFAULT_DEPENDENCY_DEFINITIONS)
    dimensions = dict(DEFAULT_CONSTANT_DIMENSIONS)
    if channel == "A_clean":
        definitions.extend(
            (DependencyDefinition("u_clean"), DependencyDefinition("r_clean"))
        )
        dimensions["u_clean"] = CHANNEL_DIMENSIONS[channel]["u_clean"]
        dimensions["r_clean"] = CHANNEL_DIMENSIONS[channel]["r_clean"]
    elif channel == "C_hidden_leak":
        definitions.extend(
            (DependencyDefinition("k_hidden"), DependencyDefinition("s_hidden"))
        )
        dimensions["k_hidden"] = CHANNEL_DIMENSIONS[channel]["k_hidden"]
        dimensions["s_hidden"] = CHANNEL_DIMENSIONS[channel]["s_hidden"]
    else:
        raise LeakageProbeError(f"unknown channel: {channel}")
    return build_dependency_catalog(definitions, dimensions)


def registered_dependency_status(
    channel: str,
    monomial: tuple[Fraction, Mapping[str, Fraction]] | None,
) -> str:
    if monomial is None:
        return NOT_APPLICABLE_REPRESENTATION_GAP
    _, exponents = monomial
    signature = normalize_exponent_signature(exponents.items())
    expansion = channel_dependency_catalog(channel).expand_signature(signature)
    if expansion.unresolved_factors:
        return UNRESOLVED_REGISTERED_PROVENANCE
    g_power = next(
        (power for name, power in expansion.signature if name == TARGET_KEY),
        Fraction(0),
    )
    return TARGET_PATH_DETECTED if g_power != 0 else NO_REGISTERED_TARGET_PATH


def _ancestors(channel: str, node: str) -> set[str]:
    parents = GENERATION_PARENTS[channel]
    seen: set[str] = set()
    stack = list(parents.get(node, ()))
    while stack:
        parent = stack.pop()
        if parent in seen:
            continue
        seen.add(parent)
        stack.extend(parents.get(parent, ()))
    return seen


def known_generation_target_leakage(channel: str, referenced_names: Iterable[str]) -> bool:
    return any(TARGET_KEY in _ancestors(channel, name) for name in referenced_names)


def enforce_candidate_origin(candidate_origin: str, promotion_eligible: bool) -> None:
    if candidate_origin != TARGET_EXPOSED_CANDIDATE:
        raise LeakageProbeError("PySR candidates must retain target-exposed origin")
    if promotion_eligible:
        raise LeakageProbeError("target-exposed candidates are never promotion-eligible")


def audit_expression(channel: str, expression: str) -> dict[str, Any]:
    if channel not in CHANNELS:
        raise LeakageProbeError(f"unknown channel: {channel}")
    try:
        parsed = parse_expression(expression, CHANNEL_PREDICTORS[channel])
    except LeakageProbeError as error:
        return {
            "candidate_origin": TARGET_EXPOSED_CANDIDATE,
            "promotion_eligible": False,
            "representation_status": PARSE_FAILURE,
            "dimensional_status": DIMENSION_UNRESOLVED,
            "registered_target_dependency": NOT_APPLICABLE_REPRESENTATION_GAP,
            "known_generation_target_leakage": False,
            "hidden_target_leakage_blind_spot": False,
            "referenced_predictors": [],
            "parse_diagnostic": str(error),
        }

    monomial = normalize_monomial(parsed)
    representation = NORMALIZED_MONOMIAL if monomial is not None else REPRESENTATIONAL_GAP
    dimensional_status, dimension = evaluate_dimension(
        parsed, CHANNEL_DIMENSIONS[channel]
    )
    registered = registered_dependency_status(channel, monomial)
    generation_leakage = known_generation_target_leakage(channel, parsed.names)
    blind_spot = (
        generation_leakage and registered == NO_REGISTERED_TARGET_PATH
    )
    record: dict[str, Any] = {
        "candidate_origin": TARGET_EXPOSED_CANDIDATE,
        "promotion_eligible": False,
        "representation_status": representation,
        "dimensional_status": dimensional_status,
        "registered_target_dependency": registered,
        "known_generation_target_leakage": generation_leakage,
        "hidden_target_leakage_blind_spot": blind_spot,
        "referenced_predictors": list(parsed.names),
    }
    if dimension is not None:
        record["computed_dimension"] = dimension_record(dimension)
    if monomial is not None:
        coefficient, exponents = monomial
        record["normalized_coefficient"] = (
            str(coefficient.numerator)
            if coefficient.denominator == 1
            else f"{coefficient.numerator}/{coefficient.denominator}"
        )
        record["normalized_exponents"] = [
            {
                "factor": name,
                "exponent": (
                    str(power.numerator)
                    if power.denominator == 1
                    else f"{power.numerator}/{power.denominator}"
                ),
            }
            for name, power in sorted(exponents.items())
        ]
    return record


EXPECTED_CANONICAL_CONTROL_AUDITS = {
    "A_clean": {
        "dimensional_status": DIMENSIONALLY_VALID,
        "registered_target_dependency": NO_REGISTERED_TARGET_PATH,
        "known_generation_target_leakage": False,
        "hidden_target_leakage_blind_spot": False,
    },
    "B_registered_leak": {
        "dimensional_status": DIMENSIONALLY_VALID,
        "registered_target_dependency": TARGET_PATH_DETECTED,
        "known_generation_target_leakage": True,
        "hidden_target_leakage_blind_spot": False,
    },
    "C_hidden_leak": {
        "dimensional_status": DIMENSIONALLY_VALID,
        "registered_target_dependency": NO_REGISTERED_TARGET_PATH,
        "known_generation_target_leakage": True,
        "hidden_target_leakage_blind_spot": True,
    },
}


def canonical_control_audits() -> dict[str, dict[str, Any]]:
    audits: dict[str, dict[str, Any]] = {}
    for channel in CHANNELS:
        audit = audit_expression(channel, CANONICAL_CONTROLS[channel])
        expected = EXPECTED_CANONICAL_CONTROL_AUDITS[channel]
        for key, value in expected.items():
            if audit.get(key) != value:
                raise LeakageProbeError(
                    f"invalid fixture for {channel}: {key}={audit.get(key)!r}, expected {value!r}"
                )
        audits[channel] = audit
    return audits


def _validate_external_record(record: Mapping[str, Any], datasets: Mapping[str, Any]) -> None:
    if record.get("schema_version") != SCHEMA_VERSION:
        raise LeakageProbeError("external schema version mismatch")
    if record.get("experiment_identifier") != EXPERIMENT_IDENTIFIER:
        raise LeakageProbeError("external experiment identifier mismatch")
    if record.get("dataset_sha256") != sha256_bytes(canonical_json_bytes(datasets)):
        raise LeakageProbeError("external dataset hash mismatch")
    source = record.get("external_source")
    if not isinstance(source, Mapping):
        raise LeakageProbeError("external source metadata missing")
    if source.get("pysr_commit") != "65b887aeaf97f1c5ae84b0ceffb370551e57ce90":
        raise LeakageProbeError("PySR commit mismatch")
    runs = record.get("runs")
    if not isinstance(runs, list) or len(runs) != len(CHANNELS) * len(SEEDS):
        raise LeakageProbeError("external run count mismatch")
    observed = {(run.get("channel"), run.get("seed")) for run in runs if isinstance(run, Mapping)}
    expected = {(channel, seed) for channel in CHANNELS for seed in SEEDS}
    if observed != expected:
        raise LeakageProbeError("external channel/seed coverage mismatch")


def candidate_identifier(channel: str, seed: int, row_index: int, equation: str) -> str:
    payload = f"{EXPERIMENT_IDENTIFIER}\0{channel}\0{seed}\0{row_index}\0{equation}"
    return "pysr-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def build_result_record(
    external: Mapping[str, Any],
    datasets: Mapping[str, Any],
    *,
    external_sha256: str,
    source_commit_sha: str,
) -> dict[str, Any]:
    _validate_external_record(external, datasets)
    controls = canonical_control_audits()
    audited_candidates: list[dict[str, Any]] = []

    for run in sorted(external["runs"], key=lambda item: (item["channel"], item["seed"])):
        channel = run["channel"]
        seed = int(run["seed"])
        candidates = run.get("candidates")
        if not isinstance(candidates, list):
            raise LeakageProbeError("external candidates must be a list")
        for row_index, raw in enumerate(candidates):
            if not isinstance(raw, Mapping):
                raise LeakageProbeError("external candidate row must be an object")
            equation = raw.get("equation")
            if not isinstance(equation, str):
                raise LeakageProbeError("external candidate equation must be text")
            audit = audit_expression(channel, equation)
            enforce_candidate_origin(
                audit["candidate_origin"], audit["promotion_eligible"]
            )
            audited_candidates.append(
                {
                    "candidate_identifier": candidate_identifier(
                        channel, seed, row_index, equation
                    ),
                    "channel": channel,
                    "seed": seed,
                    "raw_row_index": row_index,
                    "raw_equation": equation,
                    "raw_complexity": str(raw.get("complexity")),
                    "raw_loss": str(raw.get("loss")),
                    "raw_score": None if raw.get("score") is None else str(raw.get("score")),
                    **audit,
                }
            )

    counts = {
        "total_candidates": len(audited_candidates),
        "parse_failures": sum(c["representation_status"] == PARSE_FAILURE for c in audited_candidates),
        "normalized_monomials": sum(c["representation_status"] == NORMALIZED_MONOMIAL for c in audited_candidates),
        "representational_gaps": sum(c["representation_status"] == REPRESENTATIONAL_GAP for c in audited_candidates),
        "dimensionally_valid": sum(c["dimensional_status"] == DIMENSIONALLY_VALID for c in audited_candidates),
        "dimensionally_invalid": sum(c["dimensional_status"] == DIMENSIONALLY_INVALID for c in audited_candidates),
        "registered_target_paths": sum(c["registered_target_dependency"] == TARGET_PATH_DETECTED for c in audited_candidates),
        "known_generation_target_leakage": sum(bool(c["known_generation_target_leakage"]) for c in audited_candidates),
        "hidden_target_leakage_blind_spots": sum(bool(c["hidden_target_leakage_blind_spot"]) for c in audited_candidates),
    }
    recoveries = {
        channel: any(
            c["channel"] == channel
            and c["representation_status"] == NORMALIZED_MONOMIAL
            and audit_expression(channel, CANONICAL_CONTROLS[channel]).get("normalized_exponents")
            == c.get("normalized_exponents")
            for c in audited_candidates
        )
        for channel in CHANNELS
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_identifier": EXPERIMENT_IDENTIFIER,
        "methodological_result_status": "methodological_result",
        "primary_endpoint": {
            "question": (
                "Does the Channel C canonical control remain dimensionally valid with "
                "known generation target leakage but no registered algebraic target path?"
            ),
            "outcome": "BOUNDARY_CONFIRMED",
            "confirmed": controls["C_hidden_leak"]["hidden_target_leakage_blind_spot"],
        },
        "source_commit_sha": source_commit_sha,
        "raw_external_sha256": external_sha256,
        "dataset_sha256": sha256_bytes(canonical_json_bytes(datasets)),
        "dataset_channel_sha256": dataset_hashes(datasets),
        "canonical_controls": controls,
        "candidate_counts": counts,
        "canonical_signature_recovered_by_pysr": recoveries,
        "candidates": audited_candidates,
        "nonclaims": [
            "The synthetic target is not a measurement of G.",
            "PySR candidate fitness is not empirical evidence or independent corroboration.",
            "No registered target path does not establish calibration, statistical, experimental, causal, or physical independence.",
            "Repeated recovery across seeds does not remove target exposure.",
            "The synthetic generation graph is known by construction and is not a general causal-inference method.",
        ],
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LeakageProbeError(f"cannot load {path}: {error}") from error
    if not isinstance(record, dict):
        raise LeakageProbeError(f"{path} must contain a JSON object")
    return record


def _expected_preregistration_dataset_hash(preregistration: Mapping[str, Any]) -> str:
    value = preregistration.get("dataset_sha256")
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise LeakageProbeError("preregistration dataset SHA-256 is invalid")
    return value


def check_committed_artifacts() -> dict[str, Any]:
    preregistration = load_json(PREREGISTRATION_PATH)
    datasets = load_json(DATASETS_PATH)
    generated_datasets = build_datasets_record()
    if canonical_json_bytes(datasets) != canonical_json_bytes(generated_datasets):
        raise LeakageProbeError("committed synthetic dataset artifact is stale")
    dataset_sha = sha256_bytes(canonical_json_bytes(datasets))
    if _expected_preregistration_dataset_hash(preregistration) != dataset_sha:
        raise LeakageProbeError("preregistration dataset hash does not match committed bytes")

    external_bytes = EXTERNAL_PATH.read_bytes()
    external = json.loads(external_bytes)
    if not isinstance(external, dict):
        raise LeakageProbeError("external artifact must contain a JSON object")
    result = load_json(RESULT_PATH)
    source_sha = result.get("source_commit_sha")
    if not isinstance(source_sha, str):
        raise LeakageProbeError("result source commit SHA missing")

    verify_committed_source_state(
        repository_root(),
        source_sha,
        source_paths=SOURCE_PATHS,
        artifact_label="Milestone 6B PySR leakage result",
    )

    expected = build_result_record(
        external,
        datasets,
        external_sha256=sha256_bytes(external_bytes),
        source_commit_sha=source_sha,
    )
    if canonical_json_bytes(result) != canonical_json_bytes(expected):
        raise LeakageProbeError("stale or tampered 6B result artifact")
    if expected["primary_endpoint"]["confirmed"] is not True:
        raise LeakageProbeError("Channel C canonical hidden-leak fixture is invalid")
    return expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write-datasets", action="store_true")
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    args = parser.parse_args()

    if args.write_datasets:
        DATASETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATASETS_PATH.write_bytes(canonical_json_bytes(build_datasets_record()))
        print(f"Wrote deterministic synthetic datasets: {DATASETS_PATH}")
        return

    if args.check:
        try:
            result = check_committed_artifacts()
        except SourceVerificationError as error:
            exit_for_source_verification_error(error)
        except (LeakageProbeError, OSError, json.JSONDecodeError) as error:
            print(f"Milestone 6B check failed: {error}", file=sys.stderr)
            raise SystemExit(1)
        print(
            "Milestone 6B target-leakage result is current: "
            f"{result['primary_endpoint']['outcome']}."
        )
        return

    parser.error("use --check or --write-datasets")


if __name__ == "__main__":
    main()
