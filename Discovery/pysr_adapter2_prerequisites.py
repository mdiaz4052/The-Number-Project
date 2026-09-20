"""Source-pinned diagnosis of the failed worker-isolation prerequisite.

Runs trusted host metadata/system utilities only, never dependencies or Julia.
No permission changes or privileged namespace requests. One capability probe
does not retry a failed native startup or reset a setup epoch.
"""
from datetime import datetime, timezone
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import signal
import subprocess
import sys
import time

from Discovery import pysr_adapter2_runtime as runtime

ROOT, PKG, NS = runtime.ROOT, runtime.PKG, runtime.NS
SOURCE = 'Discovery/pysr_adapter2_prerequisites.py'


def diagnose():
    source_sha = runtime.git('rev-parse', 'HEAD')
    if subprocess.check_output(['git','show',source_sha+':'+SOURCE],cwd=ROOT) != (ROOT/SOURCE).read_bytes():
        raise RuntimeError('Exact diagnostic source must be committed first')
    evidence = PKG / 'setup/epoch-01'
    if (evidence/'stop.json').exists():
        raise RuntimeError('Terminal epoch cannot resume')
    task = Path('/tmp/tnp-pysr-adapter2-e01')
    if not task.is_dir():
        raise RuntimeError('Initial controller attempt must exist')
    started = runtime.now()
    status = Path('/proc/self/status').read_text()
    selected = {line.split(':',1)[0]:line.split(':',1)[1].strip()
                for line in status.splitlines() if line.startswith((
                    'Uid:','Gid:','Groups:','Cap','NoNewPrivs:','Seccomp:'))}
    uid_map = Path('/proc/self/uid_map').read_text()
    gid_map = Path('/proc/self/gid_map').read_text()
    # No values from the controller's authenticated environment are inherited.
    env = {'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    host = {'schema':NS+'/host','observed_at':started,
        'python':{'implementation':sys.implementation.name,'version':platform.python_version(),
                  'executable':sys.executable,'sha256':runtime.sha(sys.executable)},
        'platform':platform.platform(),'machine':{'process':platform.machine(),
                  'hardware':os.uname().machine,'virtualization':'not independently established'},
        'libc':list(platform.libc_ver()),'uid':os.getuid(),'gid':os.getgid(),
        'storage':{'path':str(task),'free_bytes':shutil.disk_usage(task).free,
                   'device':task.stat().st_dev,'task_created_at':datetime.fromtimestamp(task.stat().st_mtime,timezone.utc).isoformat()},
        'limits':{'RLIMIT_AS':list(resource.getrlimit(resource.RLIMIT_AS)),
                  'memory_cap_enforced':False,'native_children_executed':0},
        'isolation':{'uid_map':uid_map,'gid_map':gid_map,'process_status':selected,
            'task_uid':task.stat().st_uid,'task_mode':oct(task.stat().st_mode & 0o777),
            'namespace_probe':'namespace-capability.json',
            'credential_separation':'NOT_ESTABLISHED','network_isolation':'NOT_ESTABLISHED'},
        'relevant_environment':{'child_allowlist':env,'controller_values_copied':False}}
    runtime.write_new(evidence/'host.json',host)
    bwrap = shutil.which('bwrap')
    if not bwrap:
        raise RuntimeError('Pre-observed namespace tool vanished; retain unresolved diagnosis')
    command = [bwrap,'--unshare-all','--die-with-parent','--new-session']
    for path in ('/usr','/bin','/lib','/lib64'):
        if Path(path).exists():
            command += ['--ro-bind',path,path]
    command += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp',
                '--bind',str(task),str(task),'--chdir',str(task),'--','/usr/bin/true']
    step = 'namespace-capability'
    stdout,stderr=[evidence/(step+'.'+suffix) for suffix in ('stdout','stderr')]
    begin=runtime.now(); clock=time.monotonic(); term='EXIT'; code=None
    # Logs are open before the child; only a short trusted utility can emit.
    def preexec():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024*1024,128*1024*1024))
    with stdout.open('xb') as out,stderr.open('xb') as err:
        try:
            proc=subprocess.Popen(command,cwd=task,env=env,stdin=subprocess.DEVNULL,
                stdout=out,stderr=err,close_fds=True,preexec_fn=preexec)
        except (OSError,subprocess.SubprocessError) as exc:
            err.write((type(exc).__name__+': '+str(exc)+'\n').encode())
            term='SPAWN_ERROR'
        else:
            try:
                proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                term='TIMEOUT'; os.killpg(proc.pid,signal.SIGKILL); proc.wait()
            code=proc.returncode
            if term=='EXIT' and code<0:
                term='SIGNAL'
    record={'schema':NS+'/setup-step','epoch':1,'step':step,'source_sha':source_sha,
        'source_sha256':runtime.sha(ROOT/SOURCE),'command':command,'environment':env,
        'cwd':str(task),'identity':{'uid':os.getuid(),'gid':os.getgid(),
            'groups':os.getgroups(),'no_new_privileges':selected['NoNewPrivs']=='1',
            'restriction_mode':'controller_only_trusted_system_capability_probe'},
        'executable_sha256':runtime.sha(bwrap),'started_at':begin,'finished_at':runtime.now(),
        'elapsed_seconds':time.monotonic()-clock,'deadline_seconds':120,
        'returncode':code,'signal':-code if code is not None and code<0 else None,
        'termination':term,'capture':{'status':'COMPLETE',
            'stdout_bytes':stdout.stat().st_size,'stderr_bytes':stderr.stat().st_size,
            'total_log_limit_bytes':runtime.LOG_CAP},
        'stdout_sha256':runtime.sha(stdout),'stderr_sha256':runtime.sha(stderr)}
    runtime.write_new(evidence/(step+'.json'),record)
    print(json.dumps({'step':step,'returncode':code,'termination':term}),flush=True)
    if code==0:
        runtime.write_new(evidence/'namespace-available.json',{'available':True,
            'source_sha':source_sha,'next':'Pre-record one diagnosed recovery using this available isolated environment before any dependency/native execution.'})
        return 0
    # Require the concrete host findings, not merely any unsuccessful command.
    mappings=lambda s:[tuple(map(int,line.split())) for line in s.splitlines()]
    exhausted=(mappings(uid_map)==[(0,0,1)] and mappings(gid_map)==[(0,0,1)]
        and all(int(selected[k],16)==0 for k in ('CapPrm','CapEff','CapBnd')))
    diag=stderr.read_text()
    denied=('Operation not permitted' in diag or 'No permissions to create' in diag)
    if not (exhausted and denied and term=='EXIT' and code!=0):
        raise RuntimeError('Isolation diagnosis unresolved; no speculative failure classification')
    inventory={p.name:{'bytes':p.stat().st_size,'sha256':runtime.sha(p)}
               for p in sorted(evidence.iterdir()) if p.is_file()}
    stop={'schema':NS+'/setup-stop','observed_at':runtime.now(),'source_sha':source_sha,
        'epoch':1,'failed_step':'worker-isolation-prerequisite',
        'reason':'DISTINCT_UID_UNMAPPED_AND_UNPRIVILEGED_NAMESPACE_UNAVAILABLE',
        'recovery':{'budget':1,'used':0,'rationale':'Only UID/GID 0 is mapped and no process capabilities are available. The already-installed unprivileged namespace tool failed before launching its payload. No supported accessible isolated worker or permitted environment move is evidenced; do not alter host controls.',
            'changed_conditions':[],'prior_failure':'initial-controller-tool-output.txt'},
        'runtime_layers':{k:'NOT_EXECUTED' for k in ('standalone','python_child','pinned_dependencies','cold_bridge')},
        'activity':runtime.ACTIVITY,'unperformed':runtime.UNPERFORMED,
        'evidence_inventory':inventory}
    runtime.write_new(evidence/'stop.json',stop)
    print('NO_GO prerequisite: worker credential/staged-file separation unavailable; no external engine executed.',flush=True)
    return 2


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true',required=True)
    parser.parse_args()
    raise SystemExit(diagnose())
