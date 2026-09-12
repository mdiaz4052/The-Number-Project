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

**Final technical disposition: DEPENDENCY_CLOSURE_UNRESOLVED for both targets.**
Two environment attempts were made; **zero target replays** occurred. In epoch 2,
all pinned packages and auxiliary tools were reproduced. Controller fixture
creation then failed on workspace ownership before the required Lean controls.
The single operational retry allowance is exhausted. The workflow is now inert.

The [detached reconciliation](runner/reconciliation.json) is the controlling
package-3 disposition. The raw collector's catch-all environment-failure label
was too broad; original sealed bytes remain unchanged. This failure belongs to
the project-authored harness, not to the external mathematical proof.

[Epoch 1 sealed evidence](https://drive.google.com/file/d/1UMGLPrKYRFCmXKEsdkO5-zrRY_j_zMwH/view)
and [epoch 2 sealed evidence](https://drive.google.com/file/d/1L58D5TvrfrayTGU--w2ecA5a0KkNzejs/view)
are durably preserved. Commands, statuses, diagnostics, identities and failure
sentinels are included; no axiom/graph emptiness is inferred from those sentinels.
All seven formal package-2 boundaries remain unchanged. No proof replay,
Comparator target comparison/policy check, nanoda target replay, elaborated target
statement or measured target closure is credited.

Leave this PR unmerged; eventual merge must use **Create a merge commit**, never
squash/rebase. Independent review remains pending. Any later reuse must first
repair control/probe staging across the two Unix identities and the collector's
failure-to-axis mapping; this package does not authorize another execution.

## Diagnosed operational exception, before any target replay

Epoch 1 (`95453146f1119d809a90953d2aacee944d24d392`, run `34724754702`)
stopped at Cargo exit 101: `rustc -vV` could not be found. Rust 1.98.1
installation and direct version invocation succeeded. Neither target ran. The
raw and freshly sealed evidence is retained; archive SHA-256 is
`9c5e4a8a1d8722d811e960cd43ab0622f14311647c62ff15532f4e1a1deb7135`.

The anchor records the single packet-authorized operational exception. Epoch 2
binds `RUSTC` to `rustup which --toolchain 1.98.1 rustc` and activates only on
creation of `execute/external-ns-replay-v1-operational-retry`. All external pins
and resource limits remain unchanged. No further rerun is authorized. The first
workflow is an environment attempt, not a scientific target replay.


## Workflow-observation closure

Package 3 is decision-complete as an unsuccessful bounded execution, not as a
successful replay capability demonstration. Freeze/anchor chronology, finalized
runner activation, isolation, one justified retry and separate sealing were
preserved. Execution fidelity failed at control staging; the raw disposition also
required explicit reconciliation. The core scientific uncertainties remain open.

The cross-package recommendation is **ADJUST**, advisory only: retain minimal
current-state retrieval, immutable verification epochs, autonomous handoffs and
scope-specific independent-review qualifiers. Propose earlier execution-vehicle
and cross-user staging checks and tighter output budgeting. No standing workflow
change is adopted here, and no further housekeeping PR is proposed.
