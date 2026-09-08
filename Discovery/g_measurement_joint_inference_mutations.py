"""Bounded behavioral mutations of the separate-model logical inference boundary."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from Discovery import g_measurement_joint_inference as j

DEFAULT_OUTPUT = j.DIRECTORY / 'g_measurement_joint_representation_inference_mutation_results_v1.json'
MODULE_PATH = 'Discovery/g_measurement_joint_inference.py'
TEST_PATH = 'tests/test_g_measurement_joint_inference.py'
TEST_PREFIX = 'tests.test_g_measurement_joint_inference.JointBehaviorTests.'
ATTESTED_PATHS = j.SOURCE_PATHS + (
    'Discovery/g_measurement_joint_inference_mutations.py', TEST_PATH,
    'tests/test_g_measurement_joint_inference_mutations.py',
    'Discovery/mutation_test_runner.py',
)


def case(identifier, category, old, new, test, expected='KILLED'):
    return {'id': identifier, 'category': category, 'path': MODULE_PATH,
            'old': old, 'new': new, 'tests': [TEST_PREFIX + test], 'expected': expected}


TRUTH = 'test_all_27_verdict_combinations'
CASES = (
    case('calibration_killable_parameter_sign', 'calibration',
         "return Fraction(int(record['numerator']), int(record['denominator']))",
         "return abs(Fraction(int(record['numerator']), int(record['denominator'])))",
         'test_exact_parameter_decoding'),
    case('calibration_equivalent_mapping_copy', 'calibration',
         'return STATUS_MAP[verdict]', 'return dict(STATUS_MAP)[verdict]',
         TRUTH, 'SURVIVED'),
    case('ignore_publication', 'production', 'for name in ARTIFACT_IDS]',
         'for name in ARTIFACT_IDS[:1]]', 'test_both_publications_are_required_and_used'),
    case('ignore_required_scope', 'production', 'for scope in required:',
         'for scope in required[:1]:', 'test_required_scope_projection_and_missing_scope'),
    case('unresolved_promoted_true', 'production', "'unresolved': 'undetermined'",
         "'unresolved': 'representable'", TRUTH),
    case('unresolved_promoted_false', 'production', "'unresolved': 'undetermined'",
         "'unresolved': 'not_representable'", TRUTH),
    case('incompatible_loses_dominance', 'production', "if 'not_representable' in statuses:",
         "if 'not_representable' in statuses and 'undetermined' not in statuses:", TRUTH),
    case('erase_midpoint_distinction', 'production', 'midpoint = index == 0',
         'midpoint = True', 'test_midpoint_characterization_and_truth_invariance'),
    case('admit_e001_input', 'production', 'return path in INPUT_PATHS',
         "return path.endswith('.json')", 'test_e001_path_allowlist'),
    case('central_G_affects_decision', 'production',
         "status, rule = conjunction(statuses)\n    return {**projection",
         "status, rule = conjunction(statuses)\n"
         "    if scopes[required[0]].get('central_G', 0) > 0:\n"
         "        status = 'not_representable'\n    return {**projection",
         'test_central_values_cannot_affect_truth_or_projection'),
    case('invert_joint_status', 'production',
         "return {'status': joint, 'logical_operator': 'conjunction',",
         "joint = 'not_all_representable' if joint == 'all_representable_under_separate_declared_models' else 'all_representable_under_separate_declared_models'\n"
         "    return {'status': joint, 'logical_operator': 'conjunction',", TRUTH),
)


def mutation_tuple(definition: dict) -> tuple:
    return definition['path'], definition['old'], definition['new']


def validate_definitions(source: str) -> None:
    production = CASES[2:]
    if (len(CASES) != 11 or len({c['id'] for c in CASES}) != len(CASES)
            or mutation_tuple(CASES[0]) in {mutation_tuple(c) for c in production}
            or CASES[0]['tests'][0] in {t for c in production for t in c['tests']}):
        raise j.InferenceError('calibration must be distinct from production mutations')
    changed_hashes = []
    for c in CASES:
        if (c['path'] != MODULE_PATH or c['old'] == c['new'] or source.count(c['old']) != 1
                or not c['tests'] or any(not t.startswith(TEST_PREFIX) for t in c['tests'])):
            raise j.InferenceError('invalid, nonunique or nonbehavioral mutation definition')
        changed_hashes.append(j.digest(source.replace(c['old'], c['new']).encode()))
    if len(set(changed_hashes)) != len(CASES):
        raise j.InferenceError('calibration and production mutant bytes must be distinct')


def assess_execution(record: dict, tests: list[str]) -> str:
    """Only named unittest assertion failures count; infrastructure never counts."""
    if (record.get('runner_status') != 'completed' or record.get('tests_run') != len(tests)
            or record.get('error_tests') or record.get('skipped_tests')
            or not isinstance(record.get('failing_tests'), list)
            or not set(record['failing_tests']).issubset(tests)
            or any(marker in record.get('test_output', '') for marker in
                   ('source_state_violated', 'commit result-driving source', 'SyntaxError', 'ImportError'))):
        raise j.InferenceError('invalid mutation execution; not a kill')
    module = MODULE_PATH[:-3].replace('/', '.')
    for key in ('validated_imports_before', 'validated_imports_after'):
        if record.get(key, {}).get(module) != MODULE_PATH:
            raise j.InferenceError('mutation import binding missing')
    failures = bool(record['failing_tests'])
    if record.get('successful') is not (not failures):
        raise j.InferenceError('mutation success/failure evidence contradicts itself')
    return 'KILLED' if failures else 'SURVIVED'


def run_case(root: Path, definition: dict, *, mutate=True) -> dict:
    with TemporaryDirectory(prefix='joint-inference-mutant-') as temp:
        target = Path(temp)
        for path in ATTESTED_PATHS:
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / path, destination)
        source_path = target / MODULE_PATH
        source = source_path.read_text()
        if mutate:
            if source.count(definition['old']) != 1:
                raise j.InferenceError('mutation patch is not unique')
            source = source.replace(definition['old'], definition['new'])
            source_path.write_text(source)
        bootstrap = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('Discovery.mutation_test_runner',run_name='__main__')"
        command = [sys.executable, '-I', '-B', '-c', bootstrap, str(target),
                   '--mutation-root', str(target), '--required-module',
                   'Discovery.g_measurement_joint_inference', *definition['tests']]
        process = subprocess.run(command, cwd=target, capture_output=True, text=True,
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), timeout=60)
        if process.returncode:
            raise j.InferenceError('mutation runner process failed')
        evidence = json.loads(process.stdout)
        outcome = assess_execution(evidence, definition['tests'])
        stable = {key: evidence[key] for key in (
            'runner_status', 'tests_run', 'failing_tests', 'error_tests', 'skipped_tests',
            'successful', 'validated_imports_before', 'validated_imports_after')}
        return {'id': definition['id'], 'category': definition['category'],
                'tests': definition['tests'], 'expected': definition['expected'],
                'outcome': outcome, 'applied_source_sha256': j.digest(source.encode()),
                'evidence': stable}


def baseline_definition() -> dict:
    return {'id': 'unmutated_baseline', 'category': 'baseline', 'expected': 'SURVIVED',
            'tests': sorted({test for c in CASES for test in c['tests']})}


def validate_records(records: list, source: str) -> None:
    definitions = (baseline_definition(),) + CASES
    if not isinstance(records, list) or len(records) != len(definitions):
        raise j.InferenceError('incomplete mutation inventory')
    for definition, record in zip(definitions, records):
        if any(record.get(k) != definition[k] for k in ('id', 'category', 'tests', 'expected')):
            raise j.InferenceError('mutation definition/evidence inventory differs')
        expected_source = (source if definition['category'] == 'baseline'
                           else source.replace(definition['old'], definition['new']))
        if record.get('applied_source_sha256') != j.digest(expected_source.encode()):
            raise j.InferenceError('applied mutation source hash differs')
        outcome = assess_execution(record['evidence'], definition['tests'])
        if outcome != record.get('outcome') or outcome != definition['expected']:
            raise j.InferenceError('mutation survived or calibration invalid')


def definitions_hash() -> str:
    return j.digest(j.serialize_artifact(CASES).encode())


def envelope(snapshot: dict, records: list) -> dict:
    return {'schema_version': 1,
            'artifact_id': 'g_measurement_joint_representation_inference_mutation_results_v1',
            'source_snapshot': snapshot, 'definitions_sha256': definitions_hash(),
            'preregistration_sha256': j.PREREGISTRATION_SHA256,
            'family_status': 'valid', 'calibration_valid': True, 'production_count': 9,
            'records': records,
            'scope': 'Joint representation logic and its narrow input boundary only.',
            'anti_false_kill_rule': 'Named assertion failures only; infrastructure, import, syntax, skip and source-freshness failures are invalid.'}


def run_mutations(root: Path = j.ROOT) -> dict:
    j.verify_preregistration(root)
    j.verify_preserved_files(root)
    source = (root / MODULE_PATH).read_text()
    validate_definitions(source)
    snapshot = j.source_snapshot(root, ATTESTED_PATHS)
    records = [run_case(root, baseline_definition(), mutate=False)]
    if records[0]['outcome'] != 'SURVIVED':
        raise j.InferenceError('unmutated behavioral baseline failed')
    records += [run_case(root, definition) for definition in CASES]
    validate_records(records, source)
    return envelope(snapshot, records)


def verify_artifact(artifact: dict, root: Path = j.ROOT) -> None:
    j.verify_preregistration(root)
    source = (root / MODULE_PATH).read_text()
    validate_definitions(source)
    validate_records(artifact['records'], source)
    if artifact != envelope(j.source_snapshot(root, ATTESTED_PATHS), artifact['records']):
        raise j.InferenceError('mutation source or summary evidence is stale')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.check:
        verify_artifact(j.read_json((j.ROOT / DEFAULT_OUTPUT).read_bytes()))
        print('Joint inference mutation evidence verified: 9 production kills, valid calibration')
    else:
        artifact = run_mutations()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(j.serialize_artifact(artifact))
        print('Joint inference mutations: 9/9 production killed; calibration correct')


if __name__ == '__main__':
    main()
