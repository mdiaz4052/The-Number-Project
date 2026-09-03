from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unittest


_BOT_GUARD_RE = re.compile(
    r"""github\.actor\s*!=\s*(['\"])github-actions\[bot\]\1"""
)
_EXACT_REF_GUARD_RE = re.compile(
    r"""(?:github\.head_ref\s*==\s*(['\"])[^'\"]+\1|github\.ref\s*==\s*(['\"])refs/heads/[^'\"]+\2)"""
)
_FIELD_RE = re.compile(r"^(?P<key>[A-Za-z0-9_-]+)\s*:\s*(?P<value>.*)$")


@dataclass(frozen=True)
class _YamlLine:
    indent: int
    text: str


def _strip_comment(raw_line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(raw_line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            continue
        if char in {"'", '"'}:
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "#" and quote is None:
            return raw_line[:index]
    return raw_line


def _active_yaml_lines(text: str) -> list[_YamlLine]:
    lines: list[_YamlLine] = []
    for raw_line in text.splitlines():
        code = _strip_comment(raw_line).rstrip()
        if not code.strip():
            continue
        expanded = code.expandtabs(8)
        indent = len(expanded) - len(expanded.lstrip(" "))
        lines.append(_YamlLine(indent=indent, text=expanded.strip()))
    return lines


def _unquote_scalar(value: str) -> str:
    stripped = value.strip()
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in {"'", '"'}
    ):
        return stripped[1:-1].strip()
    return stripped


def _scalar_grants_write(value: str) -> bool:
    normalized = _unquote_scalar(value).strip().lower()
    if normalized == "write-all":
        return True
    if normalized.startswith("{") and normalized.endswith("}"):
        body = normalized[1:-1]
        for entry in body.split(","):
            if ":" not in entry:
                continue
            _, raw_value = entry.split(":", 1)
            if _unquote_scalar(raw_value).strip().lower() == "write":
                return True
    return False


def _permissions_grant_write(
    lines: list[_YamlLine], start: int, end: int
) -> bool:
    match = _FIELD_RE.match(lines[start].text)
    if match is None or match.group("key") != "permissions":
        return False
    inline = match.group("value").strip()
    if inline:
        return _scalar_grants_write(inline)

    base_indent = lines[start].indent
    for line in lines[start + 1 : end]:
        if line.indent <= base_indent:
            break
        field = _FIELD_RE.match(line.text)
        if field is None:
            continue
        if _unquote_scalar(field.group("value")).strip().lower() == "write":
            return True
    return False


def _field_extent(lines: list[_YamlLine], start: int, end: int) -> int:
    base_indent = lines[start].indent
    cursor = start + 1
    while cursor < end and lines[cursor].indent > base_indent:
        cursor += 1
    return cursor


def _job_guard_expression(
    lines: list[_YamlLine], job_start: int, job_end: int, field_indent: int
) -> str:
    for index in range(job_start + 1, job_end):
        line = lines[index]
        if line.indent != field_indent:
            continue
        match = _FIELD_RE.match(line.text)
        if match is None or match.group("key") != "if":
            continue
        value = match.group("value").strip()
        if value not in {">", ">-", "|", "|-"}:
            return value
        extent = _field_extent(lines, index, job_end)
        return " ".join(
            continuation.text
            for continuation in lines[index + 1 : extent]
            if continuation.indent > field_indent
        )
    return ""


def _guard_is_exact(expression: str) -> bool:
    return bool(
        _BOT_GUARD_RE.search(expression)
        and _EXACT_REF_GUARD_RE.search(expression)
    )


def _workflow_policy_violations(text: str) -> list[str]:
    """Return write-safety violations.

    Any job receiving write-capable GITHUB_TOKEN permissions must carry the
    bot-loop guard and an exact branch/head-ref guard on the *job-level* ``if``.
    A step-level guard never protects the job as a whole.
    """

    lines = _active_yaml_lines(text)
    if not lines:
        return []

    jobs_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.indent == 0 and line.text == "jobs:"
        ),
        None,
    )
    if jobs_index is None:
        return []
    jobs_end = next(
        (
            index
            for index in range(jobs_index + 1, len(lines))
            if lines[index].indent <= lines[jobs_index].indent
        ),
        len(lines),
    )

    workflow_write = False
    for index, line in enumerate(lines[:jobs_index]):
        match = _FIELD_RE.match(line.text)
        if (
            line.indent == 0
            and match is not None
            and match.group("key") == "permissions"
        ):
            workflow_write = _permissions_grant_write(lines, index, jobs_index)
            break

    mapping_candidates = []
    for index in range(jobs_index + 1, jobs_end):
        line = lines[index]
        match = _FIELD_RE.match(line.text)
        if match is not None and not match.group("value").strip():
            mapping_candidates.append(index)
    if not mapping_candidates:
        return []

    job_indent = min(lines[index].indent for index in mapping_candidates)
    job_starts = [
        index
        for index in mapping_candidates
        if lines[index].indent == job_indent
    ]
    violations: list[str] = []

    for position, job_start in enumerate(job_starts):
        job_end = (
            job_starts[position + 1]
            if position + 1 < len(job_starts)
            else jobs_end
        )
        child_indents = [
            lines[index].indent
            for index in range(job_start + 1, job_end)
            if lines[index].indent > job_indent
        ]
        if not child_indents:
            continue
        field_indent = min(child_indents)
        job_permissions_index: int | None = None
        job_write = workflow_write
        for index in range(job_start + 1, job_end):
            line = lines[index]
            if line.indent != field_indent:
                continue
            match = _FIELD_RE.match(line.text)
            if match is not None and match.group("key") == "permissions":
                job_permissions_index = index
                break
        if job_permissions_index is not None:
            extent = _field_extent(lines, job_permissions_index, job_end)
            job_write = _permissions_grant_write(
                lines, job_permissions_index, extent
            )
        if not job_write:
            continue

        guard = _job_guard_expression(lines, job_start, job_end, field_indent)
        if not _guard_is_exact(guard):
            job_name_match = _FIELD_RE.match(lines[job_start].text)
            assert job_name_match is not None
            violations.append(
                f"job {job_name_match.group('key')} receives write permission "
                "without one job-level if containing both the bot-loop guard "
                "and an exact head/branch-ref guard"
            )
    return violations


