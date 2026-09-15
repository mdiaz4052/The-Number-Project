"""Detached operational correction for Suite 1's post-result routing failure.

The frozen writer assumed every disposition key was named 'disposition'.
Benchmark 0's accepted reconciliation uses 'final_disposition'. No old source,
result, criterion, candidate, seed, coefficient or data is changed. Verification
below delegates numerical evaluation to exactly the frozen implementations.
"""
import argparse
import hashlib
from pathlib import Path

from Discovery import symbolic_suite as raw
from Discovery.symbolic_benchmark_engine import digest
from Discovery.source_history import verify_committed_source_state

RAW_EPOCH='d5a6845816f8183902ed68f6060becc1f58d8526'
CORRECTION_SOURCES=('Discovery/symbolic_suite_routing.py','tests/test_symbolic_suite_routing.py')
RECONCILIATION=raw.ART/'routing_reconciliation.json'
B0=raw.ROOT/'Experiments/SymbolicDiscovery/Benchmark0'
FAILURE=raw.ART/'operational_failures/reveal-55c2783a20edfa2208094129f3c5efa6cf6247cc.json'


def route(path,key,source_commit,binding_kind="artifact_state"):
    value=raw.read(path)
    if key not in ('disposition','final_disposition') or not isinstance(value.get(key),str):
        raise ValueError('explicit disposition key missing')
    return {'path':Path(path).relative_to(raw.ROOT).as_posix(),'sha256':raw.sha_file(path),
        'disposition_key':key,'disposition':value[key],'source_commit_sha':source_commit,'binding_kind':binding_kind}


def index(reconciliation_commit):
    return {'schema':'tnp-symbolic-discovery/disposition-routing-v2',
        'Benchmark0':{
            'raw_epoch':route(B0/'result.json','disposition','b01c01af1a30bbf8726842d3b05905a350cd5c1f'),
            'reconciliation':route(B0/'receipt_reconciliation.json','final_disposition','a1016953d5289dd9eca211c8b736d8d08f1a6153'),
            'authoritative':'reconciliation','suite_aggregation':None,'operational_failures':[],
            'independent_status':'accepted by Claude PR54 audit and user activation'},
        'BenchmarkSuite1':{
            'raw_epoch':route(raw.ART/'result.json','disposition',RAW_EPOCH),
            'reconciliation':route(RECONCILIATION,'disposition',reconciliation_commit,'record_producer_source'),
            'authoritative':'reconciliation',
            'suite_aggregation':route(raw.ART/'evaluation_summary.json','disposition',RAW_EPOCH),
            'operational_failures':[route(FAILURE,'disposition',RAW_EPOCH)],
            'independent_status':'PROVISIONAL — INDEPENDENT AUDIT PENDING'}}


def validate_index(value):
    if value.get('schema')!='tnp-symbolic-discovery/disposition-routing-v2' or set(value)!={'schema','Benchmark0','BenchmarkSuite1'}:
        raise ValueError('unsupported disposition routing schema')
    for name in ('Benchmark0','BenchmarkSuite1'):
        record=value[name]
        if record['authoritative']!='reconciliation' or record['reconciliation'] is None:
            raise ValueError('accepted disposition must route through reconciliation')
        for item in [record['raw_epoch'],record['reconciliation'],record['suite_aggregation'],*record['operational_failures']]:
            if item is None: continue
            path=raw.ROOT/item['path']
            if not path.resolve().is_relative_to(raw.ROOT): raise ValueError('unsafe routing path')
            actual=route(path,item['disposition_key'],item['source_commit_sha'],item['binding_kind'])
            if actual!=item: raise ValueError('stale disposition route')
            # Current correction artifact is bound by its separately recorded source
            # and unique introduction, checked below. Historical files must exist
            # with these exact bytes at their explicit immutable source commit.
            if path!=RECONCILIATION:
                if item['binding_kind']!='artifact_state': raise ValueError('historical artifact pin required')
                raw.committed(path,item['source_commit_sha'])
            elif item['binding_kind']!='record_producer_source' or item['source_commit_sha']!=raw.read(path)['correction_source_sha']:
                raise ValueError('reconciliation producer pin mismatch')
        if record['suite_aggregation'] and record['suite_aggregation']['disposition']!=record['reconciliation']['disposition']:
            raise ValueError('suite/reconciliation mismatch')
    if value['Benchmark0']['raw_epoch']['disposition']!='BENCHMARK_0_FAIL' or value['Benchmark0']['reconciliation']['disposition_key']!='final_disposition' or value['Benchmark0']['reconciliation']['disposition']!='BENCHMARK_0_PASS':
        raise ValueError('historical Benchmark0 distinction lost')


