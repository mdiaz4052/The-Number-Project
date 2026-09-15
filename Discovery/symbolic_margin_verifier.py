"""Narrow forward verifier for distinct raw-result and summary schema envelopes.

Frozen raw source, scientific criteria, records and failed-check evidence remain
unchanged. No generator/discovery/fit is called while producing reconciliation.
Explicit optional replay is reproduction of the same already revealed epoch.
"""
import argparse
from Discovery import symbolic_margin as raw
from Discovery.symbolic_benchmark_engine import digest
from Discovery.source_history import verify_committed_source_state

CORRECTION_SOURCES = ('Discovery/symbolic_margin_verifier.py', 'tests/test_symbolic_margin_verifier.py')
FAILURE = raw.ART / 'verification_failure.json'
RECONCILIATION = raw.ART / 'verification_reconciliation.json'
ROUTES = raw.ART / 'verification_routes.json'


def bind_result(summary, result, records, controls):
    """Compare full scientific payload, with explicit independent schema envelopes."""
    if summary.get('schema') != 'tnp-margin1/summary-v1' or result.get('schema') != 'tnp-margin1/raw-result-v1':
        raise ValueError('unexpected summary/raw schema')
    expected = {**summary, 'schema': 'tnp-margin1/raw-result-v1',
        'source_sha': result['source_sha'], 'selection_commit_sha': result['selection_commit_sha'],
        'evaluation_sha256': digest(records), 'controls_sha256': digest(controls),
        'summary_sha256': digest(summary), 'evaluated_at': result['evaluated_at']}
    if result != expected:
        raise ValueError('raw scientific payload or bindings differ')


def verify_science():
    raw.environment()
    stages = raw.chronology()
    p, c, sealed = [raw.read(raw.ART / n) for n in ('preregistration.v1.json', 'commitment.json', 'selection_seal.json')]
    public, inputs, eligibility, oracle, heldout = [raw.read(raw.ART / (n + '.json')) for n in ('public', 'inputs', 'eligibility', 'oracle_reveal', 'heldout')]
    outputs = raw.selections(c['dataset_ids'])
    raw.check_binding(c, sealed, outputs, oracle, heldout)
    if raw.seed_digest(oracle['seed']) != raw.read(raw.ART / 'seed_commitment.json')['seed_sha256'] or c['seed_commitment_sha256'] != raw.sha_file(raw.ART / 'seed_commitment.json'):
        raise ValueError('seed binding changed')
    if c['dataset_ids'] != raw.dataset_ids(p):
        raise ValueError('dataset order changed')
    retro, pins = raw.derive_retrospective()
    if retro != raw.read(raw.ART / 'retrospective.json') or pins != raw.read(raw.ART / 'retrospective_sources.json'):
        raise ValueError('retrospective changed')
    controls = raw.controls(p, c, public, inputs, eligibility, outputs, oracle, heldout)
    records = {rid: raw.evaluate(p, public[rid], outputs[rid], oracle['realizations'][rid], heldout[rid]) for rid in c['dataset_ids']}
    summary = raw.aggregate(p, records, all(controls.values()))
    if controls != raw.read(raw.ART / 'controls.json') or records != raw.read(raw.ART / 'evaluation.json') or summary != raw.read(raw.ART / 'summary.json'):
        raise ValueError('frozen evaluation differs')
    result = raw.read(raw.ART / 'result.json')
    bind_result(summary, result, records, controls)
    if not all(controls.values()) or not summary['integrity_pass']:
        raise ValueError('scientific integrity failure')
    preflight = raw.read(raw.ART / 'preflight.json')
    if preflight['source_manifest'] != raw.source_manifest() or not preflight['passed'] or preflight['environment'] != raw.environment():
        raise ValueError('source preflight changed')
    if preflight['mutation_record_sha256'] != raw.sha_file(raw.ART / 'mutation_preflight.json'):
        raise ValueError('mutation preflight changed')
    return stages, result


