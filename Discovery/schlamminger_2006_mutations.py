"""Calibrated, isolated Schlamminger-only semantic and provenance mutations."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import schlamminger_2006_rounding_consistency as s
from Discovery.rounding_consistency import RoundingError

DEFAULT_OUTPUT = s.DIRECTORY / 'schlamminger_2006_mutation_results_v1.json'
MODULE_PATH = 'Discovery/schlamminger_2006_rounding_consistency.py'
TEST_PREFIX = 'tests.test_schlamminger_2006_rounding_consistency.SchlammingerBehaviorTests.'
TEST_PATH = 'tests/test_schlamminger_2006_rounding_consistency.py'
ATTESTED_PATHS = s.SOURCE_PATHS + (
    'Discovery/schlamminger_2006_mutations.py', TEST_PATH,
    'tests/test_schlamminger_2006_mutations.py',
    'Discovery/mutation_test_runner.py', 'tests/support/synthetic_history.py',
    'Discovery/__init__.py', 'tests/support/__init__.py',
)


def case(identifier, category, old, new, test, expected='KILLED'):
    return {'id': identifier, 'category': category, 'path': MODULE_PATH,
            'old': old, 'new': new, 'tests': [TEST_PREFIX + test], 'expected': expected}


VALUE_OLD = "rounding_bin(decimal_fraction(row['value_ppm']), half)"
VALUE_NEW = "rounding_bin(decimal_fraction(row['value_ppm']) + Fraction(1, 10), half)"
ORACLE = 'test_exact_bins_schedule_and_independent_oracle'
CASES = (
    case('calibration_killable', 'calibration', VALUE_OLD, VALUE_NEW, ORACLE),
    case('calibration_equivalent', 'calibration',
         'No comparisons, source results, HUST values or external constants enter here.',
         'Calculate the frozen one-run budgets from calculator-only inputs.',
         ORACLE, 'SURVIVED'),
    case('source_value_substitution', 'behavioral', VALUE_OLD, VALUE_NEW, ORACLE),
    case('rounding_radius_corruption', 'behavioral',
         "half = decimal_fraction(rounding_policy['component_half_width_ppm'])",
         "half = 2 * decimal_fraction(rounding_policy['component_half_width_ppm'])", ORACLE),
    case('statistical_scope_omission', 'behavioral',
         'for scope in SCOPES:\n        rows = projection',
         'for scope in SCOPES[1:]:\n        rows = projection', ORACLE),
    case('systematic_scope_omission', 'behavioral',
         'for scope in SCOPES:\n        rows = projection',
         'for scope in SCOPES[:1]:\n        rows = projection', ORACLE),
    case('target_leakage', 'behavioral',
         "central = decimal_fraction(projection['central_value']['value'])",
         "central = decimal_fraction(projection['central_value']['value'])\n"
         "    half += decimal_fraction(load_protocol()['source_attestation']['terminal_comparisons']['statistical']['value_ppm']) / 1000000",
         'test_targets_cannot_enter_calculator_or_change_candidates'),
    case('verdict_inversion', 'behavioral',
         'outcome, index = classify(calculation, comparison)',
         "outcome, index = classify(calculation, comparison)\n"
         "        outcome = 'incompatible' if outcome == 'compatible' else 'compatible'",
         'test_verdicts_match_independent_certificate_rules'),
    case('preregistration_bypass', 'integrity',
         "    verify_preregistration_freeze(\n"
         "        root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,\n"
         "        path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256,\n"
         "    )",
         '    pass  # removed preregistration verification', 'test_freeze_gate_cannot_be_skipped'),
    case('source_pin_bypass', 'integrity',
         'def verify_source_bytes(data: bytes, protocol: dict) -> dict:\n',
         'def verify_source_bytes(data: bytes, protocol: dict) -> dict:\n    return read_json(data)\n',
         'test_source_component_substitution_deletion_and_role_mutations_fail'),
)


def assess_execution(record: dict, tests: list[str]) -> str:
    """Count assertion failures only; errors, collection and freshness kills are invalid."""
    if (record.get('runner_status') != 'completed' or record.get('tests_run') != len(tests)
            or record.get('error_tests') or record.get('skipped_tests')
            or not isinstance(record.get('failing_tests'), list)
            or not set(record['failing_tests']).issubset(tests)
            or any(marker in record.get('test_output', '') for marker in
                   ('source_state_violated', 'commit result-driving source', 'SyntaxError', 'ImportError'))):
        raise RoundingError('invalid mutation execution; not a kill')
    expected_module = MODULE_PATH[:-3].replace('/', '.')
    for key in ('validated_imports_before', 'validated_imports_after'):
        if record.get(key, {}).get(expected_module) != MODULE_PATH:
            raise RoundingError('mutation import binding missing')
    failures = bool(record['failing_tests'])
    if record.get('successful') is not (not failures):
        raise RoundingError('mutation success/failure evidence contradicts itself')
    return 'KILLED' if failures else 'SURVIVED'


def run_case(root: Path, definition: dict) -> dict:
    with TemporaryDirectory(prefix='schlamminger-mutant-') as temp:
        target = Path(temp)
        for path in ATTESTED_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        source_path = target / definition['path']
        text = source_path.read_text()
        if text.count(definition['old']) != 1:
            raise RoundingError(f"mutation patch is not unique: {definition['id']}")
        source_path.write_text(text.replace(definition['old'], definition['new']))
        # -I and explicit root bootstrap prevent the parent checkout from supplying imports.
        bootstrap = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')"
        command = [sys.executable, '-I', '-B', '-c', bootstrap, str(target),
                   '--mutation-root', str(target), '--required-module',
                   'Discovery.schlamminger_2006_rounding_consistency', *definition['tests']]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        process = subprocess.run(command, cwd=target, capture_output=True, text=True,
                                 env=environment, timeout=60)
        if process.returncode:
            raise RoundingError('mutation runner process failed')
        evidence = json.loads(process.stdout)
        outcome = assess_execution(evidence, definition['tests'])
        # Timing and temporary filesystem paths are deliberately absent from stored evidence.
        stable = {key: evidence[key] for key in (
            'runner_status', 'tests_run', 'failing_tests', 'error_tests', 'skipped_tests',
            'successful', 'validated_imports_before', 'validated_imports_after')}
        return {'id': definition['id'], 'category': definition['category'],
                'tests': definition['tests'], 'expected': definition['expected'],
                'outcome': outcome, 'evidence': stable}


def validate_records(records: list) -> None:
    if not isinstance(records, list) or len(records) != len(CASES):
        raise RoundingError('incomplete mutation inventory')
    for definition, record in zip(CASES, records):
        if any(record.get(k) != definition[k] for k in ('id', 'category', 'tests', 'expected')):
            raise RoundingError('mutation definition/evidence inventory differs')
        outcome = assess_execution(record['evidence'], definition['tests'])
        if outcome != record.get('outcome') or outcome != definition['expected']:
            raise RoundingError('mutation survival or invalid calibration')


def definitions_hash() -> str:
    return s.digest(s.serialize_artifact(CASES).encode())


def run_mutations(root: Path = s.ROOT) -> dict:
    s.verify_preregistration(root)
    s.verify_preserved_files(root)
    snapshot = s.source_snapshot(root, ATTESTED_PATHS)
    records = [run_case(root, definition) for definition in CASES]
    validate_records(records)
    return {'schema_version': 1, 'artifact_id': 'schlamminger_2006_mutation_results_v1',
            'source_snapshot': snapshot, 'definitions_sha256': definitions_hash(),
            'preregistration_sha256': s.PREREGISTRATION_SHA256,
            'family_status': 'valid', 'calibration_valid': True,
            'production_count': len(CASES)-2, 'records': records,
            'scope': 'Only Schlamminger wrapper/source boundaries; unchanged generic engine and unrelated families are not mutated.',
            'anti_false_kill_rule': 'Named assertion failures only; errors, skipped tests, collection/import failures and dirty-source freshness failures are invalid.'}


def verify_artifact(artifact: dict, root: Path = s.ROOT) -> None:
    s.verify_preregistration(root)
    if (artifact['source_snapshot'] != s.source_snapshot(root, ATTESTED_PATHS)
            or artifact['definitions_sha256'] != definitions_hash()
            or artifact['preregistration_sha256'] != s.PREREGISTRATION_SHA256
            or artifact['schema_version'] != 1
            or artifact['artifact_id'] != 'schlamminger_2006_mutation_results_v1'
            or artifact['family_status'] != 'valid' or artifact['calibration_valid'] is not True
            or artifact['production_count'] != len(CASES)-2):
        raise RoundingError('mutation source or summary evidence is stale')
    validate_records(artifact['records'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.check:
        verify_artifact(s.read_json((s.ROOT / DEFAULT_OUTPUT).read_bytes()))
        print('Schlamminger mutation evidence verified: 8 production kills, valid calibration')
    else:
        artifact = run_mutations()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(s.serialize_artifact(artifact))
        print('Schlamminger mutations: 8/8 production killed; calibration correct')


if __name__ == '__main__':
    main()
