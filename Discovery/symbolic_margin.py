"""One prospective margin epoch, immutable custody and read-only verification."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import secrets
import subprocess
import sys
import traceback

from Discovery.symbolic_benchmark_engine import encoded, digest
from Discovery.symbolic_suite_engine import prepare
from Discovery.symbolic_suite_runner import ENGINE_FILES, WORKER, staged_discovery, valid_receipt
from Discovery.symbolic_suite_routing import route, validate_index
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import verify_committed_source_state
from Discovery.symbolic_margin_science import generate, evaluate, aggregate, retrospective, dataset_ids

ROOT = Path(__file__).resolve().parents[1]
REL = 'Experiments/SymbolicDiscovery/MisspecificationMargin1'
ART = ROOT / REL
OLD = ROOT / 'Experiments/SymbolicDiscovery/BenchmarkSuite1'
PRIVATE = ROOT / '.tnp-local/margin1-private'
BRANCH = 'experiment/np-misspec-margin-01'
SOURCE_FILES = (*ENGINE_FILES, 'Discovery/symbolic_suite_runner.py', 'Discovery/symbolic_suite_worlds.py',
    'Discovery/symbolic_suite_evaluation.py', 'Discovery/symbolic_suite.py', 'Discovery/symbolic_suite_routing.py',
    'Discovery/preregistration_history.py', 'Discovery/source_history.py', 'Discovery/symbolic_margin_science.py',
    'Discovery/symbolic_margin.py', 'tests/test_symbolic_margin.py', 'tests/test_symbolic_suite.py', 'tests/margin_mutation_preflight.py')


def read(path):
    return json.loads(Path(path).read_text())


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(encoded(value))


def committed(path, sha='HEAD'):
    path = Path(path)
    data = subprocess.check_output(['git', '-C', str(ROOT), 'show', sha + ':' + path.relative_to(ROOT).as_posix()])
    if data != path.read_bytes():
        raise ValueError('committed bytes differ: ' + str(path))


def clean():
    if git('status', '--porcelain', '--untracked-files=no'):
        raise ValueError('commit tracked state before execution')


def ancestor(a, b):
    if a == b:
        raise ValueError('custody stages must be distinct')
    git('merge-base', '--is-ancestor', a, b)


def seed_digest(seed):
    return hashlib.sha256(('margin1:' + seed).encode()).hexdigest()


def source_manifest():
    return {p: sha_file(ROOT / p) for p in SOURCE_FILES}


def environment():
    if sys.version_info[:2] != (3, 12) or sys.implementation.cache_tag != 'cpython-312':
        raise ValueError('Margin1 requires frozen CPython 3.12 / cpython-312')
    return {'python_minor': '3.12', 'cache_tag': sys.implementation.cache_tag,
            'implementation': sys.implementation.name}


def verify_freeze():
    a, p = read(ART / 'anchor.json'), read(ART / 'preregistration.v1.json')
    verify_preregistration_freeze(ROOT, baseline=a['snapshot_sha'], commit=a['freeze_sha'],
        path=REL + '/preregistration.v1.json', sha256=sha_file(ART / 'preregistration.v1.json'))
    if p['instruction_snapshot_sha'] != a['snapshot_sha'] or p['scientific_base_sha'] != a['scientific_base_sha']:
        raise ValueError('base/snapshot mismatch')
    for name in ('work_order.r1.md', 'work_order_receipt.json'):
        committed(ART / name, a['snapshot_sha'])
    receipt = read(ART / 'work_order_receipt.json')
    if sha_file(ART / 'work_order.r1.md') != p['work_order_sha256'] or receipt['consumed_sha256'] != p['work_order_sha256']:
        raise ValueError('consumed instructions mismatch')
    if datetime.fromisoformat(a['created_at']) <= datetime.fromisoformat(git('show', '-s', '--format=%cI', a['freeze_sha'])):
        raise ValueError('draft anchor must follow design freeze')
    ancestor(a['scientific_base_sha'], a['snapshot_sha'])
    return a, p


def seed():
    a, p = verify_freeze()
    clean()
    environment()
    if PRIVATE.exists() or (ART / 'seed_commitment.json').exists():
        raise ValueError('seed epoch already exists; no replacement')
    source = git('rev-parse', 'HEAD')
    if datetime.fromisoformat(git('show', '-s', '--format=%cI', source)) <= datetime.fromisoformat(a['created_at']):
        raise ValueError('source precedes draft anchor')
    for path in SOURCE_FILES:
        committed(ROOT / path)
    for name in ('preflight.json', 'anchor.json', 'retrospective.json', 'retrospective_sources.json', 'mutation_preflight.json', 'mutation_preflight.attempt1.json'):
        committed(ART / name)
    preflight = read(ART / 'preflight.json')
    if not preflight['passed'] or preflight['source_manifest'] != source_manifest() or preflight['environment'] != environment():
        raise ValueError('preflight not current')
    secret = secrets.token_hex(32)
    write_new(PRIVATE / 'seed.json', {'seed': secret, 'source_sha': source})
    write_new(ART / 'seed_commitment.json', {'schema': 'tnp-margin1/seed-v1', 'source_sha': source,
        'seed_sha256': seed_digest(secret), 'preflight_sha256': sha_file(ART / 'preflight.json'),
        'preregistration_sha256': sha_file(ART / 'preregistration.v1.json'), 'environment': environment(), 'created_at': now()})
    print('Seed commitment written; publish sole-file commit before generation.')


def verify_seed(commit):
    s = read(ART / 'seed_commitment.json')
    verify_preregistration_freeze(ROOT, baseline=s['source_sha'], commit=commit,
        path=REL + '/seed_commitment.json', sha256=sha_file(ART / 'seed_commitment.json'))
    verify_committed_source_state(ROOT, s['source_sha'], source_paths=SOURCE_FILES, artifact_label='Margin1')
    if s['preflight_sha256'] != sha_file(ART / 'preflight.json') or s['preregistration_sha256'] != sha_file(ART / 'preregistration.v1.json'):
        raise ValueError('seed policy/preflight pin mismatch')
    if s['environment'] != environment():
        raise ValueError('environment mismatch')


def realize():
    _, p = verify_freeze()
    clean()
    seed_sha = git('rev-parse', 'HEAD')
    verify_seed(seed_sha)
    remote = git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()
    if not remote or remote[0] != seed_sha:
        raise ValueError('seed commitment not published at remote head')
    write_new(PRIVATE / 'generation_started.json', {'head': seed_sha, 'started_at': now()})
    s = read(ART / 'seed_commitment.json')
    secret = read(PRIVATE / 'seed.json')['seed']
    if seed_digest(secret) != s['seed_sha256']:
        raise ValueError('private seed mismatch')
    public, heldout, oracle = generate(p, secret)
    write_new(PRIVATE / 'heldout.json', heldout)
    write_new(PRIVATE / 'oracle.json', oracle)
    inputs, eligibility = {}, {}
    for rid, raw in public.items():
        inputs[rid], eligibility[rid] = prepare(raw)
    for name, value in [('public', public), ('inputs', inputs), ('eligibility', eligibility)]:
        write_new(ART / (name + '.json'), value)
    write_new(ART / 'commitment.json', {'schema': 'tnp-margin1/data-v1', 'source_sha': s['source_sha'],
        'seed_commit_sha': seed_sha, 'seed_commitment_sha256': sha_file(ART / 'seed_commitment.json'),
        'remote_publication': {'ref': 'refs/heads/' + BRANCH, 'observed_sha': remote[0], 'before_generation': True},
        **{name + '_sha256': digest(v) for name, v in [('public', public), ('inputs', inputs), ('eligibility', eligibility),
                                                      ('oracle', oracle), ('heldout', heldout)]},
        'dataset_ids': dataset_ids(p), 'created_at': now()})
    print('Generated one fixed epoch: 24 datasets, four independent matched blocks. Oracle/heldout private.')


def selections(ids):
    return {rid: read(ART / 'selection' / (rid + '.json')) for rid in ids}


def check_binding(commitment, seal, outputs, oracle, heldout):
    for actual, expected in [(digest(commitment), seal['commitment_sha256']), (digest(outputs), seal['selection_sha256']),
                             (digest(oracle), commitment['oracle_sha256']), (digest(heldout), commitment['heldout_sha256'])]:
        if actual != expected:
            raise ValueError('custody data binding mismatch')


def seal():
    clean()
    committed(ART / 'commitment.json')
    c = read(ART / 'commitment.json')
    verify_seed(c['seed_commit_sha'])
    inputs = read(ART / 'inputs.json')
    if digest(inputs) != c['inputs_sha256']:
        raise ValueError('input commitment changed')
    write_new(PRIVATE / 'selection_started.json', {'head': git('rev-parse', 'HEAD'), 'started_at': now()})
    outputs = {}
    for rid in c['dataset_ids']:
        # Individual exclusive files preserve completed cases if a later worker fails.
        outputs[rid] = staged_discovery(inputs[rid])
        write_new(ART / 'selection' / (rid + '.json'), outputs[rid])
    write_new(ART / 'selection_seal.json', {'schema': 'tnp-margin1/seal-v1', 'data_commit_sha': git('rev-parse', 'HEAD'),
        'commitment_sha256': digest(c), 'selection_sha256': digest(outputs), 'sealed_at': now(),
        'oracle_revealed': False, 'heldout_accessed': False, 'dataset_count': len(outputs)})
    print('All 24 rankings, adequacy and approximation decisions sealed; commit before evaluator reveal.')


def controls(p, c, public, inputs, eligibility, outputs, oracle, heldout):
    ids = set(dataset_ids(p))
    checks = {'complete_ids': all(set(v) == ids for v in (public, inputs, eligibility, outputs, oracle['realizations'], heldout)),
        'four_block_streams': len({t['child_seed'] for t in oracle['realizations'].values()}) == p['design']['independent_blocks'],
        'receipts': all(valid_receipt(v) for v in outputs.values()),
        'exhaustive_family': all({v['class_id'] for v in o['discovery']['ranking']} == {
            't:-2|x:1' + ('|z:' + str(k) if k else '') for k in range(-p['grammar']['max_abs_power'], p['grammar']['max_abs_power']+1)}
            for o in outputs.values()),
        'payloads': all(v['discovery']['input_sha256'] == digest(inputs[rid]) for rid, v in outputs.items()),
        'eligibility': all(prepare(raw) == (inputs[rid], eligibility[rid]) and
                           all(v['status'] != 'ineligible' for v in eligibility[rid].values()) for rid, raw in public.items()),
        'source_inventory': all(v['receipt']['worker_sha256'] == hashlib.sha256(WORKER.encode()).hexdigest() and
                               all(v['receipt']['inventory_before'][path]['sha256'] == sha_file(ROOT / path) for path in ENGINE_FILES)
                               for v in outputs.values())}
    tolerance = p['scoring']['independent_metric_tolerance']
    arithmetic = True
    for rid, output in outputs.items():
        ranking = output['discovery']['ranking']
        for candidate in ranking:
            def residual(row):
                predicted = math_product(row['features'], candidate['representative'])
                return math.log(row['target'] / predicted)
            train, valid = inputs[rid]['train'], inputs[rid]['validation']
            intercept = sum(residual(r) for r in train) / len(train)
            tr = math.sqrt(sum((intercept - residual(r))**2 for r in train) / len(train))
            va = math.sqrt(sum((intercept - residual(r))**2 for r in valid) / len(valid))
            complexity = sum(abs(float(v)) for v in candidate['expanded'].values())
            independent_held = math.sqrt(sum((intercept - residual(r))**2 for r in heldout[rid]) / len(heldout[rid]))
            from Discovery.symbolic_benchmark_engine import rmse
            arithmetic &= abs(independent_held - rmse(candidate['representative'], candidate['log_coefficient'], heldout[rid])) <= tolerance
            arithmetic &= all(abs(a-b) <= tolerance for a, b in [(intercept, candidate['log_coefficient']),
                (tr, candidate['training_rmse']), (va, candidate['validation_rmse']),
                (complexity, candidate['expanded_complexity']),
                (va + p['scoring']['complexity_lambda'] * complexity, candidate['rank_score'])])
        arithmetic &= ranking == sorted(ranking, key=lambda v: (v['rank_score'], v['expanded_complexity'], v['class_id']))
    checks['independent_all_candidate_arithmetic'] = bool(arithmetic)
    for name, value in [('public', public), ('inputs', inputs), ('eligibility', eligibility), ('oracle', oracle), ('heldout', heldout)]:
        checks[name + '_commitment'] = digest(value) == c[name + '_sha256']
    return checks


def math_product(features, powers):
    return math.prod(features[k] ** float(v) for k, v in powers.items())


def reveal():
    clean()
    committed(ART / 'selection_seal.json')
    c, seal_record = read(ART / 'commitment.json'), read(ART / 'selection_seal.json')
    outputs = selections(c['dataset_ids'])
    oracle, heldout = read(PRIVATE / 'oracle.json'), read(PRIVATE / 'heldout.json')
    check_binding(c, seal_record, outputs, oracle, heldout)
    if seed_digest(oracle['seed']) != read(ART / 'seed_commitment.json')['seed_sha256']:
        raise ValueError('seed reveal mismatch')
    write_new(PRIVATE / 'reveal_started.json', {'head': git('rev-parse', 'HEAD'), 'started_at': now()})
    p = read(ART / 'preregistration.v1.json')
    public, inputs, eligibility = [read(ART / (n + '.json')) for n in ('public', 'inputs', 'eligibility')]
    write_new(ART / 'oracle_reveal.json', oracle)
    write_new(ART / 'heldout.json', heldout)
    records = {rid: evaluate(p, public[rid], outputs[rid], oracle['realizations'][rid], heldout[rid]) for rid in c['dataset_ids']}
    checks = controls(p, c, public, inputs, eligibility, outputs, oracle, heldout)
    summary = aggregate(p, records, all(checks.values()))
    for name, value in [('evaluation', records), ('controls', checks), ('summary', summary)]:
        write_new(ART / (name + '.json'), value)
    write_new(ART / 'result.json', {**summary, 'schema': 'tnp-margin1/raw-result-v1', 'source_sha': c['source_sha'],
        'selection_commit_sha': git('rev-parse', 'HEAD'), 'evaluation_sha256': digest(records),
        'controls_sha256': digest(checks), 'summary_sha256': digest(summary), 'evaluated_at': now()})
    print(summary['disposition'] + ' — PROVISIONAL — INDEPENDENT AUDIT PENDING')


def retrospective_sources():
    paths = [OLD / n for n in ('preregistration.v1.json', 'oracle_reveal.json')]
    paths += sorted((OLD / 'selection').glob('*.json')) + sorted((OLD / 'inputs').glob('*.json'))
    paths += [ROOT / 'Experiments/SymbolicDiscovery/disposition_index.json']
    return paths


def derive_retrospective():
    p = read(ART / 'preregistration.v1.json')
    pins = {}
    for path in retrospective_sources():
        committed(path, p['retrospective']['source_sha'])
        pins[path.relative_to(ROOT).as_posix()] = sha_file(path)
    # Validate only explicit route bytes/source pins; no historical scientific replay.
    validate_index(read(ROOT / 'Experiments/SymbolicDiscovery/disposition_index.json'))
    old = read(OLD / 'preregistration.v1.json')
    oracle = read(OLD / 'oracle_reveal.json')
    ids = sorted(oracle['realizations'])
    records = {rid: read(OLD / 'selection' / (rid + '.json')) for rid in ids}
    policies = {rid: read(OLD / 'inputs' / (rid + '.json')) for rid in ids}
    return retrospective(p, old, oracle, records, policies), pins


def history():
    records, cache = {}, {}
    for sha in git('rev-list', 'HEAD').splitlines():
        tree = git('ls-tree', sha, REL)
        if tree not in cache:
            cache[tree] = set(git('ls-tree', '-r', '--name-only', sha, REL).splitlines()) if tree else set()
        records[sha] = (git('show', '-s', '--format=%P', sha).split(), cache[tree])
    return records


def introduction(h, path):
    found = [sha for sha, (parents, files) in h.items() if path in files and not any(path in h[a][1] for a in parents)]
    if len(found) != 1:
        raise ValueError('nonunique introduction: ' + path)
    return found[0]


def immutable(sha, paths):
    verify_committed_source_state(ROOT, sha, source_paths=paths, artifact_label='Margin1 immutable evidence')
    for descendant in git('rev-list', sha + '..HEAD').splitlines():
        relation = subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', sha, descendant], capture_output=True)
        if relation.returncode == 1:
            continue
        if relation.returncode or git('diff', '--name-only', sha, descendant, '--', *paths):
            raise ValueError('intervening immutable artifact/source change')


def chronology():
    a, _ = verify_freeze()
    c, sealed, result = [read(ART / n) for n in ('commitment.json', 'selection_seal.json', 'result.json')]
    h = history()
    stages = [a['snapshot_sha'], a['freeze_sha'], c['source_sha'], c['seed_commit_sha'],
              sealed['data_commit_sha'], result['selection_commit_sha'], introduction(h, REL + '/result.json')]
    for x, y in zip(stages, stages[1:]):
        ancestor(x, y)
    verify_seed(stages[3])
    if datetime.fromisoformat(git('show', '-s', '--format=%cI', stages[2])) <= datetime.fromisoformat(a['created_at']):
        raise ValueError('source before anchor')
    immutable(stages[2], SOURCE_FILES)
    expected = {0: ['work_order.r1.md', 'work_order_receipt.json'], 1: ['preregistration.v1.json'],
                2: ['anchor.json', 'preflight.json', 'retrospective.json', 'retrospective_sources.json', 'mutation_preflight.json', 'mutation_preflight.attempt1.json'],
                3: ['seed_commitment.json'], 4: ['public.json', 'inputs.json', 'eligibility.json', 'commitment.json'],
                5: ['selection_seal.json'], 6: ['oracle_reveal.json', 'heldout.json', 'evaluation.json', 'controls.json', 'summary.json', 'result.json']}
    for stage, names in expected.items():
        paths = [REL + '/' + n for n in names]
        if stage == 5:
            paths += [REL + '/selection/' + rid + '.json' for rid in c['dataset_ids']]
        if any(introduction(h, path) != stages[stage] for path in paths):
            raise ValueError('custody introduction mismatch')
        immutable(stages[stage], paths)
    if c['remote_publication'] != {'ref': 'refs/heads/' + BRANCH, 'observed_sha': stages[3], 'before_generation': True}:
        raise ValueError('seed publication receipt changed')
    # A reveal file present before the seal cannot satisfy its unique stage introduction above.
    if sealed['oracle_revealed'] or sealed['heldout_accessed'] or sealed['dataset_count'] != len(c['dataset_ids']):
        raise ValueError('invalid selection seal')
    if result['source_sha'] != c['source_sha']:
        raise ValueError('result source mismatch')
    return stages


def make_routes(raw_epoch, failure_paths=()):
    """Forward adapter: explicit keys; the frozen Suite1 make_index is never called."""
    baseline = ROOT / 'Experiments/SymbolicDiscovery/disposition_index.json'
    value = read(baseline)
    validate_index(value)
    return {'schema': 'tnp-margin1/disposition-routing-v1',
        'accepted_baseline_routes': {'path': baseline.relative_to(ROOT).as_posix(), 'sha256': sha_file(baseline),
            'Benchmark0': value['Benchmark0'], 'BenchmarkSuite1': value['BenchmarkSuite1'],
            'current_acceptance_note': 'Both independently accepted and merged; old provisional navigation is historical.'},
        'MisspecificationMargin1': {'raw_epoch': route(ART / 'result.json', 'disposition', raw_epoch),
            'study_aggregation': route(ART / 'summary.json', 'disposition', raw_epoch),
            'operational_failures': [route(path, 'disposition', raw_epoch) for path in failure_paths],
            'reconciliation': None, 'authoritative': 'raw_epoch',
            'independent_status': 'PROVISIONAL — INDEPENDENT AUDIT PENDING'}}


def write_routes():
    clean()
    committed(ART / 'result.json')
    failures = sorted((ART / 'operational_failures').glob('*.json'))
    for path in failures:
        committed(path)
    write_new(ART / 'disposition_routes.json', make_routes(git('rev-parse', 'HEAD'), failures))
    print('Explicit raw, study and historical reconciliation routes written.')


def check(replay=False):
    environment()
    stages = chronology()
    p, c, sealed = [read(ART / n) for n in ('preregistration.v1.json', 'commitment.json', 'selection_seal.json')]
    public, inputs, eligibility, oracle, heldout = [read(ART / (n + '.json')) for n in ('public', 'inputs', 'eligibility', 'oracle_reveal', 'heldout')]
    outputs = selections(c['dataset_ids'])
    check_binding(c, sealed, outputs, oracle, heldout)
    if seed_digest(oracle['seed']) != read(ART / 'seed_commitment.json')['seed_sha256'] or c['seed_commitment_sha256'] != sha_file(ART / 'seed_commitment.json'):
        raise ValueError('seed binding changed')
    if c['dataset_ids'] != dataset_ids(p):
        raise ValueError('dataset order changed')
    retro, pins = derive_retrospective()
    if retro != read(ART / 'retrospective.json') or pins != read(ART / 'retrospective_sources.json'):
        raise ValueError('retrospective changed')
    checks = controls(p, c, public, inputs, eligibility, outputs, oracle, heldout)
    records = {rid: evaluate(p, public[rid], outputs[rid], oracle['realizations'][rid], heldout[rid]) for rid in c['dataset_ids']}
    summary = aggregate(p, records, all(checks.values()))
    if checks != read(ART / 'controls.json') or records != read(ART / 'evaluation.json') or summary != read(ART / 'summary.json'):
        raise ValueError('evaluation/summary mismatch')
    result = read(ART / 'result.json')
    if any(result[k] != v for k, v in summary.items()) or result['evaluation_sha256'] != digest(records) or result['controls_sha256'] != digest(checks) or result['summary_sha256'] != digest(summary):
        raise ValueError('raw result binding mismatch')
    if not all(checks.values()) or not summary['integrity_pass']:
        raise ValueError('scientific integrity failure')
    if read(ART / 'preflight.json')['source_manifest'] != source_manifest():
        raise ValueError('source preflight changed')
    # Explicitly disclosed same-epoch generator replay: verifies pairing, strata, formula and committed streams.
    if replay:
        regenerated = generate(p, oracle['seed'])
        if tuple(map(digest, regenerated)) != tuple(map(digest, (public, heldout, oracle))):
            raise ValueError('same-epoch generation mismatch')
    route_path = ART / 'disposition_routes.json'
    if route_path.exists():
        failures = sorted((ART / 'operational_failures').glob('*.json'))
        expected = make_routes(stages[-1], failures)
        if read(route_path) != expected:
            raise ValueError('disposition routing mismatch')
        h = history()
        intro = introduction(h, REL + '/disposition_routes.json')
        ancestor(stages[-1], intro)
        immutable(intro, [REL + '/disposition_routes.json'])
    from tests.test_symbolic_suite import fixture
    live = staged_discovery(fixture())
    stale = staged_discovery(fixture(), stale_cache=True, enforce=False)
    cache = '<stage>/Discovery/__pycache__/symbolic_suite_engine.cpython-312.pyc'
    if not valid_receipt(live) or valid_receipt(stale) or cache not in stale['receipt']['successful_reads'] or cache in stale['receipt']['expected_missing_cache_attempts']:
        raise ValueError('live cache semantic failure')
    print(summary['disposition'] + '; new source, chronology, retrospective, all-candidate arithmetic and live receipt probes verified' + ('; same-epoch generation matched' if replay else ''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['seed', 'realize', 'seal', 'reveal', 'routes', 'retrospective', 'check'])
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    try:
        if args.stage == 'check':
            check(args.replay)
        elif args.stage == 'retrospective':
            result, pins = derive_retrospective()
            write_new(ART / 'retrospective.json', result)
            write_new(ART / 'retrospective_sources.json', pins)
        else:
            {'seed': seed, 'realize': realize, 'seal': seal, 'reveal': reveal, 'routes': write_routes}[args.stage]()
    except Exception as error:
        if args.stage in ('seed', 'realize', 'seal', 'reveal', 'routes'):
            path = ART / 'operational_failures' / (args.stage + '-' + git('rev-parse', 'HEAD') + '.json')
            if not path.exists():
                write_new(path, {'stage': args.stage, 'head_sha': git('rev-parse', 'HEAD'),
                    'disposition': 'MISSPEC_MARGIN_1_NO_GO', 'classification': 'operational_stage_failure_not_scientific_disposition',
                    'error': type(error).__name__ + ': ' + str(error), 'traceback': traceback.format_exc(), 'created_at': now()})
        raise


if __name__ == '__main__':
    main()
