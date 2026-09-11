"""Eight frozen semantic precision mutations with isolated assertion-only scoring."""
from __future__ import annotations
import argparse
import builtins
import io
from unittest.mock import patch
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from Discovery import nist_2026_covariance_precision as n

MODULE = n.MODULE
SELF = n.MUTATOR
TEST = n.TESTS[1]
PREFIX = 'tests.test_nist_2026_covariance_precision_mutations.PrecisionMutationBehaviorTests.'
OUTPUT = n.MUTATION_OUTPUT
COPY_PATHS = (MODULE, SELF, TEST, 'Discovery/__init__.py', 'Discovery/preregistration_history.py',
              'Discovery/source_history.py', 'Discovery/mutation_test_runner.py')
SOURCE_PATHS = n.SOURCE_PATHS
IMPORTS = {'Discovery': 'Discovery/__init__.py', 'Discovery.nist_2026_covariance_precision': MODULE,
           'Discovery.nist_2026_covariance_precision_mutations': SELF,
           'Discovery.preregistration_history': 'Discovery/preregistration_history.py',
           'Discovery.source_history': 'Discovery/source_history.py',
           'Discovery.mutation_test_runner': 'Discovery/mutation_test_runner.py',
           'tests': 'tests/__init__.py', 'tests.test_nist_2026_covariance_precision_mutations': TEST}

class MutationEvidenceError(ValueError):
    """Invalid execution or evidence is never a scientific mutation kill."""


def case(ident, old, new, test, requirement=None, expected="KILLED"):
    return {
        "id": ident, "category": "calibration" if requirement is None else "production",
        "requirement_index": requirement, "path": MODULE, "old": old, "new": new,
        "tests": [PREFIX + test], "expected": expected,
    }


CASES = (
    case('calibration_linear_term', 'B = 2 * sum((w * abs(z)', 'B = 1 * sum((w * abs(z)', 'test_faulty_calibration'),
    case('calibration_equivalent_quadratic', 'return dot(x, mv(A, x))',
         'return sum((a * b for a, b in zip(x, mv(A, x))), F(0))', 'test_equivalent_control', expected='SURVIVED'),
    case('M1_precision_width', 'return center - half_width, center + half_width',
         'return center - half_width / 2, center + half_width / 2', 'test_precision_width', 0),
    case('M2_anchor_scaling', 'a[i] * a[j] * s[i] * s[j] * P[i][j]',
         'a[i] * a[i] * s[i] * s[j] * P[i][j]', 'test_anchor_scaling', 1),
    case('M3_signed_interval', 'products = [a * b for a in left for b in right]',
         'products = [left[0] * right[0], left[1] * right[1]]', 'test_signed_interval', 2),
    case('M4_covariance_radius', 'radius = mm(mm(abs_matrix(Z), E), transpose(abs_matrix(Z)))',
         'radius = mm(mm(abs_matrix(Z), diag(tuple(E[i][i] for i in range(len(E))))), transpose(abs_matrix(Z)))',
         'test_covariance_radius', 3),
    case('M5_inverse_order', 'tuple(1 / x for x in upper_denominators)',
         'tuple(1 / x for x in lower_denominators)', 'test_inverse_order', 4),
    case('M6_display_remainder', "'upper': q + B + E", "'upper': q + B", 'test_display_remainder', 5),
    case('M7_partition_coverage', "set(frontier) == set(leaves)",
         "set(frontier) <= set(leaves)", 'test_partition_coverage', 6),
    case('M8_false_variation', "if {'flagged', 'not_flagged'} <= set(witness_classes):",
         "if lo <= cutoff and (hi is None or hi > cutoff):", 'test_false_variation', 7),
)


def baseline():
    return {
        "id": "unmutated_baseline", "category": "baseline", "requirement_index": None,
        "path": MODULE, "tests": sorted({t for c in CASES for t in c["tests"]}),
        "expected": "SURVIVED",
    }


def validate_definitions(source: str, protocol: dict) -> None:
    production = [c for c in CASES if c["category"] == "production"]
    controls = [c for c in CASES if c["category"] == "calibration"]
    if [c["requirement_index"] for c in production] != list(range(len(protocol["mutation_requirements"]))):
        raise MutationEvidenceError("one production case must cover each frozen requirement in order")
    if len(controls) != 2 or [c["expected"] for c in controls] != ["KILLED", "SURVIVED"]:
        raise MutationEvidenceError("two distinct calibration controls required")
    for c, requirement in zip(production, protocol["mutation_requirements"]):
        if c["id"] != requirement["id"] or c["tests"] != [requirement["test"]]:
            raise MutationEvidenceError("actual mutation mapping differs from frozen ids/tests")
    images = set()
    for c in CASES:
        if c["path"] != MODULE or source.count(c["old"]) != 1 or c["new"] == c["old"]:
            raise MutationEvidenceError("mutation patch missing, ambiguous, or unchanged")
        if len(c["tests"]) != 1 or not c["tests"][0].startswith(PREFIX):
            raise MutationEvidenceError("only designated behavioral assertions may score")
        images.add(n.digest(source.replace(c["old"], c["new"]).encode()))
    if len(images) != len(CASES) or len({c["id"] for c in CASES}) != len(CASES):
        raise MutationEvidenceError("mutation identities and byte images must be distinct")
    if set(controls[0]["tests"]) & {t for c in production for t in c["tests"]}:
        raise MutationEvidenceError("killable calibration oracle must be separate")


