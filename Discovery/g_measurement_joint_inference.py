"""Logical conjunction of existing representation certificates under separate models."""

from __future__ import annotations

import argparse
from datetime import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess

from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import SourceStateViolationError

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path('Experiments/GMeasurements')
PREREGISTRATION_PATH = DIRECTORY / 'g_measurement_joint_representation_inference_preregistration_v1.json'
DEFAULT_OUTPUT = DIRECTORY / 'g_measurement_joint_representation_inference_v1.json'
BASELINE = '050dde49e733d92a9897706cc7e95e1455edf559'
PREREGISTRATION_COMMIT = '08fe26861252bb426ba116e6b6231920681263eb'
PREREGISTRATION_SHA256 = '1ab4b21bb8d580010d79f6246bef1c258ee71e0b22efbf58759d5965dfe60e15'
EXTERNAL_ANCHOR = {
    'event': 'draft_pull_request_created',
    'url': 'https://github.com/mdiaz4052/The-Number-Project/pull/41',
    'created_at': '2026-09-08T01:50:02Z',
    'preregistration_commit_sha': PREREGISTRATION_COMMIT,
}
# A closed scientific-input inventory; metadata references in certificates are never followed.
INPUT_PATHS = (
    'Experiments/GMeasurements/hust_2018_aaf_rounding_consistency_v1.json',
    'Experiments/GMeasurements/schlamminger_2006_rounding_consistency_v1.json',
)
ARTIFACT_IDS = ('hust_2018_aaf_rounding_consistency_v1',
                'schlamminger_2006_rounding_consistency_v1')
PUBLICATION_IDS = ('doi:10.1038/s41586-018-0431-5', 'doi:10.1103/PhysRevD.74.082001')
REQUIRED_SCOPES = (('combined',), ('statistical', 'systematic'))
STATUS_MAP = {'compatible': 'representable', 'incompatible': 'not_representable',
              'unresolved': 'undetermined'}
SOURCE_PATHS = (
    'Discovery/g_measurement_joint_inference.py',
    'Discovery/preregistration_history.py', 'Discovery/source_history.py',
    'Discovery/__init__.py',
    'Notes/GMeasurementJointRepresentationInferenceSpecification.md',
    'Notes/GMeasurementJointRepresentationInference.md',
    PREREGISTRATION_PATH.as_posix(),
)


class InferenceError(ValueError):
    """Invalid certificate, projection, or inference evidence."""


