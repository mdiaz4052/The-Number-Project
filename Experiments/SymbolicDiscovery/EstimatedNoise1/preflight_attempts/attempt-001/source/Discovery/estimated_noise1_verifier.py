"""Read-only verification of committed bytes, chronology and derived evidence.

No discovery/generator call, network, scientific rerun, native engine, or output
file. Current receipt/cache probes are engineering fixtures only when requested.
Source checks use committed epoch bytes, not perpetual shared-worktree equality.
"""
import argparse
import ast
import datetime
import math
from pathlib import Path
import subprocess
import sys

from Discovery.estimated_noise1_calibration import digest, encoded, loads, estimate
from Discovery import estimated_noise1_schema as schema
from Discovery import estimated_noise1_reference as reference
from Discovery import estimated_noise1_science as science
from Discovery.estimated_noise1_selection import discovery_payload
from Discovery.estimated_noise1 import ROOT, PKG, REL, SOURCE_PATHS, sha, blob, git, bindings, artifact


def require(value, message):
    if not value: raise ValueError(message)


def close(actual, expected, path='$', tolerance=1e-10):
    """Numerical replay tolerance only; labels, inventories, hashes/types exact."""
    if type(expected) is dict:
        require(type(actual) is dict and set(actual) == set(expected), 'closed evidence schema '+path)
        for k in expected: close(actual[k], expected[k], path+'.'+k, tolerance)
    elif type(expected) is list:
        require(type(actual) is list and len(actual) == len(expected), 'evidence list '+path)
        for i, (a, b) in enumerate(zip(actual, expected)): close(a, b, path+f'[{i}]', tolerance)
    elif type(expected) is float:
        require(type(actual) is float and math.isfinite(actual) and
                abs(actual-expected) <= tolerance*max(1., abs(expected)), 'numeric replay '+path)
    else:
        require(type(actual) is type(expected) and actual == expected, 'exact evidence value '+path)


def creation(path):
    rel = REL+'/'+path
    commits = git('log', '--format=%H', '--', rel).splitlines()
    require(len(commits) == 1, 'artifact must be introduced once and never edited: '+path)
    require(blob(commits[0], rel) == (PKG/path).read_bytes(), 'committed artifact bytes: '+path)
    return commits[0]


