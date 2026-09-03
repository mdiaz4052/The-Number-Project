from __future__ import annotations

from pathlib import Path
import unittest


class WorkflowWriteSafetyTests(unittest.TestCase):
    def test_write_enabled_workflows_have_bot_and_exact_ref_guards(self) -> None:
        workflow_dir = Path(".github/workflows")
        for path in sorted(workflow_dir.glob("*.y*ml")):
            text = path.read_text(encoding="utf-8")
            if "contents: write" not in text:
                continue
            self.assertIn(
                "github.actor != 'github-actions[bot]'",
                text,
                msg=f"{path} lacks the required bot-loop guard",
            )
            has_exact_head_guard = "github.head_ref ==" in text
            has_exact_branch_guard = "github.ref == 'refs/heads/" in text
            self.assertTrue(
                has_exact_head_guard or has_exact_branch_guard,
                msg=(
                    f"{path} has contents: write but lacks an exact "
                    "head/branch-ref guard"
                ),
            )


if __name__ == "__main__":
    unittest.main()
