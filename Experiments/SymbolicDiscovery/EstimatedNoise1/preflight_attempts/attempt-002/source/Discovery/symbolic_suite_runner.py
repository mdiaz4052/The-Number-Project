"""Forward trusted-code runner v2: completed reads, cache misses and denials.

Python 3.12 remains the supported boundary. No hostile-code sandbox claim.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from Discovery.symbolic_benchmark_engine import encoded

ROOT = Path(__file__).resolve().parents[1]
ENGINE_FILES = tuple('Discovery/'+n+'.py' for n in (
    '__init__','symbolic_benchmark_engine','symbolic_suite_engine','constants','dimensions',
    'dimensional_search','planck_identities','dependency_definitions','monomial_constraints'))

WORKER = r'''
import sys, os, json, builtins, io, _io
# Outcome-independent standard-library closure, loaded before restricted discovery.
import fractions, hashlib, math, dataclasses, itertools, typing, argparse, csv, pathlib, __future__
stage = os.path.realpath(sys.argv[1])
stdlib = os.path.realpath(os.path.dirname(os.__file__))
request = json.load(sys.stdin)
payload, expected, probe = request['payload'], set(request['expected']), request['probe']
allowed_modules = {'Discovery' if p == 'Discovery/__init__.py' else p[:-3].replace('/','.') for p in expected}
startup_modules = set(sys.modules)
cache_paths = {os.path.dirname(p)+'/__pycache__/'+os.path.basename(p)[:-3]+'.'+sys.implementation.cache_tag+'.pyc' for p in expected}
successful, missing, denied, opened, attempts = set(), set(), set(), set(), set()

def label(path):
    if isinstance(path,int): return '<fd>/'+str(path)
    path = os.path.realpath(os.fsdecode(path))
    if path.startswith(stage+os.sep): return '<stage>/'+os.path.relpath(path,stage)
    if path.startswith(stdlib+os.sep) and 'site-packages' not in path: return '<stdlib>/'+os.path.relpath(path,stdlib)
    return '<outside>/'+os.path.basename(path)

def reject(message):
    denied.add(message)
    raise PermissionError(message)

def audit(event,args):
    if event == 'open':
        p = label(args[0]); attempts.add(p)
        if isinstance(args[0],int): reject('descriptor:'+p)
        mode = args[1]
        if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or args[2] & (os.O_WRONLY|os.O_RDWR):
            reject('write:'+p)
        if p.startswith('<stage>/') and p[8:] not in expected|cache_paths: reject('path:'+p)
        if not p.startswith(('<stage>/','<stdlib>/')): reject('path:'+p)
    if event == 'import' and args[0] not in startup_modules|allowed_modules:
        reject('module:'+args[0])
    if event.startswith(('socket.','subprocess.','os.system','os.exec','os.spawn')):
        reject('action:'+event)

class ObservedFile:
    def __init__(self,f,p): self.f,self.p=f,p
    def read(self,*a,**k):
        result=self.f.read(*a,**k); successful.add(self.p); return result
    def read1(self,*a,**k):
        result=self.f.read1(*a,**k); successful.add(self.p); return result
    def readinto(self,*a,**k):
        result=self.f.readinto(*a,**k); successful.add(self.p); return result
    def readline(self,*a,**k):
        result=self.f.readline(*a,**k); successful.add(self.p); return result
    def readlines(self,*a,**k):
        result=self.f.readlines(*a,**k); successful.add(self.p); return result
    def __iter__(self): return self
    def __next__(self):
        result=next(self.f); successful.add(self.p); return result
    def __enter__(self): self.f.__enter__(); return self
    def __exit__(self,*a): return self.f.__exit__(*a)
    def __getattr__(self,k): return getattr(self.f,k)

def observe(op):
    def wrapper(path,*a,**k):
        p=label(path)
        try:
            f=op(path,*a,**k)
        except FileNotFoundError:
            if p.startswith('<stage>/') and p[8:] in cache_paths: missing.add(p)
            else: denied.add('unexpected_missing:'+p)
            raise
        except OSError as e:
            denied.add('open_error:'+p+':'+type(e).__name__); raise
        opened.add(p)
        return ObservedFile(f,p)
    return wrapper

sys.addaudithook(audit)
builtins.open=observe(builtins.open)
io.open=observe(io.open)
_io.open=observe(_io.open)
_io.open_code=observe(_io.open_code)
sys.path.insert(0,stage)
result,error=None,None
try:
    if probe:
        if probe.startswith('module:'):
            __import__(probe.split(':',1)[1])
        else:
            with open(probe.replace('<stage>',stage),'rb') as f: f.read()
    from Discovery.symbolic_suite_engine import discover
    result=discover(payload)
except Exception as e:
    error=type(e).__name__+': '+str(e)
modules=sorted(k for k in sys.modules if k == 'Discovery' or k.startswith('Discovery.'))
unexpected=sorted(set(sys.modules)-startup_modules-allowed_modules)
print(json.dumps({'discovery':result,'error':error,'receipt':{
    'version':2,'python_minor':str(sys.version_info.major)+'.'+str(sys.version_info.minor),
    'cache_tag':sys.implementation.cache_tag,'successful_reads':sorted(successful),
    'expected_missing_cache_attempts':sorted(missing),'denied_unexpected_attempts':sorted(denied),
    'successful_opens':sorted(opened),'audit_open_attempts':sorted(attempts),
    'discovery_modules':modules,'unexpected_modules':unexpected}},sort_keys=True,allow_nan=False))
'''


def inventory(stage):
    return {p.relative_to(stage).as_posix(): {'kind':'symlink' if p.is_symlink() else 'file' if p.is_file() else 'directory',
        **({'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} if p.is_file() and not p.is_symlink() else {})}
        for p in sorted(stage.rglob('*'))}


def valid_receipt(output):
    r=output['receipt']
    expected=set(ENGINE_FILES)
    sources={'<stage>/'+p for p in expected}
    caches={'<stage>/'+str(Path(p).parent/'__pycache__'/(Path(p).stem+'.cpython-312.pyc')) for p in expected}
    modules={'Discovery' if p=='Discovery/__init__.py' else p[:-3].replace('/','.') for p in expected}
    before,after=r['inventory_before'],r['inventory_after']
    def staged(values): return {p for p in values if p.startswith('<stage>/')}
    return (output['error'] is None and r['version']==2 and r['python_minor']=='3.12' and r['cache_tag']=='cpython-312'
        and set(before)==expected|{'Discovery'} and before==after
        and all(before[p]['kind']=='file' for p in expected)
        and before['Discovery']['kind']=='directory'
        and not r['denied_unexpected_attempts'] and not r['unexpected_modules']
        and set(r['discovery_modules'])==modules
        and staged(r['successful_reads'])==sources and staged(r['successful_opens'])==sources
        and set(r['expected_missing_cache_attempts'])==caches
        and staged(r['audit_open_attempts'])==sources|caches)


class RunnerFailure(RuntimeError):
    def __init__(self,output):
        self.output=output
        super().__init__(output.get('error') or 'forward receipt/inventory failed closed')


def staged_discovery(payload, *, probe=None, stale_cache=False, enforce=True):
    if sys.version_info[:2] != (3,12):
        raise RuntimeError('Suite 1 requires frozen Python 3.12 environment')
    with tempfile.TemporaryDirectory(prefix='tnp-suite1-') as name:
        stage=Path(name)
        for p in ENGINE_FILES:
            dest=stage/p; dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/p,dest)
        if stale_cache:
            cache=stage/'Discovery/__pycache__/symbolic_suite_engine.cpython-312.pyc'
            cache.parent.mkdir(); cache.write_bytes(b'deliberately stale target-free fixture cache')
        before=inventory(stage)
        child=subprocess.run([sys.executable,'-I','-B','-c',WORKER,str(stage)],
            input=encoded({'payload':payload,'expected':list(ENGINE_FILES),'probe':probe}),
            capture_output=True,cwd=stage,env={'PATH':os.defpath,'PYTHONDONTWRITEBYTECODE':'1'},timeout=180)
        if child.returncode:
            raise RuntimeError('worker process failure: '+child.stderr.decode())
        result=json.loads(child.stdout)
        result['receipt'].update(inventory_before=before,inventory_after=inventory(stage),
            worker_sha256=hashlib.sha256(WORKER.encode()).hexdigest())
        if enforce and not valid_receipt(result): raise RunnerFailure(result)
        return result