def assess_execution(evidence: dict, tests: list[str]) -> str:
    required = {
        "runner_status", "tests_run", "failing_tests", "error_tests", "skipped_tests",
        "successful", "validated_imports_before", "validated_imports_after",
    }
    if not isinstance(evidence, dict) or not required <= evidence.keys():
        raise MutationEvidenceError("incomplete runner evidence")
    failures = evidence["failing_tests"]
    if (evidence["runner_status"] != "completed"
            or type(evidence["tests_run"]) is not int or evidence["tests_run"] != len(tests)
            or evidence["error_tests"] != [] or evidence["skipped_tests"] != []
            or not isinstance(failures, list) or any(t not in tests for t in failures)
            or len(set(failures)) != len(failures)
            or evidence["successful"] is not (not failures)
            or any(marker in evidence.get("test_output", "") for marker in (
                "SyntaxError", "ImportError", "ModuleNotFoundError", "source_state_violated",
                "history_unavailable", "ancestry_violated", "source_metadata_invalid"))):
        raise MutationEvidenceError("infrastructure, skip, source-state, or contradictory execution is invalid")
    for phase in ("validated_imports_before", "validated_imports_after"):
        imports = evidence[phase]
        if not isinstance(imports, dict) or imports != IMPORTS:
            raise MutationEvidenceError("isolated import bindings are missing or wrong")
    reads = evidence.get('observed_file_open_paths')
    allowed = set(COPY_PATHS) | {'tests/__init__.py'}
    if not isinstance(reads, list) or not allowed <= set(reads):
        raise MutationEvidenceError('isolated source reads missing')
    for path in reads:
        if path in allowed:
            continue
        parts = Path(path).parts
        if len(parts) != 3 or parts[1] != '__pycache__' or not parts[2].endswith('.pyc'):
            raise MutationEvidenceError('undeclared isolated file read')
        source_path = parts[0] + '/' + parts[2].split('.')[0] + '.py'
        if source_path not in allowed:
            raise MutationEvidenceError('undeclared bytecode read probe')
    return "KILLED" if failures else "SURVIVED"


def run_case(root: Path, definition: dict) -> dict:
    """Execute one actual changed module in a disposable, import-isolated copy."""
    with TemporaryDirectory(prefix="nist-covariance-precision-mutant-") as temp:
        target = Path(temp)
        for path in COPY_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        # Prevent an installed package named tests from shadowing the isolated tests.
        (target / "tests/__init__.py").write_bytes(b"")
        source = (target / MODULE).read_text()
        if definition["category"] != "baseline":
            if source.count(definition["old"]) != 1:
                raise MutationEvidenceError("mutation patch is not unique")
            source = source.replace(definition["old"], definition["new"])
            (target / MODULE).write_text(source)
        bootstrap = """import contextlib,io,json,pathlib,runpy,sys
root=pathlib.Path(sys.argv.pop(1)).resolve()
sys.path.insert(0,str(root))
opened=set()
def audit(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=pathlib.Path(args[0]).resolve()
        if p.is_relative_to(root): opened.add(str(p.relative_to(root)))
sys.addaudithook(audit)
__import__('Discovery.mutation_test_runner')
stream=io.StringIO()
with contextlib.redirect_stdout(stream):
    runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')
result=json.loads(stream.getvalue())
result['observed_file_open_paths']=sorted(opened)
print(json.dumps(result,sort_keys=True))
"""
        command = [sys.executable, "-I", "-B", "-c", bootstrap, str(target), "--mutation-root", str(target)]
        for module in IMPORTS:
            command.extend(["--required-module", module])
        command.extend(definition["tests"])
        execution = subprocess.run(command, cwd=target, capture_output=True, text=True,
                                   env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=60)
        if execution.returncode:
            raise MutationEvidenceError("mutation subprocess failed; no kill credit")
        evidence = json.loads(execution.stdout)
        outcome = assess_execution(evidence, definition["tests"])
        stable = {key: value for key, value in evidence.items() if key != "test_output"}
        return {**{key: definition[key] for key in (
            "id", "category", "requirement_index", "path", "tests", "expected")},
            "applied_source_sha256": n.digest(source.encode()), "outcome": outcome, "evidence": stable}


