"""Frozen adverse-result route. No continued generation/discovery/evaluation."""
from pathlib import Path

from Discovery.estimated_noise1_calibration import digest
from Discovery import estimated_noise1_science as science
from Discovery import estimated_noise1_schema as schema
from Discovery.estimated_noise1 import PKG, REL, artifact, read, sha, emit, git, raw_result, committed


def classification(error_type):
    if error_type in ('ValueError', 'RunnerFailure', 'CalibrationFailure', 'AssertionError'):
        return 'ESTABLISHED_CONTRACT_VIOLATION'
    if error_type in ('TimeoutExpired', 'CalledProcessError', 'PermissionError', 'OSError'):
        return 'ACCOUNTED_CAPABILITY_FAILURE'
    return 'MISSING_OR_UNRESOLVED_EVIDENCE'


def derive(p, failures, rows, completed_numeric_ids):
    """Only a complete per-dataset evaluation plus numeric record is interpretable."""
    if not failures: raise ValueError('adverse route requires retained failure')
    for f in failures:
        if f['classification'] != classification(f['error_type']):
            raise ValueError('failure classification must derive from retained error type')
        if f['scientific_pipeline_stopped'] is not True or f['scientific_retry_authorized'] is not False:
            raise ValueError('failure budget violated')
    good = {rid: row for rid, row in rows.items() if rid in completed_numeric_ids and row['interpretable']}
    stage = failures[0]['stage']
    statuses = {rid: {'state': 'INTERPRETABLE' if rid in good else 'FAILED' if rid in rows else 'NOT_EXECUTED',
        'stage': 'evaluation' if rid in good else stage,
        'reason': None if rid in good else 'Pipeline stopped at first retained '+stage+' failure; no retry.'}
        for rid in science.identities()}
    violations = [f['error_type']+': '+f['error'] for f in failures if f['classification'] == 'ESTABLISHED_CONTRACT_VIOLATION']
    missing = [f['error_type']+': '+f['error'] for f in failures if f['classification'] == 'MISSING_OR_UNRESOLVED_EVIDENCE']
    return science.aggregate(p, good, statuses, violations, missing)


def inputs():
    paths = sorted((PKG/'operational_failures').glob('*.json'))
    failures = [artifact(p.relative_to(PKG).as_posix(), 'operational-failure') for p in paths]
    rows = {p.stem: artifact(p.relative_to(PKG).as_posix(), 'dataset-evaluation')
            for p in (PKG/'evaluation_partial').glob('*.json')}
    numeric = {p.stem for p in (PKG/'numeric_partial').glob('*.json')}
    return failures, rows, numeric


def finalize():
    """Explicit archive-only command after committing a stopped attempt."""
    if (PKG/'result.json').exists(): raise ValueError('immutable raw result already exists')
    failures, rows, numeric = inputs()
    if not failures: raise ValueError('no stopped attempt')
    if git('status', '--porcelain', '--untracked-files=normal'): raise ValueError('commit stopped evidence first')
    retained = {p.relative_to(PKG).as_posix(): sha(p.read_bytes()) for p in PKG.rglob('*') if p.is_file()}
    summary = derive(read('preregistration.v1.json')['science'], failures, rows, numeric)
    source = failures[0]['source_sha']
    selection_commit = committed('selection_seal.json') if (PKG/'selection_seal.json').exists() else None
    emit('failure_archive.json', 'failure-archive', {'source_sha': source,
        'stopped_commit_sha': git('rev-parse', 'HEAD'), 'retained_files': retained,
        'completed_numeric_ids': sorted(numeric), 'failure_count': len(failures)})
    emit('summary.json', 'summary', summary)
    raw_result(source, selection_commit, summary, 'STOPPED_AT_FIRST_SCIENTIFIC_FAILURE')


if __name__ == '__main__': finalize()