def assess():
    stages, result = verify_science()
    failure = raw.read(FAILURE)
    if failure['stage'] != 'post-result-read-only-verification' or failure['raw_epoch_sha'] != stages[-1] or failure['frozen_source_sha'] != result['source_sha']:
        raise ValueError('failure outside repair scope')
    if failure['same_epoch_generation_replay_reached'] or 'raw result binding mismatch' not in failure['output']:
        raise ValueError('failure record mismatch')
    paths = raw.git('ls-tree', '-r', '--name-only', stages[-1], raw.REL).splitlines()
    raw.immutable(stages[-1], paths)
    return {'schema': 'tnp-margin1/verification-reconciliation-v1', 'disposition': result['disposition'],
        'raw_epoch_sha': stages[-1], 'raw_artifact_sha256': {p: raw.sha_file(raw.ROOT / p) for p in paths},
        'preserved_verifier_failure_sha256': raw.sha_file(FAILURE),
        'correction_scope': 'Explicit raw/summary schema envelopes; exact equality of every scientific field and all digest bindings.',
        'scientific_results_changed': False, 'criteria_changed': False, 'new_seed_or_selection': False,
        'review_status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING'}


def routes(reconciliation, source):
    value = raw.make_routes(reconciliation['raw_epoch_sha'])
    item = value['MisspecificationMargin1']
    item['reconciliation'] = raw.route(RECONCILIATION, 'disposition', source, 'record_producer_source')
    item['operational_failures'].append(raw.route(FAILURE, 'disposition', source))
    item['authoritative'] = 'reconciliation'
    value['schema'] = 'tnp-margin1/disposition-routing-v2'
    return value


def reconcile():
    raw.clean()
    source = raw.git('rev-parse', 'HEAD')
    for path in (*CORRECTION_SOURCES, FAILURE.relative_to(raw.ROOT).as_posix()):
        raw.committed(raw.ROOT / path)
    result = assess()
    result['correction_source_sha'] = source
    raw.write_new(RECONCILIATION, result)
    raw.write_new(ROUTES, routes(result, source))
    print(result['disposition'] + '; schema-only verification reconciliation written')


def check(replay=False):
    saved = raw.read(RECONCILIATION)
    source = saved['correction_source_sha']
    verify_committed_source_state(raw.ROOT, source, source_paths=CORRECTION_SOURCES, artifact_label='Margin1 forward verifier')
    raw.immutable(source, CORRECTION_SOURCES)
    raw.committed(FAILURE, source)
    expected = assess(); expected['correction_source_sha'] = source
    if expected != saved:
        raise ValueError('verification reconciliation changed')
    raw.ancestor(saved['raw_epoch_sha'], source)
    h = raw.history()
    for path in (RECONCILIATION, ROUTES):
        relative = path.relative_to(raw.ROOT).as_posix()
        intro = raw.introduction(h, relative)
        raw.ancestor(source, intro)
        raw.immutable(intro, [relative])
    for path in (FAILURE, raw.ART / 'disposition_routes.json'):
        relative = path.relative_to(raw.ROOT).as_posix()
        if raw.introduction(h, relative) != source:
            raise ValueError('verification-stage evidence introduction differs')
        raw.immutable(source, [relative])
    if raw.read(raw.ART / 'disposition_routes.json') != raw.make_routes(saved['raw_epoch_sha']):
        raise ValueError('original explicit-key routing changed')
    if raw.read(ROUTES) != routes(saved, source):
        raise ValueError('forward authoritative route changed')
    if replay:
        p = raw.read(raw.ART / 'preregistration.v1.json')
        oracle = raw.read(raw.ART / 'oracle_reveal.json')
        regenerated = raw.generate(p, oracle['seed'])
        if tuple(map(digest, regenerated)) != tuple(map(digest, (raw.read(raw.ART / 'public.json'), raw.read(raw.ART / 'heldout.json'), oracle))):
            raise ValueError('same-epoch generation mismatch')
    from tests.test_symbolic_suite import fixture
    live = raw.staged_discovery(fixture())
    stale = raw.staged_discovery(fixture(), stale_cache=True, enforce=False)
    cache = '<stage>/Discovery/__pycache__/symbolic_suite_engine.cpython-312.pyc'
    if not raw.valid_receipt(live) or raw.valid_receipt(stale) or cache not in stale['receipt']['successful_reads'] or cache in stale['receipt']['expected_missing_cache_attempts']:
        raise ValueError('live cache semantic failure')
    print(saved['disposition'] + '; immutable frozen science and explicit schema correction verified' + ('; same-epoch generation matched' if replay else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['reconcile', 'check'])
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    if args.stage == 'reconcile': reconcile()
    else: check(args.replay)