def verify_raw_science():
    """Read-only re-derivation through frozen functions; no generation/discovery."""
    c=raw.read(raw.ART/'commitment.json'); seal=raw.read(raw.ART/'selection_seal.json'); result=raw.read(raw.ART/'result.json')
    stages=raw.verify_chronology(c,seal,result)
    if stages[-1]!=RAW_EPOCH: raise ValueError('raw epoch identity changed')
    ids=c['realization_ids']; prereg=raw.read(raw.ART/'preregistration.v1.json')
    public=raw.directory('public',ids); inputs=raw.directory('inputs',ids)
    outputs=raw.directory('selection',ids); heldout=raw.directory('heldout',ids)
    oracle=raw.read(raw.ART/'oracle_reveal.json'); eligibility=raw.read(raw.ART/'eligibility.json')
    raw.check_bound_data(c,seal,outputs,oracle,heldout)
    if raw.seed_digest(oracle['seed'])!=raw.read(raw.ART/'seed_commitment.json')['seed_sha256'] or c['seed_commitment_sha256']!=raw.sha_file(raw.ART/'seed_commitment.json'):
        raise ValueError('seed binding mismatch')
    for key,value in [('public',public),('inputs',inputs),('eligibility',eligibility)]:
        if digest(value)!=c[key+'_sha256']: raise ValueError('data binding mismatch')
    evaluations={rid:raw.evaluate_realization(prereg,public[rid],eligibility[rid],outputs[rid],oracle['realizations'][rid],heldout[rid]) for rid in ids}
    controls=raw.boundary_controls(prereg,public,inputs,eligibility,outputs,oracle,heldout)
    summary=raw.aggregate(prereg,evaluations,all(controls.values()))
    if evaluations!=raw.directory('evaluation',ids) or controls!=raw.read(raw.ART/'boundary_controls.json') or summary!=raw.read(raw.ART/'evaluation_summary.json'):
        raise ValueError('frozen scientific evaluation mismatch')
    if any(result[k]!=v for k,v in summary.items()) or result['evaluation_sha256']!=digest(evaluations) or result['summary_sha256']!=digest(summary) or result['controls_sha256']!=digest(controls):
        raise ValueError('raw result binding mismatch')
    return result


def assess():
    result=verify_raw_science()
    raw.committed(FAILURE,RAW_EPOCH)
    failure=raw.read(FAILURE)
    if failure['stage']!='reveal' or failure['error']!="KeyError: 'disposition'" or failure['head_sha']!=result['selection_commit_sha'] or failure['disposition']!='BENCHMARK_SUITE_1_NO_GO_CAPABILITY':
        raise ValueError('correction does not match preserved routing failure')
    if not result['integrity_controls_pass']: raise ValueError('routing correction cannot excuse scientific integrity failure')
    if 'make_index(result)' not in failure['traceback'] or "value['disposition']" not in failure['traceback']:
        raise ValueError('failure is outside the narrow known schema mismatch')
    raw_paths=raw.git('ls-tree','-r','--name-only',RAW_EPOCH,raw.REL).splitlines()
    raw.immutable(RAW_EPOCH,raw_paths)
    return {'schema':'tnp-suite1/routing-reconciliation-v1','disposition':result['disposition'],
        'raw_epoch_sha':RAW_EPOCH,'raw_disposition':result['disposition'],
        'preserved_operational_disposition':failure['disposition'],
        'correction_class':'post-result export/disposition-key adapter only',
        'cause':"Benchmark0 receipt_reconciliation.json stores final_disposition; frozen writer requested disposition.",
        'raw_record_sha256':{p:raw.sha_file(raw.ROOT/p) for p in raw_paths},
        'scientific_results_changed':False,'criteria_changed':False,'new_seed_or_selection':False,
        'scientific_law_claim':False,'review_status':'PROVISIONAL — INDEPENDENT AUDIT PENDING'}


