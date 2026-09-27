"""Retained pre-seed engineering qualification; never creates a scientific seed."""
import argparse
from pathlib import Path
import subprocess
import sys
import traceback

from Discovery.estimated_noise1 import ROOT, PKG, SOURCE_PATHS, environment, sha, now, new_bytes, new_json, emit
from Discovery.estimated_noise1_calibration import digest, loads


def run(qualify=False):
    if (PKG/'seed_commitment.json').exists(): raise ValueError('preflight prohibited after scientific seed')
    attempts = PKG/'preflight_attempts'
    n = len(list(attempts.glob('attempt-*')))+1
    dest = attempts/f'attempt-{n:03d}'
    dest.mkdir(parents=True)
    started, env = now(), environment()
    manifest = {}
    for path in SOURCE_PATHS:
        raw = (ROOT/path).read_bytes()
        manifest[path] = sha(raw)
        new_bytes(dest/'source'/path, raw)
    command = [sys.executable, '-B', '-m', 'unittest', 'tests.test_estimated_noise1', '-v']
    completed = subprocess.run(command, cwd=ROOT, capture_output=True)
    new_bytes(dest/'tests.stdout', completed.stdout)
    new_bytes(dest/'tests.stderr', completed.stderr)
    report = {'started_utc': started, 'completed_utc': now(), 'environment': env,
              'source_manifest': manifest, 'command': command, 'returncode': completed.returncode,
              'stdout_sha256': sha(completed.stdout), 'stderr_sha256': sha(completed.stderr),
              'fixture_seed_label': 'deterministic engineering fixtures; e repeated 64 times, not scientific seed',
              'qualified': False, 'numerical_corners': None, 'mutations': None, 'exception': None}
    if completed.returncode == 0:
        try:
            from Discovery.estimated_noise1_fixtures import numerical_corners
            from Discovery.estimated_noise1_mutations import run as mutations
            report['numerical_corners'] = numerical_corners()
            report['mutations'] = mutations()
            report['qualified'] = report['numerical_corners']['pass']
        except Exception:
            report['exception'] = traceback.format_exc()
    report['completed_utc'] = now()
    new_json(dest/'receipt.json', report)
    if qualify and report['qualified']:
        emit('preflight.json', 'preflight', {**report, 'qualified_attempt': dest.relative_to(PKG).as_posix(),
            'attempt_receipt_sha256': sha((dest/'receipt.json').read_bytes()),
            'prior_attempts': [{'path': p.parent.relative_to(PKG).as_posix(),
                               'qualified': loads(p.read_bytes())['qualified'], 'receipt_sha256': sha(p.read_bytes())}
                              for p in sorted(attempts.glob('*/receipt.json')) if p.parent != dest]})
    print('Engineering attempt', n, 'PASS' if report['qualified'] else 'FAIL', flush=True)
    print(completed.stderr.decode(errors='replace'), end='')
    if report['exception']: print(report['exception'])
    return report['qualified']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualify', action='store_true')
    args = parser.parse_args()
    raise SystemExit(0 if run(args.qualify) else 1)
