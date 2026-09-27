"""Trusted-code pair worker using the accepted staged runner's read semantics.

Only __init__ and the pure pair estimator enter this stage. Discovery itself uses
the unchanged symbolic_suite_runner. This is not an OS/hostile-code sandbox.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from Discovery.estimated_noise1_calibration import encoded, loads
from Discovery.symbolic_suite_runner import WORKER, inventory

ROOT = Path(__file__).resolve().parents[1]
FILES = ('Discovery/__init__.py', 'Discovery/estimated_noise1_calibration.py')
CALIBRATION_WORKER = WORKER.replace(
    'from Discovery.symbolic_suite_engine import discover',
    'from Discovery.estimated_noise1_calibration import estimate as discover')


def valid(output):
    r = output['receipt']
    sources = {'<stage>/' + p for p in FILES}
    caches = {'<stage>/' + str(Path(p).parent / '__pycache__' /
              (Path(p).stem + '.cpython-312.pyc')) for p in FILES}
    modules = {'Discovery', 'Discovery.estimated_noise1_calibration'}
    before = r['inventory_before']
    staged = lambda values: {p for p in values if p.startswith('<stage>/')}
    return (output['error'] is None and r['version'] == 2 and
            r['python_minor'] == '3.12' and r['cache_tag'] == 'cpython-312' and
            set(before) == set(FILES) | {'Discovery'} and before == r['inventory_after'] and
            all(before[p]['kind'] == 'file' for p in FILES) and
            before['Discovery']['kind'] == 'directory' and
            not r['denied_unexpected_attempts'] and not r['unexpected_modules'] and
            set(r['discovery_modules']) == modules and
            staged(r['successful_reads']) == sources and staged(r['successful_opens']) == sources and
            set(r['expected_missing_cache_attempts']) == caches and
            staged(r['audit_open_attempts']) == sources | caches and
            r['worker_sha256'] == hashlib.sha256(CALIBRATION_WORKER.encode()).hexdigest())


class CalibrationFailure(RuntimeError):
    def __init__(self, output):
        self.output = output
        super().__init__(output.get('error') or 'calibration read/cache receipt invalid')


def staged_calibration(payload, *, probe=None, stale_cache=False, enforce=True):
    if sys.implementation.name != 'cpython' or sys.version_info[:2] != (3, 12):
        raise RuntimeError('CPython 3.12 required')
    with tempfile.TemporaryDirectory(prefix='tnp-estimated-noise1-cal-') as name:
        stage = Path(name)
        for p in FILES:
            dest = stage / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / p, dest)
        if stale_cache:
            cache = stage / 'Discovery/__pycache__/estimated_noise1_calibration.cpython-312.pyc'
            cache.parent.mkdir()
            cache.write_bytes(b'target-free deliberately stale fixture cache')
        before = inventory(stage)
        child = subprocess.run([sys.executable, '-I', '-B', '-c', CALIBRATION_WORKER, str(stage)],
            input=encoded({'payload': payload, 'expected': list(FILES), 'probe': probe}),
            capture_output=True, cwd=stage,
            env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=180)
        if child.returncode:
            raise CalibrationFailure({'error': 'child process failure',
                'returncode': child.returncode, 'stdout': child.stdout.decode(errors='replace'),
                'stderr': child.stderr.decode(errors='replace')})
        try:
            result = loads(child.stdout)
        except Exception as exc:
            raise CalibrationFailure({'error': 'child output parse: ' + str(exc),
                'returncode': child.returncode, 'stdout': child.stdout.decode(errors='replace'),
                'stderr': child.stderr.decode(errors='replace')}) from exc
        result['receipt'].update(inventory_before=before, inventory_after=inventory(stage),
            worker_sha256=hashlib.sha256(CALIBRATION_WORKER.encode()).hexdigest())
        if enforce and not valid(result):
            raise CalibrationFailure(result)
        return result