def serialize_artifact(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(data: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InferenceError('duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise InferenceError('nonfinite JSON value')
    return json.loads(data, object_pairs_hook=unique, parse_constant=invalid)


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True).stdout


def load_protocol(root: Path = ROOT) -> dict:
    data = (root / PREREGISTRATION_PATH).read_bytes()
    if digest(data) != PREREGISTRATION_SHA256:
        raise InferenceError('preregistration bytes changed')
    protocol = read_json(data)
    pin = protocol['specification']
    data = (root / pin['path']).read_bytes()
    if digest(data) != pin['sha256'] or len(data) != pin['byte_length']:
        raise InferenceError('specification differs from freeze')
    return protocol


def verify_preregistration(root: Path = ROOT) -> dict:
    verify_preregistration_freeze(
        root, baseline=BASELINE, commit=PREREGISTRATION_COMMIT,
        path=PREREGISTRATION_PATH.as_posix(), sha256=PREREGISTRATION_SHA256,
    )
    return load_protocol(root)


def input_path_allowed(path: str) -> bool:
    return path in INPUT_PATHS


def load_certificate(root: Path, path: str, pin: dict) -> dict:
    # Reject substitutions before filesystem access, including aliases and symlinks.
    if not input_path_allowed(path) or pin['path'] != path:
        raise InferenceError('scientific input path is not allowed')
    source = root / path
    if source.resolve() != root.resolve() / path:
        raise InferenceError('scientific input path redirects outside its literal location')
    data = source.read_bytes()
    if len(data) != pin['byte_length'] or digest(data) != pin['sha256']:
        raise InferenceError('scientific input bytes differ from freeze')
    certificate = read_json(data)
    expected_id = ARTIFACT_IDS[INPUT_PATHS.index(path)]
    if certificate.get('artifact_id') != expected_id or pin['artifact_id'] != expected_id:
        raise InferenceError('wrong certificate artifact identity')
    if certificate.get('schema_version') != 1:
        raise InferenceError('unsupported certificate version')
    return certificate


def scope_status(verdict: str) -> str:
    try:
        return STATUS_MAP[verdict]
    except (KeyError, TypeError) as error:
        raise InferenceError('unknown scope verdict') from error


def parameter(record: dict) -> Fraction:
    try:
        if set(record) != {'numerator', 'denominator'}:
            raise InferenceError('malformed schedule parameter')
        if not all(isinstance(record[k], str) for k in record):
            raise InferenceError('schedule parameter requires exact integer strings')
        return Fraction(int(record['numerator']), int(record['denominator']))
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise InferenceError('malformed schedule parameter') from error


def project_scope(scope: str, decision: dict, calculation: dict, schedule: dict,
                  membership_key: str, pointer: str) -> dict:
    """Consume only verdict and the established first successful witness identity."""
    try:
        verdict = decision['outcome']
        status = scope_status(verdict)
        witness = decision.get('witness')
        identity = midpoint = kind = None
        if verdict == 'compatible':
            if not isinstance(witness, dict) or witness.get(membership_key) is not True:
                raise InferenceError('compatible scope lacks certified witness membership')
            index = witness['candidate_index']
            candidates, parameters = calculation['candidates'], schedule['parameters']
            if (type(index) is not int or not 0 <= index < len(candidates)
                    or len(candidates) != len(parameters) or not parameters):
                raise InferenceError('invalid witness index or schedule inventory')
            selected = parameter(candidates[index]['parameter'])
            if (parameter(candidates[0]['parameter']) != 0 or Fraction(parameters[0]) != 0
                    or selected != Fraction(parameters[index]) or (selected == 0) != (index == 0)):
                raise InferenceError('witness identity disagrees with midpoint-first schedule')
            midpoint = index == 0
            kind = 'unshifted_midpoint' if midpoint else 'shifted_scheduled'
            identity = {'candidate_index': index,
                        'parameter': {'numerator': str(selected.numerator),
                                      'denominator': str(selected.denominator)},
                        'membership_verified': True,
                        'candidate_pointer': f'{pointer}/candidates/{index}'}
        elif witness is not None:
            raise InferenceError('noncompatible scope must not assert a witness')
        return {'scope': scope, 'original_verdict': verdict, 'scope_status': status,
                'witness': identity, 'unshifted_midpoint_consistent': midpoint,
                'witness_kind': kind}
    except (KeyError, TypeError, IndexError, ValueError) as error:
        raise InferenceError(f'malformed scope certificate: {scope}') from error


def project_publication(certificate: dict, artifact_id: str) -> dict:
    """Discard every measurement value and all external provenance references."""
    try:
        index = ARTIFACT_IDS.index(artifact_id)
        if certificate['artifact_id'] != artifact_id or certificate['schema_version'] != 1:
            raise InferenceError('wrong certificate identity')
        required = REQUIRED_SCOPES[index]
        scopes = {}
        for scope in required:
            if index == 0:
                decision, calculation = certificate['decision'], certificate['calculation']
                membership, pointer = 'input_and_comparison_membership_verified', '/calculation'
            else:
                if (set(certificate['terminal_decisions']) != set(required)
                        or set(certificate['calculations']) != set(required)
                        or certificate['scope_order'] != list(required)):
                    raise InferenceError('required publication scope inventory differs')
                decision = certificate['terminal_decisions'][scope]
                calculation = certificate['calculations'][scope]
                membership, pointer = 'membership_verified', f'/calculations/{scope}'
            scopes[scope] = project_scope(scope, decision, calculation,
                                         certificate['candidate_schedule'], membership, pointer)
        return {'publication_id': PUBLICATION_IDS[index], 'input_artifact_id': artifact_id,
                'required_scopes': list(required), 'scopes': scopes}
    except (KeyError, ValueError, TypeError) as error:
        raise InferenceError('malformed publication certificate') from error


def conjunction(statuses: list[str]) -> tuple[str, str]:
    """Strong three-valued conjunction of a nonempty inventory."""
    if not statuses or any(s not in STATUS_MAP.values() for s in statuses):
        raise InferenceError('nonempty valid status inventory required')
    if 'not_representable' in statuses:
        return 'not_representable', 'any_not_representable'
    if all(s == 'representable' for s in statuses):
        return 'representable', 'all_representable'
    return 'undetermined', 'otherwise_undetermined'


def publication_decision(projection: dict) -> dict:
    required, scopes = projection['required_scopes'], projection['scopes']
    if not required or len(set(required)) != len(required) or set(scopes) != set(required):
        raise InferenceError('missing or duplicate required scope')
    statuses = [scope_status(scopes[name]['original_verdict']) for name in required]
    if any(scopes[name]['scope_status'] != status for name, status in zip(required, statuses)):
        raise InferenceError('scope projection contradicts original verdict')
    status, rule = conjunction(statuses)
    return {**projection, 'status': status,
            'reasoning_trace': {'rule': rule, 'operands': [
                {'scope': name, 'status': status} for name, status in zip(required, statuses)]}}


def joint_decision(publications: list[dict]) -> dict:
    identifiers = [p['publication_id'] for p in publications]
    if len(set(identifiers)) != len(identifiers):
        raise InferenceError('publication identities must be distinct')
    status, rule = conjunction([p['status'] for p in publications])
    joint = {'representable': 'all_representable_under_separate_declared_models',
             'not_representable': 'not_all_representable', 'undetermined': 'undetermined'}[status]
    return {'status': joint, 'logical_operator': 'conjunction',
            'domains': 'source_specific_and_uncoupled',
            'reasoning_trace': {'rule': rule, 'operands': [
                {'publication_id': p['publication_id'], 'status': p['status']} for p in publications]}}


def compose(certificates: dict) -> tuple[list[dict], dict]:
    if set(certificates) != set(ARTIFACT_IDS):
        raise InferenceError('both required publications must be present')
    publications = [publication_decision(project_publication(certificates[name], name))
                    for name in ARTIFACT_IDS]
    return publications, joint_decision(publications)


def verify_inputs(root: Path, protocol: dict) -> dict:
    pins = protocol['inputs']
    if tuple(pin['path'] for pin in pins) != INPUT_PATHS:
        raise InferenceError('frozen input inventory differs from allowlist')
    certificates = {}
    for index, pin in enumerate(pins):
        if (pin['publication_id'] != PUBLICATION_IDS[index]
                or pin['required_scopes'] != list(REQUIRED_SCOPES[index])):
            raise InferenceError('frozen publication or scope inventory differs')
        epoch = pin['generating_verification_epoch']
        git(root, 'merge-base', '--is-ancestor', epoch, BASELINE)
        historical = git(root, 'show', f"{epoch}:{pin['path']}")
        if digest(historical) != pin['sha256']:
            raise InferenceError('input differs from generating verification epoch')
        certificates[pin['artifact_id']] = load_certificate(root, pin['path'], pin)
    return certificates


def verify_preserved_files(root: Path = ROOT) -> None:
    # Preservation pins exclude all E-001 artifacts; they are never opened here.
    for pin in load_protocol(root)['preserved_baseline_files']:
        data = (root / pin['path']).read_bytes()
        if len(data) != pin['byte_length'] or digest(data) != pin['sha256']:
            raise InferenceError('historical artifact or generic engine changed')


def source_snapshot(root: Path = ROOT, paths=SOURCE_PATHS) -> dict:
    commit = git(root, 'log', '-1', '--format=%H', '--', *paths).decode().strip()
    files = []
    for path in paths:
        current = (root / path).read_bytes()
        if git(root, 'show', f'{commit}:{path}') != current:
            raise SourceStateViolationError('commit result-driving source before emitting an artifact')
        files.append({'path': path, 'sha256': digest(current)})
    return {'source_commit_sha': commit, 'files': files}


def verify_implementation_chronology(root: Path, snapshot: dict) -> None:
    commit = snapshot['source_commit_sha']
    git(root, 'merge-base', '--is-ancestor', PREREGISTRATION_COMMIT, commit)
    first = git(root, 'log', '--reverse', '--diff-filter=A', '--format=%H',
                f'{PREREGISTRATION_COMMIT}..HEAD', '--', SOURCE_PATHS[0]).decode().splitlines()
    if not first:
        raise InferenceError('implementation must be introduced after freeze')
    anchor = datetime.fromisoformat(EXTERNAL_ANCHOR['created_at'].replace('Z', '+00:00'))
    # Git clocks corroborate ordering; the independently supplied PR event is the external anchor.
    for field in ('%aI', '%cI'):
        stamp = datetime.fromisoformat(git(root, 'show', '-s', f'--format={field}', first[0]).decode().strip())
        if stamp <= anchor:
            raise InferenceError('implementation timestamp does not follow external PR anchor')


def build_artifact(root: Path = ROOT) -> dict:
    protocol = verify_preregistration(root)
    certificates = verify_inputs(root, protocol)
    snapshot = source_snapshot(root)
    verify_implementation_chronology(root, snapshot)
    publications, joint = compose(certificates)
    return {'schema_version': 1, 'artifact_id': 'g_measurement_joint_representation_inference_v1',
            'provenance': {'intended_base': BASELINE,
                           'preregistration_artifact_id': protocol['artifact_id'],
                           'preregistration_path': PREREGISTRATION_PATH.as_posix(),
                           'preregistration_commit_sha': PREREGISTRATION_COMMIT,
                           'preregistration_sha256': PREREGISTRATION_SHA256,
                           'external_anchor': EXTERNAL_ANCHOR,
                           'source_snapshot': snapshot, 'inputs': protocol['inputs']},
            'publications': publications, 'joint_decision': joint,
            'nonclaims': protocol['claim_limits']}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    text = serialize_artifact(build_artifact())
    verify_preserved_files()
    if args.check:
        if (ROOT / DEFAULT_OUTPUT).read_text() != text:
            raise InferenceError('joint artifact is stale')
        print('Joint representation inference: provenance, chronology, inputs and result verified')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)


if __name__ == '__main__':
    main()
