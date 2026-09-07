"""One disposable Git fixture, with no commands outside its supplied directory."""

from pathlib import Path
import subprocess


class SyntheticHistory:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Chronology Fixture")
        self.counter = 0

    def git(self, *arguments: str) -> str:
        return subprocess.run(["git", "-C", str(self.root), *arguments],
                              capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, files: dict[str, bytes | None]) -> str:
        for relative, payload in files.items():
            path = self.root / relative
            if payload is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
        self.counter += 1
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", f"fixture {self.counter}")
        return self.git("rev-parse", "HEAD")
