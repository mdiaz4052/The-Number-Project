# External Lean Navier–Stokes pinned replay and closure

This isolated package attempts exactly the R3 and periodic Comparator targets at
`openai/NavierStokesAndEuler@f9e8bc5b38b6e212696e8a30e3e91517af887bbd`.
It measures separate replay, statement, checker, axiom and dependency axes. It does
not establish physical truth or solve an unforced Navier–Stokes problem.

PROVISIONAL — INDEPENDENT AUDIT PENDING.

## Chronology and activation

`preregistration.v1.json` embeds and hashes the controlling packet and freezes all
its pins, resources, controls, result axes, dispositions, boundaries and nonclaims.
The sole-file freeze is `8e47e770a24b60b2b1f6abea753aebca27d9abfd`.
Draft PR #53 was created at `2026-09-12T22:52:12Z` with that sole-file head.
`pr_anchor.json` was published separately before any evaluator was introduced.

The anchor records a pre-execution activation amendment: the connected GitHub
writer supports branch creation, while shell Git writes and tag creation are
unavailable. A **single creation** of `execute/external-ns-replay-v1` from the
finalized runner commit is the deliberate launch. The workflow accepts only this
branch-create event and attempt 1. PR updates, push events, subsequent report
commits and incidental branch creations do not execute the target. No rerun is
implicit. A forward execution requires the packet's diagnosed operational failure
or expressly authorized reproducibility exception and must preserve both epochs.

## Isolation and interpretation

External subprocesses run as a separate nonprivileged account in systemd services
with `NoNewPrivileges`, a read-only host filesystem, protected host homes and
processes, one writable disposable workspace and `RestrictAddressFamilies=~AF_UNIX`.
The controller opens raw logs outside that writable workspace. No GitHub, Drive,
SSH or other write credential is in the external environment. The service wrapper
and its exact arguments are recorded per command. Unsupported protection is an
explicit capability failure, never a silently weakened sandbox.

The Comparator README's user-service command is tested separately. The host
service restriction is retained even when that user-service capability is absent;
any auxiliary credit must disclose this distinction. The pinned Comparator
binary is not patched. Lean's module build, Comparator's exported kernel replay,
and actual nanoda execution remain separate evidence.

`closure.py` parses the pinned exporter format. Its graph includes type, value,
and generated declaration edges. Missing constants and unknown records fail
closed. Instance/module metadata unavailable in the export is marked unknown.
Reachable ordinary opaque values are not mislabeled as axioms. Graph traversal
does not validate analytic meaning or the kernel, compiler, OS or hardware.

The fresh sealing job downloads raw evidence and runs only the trusted validator
from the recorded runner commit. It rejects missing paths, symlinks, unsafe names,
duplicate keys/commands and log digest disagreement. Missing graph/export outputs
are nonempty `NOT_PRODUCED` failure sentinels, never successful empty closures.
The archive digest is in a detached receipt to avoid a self-referential checksum.

## Focused validation

`python -m unittest discover -s Experiments/ExternalLeanNavierStokes/controls -v`

The five Lean/Comparator controls execute on the isolated hosted runner. Python
fixtures test parser and report failures; they are not a substitute for Lean
control replay. Final repository validation reuses the standing complete Python
suite and final exact-head Verify. No unrelated local mutation family or root
Lean build belongs to this experiment.

## Disposition and evidence

Execution is pending. Both final per-target dispositions and a durable sealed
bundle (or explicit sealing failure) are required before package 3 closes.
The execution record will be linked here after the bounded run. Leave this PR
unmerged; eventual merge must use **Create a merge commit**, never squash/rebase.
