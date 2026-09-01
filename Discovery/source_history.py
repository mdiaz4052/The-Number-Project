"""Shared Git-history verification for committed experiment artifacts.

The command-line guards distinguish an unverifiable checkout (for example, an
archive or a shallow audit clone) from a verified methodological violation.  This
keeps missing history from being reported as evidence of tampering while retaining
hard failures for genuine ancestry and source-state mismatches.
"""

from __future__ import annotations

from pathlib import Path
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
