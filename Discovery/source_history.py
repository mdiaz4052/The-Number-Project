"""Shared Git-history verification for committed experiment artifacts.

The command-line guards distinguish an unverifiable checkout (for example, an
archive or a shallow audit clone) from a verified methodological violation.  This
keeps missing history from being reported as evidence of tampering while retaining
hard failures for genuine ancestry and source-state mismatches.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import re
import subprocess
import sys
from typing import Sequence


VERIFIED = "verified"


class SourceVerificationError(RuntimeError):
    """Base class carrying the stable CLI status and exit code."""

    status = "source_verification_failed"
    exit_code = 1


class SourceHistoryUnavailableError(SourceVerificationError):
    status = "history_unavailable"
    exit_code = 2


class SourceAncestryViolationError(SourceVerificationError):
    status = "ancestry_violated"


class SourceStateViolationError(SourceVerificationError):
    status = "source_state_violated"


class SourceMetadataError(SourceVerificationError):
    status = "source_metadata_invalid"


def _git(
    arguments: Sequence[str],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as error:
        raise SourceHistoryUnavailableError(
            f"Git history cannot be inspected: {error}"
        ) from error


def repository_root(path: Path = Path(".")) -> Path:
    """Return the Git root or a stable history-unavailable outcome."""

    completed = _git(("rev-parse", "--show-toplevel"), cwd=path)
    if completed.returncode != 0:
        raise SourceHistoryUnavailableError(
            "repository history is unavailable; run the check in a complete Git checkout"
        )
    return Path(completed.stdout.strip()).resolve()


def _is_shallow(root: Path) -> bool:
    completed = _git(("rev-parse", "--is-shallow-repository"), cwd=root)
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def verify_committed_source_state(
    root: Path,
    source_commit_sha: str,
    *,
    source_paths: Sequence[str],
    artifact_label: str,
) -> str:
    """Verify source ancestry and freshness with explicit failure categories."""

    if not re.fullmatch(r"[0-9a-f]{40}", source_commit_sha):
        raise SourceMetadataError(f"{artifact_label} source commit SHA is invalid")

    commit = _git(("cat-file", "-e", f"{source_commit_sha}^{{commit}}"), cwd=root)
    if commit.returncode != 0:
        if _is_shallow(root):
            raise SourceHistoryUnavailableError(
                f"{artifact_label} source commit is absent from this shallow checkout"
            )
        raise SourceMetadataError(
            f"{artifact_label} source commit is not present in repository history"
        )

    resolved = _git(("rev-parse", source_commit_sha), cwd=root)
    if resolved.returncode != 0 or resolved.stdout.strip() != source_commit_sha:
        raise SourceMetadataError(
            f"{artifact_label} source commit SHA does not resolve exactly"
        )

    ancestor = _git(
        ("merge-base", "--is-ancestor", source_commit_sha, "HEAD"),
        cwd=root,
    )
    if ancestor.returncode != 0:
        if _is_shallow(root):
            raise SourceHistoryUnavailableError(
                f"{artifact_label} source ancestry cannot be verified in this shallow checkout"
            )
        if ancestor.returncode == 1:
            raise SourceAncestryViolationError(
                f"{artifact_label} source commit is not an ancestor of HEAD"
            )
        raise SourceMetadataError(
            f"{artifact_label} source ancestry check could not be completed"
        )

    changed = _git(
        ("diff", "--quiet", source_commit_sha, "--", *source_paths),
        cwd=root,
    )
    if changed.returncode == 1:
        raise SourceStateViolationError(
            f"{artifact_label} result-driving source differs from recorded source"
        )
    if changed.returncode != 0:
        if _is_shallow(root):
            raise SourceHistoryUnavailableError(
                f"{artifact_label} source state cannot be verified in this shallow checkout"
            )
        raise SourceMetadataError(
            f"{artifact_label} source comparison could not be completed"
        )
    return VERIFIED


def exit_for_source_verification_error(error: SourceVerificationError) -> None:
    """Print one stable diagnostic and terminate without a Python traceback."""

    print(f"{error.status}: {error}", file=sys.stderr)
    raise SystemExit(error.exit_code)


def verify_preregistration_freeze(
    root: Path, *, baseline: str, commit: str, path: str, sha256: str,
) -> bytes:
    """Verify an actual preregistration-only addition and its subsequent history.

    Unlike general source-state attestation, this contract requires the recorded
    commit to be the unique first branch commit introducing the frozen file.
    Inspect every reachable descendant of the freeze, including merged side
    branches, so path-history simplification cannot hide a change and revert.
    """
    if (not all(isinstance(x, str) and re.fullmatch(r"[0-9a-f]{40}", x) for x in (baseline, commit))
            or not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256)
            or not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts):
        raise SourceMetadataError("invalid preregistration identity or relative path")
    repository_root(root)
    if _is_shallow(root):
        raise SourceHistoryUnavailableError("preregistration requires complete Git history")

    def git(*arguments: str, allow_failure: bool = False):
        try:
            result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True)
        except OSError as error:
            raise SourceHistoryUnavailableError("preregistration history unavailable") from error
        if result.returncode and not allow_failure:
            raise SourceMetadataError(f"preregistration history lookup failed: {arguments[0]}")
        return result

    for identity in (baseline, commit):
        git("cat-file", "-e", f"{identity}^{{commit}}")
    parents = git("rev-list", "--parents", "-n", "1", commit).stdout.decode().split()
    if parents != [commit, baseline]:
        raise SourceStateViolationError("preregistration sole parent differs from intended baseline")
    changed = git("diff", "--name-only", baseline, commit).stdout.decode().splitlines()
    if changed != [path]:
        raise SourceStateViolationError("first branch commit must contain the preregistration alone")
    if git("cat-file", "-e", f"{baseline}:{path}", allow_failure=True).returncode == 0:
        raise SourceStateViolationError("preregistration must first be added at its freezing commit")
    frozen = git("show", f"{commit}:{path}").stdout
    try:
        current = (root / path).read_bytes()
    except OSError as error:
        raise SourceStateViolationError("current preregistration is missing or unreadable") from error
    if frozen != current or hashlib.sha256(frozen).hexdigest() != sha256:
        raise SourceStateViolationError("preregistration bytes changed or SHA-256 differs from the frozen record")
    ancestor = git("merge-base", "--is-ancestor", commit, "HEAD", allow_failure=True)
    if ancestor.returncode == 1:
        raise SourceAncestryViolationError("preregistration ancestry violated: commit is not an ancestor of HEAD")
    if ancestor.returncode:
        raise SourceMetadataError("preregistration ancestry could not be checked")
    frozen_blob = git("rev-parse", f"{commit}:{path}").stdout
    for descendant in git("rev-list", f"{commit}..HEAD").stdout.decode().splitlines():
        relation = git("merge-base", "--is-ancestor", commit, descendant, allow_failure=True)
        if relation.returncode == 1:
            continue  # Unrelated mainline history before the freeze was merged.
        if relation.returncode:
            raise SourceMetadataError("intervening ancestry could not be checked")
        blob = git("rev-parse", "--verify", f"{descendant}:{path}", allow_failure=True)
        if blob.returncode or blob.stdout != frozen_blob:
            raise SourceStateViolationError("preregistration changed or was deleted in intervening history")
    return frozen
