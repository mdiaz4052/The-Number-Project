"""Read-only evidence authority for Adapter 2's reached isolation NO_GO.

No engine import, environment installation, native replay, file emission or
network access. This is a stage-specific archive verifier, not an adapter.
Shared living source is not frozen by this guard; provenance uses git objects.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REL = 'Experiments/SymbolicDiscovery/PySRAdapter2'
PKG = ROOT / REL
NS = 'tnp-pysr-adapter/2'
WORK_SHA = 'd6866c119695f40caefd576a8bd0c20acfd7a2441639b8933ed0d273edc73b39'
RUNTIME_SHA = '1c637ce5d5bab28092abb4987ba34071b2406052'
DIAG_SHA = 'ffb1e46c747814c1620d84ee8c3e6e2c59e566e7'
RECOVERY_SHA = 'e6eff4622f0f02c638f31d76c1b6257ba62afec5'
SOURCES = ('Discovery/pysr_adapter2_runtime.py',
           'Discovery/pysr_adapter2_prerequisites.py',
           'Discovery/pysr_adapter2_recovery.py',
           'Discovery/pysr_adapter2_verifier.py',
           'tests/test_pysr_adapter2.py')
STEP_FIELDS = {'schema','epoch','step','source_sha','source_sha256','command',
    'environment','cwd','identity','executable_sha256','started_at','finished_at',
    'elapsed_seconds','deadline_seconds','returncode','signal','termination',
    'capture','stdout_sha256','stderr_sha256'}
STOP_FIELDS = {'schema','observed_at','source_sha','epoch','failed_step','reason',
    'recovery','runtime_layers','activity','unperformed','evidence_inventory'}
HOST_FIELDS = {'schema','observed_at','python','platform','machine','libc','uid',
    'gid','storage','limits','isolation','relevant_environment'}
RESULT_FIELDS = {'schema','task','disposition','evidence_integrity','adapter_conformance',
    'operational_acceptance','review_status','outcome_blind','search_coverage',
    'scientific_evidence','stage','setup','planned_runs','evidence','limitations',
    'source_snapshot_digest'}
PLAN_FIELDS = {'schema','recorded_at','epoch','setup_epochs_total_cap',
    'recovery_used_if_launched','prior_stop_sha256','prior_diagnostic_sha256',
    'observed_failure','changed_condition','basis','upstream_reference','source_statement',
    'recovery_order_assessment','prior_stop_interpretation','deadline_seconds',
    'epoch_budget_seconds','if_failure'}
E1 = {'host.json','initial-controller-tool-output.txt','initial-retention.md',
      'namespace-capability.json','namespace-capability.stdout',
      'namespace-capability.stderr','stop.json'}
E2 = {'namespace-shared-network.json','namespace-shared-network.stdout',
      'namespace-shared-network.stderr','stop.json'}
SETUP_PATHS = ({'epoch-01/'+p for p in E1} | {'epoch-02/'+p for p in E2}
               | {'recovery_plan.json'})
ENV = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
IDENTITY = {'uid':0,'gid':0,'groups':[],'no_new_privileges':True,
            'restriction_mode':'controller_only_trusted_system_capability_probe'}
ACTIVITY = {'master_seed_created':False,'target_rows_created':0,'smoke_fits_executed':0,
            'target_fits_executed':0,'cards_issued':0,'selections_sealed':0,'heldout_evaluations':0}
UNPERFORMED = {x:'NOT_EXECUTED' for x in ('integration','fixtures','mutations',
    'native_export','seed','data','target_fits','selections','heldout')}
LAYERS = {x:'NOT_EXECUTED' for x in ('standalone','python_child','pinned_dependencies','cold_bridge')}
PROMOTION = {x:'NOT_ASSESSED' for x in ('structural_recovery','empirical_support',
    'significance','formal_proof','independent_replication','family_adequacy')}
LIMITATIONS = [
    'The host could not establish the required credential/staged-file worker isolation; no external engine executed.',
    'The first controller traceback is a complete attributed execution-tool return, not separately captured original OS stdout/stderr. The controller failed before launching any child.',
    'Both namespace child probes have full file-captured stdout/stderr, source bindings and deadline receipts.',
    'Epoch 1 preliminary no-remedy assessment is retained unchanged; the pre-recorded single recovery supersedes that assessment, not its failed evidence.',
    'No Julia download, checksum authentication, extraction, startup, bridge, dependency lock, PySR fit or native export was performed in this package.',
    'No real adapter, trusted card path, integration fixtures, eight adapter mutations, target data, selection or held-out evaluation was delivered.',
    'The old Julia SIGBUS cause remains unknown. This isolation failure is not evidence against PySR or Julia correctness.',
    'Offline verification checks retained source-bound records, not host replay or arbitrary operator truthfulness.',
    'DM-098 coverage is limited to this reached negative route. DM-099 is unexercised; no finding ID is closed.',
    'No physical-memory cap, successful worker sandbox or network isolation is claimed. No host controls or Drive sharing were changed.',
]


class EvidenceError(ValueError):
    pass


def need(value, code, message):
    if not value:
        raise EvidenceError(code + ': ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode()


def digest(obj):
    return sha(encoded(obj))


def fields(obj, names):
    need(type(obj) is dict and set(obj)==set(names),'SCHEMA','Missing or extra fields')


def loads(raw):
    need(type(raw) is bytes and len(raw)<=1048576,'SIZE','Bounded exact UTF-8 input required')
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'DUPLICATE_KEY',k)
            out[k]=v
        return out
    def bad_constant(value):
        raise EvidenceError('NONFINITE: '+value)
    try:
        obj=json.loads(raw.decode(),object_pairs_hook=pairs,parse_constant=bad_constant)
    except (UnicodeError,ValueError,RecursionError) as e:
        if isinstance(e,EvidenceError):raise
        raise EvidenceError('JSON: invalid bounded record') from e
    stack=[(obj,0)];count=0
    while stack:
        v,d=stack.pop();count+=1
        need(d<=64 and count<=100000,'SIZE','Record exceeds bounds')
        if type(v) is dict:stack.extend((x,d+1) for x in v.values())
        elif type(v) is list:stack.extend((x,d+1) for x in v)
        elif type(v) is float:need(math.isfinite(v),'NONFINITE','Nonfinite record number')
    return obj


def stamp(value):
    need(type(value) is str,'CHRONOLOGY','Timestamp string required')
    try:t=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as e:raise EvidenceError('CHRONOLOGY: invalid timestamp') from e
    need(t.tzinfo is not None,'CHRONOLOGY','Timezone required')
    return t


def hexhash(s):
    return type(s) is str and re.fullmatch('[0-9a-f]{64}',s) is not None


def same(obj, expected, code):
    # Canonical JSON comparison avoids Python bool/int equality masquerading.
    need(encoded(obj)==encoded(expected),code,'Record disagrees with derived contract')


def command(epoch):
    task='/tmp/tnp-pysr-adapter2-e0'+str(epoch)
    args=['/usr/bin/bwrap','--unshare-all']+(['--share-net'] if epoch==2 else [])
    args+=['--die-with-parent','--new-session']
    for p in ('/usr','/bin','/lib','/lib64'):args+=['--ro-bind',p,p]
    return args+['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--bind',task,task,
                 '--chdir',task,'--','/usr/bin/true']


def validate_setup(raw, anchor):
    need(type(raw) is dict and set(raw)==SETUP_PATHS,'INVENTORY','Exact reached setup inventory required')
    need(all(type(v) is bytes for v in raw.values()),'TYPE','Exact evidence bytes required')
    need(sum(map(len,raw.values()))<1024**3,'SIZE','Package evidence cap')
    get=lambda p:loads(raw[p])
    host=get('epoch-01/host.json');fields(host,HOST_FIELDS)
    need(host['schema']==NS+'/host','SCHEMA','Wrong host schema')
    same(host['python']['implementation'],'cpython','ENVIRONMENT')
    need(host['python']['version']=='3.12.14' and hexhash(host['python']['sha256']),
         'ENVIRONMENT','Observed Python identity changed')
    need(host['machine']['process']==host['machine']['hardware']=='x86_64'
         and host['libc'][0]=='glibc','ENVIRONMENT','Wrong recorded platform')
    same(host['uid'],0,'ISOLATION');same(host['gid'],0,'ISOLATION')
    iso=host['isolation']
    for k in ('uid_map','gid_map'):
        need(iso[k].split()==['0','0','1'],'ISOLATION','Single mapped identity evidence missing')
    ps=iso['process_status']
    need(all(ps[x]=='0000000000000000' for x in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb'))
         and ps['NoNewPrivs']=='1' and ps['Seccomp']=='2','ISOLATION','Recorded host restrictions changed')
    need(iso['credential_separation']==iso['network_isolation']=='NOT_ESTABLISHED'
         and iso['task_mode']=='0o700','ISOLATION','Unsupported isolation claim')
    same(host['relevant_environment'],{'child_allowlist':ENV,'controller_values_copied':False},'ISOLATION')
    same(host['limits']['native_children_executed'],0,'UNPERFORMED')
    same(host['limits']['memory_cap_enforced'],False,'ISOLATION')
    need(stamp(anchor['created_at'])<stamp(host['storage']['task_created_at'])
         <=stamp(host['observed_at']),'CHRONOLOGY','Setup predates anchor')
    text=raw['epoch-01/initial-controller-tool-output.txt'].decode()
    need('os.chown(task, WORK_UID, WORK_GID)' in text and
         "OSError: [Errno 22] Invalid argument: '/tmp/tnp-pysr-adapter2-e01'" in text,
         'FAILURE_ROUTE','Initial controller failure absent')
    retention=raw['epoch-01/initial-retention.md'].decode()
    need('Original separate OS stdout/stderr files do not exist' in retention
         and 'not truncated' in retention and 'before creating its evidence directory' in retention,
         'RETENTION','Initial capture limitation erased')
    records=[];stops=[]
    for epoch,step,expected_source,diagnostic in [
        (1,'namespace-capability',DIAG_SHA,
         b'bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted\n'),
        (2,'namespace-shared-network',RECOVERY_SHA,
         b'bwrap: setting up uid map: Operation not permitted\n')]:
        prefix=f'epoch-{epoch:02d}/';record=get(prefix+step+'.json');fields(record,STEP_FIELDS)
        need(record['schema']==NS+'/setup-step' and record['source_sha']==expected_source
             and record['step']==step,'SOURCE_PIN','Wrong stage/source')
        same(record['epoch'],epoch,'RETRY');same(record['command'],command(epoch),'ISOLATION')
        same(record['environment'],ENV,'ISOLATION');same(record['identity'],IDENTITY,'ISOLATION')
        need(record['cwd']==f'/tmp/tnp-pysr-adapter2-e0{epoch}','ISOLATION','Wrong staged directory')
        need(hexhash(record['source_sha256']) and hexhash(record['executable_sha256']),
             'SOURCE_PIN','Missing executable/source identity')
        need(stamp(anchor['created_at'])<stamp(record['started_at'])<=stamp(record['finished_at']),
             'CHRONOLOGY','Invalid child chronology')
        need(type(record['elapsed_seconds']) in (int,float) and not isinstance(record['elapsed_seconds'],bool)
             and 0<=record['elapsed_seconds']<=120,'BUDGET','Minimal probe deadline exceeded')
        same(record['deadline_seconds'],120,'BUDGET')
        same(record['returncode'],1,'FAILURE_ROUTE');same(record['signal'],None,'FAILURE_ROUTE')
        need(record['termination']=='EXIT','FAILURE_ROUTE','Expected completed prerequisite refusal')
        capture=record['capture'];fields(capture,{'status','stdout_bytes','stderr_bytes','total_log_limit_bytes'})
        same(capture['total_log_limit_bytes'],256*1024**2,'CAPTURE')
        need(capture['status']=='COMPLETE','CAPTURE','Incomplete child capture cannot be promoted')
        for suffix in ('stdout','stderr'):
            b=raw[prefix+step+'.'+suffix]
            need(sha(b)==record[suffix+'_sha256'],'RAW_BINDING','Changed diagnostic bytes')
            same(capture[suffix+'_bytes'],len(b),'CAPTURE')
        need(raw[prefix+step+'.stdout']==b'' and raw[prefix+step+'.stderr']==diagnostic,
             'FAILURE_ROUTE','Different failure is not this archived diagnosis')
        stop=get(prefix+'stop.json');fields(stop,STOP_FIELDS)
        need(stop['schema']==NS+'/setup-stop' and stop['source_sha']==record['source_sha'],
             'SOURCE_PIN','Stop belongs to another epoch')
        same(stop['epoch'],epoch,'RETRY')
        need(stamp(record['finished_at'])<=stamp(stop['observed_at']),
             'CHRONOLOGY','Stop precedes child')
        same(stop['activity'],ACTIVITY,'UNPERFORMED');same(stop['unperformed'],UNPERFORMED,'UNPERFORMED')
        same(stop['runtime_layers'],LAYERS,'UNPERFORMED')
        rec=stop['recovery'];fields(rec,{'budget','used','rationale','changed_conditions','prior_failure'})
        same(rec['budget'],1,'RETRY');same(rec['used'],epoch-1,'RETRY')
        expected_inventory={name[len(prefix):]:{'bytes':len(b),'sha256':sha(b)}
             for name,b in raw.items() if name.startswith(prefix) and name!=prefix+'stop.json'}
        same(stop['evidence_inventory'],expected_inventory,'INVENTORY')
        records.append(record);stops.append(stop)
    need(records[0]['executable_sha256']==records[1]['executable_sha256'],
         'IDENTITY','Recovery changed the namespace executable')
    need(stops[0]['failed_step']=='worker-isolation-prerequisite'
         and stops[0]['reason']=='DISTINCT_UID_UNMAPPED_AND_UNPRIVILEGED_NAMESPACE_UNAVAILABLE'
         and stops[1]['failed_step']=='namespace-shared-network'
         and stops[1]['reason']=='WORKER_ISOLATION_RECOVERY_FAILED','FAILURE_ROUTE','Stop reason changed')
    same(stops[0]['recovery']['changed_conditions'],[],'RETRY')
    same(stops[1]['recovery']['changed_conditions'],
         ['--share-net retains the existing restricted host network'],'RETRY')
    plan=get('recovery_plan.json');fields(plan,PLAN_FIELDS)
    need(plan['schema']==NS+'/recovery-plan','SCHEMA','Unknown recovery plan')
    for k,v in [('epoch',2),('setup_epochs_total_cap',2),('recovery_used_if_launched',1),
                ('deadline_seconds',120),('epoch_budget_seconds',1200)]:same(plan[k],v,'RETRY')
    need(plan['prior_stop_sha256']==sha(raw['epoch-01/stop.json'])
         and plan['prior_diagnostic_sha256']==sha(raw['epoch-01/namespace-capability.stderr']),
         'RETRY','Recovery not bound to retained failure')
    need(stamp(stops[0]['observed_at'])<=stamp(plan['recorded_at'])<stamp(records[1]['started_at']),
         'CHRONOLOGY','Recovery was not pre-recorded')
    need('--share-net' in plan['changed_condition'] and 'No package result exists yet' in plan['prior_stop_interpretation'],
         'RETRY','Recovery condition or prior assessment retention missing')
    return {'adapter_conformance':'NO_GO','evidence_integrity':'PASS',
        'disposition':'PYSR_ADAPTER_2_NO_GO','operational_acceptance':False,
        'failure_reason':stops[1]['reason'],'failed_step':stops[1]['failed_step'],
        'setup_epochs':2,'recovery_used':1,'completed_layers':[],
        'failures':[{'epoch':s['epoch'],'failed_step':s['failed_step'],'reason':s['reason']} for s in stops]}


def expected_runtime(raw,anchor):
    facts=validate_setup(raw,anchor)
    return {'schema':NS+'/runtime-qualification','state':'NO_GO','source_sha':RECOVERY_SHA,
        'environment_digest':sha(raw['epoch-01/host.json']),'setup_epochs':2,
        'completed_layers':[],'failures':facts['failures'],'limitations':LIMITATIONS}


def expected_report(raw,anchor,snapshot):
    facts=validate_setup(raw,anchor)
    return {'schema':NS+'/result','task':'NP-PYSR-ADAPTER-02',
        **{k:facts[k] for k in ('disposition','evidence_integrity','adapter_conformance','operational_acceptance')},
        'review_status':'PROVISIONAL — INDEPENDENT AUDIT PENDING','outcome_blind':False,
        'search_coverage':'NOT_ESTABLISHED','scientific_evidence':PROMOTION,
        'stage':'runtime_prerequisite',
        'setup':{'runtime_qualification':'NO_GO','integration_qualification':'NOT_EXECUTED',
            **{k:facts[k] for k in ('setup_epochs','failed_step','failure_reason','recovery_used')},
            'limitations':LIMITATIONS[:4]},
        'planned_runs':[{'run_id':f'r{i:02d}','state':'NOT_EXECUTED','fit_invocations':0,
            'reason':'worker_isolation_prerequisite_failed_before_native_execution'} for i in range(1,5)],
        'evidence':{'setup_inventory_digest':digest({p:sha(b) for p,b in sorted(raw.items())}),
            'native_output_inventory':[],'adapter_parity':'NOT_EXECUTED',
            'dimensional_domain_provenance_checks':'NOT_EXECUTED',
            'validation_diagnostics':[],'heldout_diagnostics':[],'fixtures':'NOT_EXECUTED',
            'mutations':'NOT_EXECUTED','raw_bindings':{p:sha(b) for p,b in sorted(raw.items())}},
        'limitations':LIMITATIONS,'source_snapshot_digest':digest(snapshot)}


def validate_report(report,raw,anchor,snapshot):
    fields(report,RESULT_FIELDS)
    same(report,expected_report(raw,anchor,snapshot),'DISPOSITION')
    return report['disposition']


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()


def blob(commit,path):
    return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)


def ancestor(a,b):
    need(subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=ROOT,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,
        'CHRONOLOGY','Required true-merge ancestry lost')


def commit_time(commit):
    return datetime.fromtimestamp(int(git('show','-s','--format=%ct',commit)),timezone.utc)


def read(name):return loads((PKG/name).read_bytes())


def setup_bytes():
    out={str(p.relative_to(PKG/'setup')):p.read_bytes() for p in (PKG/'setup').rglob('*') if p.is_file()}
    need(set(out)==SETUP_PATHS,'INVENTORY','Missing/extra setup evidence')
    return out


def check():
    need(sys.implementation.name=='cpython' and sys.version_info[:2]==(3,12),
         'ENVIRONMENT','Use CPython 3.12; no native dependency needed')
    anchor=read('anchor.json');snapshot=read('source_snapshot.json');seal=read('evidence_seal.json')
    fields(anchor,{'schema','base_sha','snapshot_sha','freeze_sha','pr','url','created_at'})
    need(anchor['schema']==NS+'/anchor' and anchor['pr']==60,'CHRONOLOGY','Wrong draft anchor')
    fields(snapshot,{'schema','source_sha','files','accepted_source_sha','accepted_files'})
    need(snapshot['schema']==NS+'/source-snapshot' and set(snapshot['files'])==set(SOURCES),
         'SOURCE_PIN','Wrong source inventory')
    same(snapshot['accepted_files'],{},'SOURCE_PIN')
    need(snapshot['accepted_source_sha']==anchor['base_sha'],'SOURCE_PIN','Wrong unchanged baseline')
    fields(seal,{'schema','evidence_sha','files'})
    need(snapshot['source_sha']!=seal['evidence_sha'],'CHRONOLOGY','Sources must precede result')
    for path,h in snapshot['files'].items():
        need(hexhash(h) and sha(blob(snapshot['source_sha'],path))==h,
             'SOURCE_PIN','Pinned committed source mismatch: '+path)
    chain=[anchor['base_sha'],anchor['snapshot_sha'],anchor['freeze_sha'],RUNTIME_SHA,
           DIAG_SHA,RECOVERY_SHA,snapshot['source_sha'],seal['evidence_sha'],'HEAD']
    for a,b in zip(chain,chain[1:]):ancestor(a,b)
    need(git('rev-parse',anchor['snapshot_sha']+'^')==anchor['base_sha']
         and git('rev-parse',anchor['freeze_sha']+'^')==anchor['snapshot_sha'],
         'CHRONOLOGY','Snapshot/freeze parent changed')
    need(git('show','--pretty=','--name-only',anchor['freeze_sha'])==REL+'/contract.v1.md',
         'CHRONOLOGY','Freeze must introduce only the contract')
    need(commit_time(anchor['freeze_sha'])<=stamp(anchor['created_at'])<commit_time(RUNTIME_SHA),
         'CHRONOLOGY','Source did not follow actual draft anchor')
    work=(PKG/'work_order.r1.md').read_bytes();receipt=read('work_order_receipt.json')
    need(len(work)==81176 and sha(work)==WORK_SHA==receipt['sha256'],
         'WORK_ORDER','Consumed bytes changed')
    need(work==blob(anchor['snapshot_sha'],REL+'/work_order.r1.md')
         and (PKG/'contract.v1.md').read_bytes()==blob(anchor['freeze_sha'],REL+'/contract.v1.md'),
         'CHRONOLOGY','Frozen evidence changed')
    fields(seal,{'schema','evidence_sha','files'})
    need(seal['schema']==NS+'/evidence-seal','SCHEMA','Wrong seal')
    paths={str(p.relative_to(ROOT)) for p in PKG.rglob('*') if p.is_file()}
    expected=paths-{REL+'/evidence_seal.json'}
    need(set(seal['files'])==expected,'INVENTORY','Sealed package inventory changed')
    for path,h in seal['files'].items():
        need(hexhash(h) and sha((ROOT/path).read_bytes())==h
             and (ROOT/path).read_bytes()==blob(seal['evidence_sha'],path),
             'EVIDENCE_BINDING','Sealed package bytes changed: '+path)
    need(git('log','--format=%H','--diff-filter=A','--',REL+'/result.json')==seal['evidence_sha'],
         'CHRONOLOGY','Result creation commit changed')
    # Only this package's actual epoch diff is additive. No live shared-source freeze.
    changes=git('diff','--name-status',anchor['base_sha'],seal['evidence_sha']).splitlines()
    for line in changes:
        status,path=line.split('\t',1)
        need(status=='A' and (path.startswith(REL+'/') or path in SOURCES or path=='Notes/PySRAdapter2.md'),
             'IMMUTABILITY','Existing/unrelated surface altered during package')
    raw=setup_bytes();validate_setup(raw,anchor)
    for epoch,step,source_path in [(1,'namespace-capability',SOURCES[1]),
                                    (2,'namespace-shared-network',SOURCES[2])]:
        rec=loads(raw[f'epoch-{epoch:02d}/{step}.json'])
        need(sha(blob(rec['source_sha'],source_path))==rec['source_sha256'],
             'SOURCE_PIN','Executed diagnostic source mismatch')
        need(commit_time(rec['source_sha'])<stamp(rec['started_at']),
             'CHRONOLOGY','Diagnostic execution predates source')
    host=loads(raw['epoch-01/host.json'])
    need(commit_time(RUNTIME_SHA)<stamp(host['storage']['task_created_at']),
         'CHRONOLOGY','Initial attempt predates committed runtime')
    need(raw['recovery_plan.json']==blob(RECOVERY_SHA,REL+'/setup/recovery_plan.json'),
         'CHRONOLOGY','Recovery plan was not committed before use')
    same(read('runtime_qualification.json'),expected_runtime(raw,anchor),'QUALIFICATION')
    return validate_report(read('result.json'),raw,anchor,snapshot)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['check']);p.parse_args()
    print(check())
