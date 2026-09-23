"""Opt-in, source-pinned native-runtime gate. Ordinary imports perform no setup.

Only the reached native stages are implemented here first. A successful native
gate permits a forward, committed dependency/bridge stage, not target data.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'Experiments/SymbolicDiscovery/PySRAdapter2'
NS = 'tnp-pysr-adapter/2'
SOURCE = 'Discovery/pysr_adapter2_runtime.py'
JULIA_ARCHIVE = 'julia-1.10.10-linux-x86_64.tar.gz'
JULIA_SHA = '6a78a03a71c7ab792e8673dc5cedb918e037f081ceb58b50971dfb7c64c5bf81'
CHECKSUM_URL = 'https://julialang-s3.julialang.org/bin/checksums/julia-1.10.10.sha256'
ARCHIVE_URL = 'https://julialang-s3.julialang.org/bin/linux/x64/1.10/' + JULIA_ARCHIVE
LOG_CAP = 256 * 1024 * 1024
EPOCH_BUDGET = 1200
WORK_UID = WORK_GID = 61102
ACTIVITY = dict(master_seed_created=False, target_rows_created=0,
                smoke_fits_executed=0, target_fits_executed=0, cards_issued=0,
                selections_sealed=0, heldout_evaluations=0)
UNPERFORMED = {k: 'NOT_EXECUTED' for k in (
    'integration', 'fixtures', 'mutations', 'native_export', 'seed', 'data',
    'target_fits', 'selections', 'heldout')}


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode()


def write_new(path, value):
    with Path(path).open('xb') as f:
        f.write(value if isinstance(value, bytes) else encoded(value))


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def archive_inventory(path):
    """Validate the entire tar before extracting, including link chains.

    No devices/FIFOs, absolute names, parent components, duplicate names,
    escaping links or writes through symlink parents. Legitimate internal
    links remain links. Tar ownership is not restored (numeric unprivileged UID).
    """
    inventory, links, names = [], {}, set()
    with tarfile.open(path, 'r:gz') as tar:
        members = tar.getmembers()
        for m in members:
            p = PurePosixPath(m.name)
            if p.is_absolute() or '..' in p.parts or not p.parts:
                raise ValueError('unsafe member path: ' + m.name)
            name = str(p)
            if name in names or p.parts[0] != 'julia-1.10.10':
                raise ValueError('duplicate or unexpected root: ' + name)
            names.add(name)
            if not (m.isfile() or m.isdir() or m.issym() or m.islnk()):
                raise ValueError('special member: ' + name)
            if m.mode & 0o6000:
                raise ValueError('setuid/setgid member: ' + name)
            if m.issym() or m.islnk():
                link = PurePosixPath(m.linkname)
                if link.is_absolute():
                    raise ValueError('absolute link: ' + name)
                parts = list(p.parent.parts if m.issym() else ())
                for part in link.parts:
                    if part == '..':
                        if len(parts) <= 1:
                            raise ValueError('escaping link: ' + name)
                        parts.pop()
                    elif part != '.':
                        parts.append(part)
                if not parts or parts[0] != 'julia-1.10.10':
                    raise ValueError('escaping link: ' + name)
                links[name] = '/'.join(parts)
            inventory.append({'name': name, 'size': m.size,
                              'type': m.type.decode('ascii'), 'link': m.linkname,
                              'mode': m.mode})
        symlinks = {str(PurePosixPath(m.name)) for m in members if m.issym()}
        for name in names:
            if any(str(p) in symlinks for p in PurePosixPath(name).parents):
                raise ValueError('member traverses symlink: ' + name)
        for origin in links:
            seen, target = {origin}, links[origin]
            while target in links:
                if target in seen:
                    raise ValueError('cyclic link: ' + origin)
                seen.add(target)
                target = links[target]
            if target not in names:
                raise ValueError('missing link target: ' + origin)
    return inventory


def restricted_preexec():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Python/Julia startup may reserve virtual address space; this is not an
    # untruthful 6 GiB physical-memory claim. Host limits are captured separately.
    os.setgroups([])
    os.setgid(WORK_GID)
    os.setuid(WORK_UID)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise OSError(ctypes.get_errno(), 'PR_SET_NO_NEW_PRIVS')


class Supervisor:
    def __init__(self, task, evidence, source_sha):
        self.task, self.evidence, self.source_sha = task, evidence, source_sha
        self.source_hash = sha(ROOT / SOURCE)
        self.used_seconds = 0.0
        self.log_bytes = 0
        self.steps = []
        self.env = {'PATH': '/usr/bin:/bin', 'HOME': str(task / 'home'),
                    'TMPDIR': str(task / 'tmp'), 'LANG': 'C.UTF-8',
                    'LC_ALL': 'C.UTF-8', 'PYTHONNOUSERSITE': '1',
                    'PYTHONDONTWRITEBYTECODE': '1', 'JULIA_NUM_THREADS': '1',
                    'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
                    'JULIA_DEPOT_PATH': str(task / 'depot')}
        self.restriction_mode = 'distinct_uid_no_new_privileges'
        self.prefix = []

    def run(self, step, command, deadline=120, *, namespace_probe=False):
        budget = EPOCH_BUDGET - self.used_seconds
        if budget <= 0 or self.log_bytes >= LOG_CAP:
            raise RuntimeError('Epoch budget exhausted before launch')
        deadline = min(deadline, budget)
        actual = self.prefix + list(command)
        started_at, start = now(), time.monotonic()
        outpath, errpath = [self.evidence / (step + '.' + x)
                            for x in ('stdout', 'stderr')]
        sizes = {'stdout': 0, 'stderr': 0}
        termination, code, complete = 'EXIT', None, True
        with outpath.open('xb') as out, errpath.open('xb') as err:
            try:
                proc = subprocess.Popen(actual, cwd=self.task, env=self.env,
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, close_fds=True,
                    preexec_fn=restricted_preexec)
            except (OSError, subprocess.SubprocessError) as exc:
                data = (type(exc).__name__ + ': ' + str(exc) + '\n').encode()
                err.write(data)
                sizes['stderr'] += len(data)
                self.log_bytes += len(data)
                termination = 'SPAWN_ERROR'
            else:
                sel = selectors.DefaultSelector()
                for pipe, label, dest in [(proc.stdout, 'stdout', out),
                                          (proc.stderr, 'stderr', err)]:
                    os.set_blocking(pipe.fileno(), False)
                    sel.register(pipe, selectors.EVENT_READ, (label, dest))
                killed = False
                while sel.get_map():
                    if not killed and time.monotonic() - start >= deadline:
                        termination, killed = 'TIMEOUT', True
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    for key, _ in sel.select(0.1):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            sel.unregister(key.fileobj)
                            key.fileobj.close()
                            continue
                        label, dest = key.data
                        remaining = LOG_CAP - self.log_bytes
                        kept = chunk[:max(0, remaining)]
                        dest.write(kept)
                        sizes[label] += len(kept)
                        self.log_bytes += len(kept)
                        if len(kept) < len(chunk):
                            complete = False
                            termination = 'LOG_LIMIT'
                            if not killed:
                                killed = True
                                try:
                                    os.killpg(proc.pid, signal.SIGKILL)
                                except ProcessLookupError:
                                    pass
                sel.close()
                # A child can close its logs before stopping. Deadline still binds.
                try:
                    proc.wait(timeout=max(0.01, deadline - (time.monotonic() - start)))
                except subprocess.TimeoutExpired:
                    termination = 'TIMEOUT'
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                code = proc.returncode
                if termination == 'EXIT' and code < 0:
                    termination = 'SIGNAL'
        elapsed = time.monotonic() - start
        self.used_seconds += elapsed
        record = {'schema': NS + '/setup-step', 'epoch': 1, 'step': step,
            'source_sha': self.source_sha, 'source_sha256': self.source_hash,
            'command': actual, 'environment': self.env, 'cwd': str(self.task),
            'identity': {'uid': WORK_UID, 'gid': WORK_GID, 'groups': [],
                'no_new_privileges': True, 'restriction_mode': self.restriction_mode},
            'executable_sha256': sha(actual[0]), 'started_at': started_at,
            'finished_at': now(), 'elapsed_seconds': elapsed,
            'deadline_seconds': deadline, 'returncode': code,
            'signal': -code if code is not None and code < 0 else None,
            'termination': termination,
            'capture': {'status': 'COMPLETE' if complete else 'LIMIT_STOP',
                'stdout_bytes': sizes['stdout'], 'stderr_bytes': sizes['stderr'],
                'total_log_limit_bytes': LOG_CAP},
            'stdout_sha256': sha(outpath), 'stderr_sha256': sha(errpath)}
        write_new(self.evidence / (step + '.json'), record)
        self.steps.append(record)
        print(json.dumps({'step': step, 'returncode': code,
                          'termination': termination, 'seconds': round(elapsed, 3)}), flush=True)
        return record

    def stage(self, name, text):
        p = self.task / name
        write_new(p, text.encode())
        os.chown(p, WORK_UID, WORK_GID)
        os.chmod(p, 0o400)
        write_new(self.evidence / name, text.encode())
        return str(p)

    def stop(self, failed_step, reason, layers, *, remedy=None):
        inventory = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                     for p in sorted(self.evidence.iterdir()) if p.is_file()}
        record = {'schema': NS + '/setup-stop', 'observed_at': now(),
            'source_sha': self.source_sha, 'epoch': 1, 'failed_step': failed_step,
            'reason': reason,
            'recovery': {'budget': 1, 'used': 0,
                'rationale': remedy or 'No evidenced permitted remedy; no speculative retry.',
                'changed_conditions': [], 'prior_failure': failed_step},
            'runtime_layers': layers, 'activity': ACTIVITY,
            'unperformed': UNPERFORMED, 'evidence_inventory': inventory}
        write_new(self.evidence / 'stop.json', record)
        print(json.dumps({'state': 'STOPPED', 'failed_step': failed_step, 'reason': reason}), flush=True)
        return 2


def native_gate():
    if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('CPython 3.12 required')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64' or platform.libc_ver()[0] != 'glibc':
        raise RuntimeError('Frozen native Linux glibc x86_64 recipe required')
    if git('status', '--porcelain', '--untracked-files=no'):
        raise RuntimeError('Tracked source must be clean before execution')
    source_sha = git('rev-parse', 'HEAD')
    if subprocess.check_output(['git', 'show', source_sha + ':' + SOURCE], cwd=ROOT) != (ROOT / SOURCE).read_bytes():
        raise RuntimeError('Commit the exact runtime source before execution')
    anchor = json.loads((PKG / 'anchor.json').read_text())
    if datetime.fromisoformat(anchor['created_at'].replace('Z', '+00:00')) >= datetime.now(timezone.utc):
        raise RuntimeError('Draft anchor must precede execution')
    task = Path('/tmp/tnp-pysr-adapter2-e01')
    task.mkdir(mode=0o700)  # Never reset/reuse a prior attempt silently.
    os.chown(task, WORK_UID, WORK_GID)
    for name in ('home', 'tmp', 'depot', 'project', 'extracted'):
        p = task / name
        p.mkdir(mode=0o700)
        os.chown(p, WORK_UID, WORK_GID)
    evidence = PKG / 'setup' / 'epoch-01'
    evidence.mkdir(parents=True)
    s = Supervisor(task, evidence, source_sha)
    layers = {k: 'NOT_EXECUTED' for k in ('standalone', 'python_child', 'pinned_dependencies', 'cold_bridge')}
    limits = {name: list(resource.getrlimit(getattr(resource, name)))
              for name in ('RLIMIT_AS', 'RLIMIT_DATA', 'RLIMIT_NOFILE', 'RLIMIT_NPROC', 'RLIMIT_CORE')}
    host = {'schema': NS + '/host', 'observed_at': now(),
        'python': {'implementation': sys.implementation.name, 'version': platform.python_version(),
                   'executable': sys.executable, 'sha256': sha(sys.executable)},
        'platform': platform.platform(), 'machine': {'process': platform.machine(),
                   'hardware': os.uname().machine, 'virtualization': 'not independently established'},
        'libc': list(platform.libc_ver()), 'uid': os.getuid(), 'gid': os.getgid(),
        'storage': {'path': str(task), 'free_bytes': shutil.disk_usage(task).free,
                    'statvfs_block_size': os.statvfs(task).f_bsize,
                    'mount_observation': subprocess.check_output(['findmnt','-n','-o','FSTYPE,TARGET','-T',str(task)]).decode().strip()},
        'limits': {'inherited': limits, 'core_dump_bytes': 0,
                   'memory_cap_enforced': False,
                   'memory_note': 'No physical-memory cgroup established; process address-space inherited. 6 GiB preference not claimed enforced.'},
        'isolation': {'controller_uid': os.getuid(), 'proposed_worker_uid': WORK_UID,
            'task_mode': oct(task.stat().st_mode & 0o777),
            'controller_roots': [{'path': str(p), 'mode': oct(p.stat().st_mode & 0o777),
                                  'uid': p.stat().st_uid} for p in (Path('/root'), Path('/workspace/scratch'))],
            'namespace': 'to_be_probed', 'network': 'to_be_probed'},
        'relevant_environment': {k: os.environ.get(k) for k in ('LD_LIBRARY_PATH','LD_PRELOAD','JULIA_BINDIR','JULIA_PROJECT','PYTHONHOME','PYTHONPATH')}}
    write_new(evidence / 'host.json', host)
    if host['storage']['free_bytes'] < 3 * 1024**3:
        return s.stop('host-prerequisite', 'INSUFFICIENT_LOCAL_STORAGE', layers)
    # No dependency or native engine is executed until access canaries pass.
    probe = """import ctypes,json,os,pathlib
