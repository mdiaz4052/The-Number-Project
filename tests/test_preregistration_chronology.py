"""Bad histories independently exercise every strict freeze clause."""

import hashlib
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from Discovery.source_history import (
    SourceAncestryViolationError, SourceHistoryUnavailableError, SourceMetadataError,
    SourceStateViolationError,
)
from Discovery.preregistration_history import verify_preregistration_freeze
from tests.support.synthetic_history import SyntheticHistory


PATH = "Experiments/preregister.json"
PAYLOAD = b'{"protocol":"frozen"}\n'
HASH = hashlib.sha256(PAYLOAD).hexdigest()


class PreregistrationChronologyTests(unittest.TestCase):
    def history(self, *, prior=None, extra=None):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        history = SyntheticHistory(Path(temporary.name) / "repo")
        base = history.commit({"seed": b"baseline\n", **(prior or {})})
        freeze = history.commit({PATH: PAYLOAD, **(extra or {})})
        return history, base, freeze

    def verify(self, history, base, freeze, **changes):
        arguments = {"baseline": base, "commit": freeze, "path": PATH, "sha256": HASH}
        arguments.update(changes)
        return verify_preregistration_freeze(history.root, **arguments)

    def test_valid_preregistration_only_first_commit_passes(self):
        history, base, freeze = self.history()
        history.commit({"implementation.py": b"pass\n"})
        self.assertEqual(self.verify(history, base, freeze), PAYLOAD)

    def test_wrong_parent_is_rejected(self):
        history, base, _ = self.history()
        history.git("reset", "--hard", base)
        history.commit({})  # Isolate parentage: the baseline-to-freeze diff is still one file.
        freeze = history.commit({PATH: PAYLOAD})
        with self.assertRaisesRegex(SourceStateViolationError, "sole parent"):
            self.verify(history, base, freeze)

    def test_mixed_first_commit_is_rejected(self):
        history, base, freeze = self.history(extra={"implementation.py": b"pass\n"})
        with self.assertRaisesRegex(SourceStateViolationError, "preregistration alone"):
            self.verify(history, base, freeze)

    def test_preexisting_file_cannot_be_claimed_as_first_freeze(self):
        history, base, freeze = self.history(prior={PATH: b"earlier protocol\n"})
        with self.assertRaisesRegex(SourceStateViolationError, "first be added"):
            self.verify(history, base, freeze)

    def test_unchanged_nonfreezing_commit_is_rejected(self):
        history, _, freeze = self.history()
        nonfreeze = history.commit({})
        with self.assertRaisesRegex(SourceStateViolationError, "preregistration alone"):
            self.verify(history, freeze, nonfreeze)

    def test_nonancestor_freeze_cannot_be_rescued_by_identical_worktree(self):
        history, base, freeze = self.history()
        history.git("reset", "--hard", base)
        history.commit({PATH: PAYLOAD, "implementation.py": b"squashed\n"})
        with self.assertRaises(SourceAncestryViolationError):
            self.verify(history, base, freeze)

    def test_merge_commit_cannot_be_the_freeze(self):
        history, base, freeze = self.history()
        history.git("switch", "-q", "-c", "side", base)
        history.commit({"side": b"side\n"})
        history.git("switch", "-q", "main")
        history.git("merge", "--no-ff", "-m", "merge", "side")
        with self.assertRaisesRegex(SourceStateViolationError, "sole parent"):
            self.verify(history, base, history.git("rev-parse", "HEAD"))

    def test_uncommitted_change_is_rejected(self):
        history, base, freeze = self.history()
        (history.root / PATH).write_bytes(b"changed\n")
        with self.assertRaisesRegex(SourceStateViolationError, "bytes"):
            self.verify(history, base, freeze)

    def test_current_deletion_is_rejected(self):
        history, base, freeze = self.history()
        (history.root / PATH).unlink()
        with self.assertRaisesRegex(SourceStateViolationError, "missing"):
            self.verify(history, base, freeze)

    def test_change_and_revert_is_rejected(self):
        history, base, freeze = self.history()
        history.commit({PATH: b"temporary tuning\n"})
        history.commit({PATH: PAYLOAD})
        with self.assertRaisesRegex(SourceStateViolationError, "intervening history"):
            self.verify(history, base, freeze)

    def test_delete_and_restore_is_rejected(self):
        history, base, freeze = self.history()
        history.commit({PATH: None})
        history.commit({PATH: PAYLOAD})
        with self.assertRaisesRegex(SourceStateViolationError, "intervening history"):
            self.verify(history, base, freeze)

    def test_merge_simplification_cannot_hide_side_branch_edit(self):
        history, base, freeze = self.history()
        history.git("switch", "-q", "-c", "side")
        history.commit({PATH: b"hidden tuning\n"})
        history.git("switch", "-q", "main")
        history.commit({"implementation.py": b"pass\n"})
        history.git("merge", "--no-ff", "-s", "ours", "-m", "discard side edit", "side")
        self.assertEqual((history.root / PATH).read_bytes(), PAYLOAD)
        with self.assertRaisesRegex(SourceStateViolationError, "intervening history"):
            self.verify(history, base, freeze)

    def test_unchanged_merge_and_unrelated_prefreeze_history_pass(self):
        history, base, freeze = self.history()
        history.git("switch", "-q", "-c", "side", base)
        history.commit({"other_mainline": b"unrelated\n"})
        history.git("switch", "-q", "main")
        history.commit({"implementation.py": b"pass\n"})
        history.git("merge", "--no-ff", "-m", "merge unrelated", "side")
        self.assertEqual(self.verify(history, base, freeze), PAYLOAD)

    def test_hash_mismatch_and_invalid_metadata_fail(self):
        history, base, freeze = self.history()
        with self.assertRaisesRegex(SourceStateViolationError, "SHA-256"):
            self.verify(history, base, freeze, sha256="0"*64)
        for changes in ({"commit": "main"}, {"baseline": "HEAD"}, {"sha256": "short"},
                        {"path": "../outside"}, {"path": "/absolute"}):
            with self.subTest(changes=changes), self.assertRaises(SourceMetadataError):
                self.verify(history, base, freeze, **changes)

    def test_shallow_history_fails_closed(self):
        history, base, freeze = self.history()
        history.commit({"implementation.py": b"pass\n"})
        clone = history.root.parent / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "1", history.root.as_uri(), str(clone)], check=True)
        with self.assertRaises(SourceHistoryUnavailableError):
            verify_preregistration_freeze(clone, baseline=base, commit=freeze, path=PATH, sha256=HASH)


if __name__ == "__main__":
    unittest.main()
