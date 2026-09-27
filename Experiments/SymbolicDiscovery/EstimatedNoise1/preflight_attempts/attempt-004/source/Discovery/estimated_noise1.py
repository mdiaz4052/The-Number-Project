"""One-epoch estimated-noise custody stages. Each scientific stage is exclusive.

The operator commits each stage before invoking the next. Workers receive only
the documented anonymous inputs. Private seed/oracle files stay outside Git
until the complete selection seal is committed. No automatic scientific retry.
"""
import argparse
import datetime
import hashlib
import os
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import traceback

from Discovery.estimated_noise1_calibration import encoded, digest, loads
from Discovery import estimated_noise1_schema as schema

ROOT = Path(__file__).resolve().parents[1]
REL = 'Experiments/SymbolicDiscovery/EstimatedNoise1'
PKG = ROOT / REL
SOURCE_PATHS = tuple('Discovery/'+n+'.py' for n in (
    '__init__', 'estimated_noise1', 'estimated_noise1_calibration', 'estimated_noise1_workers',
    'estimated_noise1_science', 'estimated_noise1_reference', 'estimated_noise1_schema',
    'estimated_noise1_selection', 'estimated_noise1_fixtures', 'estimated_noise1_mutations',
    'estimated_noise1_verifier', 'estimated_noise1_preflight', 'estimated_noise1_failure',
    'estimated_noise1_launch', 'symbolic_suite_runner', 'symbolic_suite_engine',
    'symbolic_suite_worlds', 'symbolic_benchmark_engine', 'constants', 'dimensions',
    'dimensional_search', 'planck_identities', 'dependency_definitions', 'monomial_constraints')) + (
    'tests/test_estimated_noise1.py', REL+'/preregistration.v1.json', REL+'/anchor.json')