denied={}
for p in ['/root','/workspace/scratch','/proc/%s/environ']:
    try:
        if p.endswith('/environ'):
            with open(p,'rb') as f: f.read(0)
        else: os.listdir(p)
        denied[p]=False
    except (PermissionError,FileNotFoundError): denied[p]=True
libc=ctypes.CDLL(None)
out={'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),'no_new_privileges':libc.prctl(39,0,0,0,0),'denied':denied,'environment_keys':sorted(os.environ),'staged_files':sorted(x.name for x in pathlib.Path('.').iterdir())}
print(json.dumps(out,sort_keys=True))
assert out['uid']==61102 and out['gid']==61102 and out['groups']==[] and out['no_new_privileges']==1 and all(denied.values())
""" % os.getpid()
    probe_path = s.stage('access_probe.py', probe)
    r = s.run('access-canary', [sys.executable, '-I', '-B', probe_path])
    if r['returncode'] != 0:
        return s.stop('access-canary', 'WORKER_RESTRICTIONS_UNAVAILABLE', layers)
    # Prefer OS namespaces; if unavailable the predeclared distinct-UID route
    # remains usable only with the passed controller/staging restrictions.
    bwrap = shutil.which('bwrap')
    if bwrap:
        prefix = [bwrap, '--unshare-all', '--die-with-parent', '--new-session']
        for p in ('/usr','/bin','/lib','/lib64'):
            if Path(p).exists():
                prefix += ['--ro-bind', p, p]
        prefix += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp',
                   '--bind',str(task),str(task),'--chdir',str(task),'--']
        r = s.run('namespace-capability', prefix + ['/usr/bin/true'])
        # Native commands need Python's system runtime and CA files too. A
        # successful namespace probe is retained; a forward source will bind
        # those exact system paths before dependency execution in that mode.
        if r['returncode'] == 0:
            write_new(evidence / 'namespace-available.json', {'available': True,
                'state':'FORWARD_SOURCE_REQUIRED_TO_BIND_PYTHON_AND_CA_PATHS'})
            return 0
    write_new(evidence / 'isolation.json', {'mode': s.restriction_mode,
        'credential_environment_inherited': False, 'controller_canaries': 'PASS',
        'network_disabled': False, 'network_limitation': 'OS network namespace unavailable; host network restrictions remain. Dependency-only network use; offline dependency mode required after resolution.',
        'limitations': 'Distinct UID plus existing permissions and staged arguments; not protection against arbitrary malicious code, same-identity peers or undeclared world-readable files.'})
    curl = shutil.which('curl')
    if not curl:
        return s.stop('download-prerequisite', 'CURL_UNAVAILABLE', layers)
    checksum_file = task / 'official.sha256'
    r = s.run('publisher-checksum', [curl, '--fail', '--show-error', '--location',
        '--connect-timeout','20','--max-time','110','--output',str(checksum_file),CHECKSUM_URL])
    if checksum_file.exists():
        write_new(evidence / 'official.sha256', checksum_file.read_bytes())
    if r['returncode'] != 0:
        return s.stop('publisher-checksum', 'OFFICIAL_CHECKSUM_FETCH_FAILED', layers)
    lines = checksum_file.read_text().splitlines()
    matches = [x.split()[0] for x in lines if len(x.split()) == 2 and x.split()[1].lstrip('*') == JULIA_ARCHIVE]
    if matches != [JULIA_SHA]:
        return s.stop('publisher-checksum', 'PUBLISHER_CHECKSUM_DISAGREEMENT', layers)
    archive = task / JULIA_ARCHIVE
    r = s.run('julia-download', [curl, '--fail', '--show-error', '--location',
        '--connect-timeout','20','--max-time','590','--output',str(archive),ARCHIVE_URL], 600)
    if r['returncode'] != 0:
        return s.stop('julia-download', 'OFFICIAL_ARCHIVE_FETCH_FAILED', layers)
    actual_hash = sha(archive)
    write_new(evidence / 'archive.json', {'url':ARCHIVE_URL, 'bytes':archive.stat().st_size,
        'expected_sha256':JULIA_SHA,'actual_sha256':actual_hash,'checksum_source':CHECKSUM_URL})
    if actual_hash != JULIA_SHA:
        return s.stop('julia-download', 'DOWNLOADED_ARCHIVE_DIGEST_MISMATCH', layers)
    try:
        inventory = archive_inventory(archive)
    except Exception as exc:
        write_new(evidence / 'archive-validation-error.txt', (type(exc).__name__ + ': ' + str(exc) + '\n').encode())
        return s.stop('archive-validation', 'UNSAFE_OR_INCOMPLETE_ARCHIVE', layers)
    write_new(evidence / 'archive_members.json', inventory)
    r = s.run('julia-extraction', ['/usr/bin/tar', '--no-same-owner', '--no-same-permissions',
        '-xzf',str(archive),'-C',str(task / 'extracted')])
    if r['returncode'] != 0:
        return s.stop('julia-extraction', 'ARCHIVE_EXTRACTION_FAILED', layers)
    julia = task / 'extracted/julia-1.10.10/bin/julia'
    if not julia.is_file() or not os.access(julia, os.X_OK):
        return s.stop('julia-extraction', 'EXPECTED_EXECUTABLE_MISSING', layers)
    write_new(evidence / 'julia-identity.json', {'path':str(julia), 'sha256':sha(julia),
        'archive_sha256':actual_hash,'extraction_complete':True})
    r = s.run('julia-standalone', [str(julia),'--startup-file=no','--history-file=no','-e',
        'println(VERSION); println(Sys.MACHINE); println(1 + 1)'])
    if r['returncode'] != 0:
        layers['standalone'] = 'FAIL'
        return s.stop('julia-standalone', 'JULIA_STANDALONE_STARTUP_FAILED', layers)
    out = (evidence / 'julia-standalone.stdout').read_text().splitlines()
    if out != ['1.10.10','x86_64-linux-gnu','2']:
        layers['standalone'] = 'FAIL'
        return s.stop('julia-standalone', 'JULIA_STANDALONE_IDENTITY_MISMATCH', layers)
    r = s.run('julia-libjulia', [str(julia),'--startup-file=no','--history-file=no','-e',
        'using Libdl; println(Libdl.dlpath("libjulia"))'])
    if r['returncode'] != 0:
        layers['standalone'] = 'FAIL'
        return s.stop('julia-libjulia', 'JULIA_STANDALONE_LIBRARY_PROBE_FAILED', layers)
    lib = Path((evidence / 'julia-libjulia.stdout').read_text().strip())
    if not lib.is_file():
        layers['standalone'] = 'FAIL'
        return s.stop('julia-libjulia', 'LIBJULIA_PATH_MISSING', layers)
    layers['standalone'] = 'PASS'
    child = """import json,platform,subprocess,sys
cmd=[sys.argv[1],'--startup-file=no','--history-file=no','-e','using Libdl; println(Libdl.dlpath("libjulia"))']
p=subprocess.run(cmd)
print(json.dumps({'python':platform.python_version(),'executable':sys.executable,'julia_returncode':p.returncode,'julia_signal':-p.returncode if p.returncode<0 else None}))
sys.exit(0 if p.returncode==0 else 1)
"""
    child_path = s.stage('python_child_probe.py',child)
    r = s.run('python-child', [sys.executable,'-I','-B',child_path,str(julia)])
    if r['returncode'] != 0:
        layers['python_child'] = 'FAIL'
        return s.stop('python-child','PYTHON_PARENT_LIBRARY_PROBE_FAILED',layers)
    layers['python_child'] = 'PASS'
    write_new(evidence / 'native_layers.json', {'state':'NATIVE_LAYERS_COMPLETE',
        'source_sha':source_sha,'runtime_layers':layers,'used_seconds':s.used_seconds,
        'log_bytes':s.log_bytes,'task':str(task),'environment':s.env,
        'not_runtime_qualified':True})
    print('Native layers passed. Commit pinned dependency/bridge source before continuing.', flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['qualify-native'])
    parser.add_argument('--execute', action='store_true', required=True)
    args = parser.parse_args()
    if args.command == 'qualify-native':
        return native_gate()


if __name__ == '__main__':
    raise SystemExit(main())