def validate_records(records: list, source: str) -> None:
    definitions = (baseline(), *CASES)
    if not isinstance(records, list) or len(records) != len(definitions):
        raise MutationEvidenceError("incomplete mutation records")
    for definition, record in zip(definitions, records):
        if not isinstance(record, dict) or any(record.get(k) != definition[k] for k in (
                "id", "category", "requirement_index", "path", "tests", "expected")):
            raise MutationEvidenceError("record inventory differs from definitions")
        applied = source if definition["category"] == "baseline" else source.replace(definition["old"], definition["new"])
        if record.get("applied_source_sha256") != n.digest(applied.encode()):
            raise MutationEvidenceError("applied mutation bytes differ")
        outcome = assess_execution(record.get("evidence"), definition["tests"])
        if outcome != definition["expected"] or record.get("outcome") != outcome:
            raise MutationEvidenceError("production survivor or invalid calibration")


def prepare(root=n.ROOT):
    p, chronology, snapshot = n.prepare(root)
    source = (root / MODULE).read_text()
    validate_definitions(source, p)
    return p, source, snapshot


def envelope(p, source, snapshot, records, observation):
    validate_records(records, source)
    if observation != {'files': sorted(SOURCE_PATHS), 'git_blobs': sorted(SOURCE_PATHS), 'isolated_subprocesses': 11, 'other_subprocesses': []}:
        raise MutationEvidenceError('mutation execution file/Git/subprocess closure differs')
    return {'schema_version': 1, 'artifact_id': n.STEM + '_mutations_v1',
            'preregistration_sha256': n.FREEZE_DIGEST, 'anchor': n.ANCHOR, 'source_snapshot': snapshot,
            'definitions': CASES, 'definitions_sha256': n.digest(n.serialize_artifact(CASES).encode()),
            'requirements': p['mutation_requirements'], 'records': records, 'execution_read_closure': observation,
            'production_count': 8, 'production_killed': sum(r['category'] == 'production' and r['outcome'] == 'KILLED' for r in records),
            'calibration_valid': True, 'family_status': 'valid', 'review_qualification': n.PROVISIONAL,
            'isolation': {'python_flags': ['-I', '-B'], 'exact_project_imports': IMPORTS,
                          'ephemeral_tests_init_sha256': n.digest(b'')},
            'anti_false_kill_rule': 'Only designated behavior assertion failures; no syntax/import/runtime/history/digest/skip failures.'}


def build_artifact(root=n.ROOT):
    # Observe real root reads and Git blob arguments, including prepare/copies;
    # child source opens and before/after imports are retained per runner record.
    files, blobs, other = set(), set(), []
    isolated = 0
    bopen, iopen, oopen, run = builtins.open, io.open, os.open, subprocess.run
    def remember(file):
        if isinstance(file, (str, os.PathLike)):
            path = Path(file).resolve()
            if path.is_relative_to(root): files.add(path.relative_to(root).as_posix())
    def b(file, *a, **kw):
        remember(file)
        return bopen(file, *a, **kw)
    def i(file, *a, **kw):
        remember(file)
        return iopen(file, *a, **kw)
    def o(file, *a, **kw):
        # shutil cleanup uses descriptor-relative directory opens. They are
        # temporary-tree operations, not cwd-relative scientific source reads.
        if kw.get('dir_fd') is None or Path(file).is_absolute(): remember(file)
        return oopen(file, *a, **kw)
    def r(cmd, *a, **kw):
        nonlocal isolated
        if cmd[0] == 'git':
            for arg in cmd:
                if ':' in str(arg):
                    path = str(arg).split(':', 1)[1]
                    if path.startswith(('Discovery/', 'Experiments/', 'Notes/', 'tests/')): blobs.add(path)
        elif len(cmd) > 3 and cmd[1:3] == ['-I', '-B']:
            isolated += 1
        else:
            other.append(str(cmd[0]))
        return run(cmd, *a, **kw)
    with patch('builtins.open', b), patch('io.open', i), patch('os.open', o), patch('subprocess.run', r):
        p, source, snapshot = prepare(root)
        # Patches, source hashes and exact assertions are bound by the committed
        # mutator and source snapshot before any isolated case executes.
        records = [run_case(root, definition) for definition in (baseline(), *CASES)]
    observation = {'files': sorted(files), 'git_blobs': sorted(blobs),
                   'isolated_subprocesses': isolated, 'other_subprocesses': other}
    return envelope(p, source, snapshot, records, observation)


def check_artifact(root=n.ROOT):
    p, source, snapshot = prepare(root)
    raw = (root / OUTPUT).read_bytes()
    artifact = n._json(raw)
    expected = envelope(p, source, snapshot, artifact['records'], artifact['execution_read_closure'])
    # JSON canonicalization normalizes Python tuple inventories to arrays.
    expected = n._json(n.serialize_artifact(expected))
    if artifact != expected or raw != n.serialize_artifact(expected).encode():
        raise MutationEvidenceError('stale/altered/noncanonical mutation evidence')
    n.verify_output_chronology(root, snapshot['source_commit_sha'], (OUTPUT.as_posix(),))
    return expected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    if args.check:
        check_artifact()
        print('NIST covariance precision mutations verified: 8 semantic kills; controls valid')
    else:
        (n.ROOT / OUTPUT).write_text(n.serialize_artifact(build_artifact()))


if __name__ == '__main__':
    main()
