"""Exact conditional audits of both Schlamminger 2006 Table VII subtotals."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from Discovery.rounding_consistency import (
    Budget, Interval, RoundingError, calculate, calculation_record, classify,
    decimal_fraction, interval_record, rounding_bin, verify_witness,
)
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import (
    SourceStateViolationError, SourceVerificationError, exit_for_source_verification_error,
)

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path('Experiments/GMeasurements')
PREREGISTRATION_PATH = DIRECTORY / 'schlamminger_2006_rounding_consistency_preregistration_v1.json'
SOURCE_PATH = DIRECTORY / 'schlamminger_2006_source_attestation_v1.json'
DEFAULT_OUTPUT = DIRECTORY / 'schlamminger_2006_rounding_consistency_v1.json'
BASELINE = '7e01334a911ab5bd664b2e32c16149c6739b5f7c'
PREREGISTRATION_COMMIT = '91f8bbc1eb652294ed772f1ce7f477d85705f23e'
PREREGISTRATION_SHA256 = '8783fa70333d2f3b41455189ecc2dcdfc1b358deb08e94914f56f8be09fcc6ad'
EXTERNAL_ANCHOR = {
    'event': 'draft_pull_request_created',
    'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/40',
    'created_at': '2026-09-08T00:43:06Z',
    'preregistration_commit_sha': PREREGISTRATION_COMMIT,
    'scope': 'Prospective classification freeze with known source data, not a blind physical prediction.',
}
SCOPES = ('statistical', 'systematic')
COMPONENT_IDS = {
    'statistical': ('weighings', 'tm_sorption', 'linearity', 'calibration', 'mass_integration'),
    'systematic': ('tm_sorption', 'calibration', 'mass_integration'),
}
SOURCE_PATHS = (
    'Discovery/rounding_consistency.py',
    'Discovery/schlamminger_2006_rounding_consistency.py',
    'Discovery/preregistration_history.py',
    'Discovery/source_history.py',
    'Notes/Schlamminger2006RoundingConsistencySpecification.md',
    PREREGISTRATION_PATH.as_posix(), SOURCE_PATH.as_posix(),
)


def serialize_artifact(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RoundingError('duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise RoundingError('nonfinite JSON value')
    return json.loads(data, object_pairs_hook=unique, parse_constant=invalid)


def load_protocol(root: Path = ROOT) -> dict:
    data = (root / PREREGISTRATION_PATH).read_bytes()
    if digest(data) != PREREGISTRATION_SHA256:
        raise RoundingError('preregistration bytes changed')
    protocol = read_json(data)
    pin = protocol['specification']
    spec = (root / pin['path']).read_bytes()
    if digest(spec) != pin['sha256'] or len(spec) != pin['byte_length']:
        raise RoundingError('bounded specification differs from freeze')
    return protocol


def verify_preregistration(root: Path = ROOT) -> dict:
    verify_preregistration_freeze(
        root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
        path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256,
    )
    return load_protocol(root)


def verify_source_bytes(data: bytes, protocol: dict) -> dict:
    if digest(data) != protocol['source_attestation_sha256']:
        raise RoundingError('source attestation bytes differ from freeze')
    attestation = read_json(data)
    if attestation != protocol['source_attestation']:
        raise RoundingError('source attestation projection differs from freeze')
    for key, hash_key in (('input_projection', 'input_projection_sha256'),
                          ('terminal_comparisons', 'terminal_projection_sha256')):
        if digest(serialize_artifact(attestation[key]).encode()) != attestation[hash_key]:
            raise RoundingError('source projection hash mismatch')
    return attestation


def load_source(root: Path = ROOT) -> tuple[dict, dict]:
    protocol = load_protocol(root)
    return protocol, verify_source_bytes((root / SOURCE_PATH).read_bytes(), protocol)


def validate_projection(projection: dict) -> None:
    """Validate a calculator-only schema; no terminal or foreign inputs accepted."""
    try:
        if (set(projection) != {'scope_order', 'component_unit', 'central_value', 'components'}
                or projection['scope_order'] != list(SCOPES)
                or projection['component_unit'] != 'ppm'
                or set(projection['components']) != set(SCOPES)):
            raise RoundingError('calculation scope inventory or unit changed')
        central = projection['central_value']
        if (set(central) != {'value', 'unit', 'role'}
                or central['unit'] != 'm^3 kg^-1 s^-2'
                or central['role'] != 'positive_schema_context_only'
                or decimal_fraction(central['value']) <= 0):
            raise RoundingError('invalid positive central context')
        for scope in SCOPES:
            rows = projection['components'][scope]
            if not isinstance(rows, list) or tuple(r['id'] for r in rows) != COMPONENT_IDS[scope]:
                raise RoundingError('component inventory differs from Table VII scope')
            for row in rows:
                if (set(row) != {'id', 'value_ppm'} or not isinstance(row['value_ppm'], str)
                        or not re.fullmatch(r'[0-9]+\.[0-9]', row['value_ppm'])
                        or decimal_fraction(row['value_ppm']) <= 0):
                    raise RoundingError('component must be a positive one-decimal ppm value')
    except (KeyError, TypeError, AttributeError) as error:
        raise RoundingError('malformed calculation projection') from error


def candidate_parameters(schedule: dict) -> tuple[Fraction, ...]:
    return tuple(Fraction(t) for t in schedule['parameters'])


def calculate_scopes(projection: dict, rounding_policy: dict, schedule: dict) -> dict:
    """No comparisons, source results, HUST values or external constants enter here."""
    validate_projection(projection)
    half = decimal_fraction(rounding_policy['component_half_width_ppm'])
    central = decimal_fraction(projection['central_value']['value'])
    parameters = candidate_parameters(schedule)
    calculations = {}
    for scope in SCOPES:
        rows = projection['components'][scope]
        budget = Budget(
            (central,),
            tuple((rounding_bin(decimal_fraction(row['value_ppm']), half),) for row in rows),
            tuple('independent' for _ in rows),
        )
        calculations[scope] = calculate(budget, parameters)
    return calculations


def comparison_intervals(comparisons: dict) -> dict:
    try:
        if not isinstance(comparisons, dict) or set(comparisons) != set(SCOPES):
            raise RoundingError('both terminal scopes are required')
        result = {}
        for scope in SCOPES:
            item = comparisons[scope]
            if (set(item) != {'scope', 'role', 'value_ppm', 'half_width_ppm'}
                    or item['scope'] != scope or item['role'] != 'terminal_only'):
                raise RoundingError('terminal comparison scope or role mismatch')
            result[scope] = rounding_bin(decimal_fraction(item['value_ppm']),
                                         decimal_fraction(item['half_width_ppm']))
        return result
    except (KeyError, TypeError, AttributeError) as error:
        raise RoundingError('missing or malformed comparison') from error


def terminal_decisions(calculations: dict, comparisons: dict) -> dict:
    if set(calculations) != set(SCOPES):
        raise RoundingError('both calculations must precede terminal decisions')
    intervals = comparison_intervals(comparisons)
    result = {}
    for scope in SCOPES:
        calculation, comparison = calculations[scope], intervals[scope]
        outcome, index = classify(calculation, comparison)
        witness = None
        if index is not None:
            witness = {'candidate_index': index,
                       'membership_verified': verify_witness(
                           calculation.budget, calculation.candidates[index], comparison)}
        result[scope] = {
            'comparison': {'role': 'terminal_only', 'source_reference': comparisons[scope],
                           'interval_ppm': interval_record(comparison),
                           'squared_interval_ppm_squared': interval_record(comparison.square())},
            'outcome': outcome, 'witness': witness,
            'exclusion': ({'calculation_enclosure_ppm_squared': interval_record(calculation.enclosure),
                           'comparison_enclosure_ppm_squared': interval_record(comparison.square()),
                           'strict_disjointness': (calculation.enclosure.high < comparison.low**2
                                                  or comparison.high**2 < calculation.enclosure.low)}
                          if outcome == 'incompatible' else None),
        }
    return result


def source_snapshot(root: Path = ROOT, paths=SOURCE_PATHS) -> dict:
    """Pin the last committed change of this explicit, fully hashed path set."""
    commit = subprocess.run(['git', '-C', str(root), 'log', '-1', '--format=%H', '--', *paths],
                            capture_output=True, text=True, check=True).stdout.strip()
    files = []
    for path in paths:
        current = (root / path).read_bytes()
        recorded = subprocess.run(['git', '-C', str(root), 'show', f'{commit}:{path}'],
                                  capture_output=True)
        if recorded.returncode or recorded.stdout != current:
            raise SourceStateViolationError('commit result-driving source before emitting an artifact')
        files.append({'path': path, 'sha256': digest(current)})
    return {'source_commit_sha': commit, 'files': files}


def verify_preserved_files(root: Path = ROOT) -> None:
    for pin in load_protocol(root)['preserved_baseline_files']:
        data = (root / pin['path']).read_bytes()
        if len(data) != pin['byte_length'] or digest(data) != pin['sha256']:
            raise RoundingError('pre-existing artifact or generic engine changed')


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    _, attestation = load_source(root)
    projection = attestation['input_projection']
    calculations = calculate_scopes(projection, protocol['rounding_policy'], protocol['candidate_schedule'])
    # Both complete calculations exist before any terminal enters classification.
    records = {scope: calculation_record(calculations[scope],
                places=protocol['calculation']['output_ppm_decimal_places']) for scope in SCOPES}
    decisions = terminal_decisions(calculations, attestation['terminal_comparisons'])
    return {
        'schema_version': 1, 'artifact_id': 'schlamminger_2006_rounding_consistency_v1',
        'kind': 'conditional_published_table_rounding_consistency',
        'integrity': {'baseline_main_sha': BASELINE, 'preregistration_commit_sha': PREREGISTRATION_COMMIT,
                      'preregistration_sha256': PREREGISTRATION_SHA256, 'external_anchor': EXTERNAL_ANCHOR,
                      'source_snapshot': source_snapshot(root),
                      'source_attestation_sha256': protocol['source_attestation_sha256']},
        'scope_order': list(SCOPES), 'input_projection': projection,
        'rounding_policy': protocol['rounding_policy'], 'candidate_schedule': protocol['candidate_schedule'],
        'calculation_policy': protocol['calculation'], 'calculations': records, 'terminal_decisions': decisions,
        'claim_limits': protocol['claim_limits'],
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        artifact = build_artifact()
        text = serialize_artifact(artifact)
        if args.check:
            verify_preserved_files()
            if (ROOT / DEFAULT_OUTPUT).read_text() != text:
                raise RoundingError('Schlamminger result artifact is stale')
            print('Schlamminger source, chronology and both rounding artifacts verified')
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text)
        else:
            print(text, end='')
    except SourceVerificationError as error:
        exit_for_source_verification_error(error)
    except (RoundingError, OSError, ValueError) as error:
        print(f'schlamminger_invalid: {error}', file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == '__main__':
    main()
