"""Capture parent-stage stdout/stderr before starting scientific operations."""
import argparse
from pathlib import Path
import subprocess
import sys

from Discovery.estimated_noise1 import ROOT, PKG, git, now, new_bytes, new_json, sha, bindings
from Discovery.estimated_noise1_schema import envelope


def launch(stage, private):
    private = Path(private).resolve()
    if private == ROOT or ROOT in private.parents: raise ValueError('private path inside repository')
    directory = private/'stage_logs'/stage
    directory.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, '-B', '-m', 'Discovery.estimated_noise1', stage, '--private-dir', str(private)]
    parent, started = git('rev-parse', 'HEAD'), now()
    with (directory/'stdout').open('xb') as stdout, (directory/'stderr').open('xb') as stderr:
        child = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr)
    new_json(directory/'receipt.json', envelope('stage-launch', {'stage': stage, 'parent_sha': parent,
        'command': command, 'started_utc': started, 'completed_utc': now(), 'returncode': child.returncode,
        'stdout_sha256': sha((directory/'stdout').read_bytes()),
        'stderr_sha256': sha((directory/'stderr').read_bytes())}, bindings()))
    if stage == 'evaluation' or child.returncode:
        for file in sorted((private/'stage_logs').rglob('*')):
            if file.is_file(): new_bytes(PKG/'execution_logs'/file.relative_to(private/'stage_logs'), file.read_bytes())
    print((directory/'stdout').read_text(), end='')
    print((directory/'stderr').read_text(), end='', file=sys.stderr)
    return child.returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('seed', 'data', 'calibration', 'discovery', 'evaluation'))
    parser.add_argument('--private-dir', required=True)
    args = parser.parse_args()
    raise SystemExit(launch(args.stage, args.private_dir))