class WorkflowWriteSafetyTests(unittest.TestCase):
    def test_repository_write_enabled_workflows_are_guarded(self) -> None:
        workflow_dir = Path(".github/workflows")
        for path in sorted(workflow_dir.glob("*.y*ml")):
            violations = _workflow_policy_violations(
                path.read_text(encoding="utf-8")
            )
            self.assertEqual(violations, [], msg=f"{path}: {violations}")

    def test_write_grant_spellings_are_detected(self) -> None:
        permissions_variants = (
            "permissions: write-all",
            "permissions:\n  contents:  write",
            "permissions:\n  contents: 'write'",
            'permissions:\n  contents: "write"',
        )
        for permissions in permissions_variants:
            with self.subTest(permissions=permissions):
                hostile = f"""{permissions}
jobs:
  patch:
    runs-on: ubuntu-latest
"""
                self.assertTrue(_workflow_policy_violations(hostile))

    def test_job_level_write_permission_is_detected(self) -> None:
        hostile = """
permissions:
  contents: read
jobs:
  patch:
    permissions:
      contents: write
    runs-on: ubuntu-latest
"""
        self.assertTrue(_workflow_policy_violations(hostile))

    def test_folded_job_level_if_is_accepted(self) -> None:
        guarded = """
permissions: write-all
jobs:
  patch:
    if: >-
      github.actor != 'github-actions[bot]' &&
      github.ref == 'refs/heads/safe'
    runs-on: ubuntu-latest
"""
        self.assertEqual(_workflow_policy_violations(guarded), [])

    def test_step_level_guard_does_not_protect_write_job(self) -> None:
        hostile = """
permissions:
  contents: write
jobs:
  patch:
    runs-on: ubuntu-latest
    steps:
      - name: guarded step only
        if: github.actor != 'github-actions[bot]' && github.ref == 'refs/heads/safe'
        run: echo unsafe-job
"""
        self.assertTrue(_workflow_policy_violations(hostile))

    def test_commented_guard_text_cannot_satisfy_policy(self) -> None:
        hostile = """
permissions:
  contents: write
jobs:
  patch:
    # if: github.actor != 'github-actions[bot]' && github.ref == 'refs/heads/safe'
    runs-on: ubuntu-latest
"""
        self.assertTrue(_workflow_policy_violations(hostile))


if __name__ == "__main__":
    unittest.main()