def reconcile():
    raw.clean()
    source=raw.git('rev-parse','HEAD')
    for p in CORRECTION_SOURCES: raw.committed(raw.ROOT/p)
    result=assess(); result['correction_source_sha']=source
    raw.write_new(RECONCILIATION,result)
    # Source commit identifies the record-producing code, not the yet-unknown
    # introduction commit; check() binds the introduction independently.
    raw.write_new(raw.INDEX,index(source))
    print(result['disposition']+'; routing corrected; raw PASS and operational NO_GO preserved unchanged')


def check(replay=False):
    saved=raw.read(RECONCILIATION); source=saved['correction_source_sha']
    verify_committed_source_state(raw.ROOT,source,source_paths=CORRECTION_SOURCES,artifact_label='Suite1 routing correction')
    raw.ancestor(RAW_EPOCH,source); raw.immutable(source,CORRECTION_SOURCES)
    actual=assess(); actual['correction_source_sha']=source
    if actual!=saved: raise ValueError('reconciliation differs from raw evidence')
    history=raw.history_presence(); intro=raw.introduction(history,raw.REL+'/routing_reconciliation.json')
    raw.ancestor(source,intro)
    raw.immutable(intro,[raw.REL+'/routing_reconciliation.json',raw.INDEX.relative_to(raw.ROOT).as_posix()])
    expected=index(source); value=raw.read(raw.INDEX)
    validate_index(value)
    if value!=expected: raise ValueError('incomplete/ambiguous disposition routing')
    if replay:
        # Explicit fixed-epoch reproducibility, never another seed or selection.
        from Discovery.symbolic_suite_worlds import generate
        c=raw.read(raw.ART/'commitment.json'); ids=c['realization_ids']
        oracle=raw.read(raw.ART/'oracle_reveal.json'); public=raw.directory('public',ids); heldout=raw.directory('heldout',ids)
        regenerated=generate(raw.read(raw.ART/'preregistration.v1.json'),oracle['seed'])
        if tuple(map(digest,regenerated))!=tuple(map(digest,(public,heldout,oracle))): raise ValueError('fixed-epoch generation replay mismatch')
        outputs=raw.directory('selection',ids)
        for rid,payload in raw.directory('inputs',ids).items():
            if raw.staged_discovery(payload)!=outputs[rid]: raise ValueError('fixed selection replay mismatch: '+rid)
    from tests.test_symbolic_suite import fixture
    live=raw.staged_discovery(fixture()); stale=raw.staged_discovery(fixture(),stale_cache=True,enforce=False)
    cache='<stage>/Discovery/__pycache__/symbolic_suite_engine.cpython-312.pyc'
    if not raw.valid_receipt(live) or raw.valid_receipt(stale) or cache not in stale['receipt']['successful_reads'] or cache in stale['receipt']['expected_missing_cache_attempts']:
        raise ValueError('forward live semantic probe failed')
    print(saved['disposition']+'; frozen science, chronology, raw failure and explicit-key routing verified'+('; same-epoch replay matched' if replay else ''))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reconcile',action='store_true'); parser.add_argument('--check',action='store_true'); parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    if args.reconcile: reconcile()
    elif args.check: check(replay=args.replay)
    else: parser.error('--reconcile or --check required')