def ancestor(a, b):
    require(subprocess.run(['git', 'merge-base', '--is-ancestor', a, b], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            'required true-merge ancestry lost')


def direct(a, b):
    require(git('rev-parse', b+'^') == a, 'stage parent chronology')


def source_check():
    if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('offline verification requires CPython 3.12')
    pre = loads((PKG/'preregistration.v1.json').read_bytes())
    prepared = loads((PKG/'preregistration.prepared.json').read_bytes())
    receipt = loads((PKG/'work_order_receipt.json').read_bytes())
    anchor = loads((PKG/'anchor.json').read_bytes())
    b = bindings()
    require(pre['task'] == 'NP-ESTIMATED-NOISE-01' and type(pre['revision']) is int and pre['revision'] == 1,
            'task revision')
    require(digest(pre['science']) == pre['science_sha256'] ==
        '19edaba69d1b2cd8b4d0235180d548eac6387b0b564863c0109a7fec6fb4c312', 'frozen science digest')
    expected = {**prepared, 'schema': 'tnp-estimated-noise/preregistration-v1', 'state': 'FROZEN',
                'launch_binding': pre['launch_binding']}
    schema.same(pre, expected, 'only launch bindings/schema/state may change')
    require(sha((PKG/'work_order.r1.md').read_bytes()) == '21f0558af43835ba33c107cf8cf85bae869a4c8212f17c7c0ba2f1f74400ca1e', 'work order bytes')
    require(sha((PKG/'preregistration.prepared.json').read_bytes()) ==
        '1c811c465f9d1d404d8a9f11dc4ef1628598045fd4616d50a5ed435cab6dd06f', 'prepared bytes')
    snapshot = creation('work_order.r1.md')
    require(creation('work_order_receipt.json') == creation('preregistration.prepared.json') == snapshot, 'snapshot epoch')
    freeze = creation('preregistration.v1.json')
    require(git('diff-tree', '--no-commit-id', '--name-only', '-r', freeze) == REL+'/preregistration.v1.json',
            'sole-file preregistration freeze')
    direct(snapshot, freeze)
    schema.same(pre['launch_binding'], {'actual_base_sha': receipt['actual_base_sha'],
        'instruction_snapshot_sha': snapshot, 'consumed_work_order_sha256': receipt['consumed_work_order']['sha256'],
        'prepared_preregistration_sha256': receipt['prepared_preregistration']['sha256']}, 'launch bindings')
    direct(b['actual_base_sha'], snapshot)
    require(anchor['base_sha'] == b['actual_base_sha'] and anchor['snapshot_sha'] == snapshot and
            anchor['freeze_sha'] == freeze, 'anchor linkage')
    created = datetime.datetime.fromisoformat(anchor['pr_created_at'].replace('Z', '+00:00'))
    frozen = datetime.datetime.fromisoformat(git('show', '-s', '--format=%cI', freeze))
    require(created > frozen, 'server PR anchor must be strictly after freeze')
    pf = artifact('preflight.json', 'preflight')
    require(set(pf['source_manifest']) == set(SOURCE_PATHS), 'complete source closure')
    require(pf['qualified'] is True, 'preflight must qualify')
    require(pf['mutations']['baseline'] == pf['mutations']['equivalent_control'] == 'SURVIVED', 'mutation controls')
    require(set(pf['mutations']['mutants']) == {f'M{i}' for i in range(1, 11)} and
            all(v['status'] == 'KILLED' and v['designated_assertion'] == v['observed_assertion']
                for v in pf['mutations']['mutants'].values()), 'all ten semantic mutations')
    source = artifact('seed_commitment.json', 'seed-commitment')['source_sha'] if (PKG/'seed_commitment.json').exists() else creation('preflight.json')
    require(creation('preflight.json') == source, 'qualified source epoch')
    for path, h in pf['source_manifest'].items():
        require(sha(blob(source, path)) == h, 'committed source pin '+path)
    ancestor(freeze, source)
    ancestor(source, git('rev-parse', 'HEAD'))
    # Fixed used-epoch comparison only; future shared modules may evolve.
    changed = git('diff', '--name-status', b['actual_base_sha'], source).splitlines()
    require(all(line.startswith('A\t') for line in changed), 'existing source/workflow boundary modified')
    return pre['science'], pf, source


def literal_worker(source):
    tree = ast.parse(blob(source, 'Discovery/symbolic_suite_runner.py'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'WORKER' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('pinned runner worker not found')


def receipt_check(output, source, manifest, *, calibration=False):
    schema.worker(output, schema.CAL_RESULT if calibration else schema.DISCOVERY)
    files = ('Discovery/__init__.py', 'Discovery/estimated_noise1_calibration.py') if calibration else tuple(
        'Discovery/'+n+'.py' for n in ('__init__', 'symbolic_benchmark_engine', 'symbolic_suite_engine',
        'constants', 'dimensions', 'dimensional_search', 'planck_identities', 'dependency_definitions', 'monomial_constraints'))
    text = literal_worker(source)
    if calibration:
        text = text.replace('from Discovery.symbolic_suite_engine import discover',
                            'from Discovery.estimated_noise1_calibration import estimate as discover')
    r = output['receipt']
    sources = {'<stage>/'+p for p in files}
    caches = {'<stage>/'+str(Path(p).parent/'__pycache__'/(Path(p).stem+'.cpython-312.pyc')) for p in files}
    modules = {'Discovery' if p == 'Discovery/__init__.py' else p[:-3].replace('/', '.') for p in files}
    expected_inventory = {'Discovery': {'kind': 'directory'}, **{p: {'kind': 'file',
        'size': len(blob(source, p)), 'sha256': manifest[p]} for p in files}}
    schema.same(r['inventory_before'], expected_inventory, 'worker staged source inventory')
    schema.same(r['inventory_after'], expected_inventory, 'worker inventory changed')
    require(r['version'] == 2 and r['python_minor'] == '3.12' and r['cache_tag'] == 'cpython-312', 'worker runtime')
    require(r['worker_sha256'] == sha(text.encode()), 'worker code identity')
    require(not r['denied_unexpected_attempts'] and not r['unexpected_modules'], 'forbidden worker access')
    require(set(r['discovery_modules']) == modules, 'worker module inventory')
    staged = lambda values: {v for v in values if v.startswith('<stage>/')}
    require(staged(r['successful_reads']) == staged(r['successful_opens']) == sources, 'completed source read receipt')
    require(set(r['expected_missing_cache_attempts']) == caches and
            staged(r['audit_open_attempts']) == sources | caches, 'fresh-cache receipt semantics')


def check(*, numeric=True):
    p, pf, source = source_check()
    seed = artifact('seed_commitment.json', 'seed-commitment')
    schema.validate(seed, schema.SEED)
    schema.same(seed['environment'], pf['environment'], 'seed environment')
    require(seed['source_manifest_sha256'] == digest(pf['source_manifest']), 'seed closure binding')
    seed_commit = creation('seed_commitment.json')
    direct(source, seed_commit)
    require(git('diff-tree', '--no-commit-id', '--name-only', '-r', seed_commit) == REL+'/seed_commitment.json',
            'sole-file seed commitment')
    com = artifact('commitment.json', 'commitment'); schema.validate(com, schema.COMMITMENT)
    require(com['source_sha'] == source and com['seed_commit_sha'] == seed_commit and
            com['remote_readback']['head'] == seed_commit, 'published seed linkage')
    require(com['remote_readback']['ref'] == 'refs/heads/experiment/np-estimated-noise-01' and
            com['remote_readback']['observed_utc'] < com['generated_utc'], 'remote-before-generation chronology')
    data_commit = creation('commitment.json'); direct(seed_commit, data_commit)
    public = artifact('public.json', 'public')['datasets']
    calibration_records = artifact('calibration.json', 'calibration')['datasets']
    for name in ('public', 'calibration'):
        require(creation(name+'.json') == data_commit and sha((PKG/(name+'.json')).read_bytes()) == com[name+'_sha256'], 'data seal')
    schema.scientific_inputs(public, calibration_records)
    estimates = artifact('calibration_estimates.json', 'calibration-estimates')
    require(set(estimates) == {'source_sha', 'data_commit_sha', 'records'}, 'estimate envelope data schema')
    require(estimates['source_sha'] == source and estimates['data_commit_sha'] == data_commit, 'calibration source')
    cs = artifact('calibration_seal.json', 'calibration-seal'); schema.validate(cs, schema.CAL_SEAL)
    cal_commit = creation('calibration_seal.json'); direct(data_commit, cal_commit)
    require(creation('calibration_estimates.json') == cal_commit and cs['record_count'] == 96, 'all-calibration commit')
    require(cs['source_sha'] == source and cs['data_commit_sha'] == data_commit and
            cs['estimates_sha256'] == sha((PKG/'calibration_estimates.json').read_bytes()) and
            cs['calibration_sha256'] == com['calibration_sha256'], 'calibration input/output binding')
    schema.same(cs['settings'], science.settings(p), 'fixed estimation policy')
    ids = science.identities()
    require(set(estimates['records']) == set(cs['output_hashes']) == set(ids), 'calibration inventory')
    for rid in ids:
        output = estimates['records'][rid]
        receipt_check(output, source, pf['source_manifest'], calibration=True)
        payload = {'dataset_id': rid, 'pairs': calibration_records[rid], 'settings': science.settings(p)}
        close(output['discovery'], estimate(payload), tolerance=1e-12)
        path = f'calibration_workers/{rid}.json'
        require(creation(path) == cal_commit and sha((PKG/path).read_bytes()) == cs['output_hashes'][rid], 'calibration worker hash')
        schema.same(artifact(path, 'calibration-worker'), {'source_sha': source, 'data_commit_sha': data_commit,
                                                         'worker': output}, 'calibration output linkage')
    ss = artifact('selection_seal.json', 'selection-seal'); schema.validate(ss, schema.SELECTION_SEAL)
    selection_commit = creation('selection_seal.json'); direct(cal_commit, selection_commit)
    require(ss['source_sha'] == source and ss['calibration_seal_commit_sha'] == cal_commit and
            ss['record_count'] == 96 and ss['principal_fits'] == 480 and ss['diagnostic_refits'] == 96 and
            set(ss['files']) == set(ids), 'all-selection inventory')
    selections = {}
    for rid in ids:
        path = f'selection/{rid}.json'
        require(creation(path) == selection_commit and sha((PKG/path).read_bytes()) == ss['files'][rid], 'selection byte seal')
        sel = artifact(path, 'selection'); schema.validate_selection(sel)
        receipt_check(sel['worker'], source, pf['source_manifest'])
        require(sel['dataset_id'] == rid and sel['source_sha'] == source and sel['data_commit_sha'] == data_commit and
                sel['calibration_seal_sha256'] == sha((PKG/'calibration_seal.json').read_bytes()) and
                sel['calibration_seal_commit_sha'] == cal_commit, 'selection identity/pins')
        e = estimates['records'][rid]['discovery']['estimates']
        payload = discovery_payload(public[rid], science.policy(p, e['64']['upper95_threshold']))
        d = sel['worker']['discovery']
        require(digest(payload) == sel['payload_sha256'] == d['input_sha256'], 'primary estimated policy input')
        schema.same(sel['operational'], science.operational(p, d, e), 'sealed six decisions')
        require(d['minimum_validation_rmse'] == min(c['validation_rmse'] for c in d['ranking']) and
                d['approximation_status'] == ('predictive_approximation' if sel['operational']['approximation'] else 'poor_approximation'),
                'discovery family/approximation diagnostics')
        selections[rid] = sel
    oracle = artifact('oracle_reveal.json', 'oracle-reveal')
    heldout = artifact('heldout.json', 'heldout')['datasets']
    schema.scientific_inputs(public, calibration_records, heldout, oracle)
    require(sha(('estimated-noise1:'+oracle['seed']).encode()) == seed['seed_sha256'] and
            sha(oracle['seed'].encode()) == com['private_hashes']['seed.txt'], 'seed reveal')
    result_commit = creation('result.json'); direct(selection_commit, result_commit)
    for name in ('oracle_reveal.json', 'heldout.json'):
        require(creation(name) == result_commit and sha((PKG/name).read_bytes()) == com['private_hashes'][name], 'private reveal hash/epoch')
    ev = artifact('evaluation.json', 'evaluation')
    require(set(ev) == {'source_sha', 'selection_seal_commit_sha', 'datasets'} and
            ev['source_sha'] == source and ev['selection_seal_commit_sha'] == selection_commit and
            set(ev['datasets']) == set(ids), 'evaluation identity')
    controls = artifact('controls.json', 'controls')
    require(set(controls) == {'source_sha', 'selection_seal_commit_sha', 'generation', 'calibration', 'candidates',
        'custody_verified', 'inventory_verified', 'environment_matches'}, 'controls schema')
    require(controls['source_sha'] == source and controls['selection_seal_commit_sha'] == selection_commit and
            controls['custody_verified'] is True and controls['inventory_verified'] is True and
            controls['environment_matches'] is True, 'custody controls')
    numeric_cal, numeric_candidates = {}, {}
    for rid in ids:
        e = estimates['records'][rid]['discovery']['estimates']
        truth = oracle['datasets'][rid]
        expected = science.evaluate(p, selections[rid], truth, heldout[rid], e)
        close(ev['datasets'][rid], expected)
        if numeric:
            intended = [truth['epsilon']*(r['u1']-r['u2']) for r in oracle['blocks'][str(truth['block'])]['calibration']]
            numeric_cal[rid] = reference.calibration(calibration_records[rid], science.settings(p), e, intended)
            numeric_candidates[rid] = reference.candidate_arithmetic(public[rid], selections[rid]['worker']['discovery']['ranking'],
                heldout=heldout[rid], truth=truth, metrics={c['class_id']: c for c in ev['datasets'][rid]['candidates']})
        for directory, kind, expected_value in (
            ('evaluation_partial', 'dataset-evaluation', ev['datasets'][rid]),
            ('numeric_partial', 'dataset-numerics', {'calibration': controls['calibration'][rid], 'candidates': controls['candidates'][rid]})):
            path = f'{directory}/{rid}.json'
            require(creation(path) == result_commit, 'partial record epoch')
            schema.same(artifact(path, kind), expected_value, 'preserved incremental result')
    if numeric:
        close(controls['generation'], reference.generation(p, public, calibration_records, heldout, oracle))
        close(controls['calibration'], numeric_cal)
        close(controls['candidates'], numeric_candidates)
    statuses = {rid: {'state': 'INTERPRETABLE', 'stage': 'evaluation', 'reason': None} for rid in ids}
    derived = science.aggregate(p, ev['datasets'], statuses, [], [])
    summary = artifact('summary.json', 'summary')
    schema.same(summary, derived, 'summary must derive from all evidence and preserve adverse outcomes')
    result = artifact('result.json', 'raw-result'); schema.validate(result, schema.RESULT)
    expected_result = {'source_sha': source, 'selection_seal_commit_sha': selection_commit,
        **{k+'_sha256': sha((PKG/(k+'.json')).read_bytes()) for k in ('summary', 'evaluation', 'controls')},
        **{k: derived[k] for k in ('disposition', 'evidence_integrity', 'interpretable_datasets', 'expected_datasets', 'review_status')},
        'operational_status': 'COMPLETED', 'outcome_blind': False, 'scientific_law_claim': False}
    schema.same(result, expected_result, 'raw result derivation')
    for name in ('evaluation.json', 'controls.json', 'summary.json'):
        require(creation(name) == result_commit, 'raw evidence epoch')
    if (PKG/'evidence_seal.json').exists():
        seal = artifact('evidence_seal.json', 'evidence-seal')
        require(set(seal) == {'source_sha', 'result_commit_sha', 'files'} and
                seal['source_sha'] == source and seal['result_commit_sha'] == result_commit, 'evidence seal pins')
        ancestor(result_commit, creation('evidence_seal.json'))
        expected_paths = {p.relative_to(PKG).as_posix() for p in PKG.rglob('*') if p.is_file() and
                          p.name not in ('evidence_seal.json', 'verification_routes.json')}
        require(set(seal['files']) == expected_paths, 'complete evidence path census')
        for path, h in seal['files'].items(): require(sha((PKG/path).read_bytes()) == h, 'evidence integrity '+path)
        routes = artifact('verification_routes.json', 'verification-routes')
        schema.same(routes['raw'], {'path': REL+'/result.json', 'sha256': sha((PKG/'result.json').read_bytes()),
                    'disposition_key': 'data.disposition', 'disposition': result['disposition']}, 'raw route')
        require(routes['reconciliation'] is None, 'no unrecorded reconciliation')
    return {'disposition': derived['disposition'], 'evidence_integrity': derived['evidence_integrity'],
            'interpretable_datasets': derived['interpretable_datasets'], 'source_sha': source,
            'result_commit_sha': result_commit, 'review_status': derived['review_status']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check'])
    parser.parse_args()
    print(encoded(check()).decode(), end='')


if __name__ == '__main__': main()
