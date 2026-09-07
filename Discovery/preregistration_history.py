"""Strict preregistration freezes, separate from historical source-state attestation."""

from pathlib import Path
import hashlib
import re
import subprocess

from Discovery.source_history import (
    SourceMetadataError, SourceHistoryUnavailableError, SourceStateViolationError,
    SourceAncestryViolationError, repository_root, _is_shallow,
)


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
