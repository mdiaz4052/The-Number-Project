"""Offline custody/disposition verifier for PySRAdapter1's terminal setup epoch.

This is not a real-generator adapter. No dependency install, Julia execution,
fit, card issuance, stochastic replay, or claim of upstream incompatibility.
The only implemented route is the reached setup NO_GO; other stages fail closed.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import subprocess
import sys

from Discovery import candidate_exchange as cx

ROOT = Path(__file__).resolve().parents[1]
REL = 'Experiments/SymbolicDiscovery/PySRAdapter1'
PKG = ROOT / REL
TASK = 'NP-PYSR-ADAPTER-01'
NS = 'np-pysr-adapter/1'
WORK_SHA = '938d7c884cc2b6add3dae4775de8159b387d2addd7fd5654f4cd50eff3670583'
JULIA_SHA = '6a78a03a71c7ab792e8673dc5cedb918e037f081ceb58b50971dfb7c64c5bf81'
JULIA_ARCHIVE = 'julia-1.10.10-linux-x86_64.tar.gz'
STEP_IDS = ('attempt-01', 'julia-download-01', 'julia-verify-01',
            'python-install-01', 'extraction-retry-01', 'julia-resolve-01')
SETUP_NAMES = tuple(sorted(
    [s + ext for s in STEP_IDS for ext in ('.json', '.stdout', '.stderr')]
    + ['engine-env.json', 'extraction-failure.json', 'juliacall-juliapkg.json',
       'pysr-juliapkg.json', 'python-freeze.txt', 'python-resolution.json',
       'requested-juliapkg.json', 'resolve_stack.py', 'setup_step.py', 'stop.json']))
SOURCE_PATHS = (
    'Discovery/pysr_adapter_setup_verifier.py', 'tests/test_pysr_adapter_setup.py',
    'Discovery/candidate_exchange.py', 'Discovery/dimensions.py',
    'Discovery/symbolic_benchmark_engine.py', 'Discovery/dependency_definitions.py',
    'Discovery/planck_identities.py', 'Discovery/constants.py',
    'Discovery/dimensional_search.py', 'Discovery/monomial_constraints.py',
) + tuple(REL + '/' + n for n in (
    'work_order.r1.md', 'work_order_receipt.json', 'contract.v1.md', 'anchor.json',
)) + tuple(REL + '/setup/' + n for n in SETUP_NAMES)
RESULT_FIELDS = {'schema', 'task', 'disposition', 'stage', 'evidence_integrity',
    'adapter_conformance', 'operational_acceptance', 'review_status', 'outcome_blind',
    'search_coverage', 'scientific_evidence', 'source_binding', 'evidence',
    'planned_runs', 'limitations'}
UNPERFORMED = ('native_export_qualification', 'adapter_implementation',
              'adapter_fixtures', 'eight_adapter_mutations')
LIMITATIONS = [
    'Terminal setup-only NO_GO; no executable adapter was qualified or delivered.',
    'SIGBUS root cause unresolved; not evidence of an upstream PySR/Julia defect.',
    'Initial tar ownership-failure output survives as attributed excerpts, not full stderr.',
    'Python packages resolved, but backend and complete transitive Julia locks did not.',
    'No native outputs, arithmetic parity, dimensions, domains or DM-099 gate were exercised.',
    'No target seed, data, search, selection or heldout evaluation occurred.',
    'Offline checks validate committed records; they do not rerun Julia or prove operator truthfulness.',
    'DM-098 coverage is limited to this reached setup route; no broad outcome framework or finding closure.',
]


def require(condition, code, message):
    cx.require(condition, code, message)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def stamp(value):
    require(type(value) is str, 'CHRONOLOGY', 'Timestamp must be a string.')
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise cx.ContractError('CHRONOLOGY', 'Malformed timestamp.') from exc
    require(t.tzinfo is not None, 'CHRONOLOGY', 'Timezone required.')
    return t


def setup_bytes():
    paths = {p.name: p.read_bytes() for p in (PKG / 'setup').iterdir() if p.is_file()}
    require(set(paths) == set(SETUP_NAMES), 'INVENTORY', 'Exact setup evidence inventory required.')
    return paths


def validate_setup(raw, draft_time):
    """Derive the reached prerequisite failure from retained records and diagnostics.

    Caller data is not a verification token. check() additionally binds all bytes
    to their source/evidence commits. Logs are receipts, never native replay.
    """
    require(type(raw) is dict and set(raw) == set(SETUP_NAMES),
            'INVENTORY', 'Missing, extra or substituted setup evidence.')
    records = {}
    base_fields = {'schema', 'command', 'started_at', 'finished_at', 'returncode',
                   'stdout_sha256', 'stderr_sha256'}
    for name in STEP_IDS:
        r = cx.loads(raw[name + '.json'])
        fields = base_fields | ({'attempt', 'stage', 'python', 'platform'}
                               if name == 'attempt-01' else {'step'})
        cx.fields(r, fields)
        require(r['schema'] == NS + ('/setup-attempt' if name == 'attempt-01' else '/setup-step'),
                'SCHEMA', 'Wrong setup receipt schema.')
        require(type(r['returncode']) is int and type(r['command']) is list
                and all(type(x) is str for x in r['command']), 'SCHEMA', 'Invalid process receipt.')
        require(stamp(draft_time) <= stamp(r['started_at']) <= stamp(r['finished_at']),
                'CHRONOLOGY', 'Setup must follow draft anchor; negative duration forbidden.')
        if name != 'attempt-01':
            require(r['step'] == name, 'IDENTITY', 'Step identity mismatch.')
        for suffix in ('stdout', 'stderr'):
            require(type(raw[name + '.' + suffix]) is bytes
                    and cx.sha(raw[name + '.' + suffix]) == r[suffix + '_sha256'],
                    'RAW_BINDING', 'Diagnostic bytes disagree with receipt.')
        records[name] = r
    first = records['attempt-01']
    require(first['attempt'] == 1 and first['stage'] == 'official_julia_checksum_transport'
            and first['python']['implementation'] == 'cpython'
            and first['python']['version'] == '3.12.14', 'ENVIRONMENT', 'Wrong initial setup identity.')
    for name in STEP_IDS[:-1]:
        require(records[name]['returncode'] == 0, 'PREREQUISITE', 'Earlier qualified step did not succeed.')
    require(first['command'][-1] == 'https://julialang-s3.julialang.org/bin/checksums/julia-1.10.10.sha256',
            'IDENTITY', 'Wrong checksum source.')
    checksum_lines = raw['attempt-01.stdout'].decode().splitlines()
    require(checksum_lines.count(JULIA_SHA + '  ' + JULIA_ARCHIVE) == 1,
            'IDENTITY', 'Official platform checksum missing or duplicated.')
    require(records['julia-download-01']['command'][-1] ==
            'https://julialang-s3.julialang.org/bin/linux/x64/1.10/' + JULIA_ARCHIVE,
            'IDENTITY', 'Wrong binary source.')
    require(raw['julia-verify-01.stdout'].decode().strip() ==
            'bytes 173848413 sha256 ' + JULIA_SHA, 'IDENTITY', 'Binary verification disagrees.')
    require(records['python-install-01']['command'][-1] == 'pysr==1.5.10',
            'IDENTITY', 'PySR target changed.')
    requested = cx.loads(raw['requested-juliapkg.json'])
    require(requested == {'packages': {'SymbolicRegression': {
        'uuid': '8254be44-1295-4e6a-a16d-46603ac705cb', 'version': '=1.11.0'}}},
        'IDENTITY', 'Backend target changed.')
    require(cx.loads(raw['pysr-juliapkg.json'])['packages']['SymbolicRegression']['version'] == '~1.11.0',
            'IDENTITY', 'Pinned PySR compatibility declaration changed.')
    resolution = cx.loads(raw['python-resolution.json'])
    require(resolution['qualified'] is False, 'EVIDENCE', 'Python install is not full stack qualification.')
    packages = resolution['packages']
    require(type(packages) is list and len({p['name'] for p in packages}) == len(packages),
            'INVENTORY', 'Duplicate package identity.')
    versions = {p['name']: p['version'] for p in packages}
    require(versions.get('pysr') == '1.5.10' and versions.get('juliacall') == '0.9.26'
            and versions.get('juliapkg') == '0.1.26', 'IDENTITY', 'Python stack identity changed.')
    freeze = raw['python-freeze.txt'].decode().splitlines()
    for p in packages:
        h = p['download_info']['archive_info']['hashes']['sha256']
        require(type(h) is str and re.fullmatch('[0-9a-f]{64}', h) is not None,
                'IDENTITY', 'Missing package distribution digest.')
        require(p['name'] + '==' + p['version'] in freeze, 'IDENTITY', 'Package lock mismatch.')
    extraction = cx.loads(raw['extraction-failure.json'])
    require(extraction['returncode'] == 2 and extraction['setup_retry_used'] == 1
            and 'truncated' in extraction['retention']
            and any('Cannot change ownership' in x for x in extraction['stderr_excerpts']),
            'RETRY', 'First extraction failure and incomplete retention must remain explicit.')
    require(records['extraction-retry-01']['command'] == ['tar', '--no-same-owner', '-xzf',
            '.tnp-local/' + JULIA_ARCHIVE, '-C', '.tnp-local'],
            'RETRY', 'Only diagnosed extraction retry is authorized.')
    failure = records['julia-resolve-01']
    require(failure['command'] == ['timeout', '600', '.tnp-local/venv/bin/python',
            '.tnp-local/resolve_stack.py'] and failure['returncode'] == 1,
            'FAILURE_ROUTE', 'Expected failed resolver process is absent.')
    trace = raw['julia-resolve-01.stderr'].decode()
    require('subprocess.CalledProcessError:' in trace and 'Signals.SIGBUS: 7' in trace
            and 'using Libdl' in trace and 'libjulia' in trace,
            'FAILURE_ROUTE', 'Reported SIGBUS prerequisite failure lacks its diagnostic.')
    require('Using Julia 1.10.10' in raw['julia-resolve-01.stdout'].decode(),
            'IDENTITY', 'Resolver did not identify the pinned Julia runtime.')
    for a, b in [('attempt-01', 'julia-download-01'), ('julia-download-01', 'julia-verify-01'),
                 ('julia-verify-01', 'extraction-retry-01'),
                 ('extraction-retry-01', 'julia-resolve-01'),
                 ('python-install-01', 'julia-resolve-01')]:
        require(stamp(records[a]['finished_at']) <= stamp(records[b]['started_at']),
                'CHRONOLOGY', 'Prerequisite order violated.')
    stop = cx.loads(raw['stop.json'])
    require(stop['schema'] == NS + '/setup-stop' and stop['failed_step'] == 'julia-resolve-01'
            and stop['failure_class'] == 'JULIA_LIBJULIA_PROBE_SIGBUS'
            and stop['underlying_signal'] == 7 and stop['wrapper_returncode'] == 1,
            'FAILURE_ROUTE', 'Stop record disagrees with actual failed step.')
    require(stop['retry_budget'] == stop['retry_used'] == 1
            and stop['retry_evidence'] == 'extraction-failure.json', 'RETRY', 'Retry limit changed.')
    require(stamp(stop['observed_at']) >= stamp(failure['finished_at']), 'CHRONOLOGY', 'Stop predates failure.')
    for key in ('qualified_environment', 'master_seed_created', 'julia_project_exists',
                'julia_manifest_exists', 'full_native_stack_imported'):
        require(stop[key] is False, 'UNPERFORMED', 'Unperformed prerequisite falsely promoted.')
    for key in ('smoke_fits_executed', 'target_fits_executed', 'target_rows_created',
                'cards_issued', 'selections_sealed', 'heldout_evaluations'):
        require(type(stop[key]) is int and stop[key] == 0, 'UNPERFORMED', 'Setup NO_GO cannot contain live results.')
    require(all(stop[k] == 'NOT_EXECUTED' for k in UNPERFORMED), 'UNPERFORMED', 'Unreached checks claimed.')
    require(set(stop['script_sha256']) == {'setup_step.py', 'resolve_stack.py', 'engine-env.json'},
            'SOURCE_PIN', 'Incomplete setup-source binding.')
    for path, digest in stop['script_sha256'].items():
        require(cx.sha(raw[path]) == digest, 'SOURCE_PIN', 'Setup script bytes changed.')
    # Derived only after actual failure, stage/identity/chronology and zero-output checks.
    return {'disposition': 'PYSR_ADAPTER_1_NO_GO', 'adapter_conformance': 'NO_GO',
            'evidence_integrity': 'PASS', 'operational_acceptance': False,
            'failure_class': stop['failure_class'], 'unperformed': {k: stop[k] for k in UNPERFORMED}}


def expected_report(raw, anchor, binding):
    outcome = validate_setup(raw, anchor['created_at'])
    return {'schema': NS + '/result', 'task': TASK,
        **{k: outcome[k] for k in ('disposition', 'adapter_conformance', 'evidence_integrity', 'operational_acceptance')},
        'stage': 'setup', 'review_status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING',
        'outcome_blind': False, 'search_coverage': 'NOT_ESTABLISHED',
        'scientific_evidence': dict(cx.PROMOTION), 'source_binding': cx.digest(binding),
        'evidence': {'failure_class': outcome['failure_class'], 'unperformed': outcome['unperformed'],
            'setup_file_sha256': {n: cx.sha(raw[n]) for n in SETUP_NAMES},
            'native_output_inventory': [], 'adapter_parity': 'NOT_EXECUTED',
            'dimensional_domain_provenance_checks': 'NOT_EXECUTED',
            'validation_diagnostics': [], 'heldout_diagnostics': []},
        'planned_runs': [{'run_id': f'r{i:02d}', 'state': 'NOT_EXECUTED',
                          'reason': 'prerequisite_failed_before_seed_generation'} for i in range(1, 5)],
        'limitations': LIMITATIONS}


def validate_report(report, raw, anchor, binding):
    cx.bounded(report)
    cx.fields(report, RESULT_FIELDS)
    require(report == expected_report(raw, anchor, binding), 'DISPOSITION',
            'Report must be derived from retained stage-specific evidence, not a chosen label.')
    return report['disposition']


def ancestor(a, b):
    require(subprocess.run(['git', 'merge-base', '--is-ancestor', a, b], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            'CHRONOLOGY', 'Required true-merge ancestry lost.')


def read(name):
    return cx.loads((PKG / name).read_bytes())


def source_check():
    require(sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 12),
            'ENVIRONMENT', 'Offline epoch keeps the CPython 3.12 boundary.')
    anchor, binding = read('anchor.json'), read('source_binding.json')
    cx.fields(binding, {'schema', 'source_sha', 'files'})
    require(binding['schema'] == NS + '/source-binding' and set(binding['files']) == set(SOURCE_PATHS),
            'SOURCE_PIN', 'Exact result-driving source inventory required.')
    for path, digest in binding['files'].items():
        raw = (ROOT / path).read_bytes()
        committed = subprocess.check_output(['git', 'show', binding['source_sha'] + ':' + path], cwd=ROOT)
        require(cx.sha(raw) == digest and raw == committed, 'SOURCE_PIN', 'Source/evidence bytes changed: ' + path)
    require(cx.sha((PKG / 'work_order.r1.md').read_bytes()) == WORK_SHA == read('work_order_receipt.json')['sha256'],
            'SOURCE_PIN', 'Consumed instructions changed.')
    require(git('show', '--pretty=', '--name-only', anchor['freeze_sha']) == REL + '/contract.v1.md',
            'CHRONOLOGY', 'Freeze must be a sole-file commit.')
    require(subprocess.check_output(['git', 'show', anchor['freeze_sha'] + ':' + REL + '/contract.v1.md'],
            cwd=ROOT) == (PKG / 'contract.v1.md').read_bytes(), 'SOURCE_PIN', 'Frozen contract changed.')
    for a, b in zip([anchor['base_sha'], anchor['snapshot_sha'], anchor['freeze_sha'], binding['source_sha']],
                    [anchor['snapshot_sha'], anchor['freeze_sha'], binding['source_sha'], git('rev-parse', 'HEAD')]):
        ancestor(a, b)
    require(stamp(git('show', '-s', '--format=%cI', anchor['freeze_sha'])) <= stamp(anchor['created_at'])
            < stamp(git('show', '-s', '--format=%cI', binding['source_sha'])),
            'CHRONOLOGY', 'Draft anchor must precede implementation source.')
    # Inspect this epoch, not future living repository configuration.
    changed = git('diff', '--name-status', anchor['base_sha'], binding['source_sha']).splitlines()
    for line in changed:
        status, path = line.split('\t')
        require(status == 'A' and (path.startswith(REL + '/') or
                path.startswith('Discovery/pysr_adapter') or path.startswith('tests/test_pysr_adapter')
                or path == 'Notes/PySRAdapter1.md'), 'IMMUTABILITY', 'Epoch modified an accepted surface.')
    raw = setup_bytes()
    validate_setup(raw, anchor['created_at'])
    return anchor, binding, raw


def check():
    anchor, binding, raw = source_check()
    report, seal = read('result.json'), read('evidence_seal.json')
    cx.fields(seal, {'schema', 'evidence_sha', 'files'})
    require(seal['schema'] == NS + '/evidence-seal'
            and set(seal['files']) == {'result.json', 'source_binding.json'},
            'EVIDENCE_BINDING', 'Missing mandatory result seal.')
    for name, digest in seal['files'].items():
        data = (PKG / name).read_bytes()
        require(cx.sha(data) == digest and data == subprocess.check_output(
            ['git', 'show', seal['evidence_sha'] + ':' + REL + '/' + name], cwd=ROOT),
            'EVIDENCE_BINDING', 'Sealed evidence bytes changed.')
        require(git('log', '--diff-filter=A', '--format=%H', '--', REL + '/' + name).splitlines()
                == [seal['evidence_sha']], 'EVIDENCE_BINDING', 'Unique evidence introduction lost.')
    ancestor(binding['source_sha'], seal['evidence_sha'])
    ancestor(seal['evidence_sha'], git('rev-parse', 'HEAD'))
    # Setup receipt inventory is exact. No target assets are permitted in this terminal package.
    allowed = {'work_order.r1.md', 'work_order_receipt.json', 'contract.v1.md', 'anchor.json',
               'source_binding.json', 'result.json', 'evidence_seal.json'} | {'setup/' + n for n in SETUP_NAMES}
    actual = {str(p.relative_to(PKG)) for p in PKG.rglob('*') if p.is_file()}
    require(actual == allowed, 'INVENTORY', 'Unexpected/missing package evidence; no target artifacts authorized.')
    return validate_report(report, raw, anchor, binding)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check'])
    parser.parse_args()
    print(check())
