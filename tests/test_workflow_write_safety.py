from __future__ import annotations

from pathlib import Path
import unittest


class WorkflowWriteSafetyTests(unittest.TestCase):
    @staticmethod
    def _active_lines(text: str) -> list[str]:
        active: list[str] = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Workflow safety tokens in this repository do not require literal '#'.
            # Removing trailing comments prevents a comment from satisfying a guard.
            code = raw_line.split("#", 1)[0].strip()
            if code:
                active.append(code)
        return active

    def test_write_enabled_workflows_have_bot_and_exact_ref_guards(self) -> None:
        workflow_dir = Path(".github/workflows")
        for path in sorted(workflow_dir.glob("*.y*ml")):
            text = path.read_text(encoding="utf-8")
            active_lines = self._active_lines(text)
            if not any("contents: write" in line for line in active_lines):
                continue

            if_lines = [
                line
                for line in active_lines
                if line.startswith("if:") or line.startswith("if: ")
            ]
            guarded = any(
                "github.actor != 'github-actions[bot]'" in line
                and (
                    "github.head_ref ==" in line
                    or "github.ref == 'refs/heads/" in line
                )
                for line in if_lines
            )
            self.assertTrue(
                guarded,
                msg=(
                    f"{path} has contents: write but lacks one active if-condition "
                    "containing both the bot-loop guard and an exact head/branch-ref guard"
                ),
            )

    def test_commented_guard_text_cannot_satisfy_policy(self) -> None:
        hostile = """
permissions:
  contents: write
jobs:
  patch:
    # if: github.actor != 'github-actions[bot]' && github.ref == 'refs/heads/safe'
    runs-on: ubuntu-latest
"""
        active = self._active_lines(hostile)
        self.assertTrue(any("contents: write" in line for line in active))
        self.assertFalse(
            any(
                "github.actor != 'github-actions[bot]'" in line
                and "github.ref == 'refs/heads/" in line
                for line in active
                if line.startswith("if:")
            )
        )


if __name__ == "__main__":
    unittest.main()