def sha(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.datetime.now(datetime.UTC).isoformat()
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
def blob(commit, path): return subprocess.check_output(['git', 'show', commit+':'+path], cwd=ROOT)
def read(name): return loads((PKG/name).read_bytes())


def new_bytes(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def new_json(path, value): new_bytes(path, encoded(value))


def environment():
    if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('CPython 3.12 required')
    return {'implementation': sys.implementation.name, 'version': sys.version,
        'version_info': list(sys.version_info[:3]), 'executable': str(Path(sys.executable).resolve()),
        'executable_sha256': sha(Path(sys.executable).resolve().read_bytes()),
        'platform': platform.platform(), 'machine': platform.machine(), 'cache_tag': sys.implementation.cache_tag}


def bindings():
    p, a = read('preregistration.v1.json'), read('anchor.json')
    return {'actual_base_sha': p['launch_binding']['actual_base_sha'], 'freeze_sha': a['freeze_sha'],
            'preregistration_sha256': sha((PKG/'preregistration.v1.json').read_bytes()),
            'science_sha256': p['science_sha256']}


def emit(name, kind, data):
    record = schema.envelope(kind, data, bindings())
    new_json(PKG/name, record)
    return record


def artifact(name, kind):
    return schema.unwrap((PKG/name).read_bytes(), kind, bindings())


def committed(name):
    path = REL+'/'+name
    head = git('rev-parse', 'HEAD')
    if blob(head, path) != (PKG/name).read_bytes(): raise ValueError('uncommitted input '+name)
    commits = git('log', '--format=%H', '--', path).splitlines()
    if len(commits) != 1: raise ValueError('immutable artifact edited '+name)
    return commits[0]


def before(stage, private):
    if list((PKG/'operational_failures').glob('*.json')):
        raise RuntimeError('scientific pipeline stopped; no retries')
    if git('status', '--porcelain', '--untracked-files=normal'):
        raise RuntimeError('commit all preceding evidence before next stage')
    seed = artifact('seed_commitment.json', 'seed-commitment') if stage != 'seed' else None
    source = seed['source_sha'] if seed else git('rev-parse', 'HEAD')
    pf = artifact('preflight.json', 'preflight')
    schema.same(environment(), pf['environment'], 'execution environment differs from qualified environment')
    for path, h in pf['source_manifest'].items():
        if sha(blob(source, path)) != h or sha((ROOT/path).read_bytes()) != h:
            raise ValueError('source-before-use pin mismatch '+path)
    if not pf['qualified']: raise ValueError('unqualified source')
    if seed and seed['source_manifest_sha256'] != digest(pf['source_manifest']):
        raise ValueError('seed/source binding')
    # These exclusive markers persist even when the scientific child fails.
    private.mkdir(parents=True, exist_ok=True)
    new_json(private/(stage+'.attempt.json'), {'stage': stage, 'started_utc': now(), 'source_sha': source})
    return source, pf


def seed_stage(private):
    source, pf = before('seed', private)
    value = secrets.token_hex(32)
    new_bytes(private/'seed.txt', value.encode())
    data = {'source_sha': source, 'source_manifest_sha256': digest(pf['source_manifest']),
            'seed_sha256': sha(('estimated-noise1:'+value).encode()), 'environment': environment(), 'created_utc': now()}
    schema.validate(data, schema.SEED)
    emit('seed_commitment.json', 'seed-commitment', data)


def data_stage(private):
    from Discovery.estimated_noise1_science import generate, identities
    source, _ = before('data', private)
    seed_commit = committed('seed_commitment.json')
    if git('rev-parse', 'HEAD') != seed_commit: raise ValueError('seed must be the current sole-file epoch')
    changed = git('diff-tree', '--no-commit-id', '--name-only', '-r', seed_commit).splitlines()
    if changed != [REL+'/seed_commitment.json']: raise ValueError('seed epoch not sole-file')
    remote = git('ls-remote', 'origin', 'refs/heads/experiment/np-estimated-noise-01').split()
    if remote != [seed_commit, 'refs/heads/experiment/np-estimated-noise-01']:
        raise ValueError('seed commitment not published at actual remote head')
    observed = {'head': remote[0], 'ref': remote[1], 'url': 'https://github.com/mdiaz4052/The-Number-Project',
                'observed_utc': now()}
    new_json(private/'remote_seed_readback.json', observed)
    seed = (private/'seed.txt').read_text()
    if sha(('estimated-noise1:'+seed).encode()) != artifact('seed_commitment.json', 'seed-commitment')['seed_sha256']:
        raise ValueError('private seed does not open commitment')
    p = read('preregistration.v1.json')['science']
    public, calibration, heldout, oracle = generate(p, seed)
    schema.scientific_inputs(public, calibration, heldout, oracle)
    new_json(private/'heldout.json', schema.envelope('heldout', {'datasets': heldout}, bindings()))
    new_json(private/'oracle_reveal.json', schema.envelope('oracle-reveal', oracle, bindings()))
    emit('public.json', 'public', {'datasets': public})
    emit('calibration.json', 'calibration', {'datasets': calibration})
    commitment = {'source_sha': source, 'seed_commit_sha': seed_commit, 'remote_readback': observed,
        'generated_utc': now(), 'public_sha256': sha((PKG/'public.json').read_bytes()),
        'calibration_sha256': sha((PKG/'calibration.json').read_bytes()),
        'private_hashes': {name: sha((private/name).read_bytes()) for name in ('oracle_reveal.json', 'heldout.json', 'seed.txt')},
        'dataset_ids': identities()}
    schema.validate(commitment, schema.COMMITMENT)
    emit('commitment.json', 'commitment', commitment)


def calibration_stage(private):
    from Discovery.estimated_noise1_workers import staged_calibration
    from Discovery.estimated_noise1_science import settings, identities
    source, _ = before('calibration', private)
    data_commit = committed('commitment.json')
    for name in ('public.json', 'calibration.json'):
        if committed(name) != data_commit: raise ValueError('data epoch mismatch')
    records = artifact('calibration.json', 'calibration')['datasets']
    p = read('preregistration.v1.json')['science']
    result = {}
    for rid in identities():
        payload = {'dataset_id': rid, 'pairs': records[rid], 'settings': settings(p)}
        output = staged_calibration(payload)
        schema.worker(output, schema.CAL_RESULT)
        result[rid] = output
        emit(f'calibration_workers/{rid}.json', 'calibration-worker',
             {'source_sha': source, 'data_commit_sha': data_commit, 'worker': output})
    emit('calibration_estimates.json', 'calibration-estimates',
         {'source_sha': source, 'data_commit_sha': data_commit, 'records': result})
    seal = {'source_sha': source, 'data_commit_sha': data_commit,
        'estimates_sha256': sha((PKG/'calibration_estimates.json').read_bytes()),
        'calibration_sha256': sha((PKG/'calibration.json').read_bytes()),
        'record_count': len(result), 'settings': settings(p),
        'output_hashes': {rid: sha((PKG/f'calibration_workers/{rid}.json').read_bytes()) for rid in result},
        'created_utc': now()}
    schema.validate(seal, schema.CAL_SEAL)
    emit('calibration_seal.json', 'calibration-seal', seal)


def discovery_stage(private):
    from Discovery.symbolic_suite_runner import staged_discovery
    from Discovery.estimated_noise1_selection import discovery_payload
    from Discovery.estimated_noise1_science import policy, operational, identities
    source, _ = before('discovery', private)
    cal_commit = committed('calibration_seal.json')
    if committed('calibration_estimates.json') != cal_commit: raise ValueError('calibration seal linkage')
    cal_seal = artifact('calibration_seal.json', 'calibration-seal')
    if cal_seal['record_count'] != 96: raise ValueError('all calibrations must precede discovery')
    public = artifact('public.json', 'public')['datasets']
    estimates = artifact('calibration_estimates.json', 'calibration-estimates')['records']
    p = read('preregistration.v1.json')['science']
    files, diagnostic_count = {}, 0
    for rid in identities():
        e = estimates[rid]['discovery']['estimates']
        payload = discovery_payload(public[rid], policy(p, e['64']['upper95_threshold']))
        output = staged_discovery(payload)
        schema.worker(output, schema.DISCOVERY)
        result = {'dataset_id': rid, 'source_sha': source, 'data_commit_sha': cal_seal['data_commit_sha'],
            'calibration_seal_sha256': sha((PKG/'calibration_seal.json').read_bytes()),
            'calibration_seal_commit_sha': cal_commit, 'payload_sha256': digest(payload),
            'worker': output, 'operational': operational(p, output['discovery'], e)}
        schema.validate_selection(result)
        emit(f'selection/{rid}.json', 'selection', result)
        files[rid] = sha((PKG/f'selection/{rid}.json').read_bytes())
        diagnostic_count += len(output['discovery']['group_diagnostics'])
    seal = {'source_sha': source, 'calibration_seal_commit_sha': cal_commit, 'files': files,
            'created_utc': now(), 'record_count': len(files), 'principal_fits': 5*len(files),
            'diagnostic_refits': diagnostic_count}
    schema.validate(seal, schema.SELECTION_SEAL)
    emit('selection_seal.json', 'selection-seal', seal)


def evaluation_stage(private):
    from Discovery import estimated_noise1_science as science
    from Discovery import estimated_noise1_reference as reference
    source, _ = before('evaluation', private)
    selection_commit = committed('selection_seal.json')
    seal = artifact('selection_seal.json', 'selection-seal')
    if seal['record_count'] != 96 or set(seal['files']) != set(science.identities()):
        raise ValueError('no evaluator access before complete committed selection seal')
    for rid, h in seal['files'].items():
        if committed(f'selection/{rid}.json') != selection_commit or sha((PKG/f'selection/{rid}.json').read_bytes()) != h:
            raise ValueError('selection seal linkage')
    # First evaluator read of the committed private data. Copy the original bytes.
    com = artifact('commitment.json', 'commitment')
    for name in ('oracle_reveal.json', 'heldout.json'):
        raw = (private/name).read_bytes()
        if sha(raw) != com['private_hashes'][name]: raise ValueError('private commitment mismatch')
        new_bytes(PKG/name, raw)
    public = artifact('public.json', 'public')['datasets']
    calibration = artifact('calibration.json', 'calibration')['datasets']
    oracle = artifact('oracle_reveal.json', 'oracle-reveal')
    heldout = artifact('heldout.json', 'heldout')['datasets']
    schema.scientific_inputs(public, calibration, heldout, oracle)
    p = read('preregistration.v1.json')['science']
    generation = reference.generation(p, public, calibration, heldout, oracle)
    estimates = artifact('calibration_estimates.json', 'calibration-estimates')['records']
    records, cal_checks, numeric_checks = {}, {}, {}
    for rid in science.identities():
        e = estimates[rid]['discovery']['estimates']
        truth = oracle['datasets'][rid]
        selection = artifact(f'selection/{rid}.json', 'selection')
        result = science.evaluate(p, selection, truth, heldout[rid], e)
        emit(f'evaluation_partial/{rid}.json', 'dataset-evaluation', result)
        records[rid] = result
        bank = oracle['blocks'][str(truth['block'])]['calibration']
        intended = [truth['epsilon']*(r['u1']-r['u2']) for r in bank]
        cal_checks[rid] = reference.calibration(calibration[rid], science.settings(p), e, intended)
        numeric_checks[rid] = reference.candidate_arithmetic(public[rid], selection['worker']['discovery']['ranking'],
            heldout=heldout[rid], truth=truth, metrics={c['class_id']: c for c in result['candidates']})
        emit(f'numeric_partial/{rid}.json', 'dataset-numerics',
             {'calibration': cal_checks[rid], 'candidates': numeric_checks[rid]})
    emit('evaluation.json', 'evaluation', {'source_sha': source,
        'selection_seal_commit_sha': selection_commit, 'datasets': records})
    emit('controls.json', 'controls', {'source_sha': source, 'selection_seal_commit_sha': selection_commit,
        'generation': generation, 'calibration': cal_checks, 'candidates': numeric_checks,
        'custody_verified': True, 'inventory_verified': True, 'environment_matches': True})
    statuses = {rid: {'state': 'INTERPRETABLE', 'stage': 'evaluation', 'reason': None} for rid in science.identities()}
    summary = science.aggregate(p, records, statuses, [], [])
    emit('summary.json', 'summary', summary)
    raw_result(source, selection_commit, summary, 'COMPLETED')


def raw_result(source, selection_commit, summary, operational_status):
    data = {'source_sha': source, 'selection_seal_commit_sha': selection_commit,
        'summary_sha256': sha((PKG/'summary.json').read_bytes()),
        **{name+'_sha256': sha((PKG/(name+'.json')).read_bytes()) if (PKG/(name+'.json')).exists() else None
           for name in ('evaluation', 'controls')},
        **{k: summary[k] for k in ('disposition', 'evidence_integrity', 'interpretable_datasets',
                                   'expected_datasets', 'review_status')},
        'operational_status': operational_status, 'outcome_blind': False, 'scientific_law_claim': False}
    schema.validate(data, schema.RESULT)
    emit('result.json', 'raw-result', data)


def failure(stage, exc):
    from Discovery.estimated_noise1_failure import classification
    index = len(list((PKG/'operational_failures').glob('*.json')))+1
    record = {'stage': stage, 'parent_sha': git('rev-parse', 'HEAD'),
        'source_sha': artifact('seed_commitment.json', 'seed-commitment')['source_sha'] if (PKG/'seed_commitment.json').exists() else git('rev-parse', 'HEAD'),
        'observed_utc': now(), 'classification': classification(type(exc).__name__),
        'error_type': type(exc).__name__, 'error': str(exc), 'traceback': traceback.format_exc(),
        'worker_output': getattr(exc, 'output', None),
        'retention': 'Full Python traceback and any structured worker output retained. Parent stdout/stderr captured by launcher. No unavailable child raw stream is claimed.',
        'scientific_pipeline_stopped': True, 'scientific_retry_authorized': False}
    emit(f'operational_failures/{index:03d}-{stage}.json', 'operational-failure', record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('seed', 'data', 'calibration', 'discovery', 'evaluation'))
    parser.add_argument('--private-dir', required=True)
    args = parser.parse_args()
    private = Path(args.private_dir).resolve()
    if private == ROOT or ROOT in private.parents:
        raise ValueError('private custody must be outside repository')
    try:
        {'seed': seed_stage, 'data': data_stage, 'calibration': calibration_stage,
         'discovery': discovery_stage, 'evaluation': evaluation_stage}[args.stage](private)
    except Exception as exc:
        failure(args.stage, exc)
        raise
    print(args.stage+' complete; commit this stage before proceeding')


if __name__ == '__main__': main()
