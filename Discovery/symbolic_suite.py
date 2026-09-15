"""Prospective Suite 1 custody, one fixed realization set and read-only verifier."""
import argparse
import copy
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
from Discovery.symbolic_suite_runner import ENGINE_FILES, staged_discovery, valid_receipt, RunnerFailure, WORKER
from Discovery.symbolic_suite_evaluation import evaluate_realization, aggregate
from Discovery.preregistration_history import verify_preregistration_freeze
from Discovery.source_history import verify_committed_source_state

ROOT=Path(__file__).resolve().parents[1]
REL='Experiments/SymbolicDiscovery/BenchmarkSuite1'
ART=ROOT/REL
PRIVATE=ROOT/'.tnp-local/suite1-private'
BRANCH='experiment/symbolic-benchmark-suite-1'
SOURCE_FILES=(*ENGINE_FILES,'Discovery/symbolic_suite_runner.py','Discovery/symbolic_suite_worlds.py',
    'Discovery/symbolic_suite_evaluation.py','Discovery/symbolic_suite.py',
    'Discovery/preregistration_history.py','Discovery/source_history.py','tests/test_symbolic_suite.py')
INDEX=ROOT/'Experiments/SymbolicDiscovery/disposition_index.json'


def read(path): return json.loads(Path(path).read_text())
def sha_file(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def git(*args): return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def write_new(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream: stream.write(encoded(value))


def committed(path,sha='HEAD'):
    rel=Path(path).relative_to(ROOT).as_posix()
    if subprocess.check_output(['git','-C',str(ROOT),'show',sha+':'+rel])!=Path(path).read_bytes():
        raise ValueError('required committed bytes differ: '+rel)


def clean():
    if git('status','--porcelain','--untracked-files=no'):
        raise ValueError('commit all tracked state before scientific execution')


def ancestor(a,b):
    if a==b: raise ValueError('custody stages must be distinct')
    git('merge-base','--is-ancestor',a,b)


def verify_freeze():
    anchor=read(ART/'anchor.json')
    verify_preregistration_freeze(ROOT,baseline=anchor['base_sha'],commit=anchor['freeze_sha'],
        path=REL+'/preregistration.v1.json',sha256=anchor['preregistration_sha256'])
    if datetime.fromisoformat(anchor['created_at'])<=datetime.fromisoformat(git('show','-s','--format=%cI',anchor['freeze_sha'])):
        raise ValueError('published draft anchor must postdate freeze')
    return anchor


def source_manifest(): return {p:sha_file(ROOT/p) for p in SOURCE_FILES}

def seed_digest(seed): return hashlib.sha256(('suite1:'+seed).encode()).hexdigest()


def seed():
    anchor=verify_freeze(); clean()
    source=git('rev-parse','HEAD')
    if PRIVATE.exists() or (ART/'seed_commitment.json').exists(): raise ValueError('seed epoch already exists')
    if datetime.fromisoformat(git('show','-s','--format=%cI',source))<=datetime.fromisoformat(anchor['created_at']):
        raise ValueError('source must postdate published design anchor')
    for p in SOURCE_FILES: committed(ROOT/p)
    preflight=read(ART/'preflight.json')
    if not preflight['passed'] or preflight['source_manifest']!=source_manifest():
        raise ValueError('outcome-independent preflight not current')
    secret=secrets.token_hex(32)
    write_new(PRIVATE/'seed.json',{'seed':secret,'source_sha':source})
    write_new(ART/'seed_commitment.json',{'schema':'tnp-suite1/seed-commitment-v1','seed_sha256':seed_digest(secret),
        'source_sha':source,'preregistration_sha256':anchor['preregistration_sha256'],
        'preflight_sha256':sha_file(ART/'preflight.json'),'created_at':now(),'realization_count':read(ART/'preregistration.v1.json')['design']['total_realizations']})
    print('Seed commitment written. Publish this sole-file commit before generation; seed remains hidden.')


def verify_seed(source,seed_commit_sha):
    verify_preregistration_freeze(ROOT,baseline=source,commit=seed_commit_sha,
        path=REL+'/seed_commitment.json',sha256=sha_file(ART/'seed_commitment.json'))
    verify_committed_source_state(ROOT,source,source_paths=SOURCE_FILES,artifact_label='Suite 1')


def realize():
    from Discovery.symbolic_suite_worlds import generate
    verify_freeze(); clean(); committed(ART/'seed_commitment.json')
    seed_record=read(ART/'seed_commitment.json'); seed_sha=git('rev-parse','HEAD')
    verify_seed(seed_record['source_sha'],seed_sha)
    # Independent remote ref read confirms publication before invoking generator.
    remote=git('ls-remote','origin','refs/heads/'+BRANCH).split()
    if not remote or remote[0]!=seed_sha: raise ValueError('seed commitment not at published branch head')
    if (ART/'commitment.json').exists() or (PRIVATE/'realization_started.json').exists():
        raise ValueError('one fixed realization set only; do not reroll')
    secret=read(PRIVATE/'seed.json')['seed']
    if seed_digest(secret)!=seed_record['seed_sha256']: raise ValueError('seed commitment mismatch')
    write_new(PRIVATE/'realization_started.json',{'seed_commit_sha':seed_sha,'started_at':now()})
    prereg=read(ART/'preregistration.v1.json')
    public,heldout,oracle=generate(prereg,secret)
    write_new(PRIVATE/'oracle.json',oracle); write_new(PRIVATE/'heldout.json',heldout)
    inputs,eligibility={},{}
    for rid,raw in public.items():
        inputs[rid],eligibility[rid]=prepare(raw)
        write_new(ART/'public'/f'{rid}.json',raw); write_new(ART/'inputs'/f'{rid}.json',inputs[rid])
    write_new(ART/'eligibility.json',eligibility)
    write_new(ART/'commitment.json',{'schema':'tnp-suite1/data-commitment-v1','source_sha':seed_record['source_sha'],
        'seed_commit_sha':seed_sha,'seed_commitment_sha256':sha_file(ART/'seed_commitment.json'),
        'seed_publication':{'remote_ref':'refs/heads/'+BRANCH,'observed_sha':remote[0],'observed_before_generation':True},
        'created_at':now(),'public_sha256':digest(public),'inputs_sha256':digest(inputs),'eligibility_sha256':digest(eligibility),
        'oracle_sha256':digest(oracle),'heldout_sha256':digest(heldout),'realization_ids':sorted(public)})
    print(f'Generated the single committed-seed set: {len(public)} realizations. Truth and heldout unrevealed.')


def directory(name,ids): return {rid:read(ART/name/f'{rid}.json') for rid in ids}


def seal():
    clean(); committed(ART/'commitment.json')
    c=read(ART/'commitment.json')
    verify_committed_source_state(ROOT,c['source_sha'],source_paths=SOURCE_FILES,artifact_label='Suite 1')
    inputs=directory('inputs',c['realization_ids'])
    if digest(inputs)!=c['inputs_sha256']: raise ValueError('inputs changed')
    results={}
    for rid,payload in inputs.items():
        path=ART/'selection'/f'{rid}.json'
        if path.exists(): raise ValueError('selection already exists; preserve prior attempt')
        results[rid]=staged_discovery(payload)
        write_new(path,results[rid])
    write_new(ART/'selection_seal.json',{'schema':'tnp-suite1/selection-seal-v1','commitment_commit_sha':git('rev-parse','HEAD'),
        'commitment_sha256':digest(c),'selection_sha256':digest(results),'sealed_at':now(),
        'oracle_revealed':False,'heldout_accessed':False,'realization_count':len(results)})
    print('All selections and adequacy/approximation decisions sealed. Commit before reveal.')


def check_bound_data(commitment,selection,outputs,oracle,heldout):
    if digest(commitment)!=selection['commitment_sha256']: raise ValueError('commitment changed')
    if digest(outputs)!=selection['selection_sha256']: raise ValueError('selection changed')
    if digest(oracle)!=commitment['oracle_sha256']: raise ValueError('oracle changed')
    if digest(heldout)!=commitment['heldout_sha256']: raise ValueError('heldout changed')


def boundary_controls(prereg,public,inputs,eligibility,outputs,oracle,heldout):
    checks={}
    checks['complete_ids']=set(public)==set(inputs)==set(eligibility)==set(outputs)==set(heldout)==set(oracle['realizations']) and len(public)==prereg['design']['total_realizations']
    checks['seed_stream_uniqueness']=len({v['child_seed'] for v in oracle['realizations'].values()})==len(public)
    checks['forward_receipts']=all(valid_receipt(o) for o in outputs.values())
    checks['source_inventory']=all(all(o['receipt']['inventory_before'][p]['sha256']==sha_file(ROOT/p) for p in ENGINE_FILES)
        and o['receipt']['worker_sha256']==hashlib.sha256(WORKER.encode()).hexdigest() for o in outputs.values())
    checks['payload_identity']=all(o['discovery']['input_sha256']==digest(inputs[rid]) for rid,o in outputs.items())
    checks['no_candidate_law_claim']=all(o['discovery']['structural_recovery_claim'] is False and
        all(c['evidence_class']=='GENERATED/FITTED CANDIDATE' and c['scientific_significance']=='not_assigned' for c in o['discovery']['ranking']) for o in outputs.values())
    # Independent scalar arithmetic verifies every stored fit/metric/rank, without invoking discovery.
    tolerance=prereg['scoring']['independent_metric_tolerance']; metrics=True
    for rid,o in outputs.items():
        raw=inputs[rid]; ranking=o['discovery']['ranking']
        for c in ranking:
            def residual(row):
                prediction=math.prod(row['features'][k]**float(p) for k,p in c['representative'].items())
                return math.log(row['target']/prediction)
            intercept=sum(residual(row) for row in raw['train'])/len(raw['train'])
            train=math.sqrt(sum((intercept-residual(row))**2 for row in raw['train'])/len(raw['train']))
            valid=math.sqrt(sum((intercept-residual(row))**2 for row in raw['validation'])/len(raw['validation']))
            complexity=sum(abs(float(p)) for p in c['expanded'].values())
            metrics &= all(abs(a-b)<=tolerance for a,b in [(intercept,c['log_coefficient']),
                (train,c['training_rmse']),(valid,c['validation_rmse']),(complexity,c['expanded_complexity']),
                (valid+raw['policy']['complexity_lambda']*complexity,c['rank_score'])])
        ordered=sorted(ranking,key=lambda c:(c['rank_score'],c['expanded_complexity'],c['class_id']))
        metrics &= [c['class_id'] for c in ranking]==[c['class_id'] for c in ordered] and [c['rank'] for c in ranking]==list(range(1,len(ranking)+1))
    checks['independent_all_candidate_arithmetic']=bool(metrics)
    checks['pre_score_eligibility']=all(prepare(raw)==(inputs[rid],eligibility[rid]) for rid,raw in public.items())
    return checks


def make_index(result):
    baseline=ROOT/'Experiments/SymbolicDiscovery/Benchmark0'
    def entry(path):
        value=read(path)
        return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha_file(path),'disposition':value['disposition']}
    return {'schema':'tnp-symbolic-discovery/disposition-routing-v1',
        'Benchmark0':{'raw_epoch':entry(baseline/'result.json'),'reconciliation':entry(baseline/'receipt_reconciliation.json'),
            'authoritative':'reconciliation','suite_aggregation':None,'independent_status':'accepted by Claude PR54 audit and user activation'},
        'BenchmarkSuite1':{'raw_epoch':entry(ART/'result.json'),'reconciliation':None,'authoritative':'raw_epoch',
            'suite_aggregation':{'path':REL+'/evaluation_summary.json','sha256':sha_file(ART/'evaluation_summary.json'),
                                 'disposition':result['disposition']},'independent_status':'pending'}}


def validate_index(index):
    expected={'Benchmark0','BenchmarkSuite1','schema'}
    if set(index)!=expected or index['schema']!='tnp-symbolic-discovery/disposition-routing-v1': raise ValueError('invalid disposition index')
    for name in ('Benchmark0','BenchmarkSuite1'):
        item=index[name]
        for route in ('raw_epoch','reconciliation','suite_aggregation'):
            info=item[route]
            if info is None: continue
            path=ROOT/info['path']
            if path.resolve().is_relative_to(ROOT) is False: raise ValueError('unsafe index path')
            value=read(path)
            if sha_file(path)!=info['sha256'] or value['disposition']!=info['disposition']: raise ValueError('stale disposition route')
        if item['authoritative'] not in ('raw_epoch','reconciliation') or item[item['authoritative']] is None: raise ValueError('missing authoritative route')
    if index['Benchmark0']['authoritative']!='reconciliation': raise ValueError('Benchmark0 must route to accepted reconciliation')
    if index['BenchmarkSuite1']['suite_aggregation']['disposition']!=index['BenchmarkSuite1'][index['BenchmarkSuite1']['authoritative']]['disposition']:
        raise ValueError('suite disposition mismatch')


def reveal():
    clean(); committed(ART/'selection_seal.json')
    c=read(ART/'commitment.json'); selection=read(ART/'selection_seal.json'); ids=c['realization_ids']
    outputs=directory('selection',ids)
    oracle,heldout=read(PRIVATE/'oracle.json'),read(PRIVATE/'heldout.json')
    check_bound_data(c,selection,outputs,oracle,heldout)
    if seed_digest(oracle['seed'])!=read(ART/'seed_commitment.json')['seed_sha256']: raise ValueError('seed reveal mismatch')
    prereg=read(ART/'preregistration.v1.json'); public=directory('public',ids); inputs=directory('inputs',ids); eligibility=read(ART/'eligibility.json')
    write_new(ART/'oracle_reveal.json',oracle)
    for rid,rows in heldout.items(): write_new(ART/'heldout'/f'{rid}.json',rows)
    evaluations={rid:evaluate_realization(prereg,public[rid],eligibility[rid],outputs[rid],oracle['realizations'][rid],heldout[rid]) for rid in ids}
    for rid,value in evaluations.items(): write_new(ART/'evaluation'/f'{rid}.json',value)
    controls=boundary_controls(prereg,public,inputs,eligibility,outputs,oracle,heldout)
    summary=aggregate(prereg,evaluations,all(controls.values()))
    write_new(ART/'boundary_controls.json',controls)
    write_new(ART/'evaluation_summary.json',summary)
    result={**summary,'schema':'tnp-suite1/raw-result-v1','source_sha':c['source_sha'],
        'selection_commit_sha':git('rev-parse','HEAD'),'selection_sha256':selection['selection_sha256'],
        'evaluation_sha256':digest(evaluations),'summary_sha256':digest(summary),'controls_sha256':digest(controls),'evaluated_at':now()}
    write_new(ART/'result.json',result)
    write_new(INDEX,make_index(result))
    print(summary['disposition']+' — provisional, independent review pending')


def history_presence():
    """Full reachable graph, cached subtree listings; no path-simplified ancestry."""
    history={}; trees={}
    for sha in git('rev-list','HEAD').splitlines():
        tree=git('ls-tree',sha,REL)
        if tree not in trees:
            trees[tree]=set(git('ls-tree','-r','--name-only',sha,REL).splitlines()) if tree else set()
        history[sha]=(git('show','-s','--format=%P',sha).split(),trees[tree])
    return history


def introduction(history,path):
    candidates=[sha for sha,(parents,files) in history.items() if path in files and
        not any(path in history[parent][1] for parent in parents)]
    if len(candidates)!=1: raise ValueError('nonunique introduction: '+path)
    return candidates[0]


def immutable(sha,paths):
    verify_committed_source_state(ROOT,sha,source_paths=paths,artifact_label='Suite1 immutable epoch')
    for descendant in git('rev-list',sha+'..HEAD').splitlines():
        relation=subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',sha,descendant],capture_output=True)
        if relation.returncode==1: continue
        if relation.returncode: raise ValueError('cannot establish artifact ancestry')
        if git('diff','--name-only',sha,descendant,'--',*paths): raise ValueError('intervening immutable artifact/source change')


def verify_chronology(c,selection,result):
    anchor=verify_freeze(); history=history_presence()
    stages=[anchor['freeze_sha'],c['source_sha'],c['seed_commit_sha'],selection['commitment_commit_sha'],result['selection_commit_sha'],
        introduction(history,REL+'/result.json')]
    for a,b in zip(stages,stages[1:]): ancestor(a,b)
    verify_seed(c['source_sha'],c['seed_commit_sha'])
    if introduction(history,REL+'/seed_commitment.json')!=stages[2] or introduction(history,REL+'/commitment.json')!=stages[3] or introduction(history,REL+'/selection_seal.json')!=stages[4]:
        raise ValueError('custody marker introduction mismatch')
    if c['seed_publication']!={'remote_ref':'refs/heads/'+BRANCH,'observed_sha':stages[2],'observed_before_generation':True}:
        raise ValueError('seed publication mismatch')
    source_intro=git('log','--diff-filter=A','--format=%H','--','Discovery/symbolic_suite_worlds.py').splitlines()
    if source_intro!=[c['source_sha']]: raise ValueError('generator introduction differs from source epoch')
    if datetime.fromisoformat(git('show','-s','--format=%cI',c['source_sha']))<=datetime.fromisoformat(anchor['created_at']):
        raise ValueError('source predates anchor')
    immutable(c['source_sha'],SOURCE_FILES)
    groups={sha:[] for sha in stages}
    for path in sorted(ART.rglob('*.json')):
        relative=path.relative_to(ROOT).as_posix()
        if path.name=='preregistration.v1.json': stage=stages[0]
        elif path.name in ('anchor.json','preflight.json'): stage=stages[1]
        elif path.name=='seed_commitment.json': stage=stages[2]
        elif path.name in ('commitment.json','eligibility.json') or '/public/' in relative or '/inputs/' in relative: stage=stages[3]
        elif path.name=='selection_seal.json' or '/selection/' in relative: stage=stages[4]
        elif path.name in ('oracle_reveal.json','result.json','boundary_controls.json','evaluation_summary.json') or '/heldout/' in relative or '/evaluation/' in relative: stage=stages[5]
        else: continue
        if introduction(history,relative)!=stage: raise ValueError('artifact in wrong custody stage: '+relative)
        groups[stage].append(relative)
    for sha,paths in groups.items():
        if paths: immutable(sha,paths)
    baseline_paths=['Experiments/SymbolicDiscovery/Benchmark0','Discovery/symbolic_benchmark.py',
        'Discovery/symbolic_benchmark_engine.py','Discovery/symbolic_benchmark_worlds.py',
        'Discovery/symbolic_benchmark_receipt.py','Notes/SymbolicBenchmark0.md']
    if git('diff','--name-only',anchor['base_sha'],'HEAD','--',*baseline_paths): raise ValueError('Benchmark0 historical bytes changed')
    return stages


def check(replay=False):
    c=read(ART/'commitment.json'); selection=read(ART/'selection_seal.json'); result=read(ART/'result.json'); ids=c['realization_ids']
    verify_chronology(c,selection,result)
    prereg=read(ART/'preregistration.v1.json'); public=directory('public',ids); inputs=directory('inputs',ids)
    outputs=directory('selection',ids); heldout=directory('heldout',ids); oracle=read(ART/'oracle_reveal.json'); eligibility=read(ART/'eligibility.json')
    check_bound_data(c,selection,outputs,oracle,heldout)
    if seed_digest(oracle['seed'])!=read(ART/'seed_commitment.json')['seed_sha256']: raise ValueError('seed digest mismatch')
    if c['seed_commitment_sha256']!=sha_file(ART/'seed_commitment.json'): raise ValueError('seed commitment hash mismatch')
    for key,value in [('public',public),('inputs',inputs),('eligibility',eligibility)]:
        if digest(value)!=c[key+'_sha256']: raise ValueError('data hash mismatch: '+key)
    if replay:
        from Discovery.symbolic_suite_worlds import generate
        regenerated=generate(prereg,oracle['seed'])
        if tuple(map(digest,regenerated))!=tuple(map(digest,(public,heldout,oracle))): raise ValueError('fixed-seed generation replay mismatch')
        for rid,payload in inputs.items():
            if staged_discovery(payload)!=outputs[rid]: raise ValueError('sealed selection replay mismatch: '+rid)
    evaluations={rid:evaluate_realization(prereg,public[rid],eligibility[rid],outputs[rid],oracle['realizations'][rid],heldout[rid]) for rid in ids}
    if evaluations!=directory('evaluation',ids): raise ValueError('evaluation differs from frozen criteria')
    controls=boundary_controls(prereg,public,inputs,eligibility,outputs,oracle,heldout)
    if controls!=read(ART/'boundary_controls.json'): raise ValueError('integrity controls stale')
    summary=aggregate(prereg,evaluations,all(controls.values()))
    if summary!=read(ART/'evaluation_summary.json'): raise ValueError('summary stale')
    if any(result[k]!=v for k,v in summary.items()) or result['evaluation_sha256']!=digest(evaluations) or result['summary_sha256']!=digest(summary) or result['controls_sha256']!=digest(controls): raise ValueError('raw result binding mismatch')
    validate_index(read(INDEX))
    if read(INDEX)!=make_index(result): raise ValueError('disposition index does not cover authoritative files')
    # FH-19 forward live semantics, using outcome-independent fixture only.
    from tests.test_symbolic_suite import fixture
    live=staged_discovery(fixture())
    stale=staged_discovery(fixture(),stale_cache=True,enforce=False)
    cache='<stage>/Discovery/__pycache__/symbolic_suite_engine.cpython-312.pyc'
    if not valid_receipt(live) or valid_receipt(stale) or cache not in stale['receipt']['successful_reads'] or cache in stale['receipt']['expected_missing_cache_attempts']:
        raise ValueError('live cache semantic probe failed')
    print(summary['disposition']+'; immutable chronology, seed, receipts, routing and evaluation verified'+('; fixed-epoch replay matched' if replay else ''))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',nargs='?',choices=('seed','realize','seal','reveal'))
    parser.add_argument('--check',action='store_true'); parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    if args.check: check(replay=args.replay); return
    if not args.stage: parser.error('stage or --check required')
    try: {'seed':seed,'realize':realize,'seal':seal,'reveal':reveal}[args.stage]()
    except Exception as error:
        failure={'stage':args.stage,'head_sha':git('rev-parse','HEAD'),'recorded_at':now(),
            'error':type(error).__name__+': '+str(error),'traceback':traceback.format_exc(),
            'receipt':error.output if isinstance(error,RunnerFailure) else None,
            'disposition':'BENCHMARK_SUITE_1_NO_GO_CAPABILITY','scientific_interpretation':'Operational failure; preserve partial artifacts and fixed seed. No retry or scientific tuning implied.'}
        path=ART/'operational_failures'/(args.stage+'-'+failure['head_sha']+'.json')
        if not path.exists(): write_new(path,failure)
        raise


if __name__=='__main__': main()
