#!/usr/bin/env bash
set -euo pipefail
# This file controls the hosted runner; external code never runs as the job user.
task_root=/var/lib/tnp-external
task_code=/opt/tnp-external-code
task_raw="$RUNNER_TEMP/external-ns-raw"
mkdir -p "$task_raw"
sudo install -d -m 755 "$task_root" "$task_code" /opt/tnp-bin
sudo cp -a Experiments/ExternalLeanNavierStokes/. "$task_code/"
sudo chmod -R a-w "$task_code"
sudo useradd --system --home-dir "$task_root/work/home" --shell /usr/sbin/nologin tnpexternal
sudo install -d -o tnpexternal -g tnpexternal -m 755 "$task_root/work"
for task_dir in home tmp; do
  sudo install -d -o tnpexternal -g tnpexternal -m 755 "$task_root/work/$task_dir"
done
# Go is installed by the exact setup-go action/version, not by external scripts.
if command -v go >/dev/null; then
  task_go_root="$(go env GOROOT)"
  sudo ln -s "$task_go_root" /opt/tnp-go
fi
if command -v rustup >/dev/null; then
  sudo cp -L "$(command -v rustup)" /opt/tnp-bin/rustup
  sudo chmod 755 /opt/tnp-bin/rustup
fi
export TNP_CODE_SHA
TNP_CODE_SHA="$(git rev-parse HEAD)"
python3 "$task_code/runner/execute.py" --work "$task_root/work" --raw "$task_raw"
python3 "$task_code/runner/seal.py" validate "$task_raw"
