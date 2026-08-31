from pathlib import Path
import subprocess
import tempfile
import unittest

from Discovery.source_history import (
    VERIFIED,
    SourceAncestryViolationError,
    SourceHistoryUnavailableError,
    SourceStateViolationError,
    repository_root,
    verify_committed_source_state,
)


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class SourceHistoryTests(unittest.TestCase):
    def _repository(self, parent: Path) -> tuple[Path, str, str]:
        root = parent / "repository"
        root.mkdir()
        _git(root, "init", "-b", "main")
        _git(root, "config", "user.name", "Source History Test")
        _git(root, "config", "user.email", "source-history@example.invalid")
        (root / "source.txt").write_text("source\n", encoding="utf-8")
        _git(root, "add", "source.txt")
        _git(root, "commit", "-m", "source")
        source = _git(root, "rev-parse", "HEAD")
        (root / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
        _git(root, "add", "unrelated.txt")
        _git(root, "commit", "-m", "unrelated")
        head = _git(root, "rev-parse", "HEAD")
        return root, source, head

    def test_complete_unchanged_ancestor_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, source, _ = self._repository(Path(temporary))
            self.assertEqual(
                verify_committed_source_state(
                    root,
                    source,
                    source_paths=("source.txt",),
                    artifact_label="fixture",
                ),
                VERIFIED,
            )

    def test_no_git_history_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(SourceHistoryUnavailableError):
                repository_root(Path(temporary))

    def test_shallow_clone_reports_history_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root, source, _ = self._repository(parent)
            shallow = parent / "shallow"
            subprocess.run(
                ["git", "clone", "--quiet", "--depth", "1", f"file://{root}", str(shallow)],
                check=True,
            )
            with self.assertRaises(SourceHistoryUnavailableError):
                verify_committed_source_state(
                    shallow,
                    source,
                    source_paths=("source.txt",),
                    artifact_label="fixture",
                )

    def test_full_nonancestor_is_a_hard_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, source, head = self._repository(Path(temporary))
            _git(root, "switch", "--quiet", "-c", "side", source)
            (root / "side.txt").write_text("side\n", encoding="utf-8")
            _git(root, "add", "side.txt")
            _git(root, "commit", "-m", "side")
            side = _git(root, "rev-parse", "HEAD")
            _git(root, "switch", "--quiet", "main")
            self.assertEqual(_git(root, "rev-parse", "HEAD"), head)
            with self.assertRaises(SourceAncestryViolationError):
                verify_committed_source_state(
                    root,
                    side,
                    source_paths=("source.txt",),
                    artifact_label="fixture",
                )

    def test_changed_result_driving_source_is_a_hard_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root, source, _ = self._repository(Path(temporary))
            (root / "source.txt").write_text("changed\n", encoding="utf-8")
            _git(root, "add", "source.txt")
            _git(root, "commit", "-m", "change source")
            with self.assertRaises(SourceStateViolationError):
                verify_committed_source_state(
                    root,
                    source,
                    source_paths=("source.txt",),
                    artifact_label="fixture",
                )


if __name__ == "__main__":
    unittest.main()
