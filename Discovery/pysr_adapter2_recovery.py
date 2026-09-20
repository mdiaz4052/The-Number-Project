"""One diagnosed, source-pinned recovery of the namespace prerequisite.

The initial bwrap failure is specifically NETLINK_ROUTE setup, not evidence that
filesystem isolation works or fails. Retain the host network under the work
order's explicit allowance; keep every filesystem/process isolation request.
No host security control is modified and no dependency/native engine is launched.
"""
import argparse
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
from Discovery import pysr_adapter2_runtime as r

SOURCE = 'Discovery/pysr_adapter2_recovery.py'


def main():
    source_sha=r.git('rev-parse','HEAD')
    if subprocess.check_output(['git','show',source_sha+':'+SOURCE],cwd=r.ROOT)!=(r.ROOT/SOURCE).read_bytes():
        raise RuntimeError('Recovery source must be committed before execution')
    old=r.PKG/'setup/epoch-01'
    plan=r.PKG/'setup/recovery_plan.json'
    if not plan.exists() or not (old/'stop.json').exists():
        raise RuntimeError('Committed plan and retained failed epoch required')
    if subprocess.check_output(['git','show',source_sha+':'+str(plan.relative_to(r.ROOT))],cwd=r.ROOT)!=plan.read_bytes():
        raise RuntimeError('Recovery plan must predate execution')
    task=Path('/tmp/tnp-pysr-adapter2-e02');task.mkdir(mode=0o700)
    evidence=r.PKG/'setup/epoch-02';evidence.mkdir()
    command=['/usr/bin/bwrap','--unshare-all','--share-net','--die-with-parent','--new-session']
    for p in ('/usr','/bin','/lib','/lib64'):
        if Path(p).exists(): command+=['--ro-bind',p,p]
    command+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--bind',str(task),str(task),
              '--chdir',str(task),'--','/usr/bin/true']
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    step='namespace-shared-network';stdout=evidence/(step+'.stdout');stderr=evidence/(step+'.stderr')
    begin=r.now();clock=time.monotonic();code=None;term='EXIT'
    def preexec():
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024*1024,128*1024*1024))
    with stdout.open('xb') as out,stderr.open('xb') as err:
        try:
            p=subprocess.Popen(command,cwd=task,env=env,stdin=subprocess.DEVNULL,
                stdout=out,stderr=err,close_fds=True,preexec_fn=preexec)
        except (OSError,subprocess.SubprocessError) as e:
            err.write((type(e).__name__+': '+str(e)+'\n').encode());term='SPAWN_ERROR'
        else:
            try:p.wait(timeout=120)
            except subprocess.TimeoutExpired:
                term='TIMEOUT';os.killpg(p.pid,signal.SIGKILL);p.wait()
            code=p.returncode
            if term=='EXIT' and code<0:term='SIGNAL'
    status=Path('/proc/self/status').read_text()
    fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in status.splitlines() if ':' in line}
    rec={'schema':r.NS+'/setup-step','epoch':2,'step':step,'source_sha':source_sha,
        'source_sha256':r.sha(r.ROOT/SOURCE),'command':command,'environment':env,'cwd':str(task),
        'identity':{'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),
            'no_new_privileges':fields['NoNewPrivs']=='1',
            'restriction_mode':'controller_only_trusted_system_capability_probe'},
        'executable_sha256':r.sha('/usr/bin/bwrap'),'started_at':begin,'finished_at':r.now(),
        'elapsed_seconds':time.monotonic()-clock,'deadline_seconds':120,'returncode':code,
        'signal':-code if code is not None and code<0 else None,'termination':term,
        'capture':{'status':'COMPLETE','stdout_bytes':stdout.stat().st_size,
            'stderr_bytes':stderr.stat().st_size,'total_log_limit_bytes':r.LOG_CAP},
        'stdout_sha256':r.sha(stdout),'stderr_sha256':r.sha(stderr)}
    r.write_new(evidence/(step+'.json'),rec)
    if code==0:
        r.write_new(evidence/'namespace_available.json',{'source_sha':source_sha,'state':'NAMESPACE_CAPABILITY_ONLY','credential_canary_required':True,'runtime_qualified':False})
        print('Namespace capability available; credential canary and native gates remain required.')
        return 0
    inventory={p.name:{'bytes':p.stat().st_size,'sha256':r.sha(p)} for p in sorted(evidence.iterdir()) if p.is_file()}
    stop={'schema':r.NS+'/setup-stop','observed_at':r.now(),'source_sha':source_sha,'epoch':2,
        'failed_step':step,'reason':'WORKER_ISOLATION_RECOVERY_FAILED',
        'recovery':{'budget':1,'used':1,'rationale':'Single diagnosed host-network recovery failed. No further setup epoch or speculative change is authorized.',
            'changed_conditions':['--share-net retains the existing restricted host network'],
            'prior_failure':'../epoch-01/namespace-capability.stderr'},
        'runtime_layers':{k:'NOT_EXECUTED' for k in ('standalone','python_child','pinned_dependencies','cold_bridge')},
        'activity':r.ACTIVITY,'unperformed':r.UNPERFORMED,'evidence_inventory':inventory}
    r.write_new(evidence/'stop.json',stop)
    print('Recovery failed; no dependency, Julia, PySR, smoke or target execution.')
    return 2


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true',required=True);p.parse_args()
    raise SystemExit(main())
