"""One bounded experiment. Host controller never imports external executable code.

Every external subprocess runs in a separate unprivileged systemd service with a
minimal environment. Raw logs are opened by the controller outside writable paths.
No network credentials or host home directories are passed to external processes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback

from closure import Export, ClosureError, require, read_json, write_json, digest, dumps, classify_axiom, print_axioms

ROOT=Path(__file__).resolve().parents[1]
P=read_json((ROOT/'preregistration.v1.json').read_text())
A=read_json((ROOT/'pr_anchor.json').read_text())
FILES={
 'lean-toolchain':('b814d987e0c93cb99938be934d9b277778495ba1','8190e75a201741065fe508b28955dd64dd72d090babe5f70ce6848879d68ae88'),
 'lakefile.toml':('9ebc030daf98b40aeb90636ef2016d791ad5dd3a',None),
 'lake-manifest.json':('f07a8454cb6200d90bcc4371bc9965e9f8f46c7d','5ec1dc8e009008d0efb9601cd38f6ba54e753fd538b0e5f8c3e6c5ec72ee1e09'),
 'ComparatorChallenges/NavierStokes.json':('b5fd32b1211faf7d282dac09d70be5527da9f486','7610ecead7b390d80ff7f4229a3ff8f18d630e046f7ad1de4f92c7e8e76845b8'),
 'ComparatorChallenges/NavierStokes.lean':('673fb19e26e60818d446363afd953f618719f99b','0cd193b8d5cbd0266e6e2f72e68dd5abcdcf2430ebd435dd9289737e9aa7da61'),
 'NavierStokes/ComparatorSolution.lean':('cc232068cd384dbbddce2753b1fc4a4017c0f2d7','52950d5d618a8d34c9bfbdb16641c81c276e97b6d7fd2a76c08577353f0b0227')}
TOOLS={
 'landrun':{'url':'https://github.com/Zouuup/landrun.git','sha':'811cfff51ceaf3d9843708aa6d22e9b84ccac8b4','tree':'43dceb21e38ff9cb4a711d780dd5ef89adf0fd15','blobs':{'go.mod':'cc2eb73dc92b59c74de696c3e441f706f62fee34','go.sum':'fcbf6385db0820864b0bc5d8f81ec1f95b4e8c97'}},
 'nanoda':{'url':'https://github.com/ammkrn/nanoda_lib.git','sha':'4c544ed4099c8227f07d5de77ad1e69fb0740a27','tree':'e8816d9dc69c669d99181a8fece5aaeed9a6c13d','blobs':{'Cargo.toml':'faec73d980e02394440962455570381cc15a81a5','Cargo.lock':'08fdae41eb8519d052d276f421563d777f69133c'}},
 'Comparator':{'url':P['packages']['Comparator']['url'],'sha':P['packages']['Comparator']['rev']}}
BOUNDARIES=[
 ('Actual profile and certificates',['NominalConeAssembly.exists_nominal_cone','ModulatedProfileAssembly.exists_of_certificate']),
 ('Singular-axis argument',['BaseResidual.baseVelocity_axis_tendsto_atTop','FinalSlowBase.axis_tendsto']),
 ('Finite stages and limits',['ActualCyclePreservation.state_*','ActualCycleCoherence.mean_input_of_transport','GluedStageEstimates.actualStageEstimates','GermEndpointInputs.actual_germ_stage_endpoints_of_estimates']),
 ('Admissible forcing/extension jets',['CandidateFromLimits.force_smooth','CandidateFromLimits.candidate_properties']),
 ('Whole-space uniqueness/comparison',['CandidateProperties.no_global_solution_one','WholeSpaceUniqueness.classical_uniqueness_on_Icc','PressureFlux.exists_uniform_actual_pressure_flux_bound','WholeSpaceComparisonClosure.eq_of_pressure_flux_bound']),
 ('Periodic uniqueness',['PeriodicViscosity.excludes_global_solution','PeriodicViscosityUniqueness.classical_uniqueness_on_Icc','MaximalLifespan.unbounded_excludes_continuous_extension']),
 ('Statement and trusted foundation',[])]


def utc(): return datetime.now(timezone.utc).isoformat()
def status(state, reason=None, failure=None): return {'status':state,'reason':reason,'failure_class':failure}
def blob(raw): return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def source_identity(raw, expected_blob, expected_sha256=None):
    if blob(raw)!=expected_blob or (expected_sha256 and digest(raw)!=expected_sha256):
        raise Stop('SOURCE_IDENTITY_FAILURE','source bytes do not match frozen identity')


class Stop(RuntimeError):
    def __init__(self, failure, reason, command=None):
        super().__init__(reason); self.failure=failure; self.command=command


class Run:
    def __init__(self, work, raw):
        self.work=Path(work); self.raw=Path(raw)
        self.start=time.monotonic(); self.ordinal=0; self.commands=[]; self.max_workspace=0
        self.failure=None; self.target_started=False
        self.env={'PATH':'/opt/tnp-go/bin:/usr/local/bin:/usr/bin:/bin','HOME':str(self.work/'home'),
          'ELAN_HOME':str(self.work/'elan'),'RUSTUP_HOME':str(self.work/'rustup'), 'CARGO_HOME':str(self.work/'cargo'),
          'LEAN_NUM_THREADS':'1','GOTOOLCHAIN':'local','GOMODCACHE':str(self.work/'gomod'), 'GOCACHE':str(self.work/'gocache'),
          'GOFLAGS':'-mod=readonly','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',
          'LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(self.work/'tmp')}
        for name in ('logs','graphs','exports','statements','identities','controls'):(self.raw/name).mkdir(parents=True,exist_ok=True)
        self.identity={'expected':{'external':P['external'],'packages':P['packages'],'tools':TOOLS,'files':FILES},'actual':{},'status':'NOT_ESTABLISHED'}
        self.targets={key:{'name':name,'axes':{axis:status('NOT_RUN','predecessor not established') for axis in P['result_axes']},'primary_disposition':'DEPENDENCY_CLOSURE_UNRESOLVED',
            'failure_class':None,'declaration_exists':None,'declaration_kind':None,'statement':None,'structural_digest':None,'challenge_comparison':None,'evidence':{},
            'limitations':['No physical/unforced/Navier–Stokes solution claim.','Formal ancestry does not semantically validate analytic lemmas.']} for key,name in zip(('R3','periodic'),P['targets'])}
        self.controls={'status':'NOT_RUN','reason':'toolchain/extractor not yet available','results':[]}
        self.axioms={k:{'status':'NOT_RUN','measured_axioms':None,'scanners':{},'agreement':None} for k in self.targets}
        self.graphs={k:{'status':'NOT_RUN','node_count':None,'edge_count':None,'unresolved_references':None,'reason':'export unavailable'} for k in self.targets}
        self.boundaries=[{'category':name,'anchors':anchors,'targets':{k:{'narrowing':'unchanged','reachability':None,'paths':None,'reason':'replay and closure not established'} for k in self.targets}} for name,anchors in BOUNDARIES]
        self.manifest={'schema_version':'1.0','specification_version':'1.0','specification_sha256':P['specification']['sha256'],
          'preregistration_version':1,'preregistration_sha256':digest((ROOT/'preregistration.v1.json').read_bytes()),'schema_sha256':digest((ROOT/'schema/result.schema.json').read_bytes()),
          'outcome_blind':False,'number_project_base':P['number_project_base'],'freeze_commit':A['freeze_head'],'draft_pr_created_at':A['created_at'],
          'runner_code_commit':os.environ.get('TNP_CODE_SHA'),'workflow':os.environ.get('GITHUB_WORKFLOW'),'run_id':os.environ.get('GITHUB_RUN_ID'),
          'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'job_key':os.environ.get('GITHUB_JOB'),'job_id':None,
          'job_id_reason':'numeric job ID is bound in detached GitHub API receipt after execution; environment supplies only job key',
          'external':P['external'],'start_utc':utc(),'end_utc':None,'resource_caps':P['resource_limits'],'planned_run_ordinal':1,'rerun_justification':None,
          'raw_artifact':{'name':'external-ns-raw-'+os.environ.get('GITHUB_RUN_ID','local'),'id':None,'digest':None,'reason':'filled by GitHub artifact receipt after upload'},
          'sealed_artifact':{'id':None,'digest':None,'reason':'separate sealing receipt; no self-referential digest'},
          'target_execution_started':False,'actual_runner':{'ImageOS':os.environ.get('ImageOS'),'ImageVersion':os.environ.get('ImageVersion'),
          'uname':list(os.uname()),'os_release':Path('/etc/os-release').read_text(),'logical_cpus':os.cpu_count(),
            'service_cpu_affinity':[min(os.sched_getaffinity(0))],
            'memory_info':Path('/proc/meminfo').read_text(),'free_disk_bytes':shutil.disk_usage(self.work).free},'activation_amendment':A['activation_amendment']}
        self.save()

    def service(self, argv, cwd):
        unit='tnp-ext-'+str(os.getpid())+'-'+str(self.ordinal)
        # Dedicated account and filesystem isolation protect runner credentials from
        # both file reads and /proc inspection. Only work is writable, raw/code are not.
        args=['sudo','-n','systemd-run','--quiet','--wait','--pipe','--collect','--service-type=exec','--unit='+unit,'--uid=tnpexternal',
          '--working-directory='+str(cwd),'-p','NoNewPrivileges=yes','-p','ProtectSystem=strict','-p','ProtectHome=yes',
          '-p','PrivateTmp=yes','-p','PrivateDevices=yes','-p','ProtectProc=invisible',
          '-p','InaccessiblePaths=/home /root /run/user -/run/credentials','-p','ReadWritePaths='+str(self.work),
          '-p','RestrictAddressFamilies=~AF_UNIX','-p','CapabilityBoundingSet=','-p','RestrictSUIDSGID=yes',
          '-p','CPUAffinity='+str(min(os.sched_getaffinity(0))),
          '-p','RuntimeMaxSec='+str(max(1,int(236*60-(time.monotonic()-self.start))))]
        # Exec env is constructed from scratch, not inherited from GitHub Actions.
        args+=['--','/usr/bin/env','-i']+[k+'='+v for k,v in sorted(self.env.items())]
        args+=['/usr/bin/time','-v','--']+list(map(str,argv))
        return args,unit

    def command(self, stage, argv, cwd=None, failure='BUILD_OR_CONFIGURATION_FAILURE', check=True, export=False):
        self.ordinal+=1; ident=f'{self.ordinal:03d}-{stage}'
        cwd=Path(cwd or self.work); out=self.raw/'logs'/(ident+'.stdout.log'); err=self.raw/'logs'/(ident+'.stderr.log')
        command,unit=self.service(argv,cwd)
        record={'command_id':ident,'stage':stage,'argv':list(map(str,argv)),'wrapper_argv':command,'cwd':str(cwd),
          'start_utc':utc(),'end_utc':None,'exit_code':None,'signal':None,'timeout':False,'elapsed_seconds':None,'peak_rss_kib':None,
          'stdout':str(out.relative_to(self.raw)),'stderr':str(err.relative_to(self.raw)),'failure_class':None,'decisive_diagnostic':None}
        start=time.monotonic(); cap=P['resource_limits']['export_bytes_per_target'] if export else P['resource_limits']['single_log_bytes']; resource_reason=None
        with out.open('wb') as fo,err.open('wb') as fe:
            proc=subprocess.Popen(command,stdout=fo,stderr=fe,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},start_new_session=True)
            while proc.poll() is None:
                if time.monotonic()-self.start >= 236*60: resource_reason='execute wall-clock reserve reached'; record['timeout']=True
                if out.stat().st_size > cap or err.stat().st_size > P['resource_limits']['single_log_bytes']:resource_reason='raw output cap'
                usage=subprocess.run(['du','-sb',str(self.work)],capture_output=True,text=True)
                if usage.returncode==0:
                    used=int(usage.stdout.split()[0]); self.max_workspace=max(used,self.max_workspace)
                    if used>P['resource_limits']['workspace_bytes']:resource_reason='workspace cap'
                if resource_reason:
                    subprocess.run(['sudo','-n','systemctl','kill','--kill-whom=all',unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    os.killpg(proc.pid,signal.SIGTERM); break
                time.sleep(1)
            try: code=proc.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL); code=proc.wait()
        stderr=err.read_text(errors='replace')
        m=re.search(r'Maximum resident set size \(kbytes\): (\d+)',stderr)
        record.update(end_utc=utc(),exit_code=code,signal=-code if code<0 else None,elapsed_seconds=time.monotonic()-start,
            peak_rss_kib=int(m[1]) if m else None,stdout_sha256=digest(out.read_bytes()),stderr_sha256=digest(err.read_bytes()))
        if code or resource_reason:
            record['failure_class']='RESOURCE_LIMIT' if resource_reason else failure
            record['decisive_diagnostic']=resource_reason or stderr[:4000] or out.read_text(errors='replace')[:4000] or 'nonzero exit with no diagnostic'
        self.commands.append(record)
        with (self.raw/'commands.ndjson').open('a') as f:f.write(dumps(record)+'\n')
        print(ident,code,record['failure_class'] or 'PASS',flush=True)
        if check and record['failure_class']: raise Stop(record['failure_class'],record['decisive_diagnostic'],ident)
        return record,out,err

    def text(self,*args,**kw):return self.command(*args,**kw)[1].read_text().strip()

    def clone(self,name,url,sha,tree=None,blobs=None,parent=None):
        d=Path(parent or self.work)/name
        self.command(name+'-git-init',['git','init',str(d)])
        self.command(name+'-origin',['git','remote','add','origin',url],d)
        self.command(name+'-fetch',['git','-c','credential.helper=','fetch','--depth=1','origin',sha],d,'DEPENDENCY_OR_VERSION_FAILURE')
        self.command(name+'-detach',['git','checkout','--detach','FETCH_HEAD'],d)
        actual=self.text(name+'-head',['git','rev-parse','HEAD'],d)
        actual_tree=self.text(name+'-tree',['git','rev-parse','HEAD^{tree}'],d)
        if actual!=sha or (tree and actual_tree!=tree):raise Stop('SOURCE_IDENTITY_FAILURE',name+' commit/tree mismatch')
        if self.text(name+'-clean',['git','status','--porcelain','--untracked-files=no'],d):raise Stop('SOURCE_IDENTITY_FAILURE',name+' tracked tree dirty')
        ls=self.command(name+'-ls-tree',['git','ls-tree','-r','--full-tree','HEAD'],d)[1]
        file_values={}
        for path,expected in (blobs or {}).items():
            raw=(d/path).read_bytes(); value=blob(raw); file_values[path]={'blob':value,'sha256':digest(raw)}
            source_identity(raw,expected)
        self.identity['actual'][name]={'head':actual,'tree':actual_tree,'origin':url,'clean_tracked_tree':True,'ls_tree_sha256':digest(ls.read_bytes()),'files':file_values}
        self.save(); return d

    def environment(self):
        # Failure of this capability probe means no external tool/source code ran.
        self.command('isolation-probe',['/usr/bin/true'],failure='UNAVAILABLE_RUNNER_CAPABILITY')
        for name,argv in [('uname',['uname','-a']),('os',['cat','/etc/os-release']),('cpu',['lscpu']),('memory',['cat','/proc/meminfo']),('disk',['df','-B1','-T',str(self.work)]),
            ('git',['git','--version']),('curl',['curl','--version']),('tar',['tar','--version']),('sha256',['sha256sum','--version']),('go',['go','version'])]:
            self.manifest['actual_runner'][name]=self.text('identity-'+name,argv)
        self.manifest['actual_runner'].update(ImageOS=os.environ.get('ImageOS'),ImageVersion=os.environ.get('ImageVersion'),architecture=os.uname().machine)
        if not self.manifest['actual_runner']['go'].startswith('go version go1.24.0 '):raise Stop('DEPENDENCY_OR_VERSION_FAILURE','Go is not 1.24.0')
        self.src=self.clone('external','https://github.com/openai/NavierStokesAndEuler.git',P['external']['commit'],P['external']['tree'],{p:v[0] for p,v in FILES.items()})
        for path,(_,sha256) in FILES.items():
            if sha256 and digest((self.src/path).read_bytes())!=sha256:raise Stop('SOURCE_IDENTITY_FAILURE',path+' SHA256 mismatch')
        m=read_json((self.src/'lake-manifest.json').read_text())
        actual={v['name']:{'url':v['url'],'rev':v['rev']} for v in m['packages']}
        if actual!=P['packages'] or len(m['packages'])!=11 or any(v['type']!='git' for v in m['packages']):raise Stop('SOURCE_IDENTITY_FAILURE','complete manifest mismatch')
        cfg=read_json((self.src/'ComparatorChallenges/NavierStokes.json').read_text())
        for k,v in {'challenge_module':'ComparatorChallenges.NavierStokes','solution_module':'NavierStokes.ComparatorSolution','theorem_names':P['targets'],'permitted_axioms':P['permitted_axioms'],'enable_nanoda':True}.items():
            if cfg.get(k)!=v:raise Stop('SOURCE_IDENTITY_FAILURE','Comparator config mismatch: '+k)
        elan=self.work/'elan.tar.gz'
        self.command('elan-download',['curl','--fail','--location','--retry','0','--output',elan,'https://github.com/leanprover/elan/releases/download/v4.2.4/elan-x86_64-unknown-linux-gnu.tar.gz'],failure='DEPENDENCY_OR_VERSION_FAILURE')
        if digest(elan.read_bytes())!='42b94d4244e8353142c456ec0e4ca6528fd898a6c604d4059f494e706e431f63':raise Stop('SOURCE_IDENTITY_FAILURE','Elan release SHA256 mismatch')
        self.command('elan-unpack',['tar','-xzf',elan,'-C',self.work])
        self.command('elan-install',[self.work/'elan-init','-y','--no-modify-path','--default-toolchain','none'])
        self.env['PATH']=str(self.work/'elan/bin')+':'+self.env['PATH']
        self.command('lean-install',['elan','toolchain','install',P['external']['lean_toolchain']],failure='DEPENDENCY_OR_VERSION_FAILURE')
        for name,argv in [('elan',['elan','--version']),('lean',['lean','--version']),('lake',['lake','--version']),('lean_prefix',['lean','--print-prefix'])]:self.identity['actual'][name]=self.text(name+'-version',argv,self.src)
        if not self.identity['actual']['elan'].startswith('elan 4.2.4'):raise Stop('DEPENDENCY_OR_VERSION_FAILURE','Elan version mismatch')
        if not self.identity['actual']['lean'].startswith('Lean (version 4.34.0-rc2,'):raise Stop('DEPENDENCY_OR_VERSION_FAILURE','exact Lean version mismatch')
        for name in TOOLS:
            t=TOOLS[name]; setattr(self,name.lower(),self.clone(name,t['url'],t['sha'],t.get('tree'),t.get('blobs')))
        export_pin=P['packages']['lean4export']
        comp_manifest=read_json((self.comparator/'lake-manifest.json').read_text())
        if len(comp_manifest['packages'])!=1 or any(comp_manifest['packages'][0].get(k)!=v for k,v in {'name':'lean4export',**export_pin}.items()):raise Stop('SOURCE_IDENTITY_FAILURE','Comparator manifest exporter pin mismatch')
        self.command('landrun-build',['go','build','-mod=readonly','-o','landrun','cmd/landrun/main.go'],self.landrun)
        # rustup launcher is an installed runner utility, copied read-only by run.sh;
        # its binary identity is recorded, while compiler selection remains exact.
        self.command('rust-install',['/opt/tnp-bin/rustup','toolchain','install','1.98.1','--profile','minimal','--no-self-update'],failure='DEPENDENCY_OR_VERSION_FAILURE')
        self.identity['actual']['rust']=self.text('rust-version',['/opt/tnp-bin/rustup','run','1.98.1','rustc','--version'])
        self.identity['actual']['cargo']=self.text('cargo-version',['/opt/tnp-bin/rustup','run','1.98.1','cargo','--version'])
        if not self.identity['actual']['rust'].startswith('rustc 1.98.1 '):raise Stop('DEPENDENCY_OR_VERSION_FAILURE','Rust compiler mismatch')
        self.command('nanoda-build',['/opt/tnp-bin/rustup','run','1.98.1','cargo','build','--release','--locked'],self.nanoda)
        self.command('comparator-packages-directory',['mkdir','-p',self.comparator/'.lake/packages'])
        self.clone('lean4export',export_pin['url'],export_pin['rev'],parent=self.comparator/'.lake/packages')
        self.command('comparator-build',['lake','build','lean4export','comparator'],self.comparator)
        exp=self.comparator/'.lake/packages/lean4export'
        if self.text('exporter-head',['git','rev-parse','HEAD'],exp)!=export_pin['rev']:raise Stop('SOURCE_IDENTITY_FAILURE','resolved exporter mismatch')
        self.exporter=exp/'.lake/build/bin/lean4export'; self.compbin=self.comparator/'.lake/build/bin/comparator'; self.nanobin=self.nanoda/'target/release/nanoda_bin'; self.landbin=self.landrun/'landrun'
        self.env.update(COMPARATOR_LANDRUN=str(self.landbin),COMPARATOR_LEAN4EXPORT=str(self.exporter),COMPARATOR_NANODA=str(self.nanobin))
        for name,path in [('landrun',self.landbin),('Comparator',self.compbin),('lean4export',self.exporter),('nanoda',self.nanobin),('rustup',Path('/opt/tnp-bin/rustup'))]:
            self.identity['actual'][name+'_binary']={'path':str(path),'size':path.stat().st_size,'sha256':digest(path.read_bytes())}
        self.command('mathlib-cache',['lake','exe','cache','get'],self.src,'DEPENDENCY_OR_VERSION_FAILURE')
        packages={}
        for name,pin in P['packages'].items():
            d=self.src/'.lake/packages'/name
            head=self.text('package-'+name+'-head',['git','rev-parse','HEAD'],d)
            origin=self.text('package-'+name+'-origin',['git','remote','get-url','origin'],d)
            clean=self.text('package-'+name+'-clean',['git','status','--porcelain','--untracked-files=no'],d)
            if head!=pin['rev'] or origin!=pin['url'] or clean:raise Stop('SOURCE_IDENTITY_FAILURE','resolved package mismatch '+name)
            packages[name]={'head':head,'origin':origin,'tracked_tree_clean':True}
        self.identity['actual']['resolved_packages']=packages
        for name in TOOLS:
            d=getattr(self,name.lower())
            if self.text(name+'-postbuild-clean',['git','status','--porcelain','--untracked-files=no'],d):raise Stop('SOURCE_IDENTITY_FAILURE','tool source modified during build: '+name)
        if self.text('exporter-postbuild-clean',['git','status','--porcelain','--untracked-files=no'],exp):raise Stop('SOURCE_IDENTITY_FAILURE','exporter source modified during build')
        self.verify_sources()
        if any(self.src.glob('.lake/build/lib/lean/**/ComparatorSolution.olean')) or (self.src/'.lake/build/lib/lean/ComparatorChallenges/NavierStokes.olean').exists():raise Stop('SOURCE_IDENTITY_FAILURE','target/reference preexisting root olean')
        self.identity['actual']['root_target_oleans_before_execution']='ABSENT'
        # Probe strict deny behavior even though pinned Comparator selects best-effort.
        common=[self.landbin,'--best-effort','--ro','/','--rox','/usr','--rox','/bin','--rox','/lib','--rox','/lib64','--rw','/dev','--']
        allowed=self.command('landrun-read',common+['cat','/etc/os-release'],check=False)
        denied=self.command('landrun-denied-write',common+['touch',self.work/'outside-landrun-writable'],check=False)
        self.land_ok=allowed[0]['exit_code']==0 and denied[0]['exit_code']!=0 and not (self.work/'outside-landrun-writable').exists()
        user=self.command('outer-user-systemd-capability',['systemd-run','--user','--wait','--pipe','--property=RestrictAddressFamilies=~AF_UNIX','--','/usr/bin/true'],failure='UNAVAILABLE_RUNNER_CAPABILITY',check=False)
        self.identity['actual']['outer_user_systemd']=status('PASS' if user[0]['exit_code']==0 else 'UNAVAILABLE','Recorded separately. Every command already runs under host system service AF_UNIX denial and unprivileged UID.','UNAVAILABLE_RUNNER_CAPABILITY' if user[0]['exit_code'] else None)
        self.identity['actual']['landrun_controls']=status('PASS' if self.land_ok else 'FAIL',failure=None if self.land_ok else 'UNAVAILABLE_RUNNER_CAPABILITY')
        self.identity['status']='ESTABLISHED'; self.save()

    def verify_sources(self):
        for path,(expected,sha256) in FILES.items():
            raw=(self.src/path).read_bytes()
            source_identity(raw,expected,sha256)
        if self.text('external-tracked-clean',['git','status','--porcelain','--untracked-files=no'],self.src):raise Stop('SOURCE_IDENTITY_FAILURE','external tracked files changed')

    def probe(self,key,module,target,cwd):
        file=self.work/('Probe_'+key+'.lean')
        source=(ROOT/'runner/ClosureProbe.lean').read_text().replace('import Lean','import Lean\nimport '+module,1)
        file.write_text(source+'\n#closure_probe '+target+'\n#print axioms '+target+'\n')
        record,out,err=self.command(key+'-statement-and-axioms',['lake','env','lean',file],cwd,'EXTRACTION_OR_TOOLING_FAILURE')
        raw=out.read_text(); marker='TNP_STATEMENT_JSON '
        statements=[read_json(line.split(marker,1)[1]) for line in raw.splitlines() if marker in line]
        require(len(statements)==1 and statements[0]['name']==target,'missing/ambiguous statement extraction')
        return statements[0],print_axioms(raw,target),record

    def export(self,key,module,target,cwd):
        record,out,err=self.command(key+'-export',['lake','env',self.exporter,'--export-unsafe',module,'--',target],cwd,'EXTRACTION_OR_TOOLING_FAILURE',export=True)
        e=Export(out,P['resource_limits']); summary,names,path=e.graph(target,self.raw/'graphs',key)
        dest=self.raw/'exports'/(key+'.export.ndjson.gz')
        with out.open('rb') as f,dest.open('wb') as raw:
            with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as z:shutil.copyfileobj(f,z)
        summary.update(export_sha256=digest(out.read_bytes()),compressed_export_sha256=digest(dest.read_bytes()),export_metadata=e.meta)
        return e,summary,names,path,record

    def run_controls(self):
        spec=importlib.util.spec_from_file_location('fixtures',ROOT/'controls/fixtures.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        directory=self.work/'controls'; keys=mod.generate(directory,P['external']['lean_toolchain'])
        subprocess.run(['sudo','chown','-R','tnpexternal:tnpexternal',str(directory)],check=True)
        results=[]; closure_ok=True; comparator_ok=self.land_ok
        for key in keys:
            d=directory/key; item={'id':key,'status':'NOT_RUN'}
            try:
                if self.land_ok:
                    r,o,e=self.command('control-'+key+'-comparator',['lake','env',self.compbin,'config.json'],d,check=False)
                    message=o.read_text()+e.read_text()
                    expected=(r['exit_code']==0 and 'Your solution is okay!' in message) if key=='clean' else r['exit_code']!=0
                    if key in ('reachable_custom','sorry'):expected=expected and ('Illegal axiom detected:' in message)
                    if key=='statement_mismatch':expected=expected and ('Challenge and solution theorem statement do not match:' in message)
                    item['comparator_expected_rejection_or_acceptance']=expected; item['comparator_command']=r['command_id']; comparator_ok &= expected
                else:item['comparator']=status('NOT_RUN','landrun capability unavailable','UNAVAILABLE_RUNNER_CAPABILITY')
                self.command('control-'+key+'-build',['lake','build','Solution'],d)
                statement,axioms,probe=self.probe('control-'+key,'Solution','probe',d)
                exp,summary,names,path,record=self.export('control-'+key,'Solution','probe',d)
                expected=[] if key in ('clean','statement_mismatch') else ['usedCustom'] if key=='reachable_custom' else ['sorryAx']
                require(summary['axioms']==axioms==expected,'control axiom disagreement')
                require('unusedCustom' not in names and 'unusedPlaceholder' not in names,'unused control leaked into closure')
                item.update(status='PASS',measured_axioms=axioms,graph=summary)
                if key=='clean':
                    try: exp.graph('missing_exact_target')
                    except ClosureError:item['missing_target_sentinel']='PASS'
                    else:raise ClosureError('missing target returned success')
                    try: source_identity(b'actual','0'*40)
                    except Stop as exc:
                        require(exc.failure=='SOURCE_IDENTITY_FAILURE','wrong source failure class')
                        item['wrong_source_sentinel']='PASS'
                    else:raise ClosureError('wrong SHA returned success')
                    try:self.export('control-missing-target','Solution','missing_exact_target',d)
                    except (Stop,ClosureError):item['missing_target_export_sentinel']='PASS'
                    else:raise ClosureError('missing target exporter returned credited closure')
            except (Stop,ClosureError,ValueError) as exc:
                item.update(status='FAIL',reason=str(exc)); closure_ok=False
            results.append(item);self.controls={'status':'RUNNING','results':results};self.save()
        self.controls={'status':'PASS' if closure_ok and comparator_ok else 'PARTIAL_OR_FAILED','closure_controls_passed':closure_ok,'comparator_controls_passed':comparator_ok,'results':results}
        self.save()

    def replay(self):
        self.verify_sources()
        if shutil.disk_usage(self.work).free < P['resource_limits']['minimum_free_disk_bytes']:raise Stop('RESOURCE_LIMIT','less than 12 GiB free before target stage')
        self.target_started=True; self.manifest['target_execution_started']=True;self.manifest['target_execution_start_utc']=utc();self.save()
        for t in self.targets.values():t['axes']['environment_identity']=status('PASS')
        comp_pass=False; comp_r=None; comp_message=''
        if self.land_ok and self.controls.get('comparator_controls_passed'):
            comp_r,o,e=self.command('target-comparator',['lake','env',self.compbin,'ComparatorChallenges/NavierStokes.json'],self.src,check=False)
            comp_message=o.read_text()+e.read_text()
            comp_pass=comp_r['exit_code']==0 and 'Your solution is okay!' in comp_message and all(n in comp_message for n in P['targets'])
        names_bound=all(n in comp_message for n in P['targets'])
        compared=names_bound and ('Running nanoda kernel on solution' in comp_message or 'Running Lean default kernel on solution.' in comp_message)
        kernel_pass='Lean default kernel accepts the solution' in comp_message
        exported_solution=names_bound and re.search(r'Exporting .* from NavierStokes.ComparatorSolution',comp_message) is not None
        sandbox_failure=comp_r is not None and not exported_solution and any(x in comp_message.lower() for x in ('landlock','sandbox','failed to connect to bus','operation not permitted'))
        fallback=comp_r is None or sandbox_failure
        for t in self.targets.values():
            for axis in ('comparator_statement_identity','comparator_axiom_policy'):
                t['axes'][axis]=status('PASS' if compared or comp_pass else 'UNRESOLVED',
                    'pinned Comparator passed statement and axiom stages before kernel invocation' if compared else comp_message[:2000] or 'Comparator control/capability unavailable',
                    None if compared or comp_pass else 'UNAVAILABLE_RUNNER_CAPABILITY' if fallback else 'EXTRACTION_OR_TOOLING_FAILURE')
            if exported_solution or kernel_pass or comp_pass:
                t['axes']['target_elaboration']=status('PASS','Comparator completed narrow solution build and reached export')
                t['axes']['lean_kernel_replay']=status('PASS','Comparator exported kernel replay' if kernel_pass else 'Lean checked root target module; exported replay not established')
            if 'Running nanoda kernel on solution' in comp_message:
                passed='nanoda kernel accepts the solution' in comp_message
                t['axes']['nanoda_replay']=status('PASS' if passed else 'FAIL','actual Comparator nanoda invocation',None if passed else comp_r['failure_class'])
            if 'Challenge and solution theorem statement do not match:' in comp_message:
                t['axes']['comparator_statement_identity']=status('FAIL','pinned Comparator statement mismatch','STATEMENT_IDENTITY_FAILURE')
                t['primary_disposition']='STATEMENT_TARGET_MISMATCH';t['failure_class']='STATEMENT_IDENTITY_FAILURE'
            elif 'Illegal axiom detected:' in comp_message:
                t['axes']['comparator_axiom_policy']=status('VIOLATION','pinned Comparator illegal axiom','AXIOM_POLICY_FAILURE')
                t['primary_disposition']='AXIOM_CLOSURE_VIOLATION';t['failure_class']='AXIOM_POLICY_FAILURE'
            elif 'Lean default kernel rejects the solution' in comp_message:
                t['axes']['lean_kernel_replay']=status('FAIL','pinned Lean kernel rejected export','THEOREM_OR_PROOF_FAILURE')
                t['primary_disposition']='REPLAY_FAILED_FORMAL';t['failure_class']='THEOREM_OR_PROOF_FAILURE'
            elif comp_r and not exported_solution and not fallback:
                fail=comp_r['failure_class'] or 'EXTRACTION_OR_TOOLING_FAILURE'
                if fail!='RESOURCE_LIMIT' and re.search(r'(type mismatch|unsolved goals|kernel error)',comp_message):fail='THEOREM_OR_PROOF_FAILURE'
                t['failure_class']=fail
                t['primary_disposition']='REPLAY_FAILED_FORMAL' if fail=='THEOREM_OR_PROOF_FAILURE' else 'DEPENDENCY_CLOSURE_UNRESOLVED'
                t['axes']['target_elaboration']=status('FAIL',comp_r['command_id'],fail)
                t['axes']['lean_kernel_replay']=status('NOT_RUN','Comparator did not reach replay',fail)
        if fallback:
            # Packet-authorized fallback only for unavailable Comparator sandbox or
            # gated control capability. Never retry a formal/statement/policy failure.
            r,o,e=self.command('target-fallback-lean',['lake','build','NavierStokes.ComparatorSolution'],self.src,check=False)
            for t in self.targets.values():
                if r['exit_code']==0:
                    t['axes']['target_elaboration']=status('PASS','narrow module build')
                    t['axes']['lean_kernel_replay']=status('PASS','Lean checked root target module; dependency cache trust is recorded')
                else:
                    fail=r['failure_class']; msg=o.read_text()+e.read_text()
                    if fail!='RESOURCE_LIMIT' and re.search(r'(type mismatch|unsolved goals|kernel error)',msg):fail='THEOREM_OR_PROOF_FAILURE'
                    for axis in ('target_elaboration','lean_kernel_replay'):t['axes'][axis]=status('FAIL','see '+r['command_id'],fail)
                    t['primary_disposition']='REPLAY_FAILED_FORMAL' if fail=='THEOREM_OR_PROOF_FAILURE' else 'DEPENDENCY_CLOSURE_UNRESOLVED';t['failure_class']=fail
        self.verify_sources();self.save()
        closure_names={}
        for key,t in self.targets.items():
            if t['axes']['target_elaboration']['status']!='PASS' or t['primary_disposition'] in ('STATEMENT_TARGET_MISMATCH','AXIOM_CLOSURE_VIOLATION','REPLAY_FAILED_FORMAL'):continue
            try:
                olean=self.src/'.lake/build/lib/lean/NavierStokes/ComparatorSolution.olean'
                require(olean.is_file(),'missing executed target olean')
                t['evidence']['olean']={'path':str(olean),'sha256':digest(olean.read_bytes()),'size':olean.stat().st_size,'mtime_ns':olean.stat().st_mtime_ns}
                statement,printed,probe_record=self.probe(key,'NavierStokes.ComparatorSolution',t['name'],self.src)
                t.update(declaration_exists=True,declaration_kind='theorem',statement=statement)
                (self.raw/'statements'/(key+'.txt')).write_text(statement['elaborated_type']+'\n')
                t['axes']['elaborated_statement_extraction']=status('PASS',probe_record['command_id'])
                exp,summary,names,path,export_record=self.export(key,'NavierStokes.ComparatorSolution',t['name'],self.src)
                closure_names[key]=names; self.graphs[key]=summary;t['structural_digest']=summary['type_digest']
                measured=summary['axioms']; bad=[n for n in measured if n not in P['permitted_axioms']]
                self.axioms[key]={'status':'MEASURED','measured_axioms':measured,'leaf_classifications':{n:classify_axiom(n,P['permitted_axioms']) for n in measured},
                    'scanners':{'print_axioms':{'status':'PASS','axioms':printed,'command':probe_record['command_id']},'export':{'status':'PASS','axioms':measured,'command':export_record['command_id']},
                                'comparator_policy':t['axes']['comparator_axiom_policy']},'agreement':measured==printed,'trusted_paths':summary['trusted_paths']}
                if measured!=printed:raise ClosureError('axiom scanner disagreement')
                trusted_bad=[n['name'] for n in summary['trusted_nodes'] if n['safety'] in ('unsafe','partial')]
                if bad or trusted_bad:
                    t['axes']['axiom_closure']=status('VIOLATION',str(bad+trusted_bad),'AXIOM_POLICY_FAILURE');t['primary_disposition']='AXIOM_CLOSURE_VIOLATION';t['failure_class']='AXIOM_POLICY_FAILURE'
                elif not self.controls.get('closure_controls_passed'):
                    t['axes']['axiom_closure']=status('UNRESOLVED','closure control failure','EXTRACTION_OR_TOOLING_FAILURE');t['primary_disposition']='REPLAY_ESTABLISHED_CLOSURE_PARTIAL'
                else:
                    t['axes']['axiom_closure']=status('PASS' if compared else 'PARTIAL','print/export agree; Comparator agreement '+str(compared));t['primary_disposition']='REPLAY_ESTABLISHED_CLOSURE_PARTIAL'
                t['axes']['dependency_graph']=status('PASS' if self.controls.get('closure_controls_passed') else 'UNRESOLVED','machine fixed point; see graph artifacts')
                # Separate actual nanoda execution, even if outer Comparator unavailable.
                if t['axes']['nanoda_replay']['status']=='NOT_RUN' and not bad:
                    config=self.work/(key+'-nanoda.json')
                    raw_export=self.raw/export_record['stdout']
                    copy=self.work/(key+'.ndjson'); shutil.copyfile(raw_export,copy)
                    write_json(config,{'use_stdin':False,'export_file_path':str(copy),'permitted_axioms':P['permitted_axioms'],'unpermitted_axiom_hard_error':True,'nat_extension':True,'string_extension':True})
                    r,_,_=self.command(key+'-nanoda',[self.nanobin,config],check=False)
                    t['axes']['nanoda_replay']=status('PASS' if r['exit_code']==0 else 'FAIL',r['command_id'],r['failure_class'])
                # Challenge is independently built/extracted with unchanged source.
                self.command(key+'-challenge-build',['lake','build','ComparatorChallenges.NavierStokes'],self.src)
                cstatement,_,_=self.probe(key+'-challenge','ComparatorChallenges.NavierStokes',t['name'],self.src)
                _,cs,_,_,_=self.export(key+'-challenge','ComparatorChallenges.NavierStokes',t['name'],self.src)
                same=cs['type_digest']==summary['type_digest']
                t['challenge_comparison']={'structural_type_digest_equal':same,'pretty_types_equal':statement['elaborated_type']==cstatement['elaborated_type'],
                    'challenge_elaborated_type':cstatement['elaborated_type'],'comparator_primary':comp_pass,
                    'package2_interpretation':'requires report review: positive viscosity; existential initial velocity and forcing; appropriate admissibility; no global pair'}
                if not same:
                    t['primary_disposition']='STATEMENT_TARGET_MISMATCH';t['failure_class']='STATEMENT_IDENTITY_FAILURE'
                elif compared and kernel_pass and self.controls.get('closure_controls_passed') and not bad and not trusted_bad:
                    t['primary_disposition']='REPLAY_AND_CLOSURE_ESTABLISHED' if t['axes']['nanoda_replay']['status']=='PASS' else 'REPLAY_AND_CLOSURE_ESTABLISHED_AUXILIARY_KERNEL_UNRESOLVED'
                self.narrow(key,exp,names,path,t)
            except (Stop,ClosureError,ValueError,KeyError,OSError) as exc:
                t['primary_disposition']='REPLAY_ESTABLISHED_CLOSURE_PARTIAL' if t['primary_disposition'] not in ('AXIOM_CLOSURE_VIOLATION','STATEMENT_TARGET_MISMATCH') else t['primary_disposition']
                t['failure_class']=getattr(exc,'failure','EXTRACTION_OR_TOOLING_FAILURE');t['extraction_failure']=str(exc)
            self.save()
        if len(closure_names)==2:self.graphs['overlap']={'shared':len(closure_names['R3']&closure_names['periodic']),'R3_unique':sorted(closure_names['R3']-closure_names['periodic']),'periodic_unique':sorted(closure_names['periodic']-closure_names['R3'])}

    def narrow(self,key,exp,names,path,t):
        def anchor_evidence(n):
            todo=[n];seen=set();leaves=set()
            while todo:
                m=todo.pop()
                if m in seen:continue
                seen.add(m)
                if exp.decls[m]['kind']=='axiom':leaves.add(m)
                todo.extend(x for x,k in exp.decls[m]['edges'])
            return {'name':n,'path':path(n),'kind':exp.decls[n]['kind'],'body_present':exp.decls[n]['body_present'],
                'axiom_leaves':sorted(leaves),'replay':t['axes']['lean_kernel_replay'],'reachable_closure_nodes':len(seen)}
        for row in self.boundaries:
            records=[]
            for anchor in row['anchors']:
                if anchor.endswith('*'):matches=sorted(n for n in names if anchor[:-1] in n)
                else:matches=sorted(n for n in names if n==anchor or n.endswith('.'+anchor))
                records.append({'anchor':anchor,'resolution':'ABSENT' if not matches else 'MATCHED_PATTERN' if anchor.endswith('*') else 'UNIQUE' if len(matches)==1 else 'AMBIGUOUS',
                    'matches':[anchor_evidence(n) for n in matches]})
            complete=t['primary_disposition'].startswith('REPLAY_AND_CLOSURE_ESTABLISHED')
            row['targets'][key]={'narrowing':'narrowed' if complete else 'unchanged','anchor_records':records,'replay':t['axes']['lean_kernel_replay'],
                'remaining_uncertainty':'Formal ancestry does not establish the mathematical meaning of every analytic lemma; '+('permitted closure measured' if complete else 'complete credited closure not established')}
        t['axes']['package2_boundary_narrowing']=status('REPORTED','see stopping_boundaries.json')

    def save(self):
        for name,obj in [('run_manifest',self.manifest),('identity',self.identity),('controls',self.controls),('targets',self.targets),('axioms',self.axioms),('dependency_summary',self.graphs),('stopping_boundaries',self.boundaries)]:write_json(self.raw/(name+'.json'),obj)

    def finish(self):
        self.manifest.update(end_utc=utc(),elapsed_seconds=time.monotonic()-self.start,max_workspace_bytes=self.max_workspace,target_execution_started=self.target_started)
        if self.failure:
            self.manifest['terminal_failure']=self.failure
            for t in self.targets.values():
                if not self.target_started:
                    t['primary_disposition']='ENVIRONMENT_NOT_REPRODUCIBLE';t['failure_class']=self.failure['failure_class']
                    t['axes']['environment_identity']=status('FAIL',self.failure['reason'],self.failure['failure_class'])
                    for axis in t['axes']:
                        if axis!='environment_identity':t['axes'][axis]=status('NOT_RUN',self.failure['reason'],self.failure['failure_class'])
        for key,t in self.targets.items():
            for axis in ('axiom_closure','dependency_graph','elaborated_statement_extraction'):
                if t['axes'][axis]['status']=='NOT_RUN' and self.target_started:t['axes'][axis]['failure_class']=t.get('failure_class')
            # Explicit failure sentinels in required paths, never empty exports/graphs.
            missing={'status':'NOT_PRODUCED','target':t['name'],'failure_class':t.get('failure_class'),'reason':t.get('extraction_failure') or (self.failure or {}).get('reason') or 'predecessor failed'}
            for suffix in ('nodes','edges'):
                p=self.raw/'graphs'/(key+'.'+suffix+'.ndjson.gz')
                if not p.exists():
                    from closure import gzip_lines
                    gzip_lines(p,[missing])
            p=self.raw/'exports'/(key+'.export.ndjson.gz')
            if not p.exists():
                from closure import gzip_lines
                gzip_lines(p,[missing])
            p=self.raw/'statements'/(key+'.txt')
            if not p.exists():p.write_text('NOT_PRODUCED: '+dumps(missing)+'\n')
        if not (self.raw/'commands.ndjson').exists():(self.raw/'commands.ndjson').write_text('')
        self.save()
        report=['# External Lean Navier–Stokes pinned replay/closure — raw execution report','',
            'PROVISIONAL — INDEPENDENT AUDIT PENDING','',
            'External commit: '+P['external']['commit'], 'Runner commit: '+str(self.manifest['runner_code_commit']),
            'Target execution started: '+str(self.target_started),'', '| Target | Primary disposition |','|---|---|']
        report += ['| '+k+' | '+t['primary_disposition']+' |' for k,t in self.targets.items()]
        report += ['','Failure: '+dumps(self.failure),'','Missing exports/graphs are labeled failure sentinels, not empty closures.','Machine ancestry is conditional on the recorded tools and trusted foundations. No physical or unforced blow-up claim.']
        (self.raw/'final_report.md').write_text('\n'.join(report)+'\n')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--raw',required=True);args=ap.parse_args()
    run=Run(args.work,args.raw)
    try:
        run.environment();run.run_controls();run.replay()
    except Stop as exc:run.failure={'failure_class':exc.failure,'reason':str(exc),'command_id':exc.command}
    except Exception as exc:
        run.failure={'failure_class':'EXTRACTION_OR_TOOLING_FAILURE','reason':str(exc),'command_id':None}
        (run.raw/'logs/controller.stderr.log').write_text(traceback.format_exc())
    finally:run.finish()
    return 0


if __name__=='__main__':sys.exit(main())
