"""Subprocess-level CLI integration tests using only local temporary directories."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / ".tmp" / "test-fixtures"


def local_tempdir() -> tempfile.TemporaryDirectory[str]:
    fixture_root = FIXTURE_ROOT.resolve()
    if not fixture_root.is_relative_to(REPO_ROOT.resolve()):
        raise RuntimeError(f"fixture root escaped workspace: {fixture_root}")
    fixture_root.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(dir=fixture_root)
    if not Path(temporary.name).resolve().is_relative_to(fixture_root):
        temporary.cleanup()
        raise RuntimeError("temporary fixture escaped workspace fixture root")
    return temporary


def run_local_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "SystemRoot": os.environ.get("SystemRoot", ""),
        "LANG": os.environ.get("LANG", "C"),
        "PYTHONNOUSERSITE": "1",
    }
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class CliBaselineTests(unittest.TestCase):
    def test_manager_help_is_non_interactive(self) -> None:
        result = run_local_cli("manage_git_pro.py", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--reset-timestamp", result.stdout)

    def test_manager_empty_directory_has_deterministic_summary(self) -> None:
        with local_tempdir() as directory:
            result = run_local_cli(
                "manage_git_pro.py",
                "--lang",
                "EN",
                "--directory",
                directory,
                "--skip-update",
                "--skip-convert",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Execution Summary:", result.stdout)
        self.assertIn("All tasks completed.", result.stdout)

    def test_install_cli_rejects_missing_or_conflicting_environment_selector(self) -> None:
        missing = run_local_cli("auto_installer.py", "--install", "--lang", "EN")
        self.assertEqual(missing.returncode, 2)
        self.assertIn("one of the arguments", missing.stderr)

        conflicting = run_local_cli(
            "auto_installer.py",
            "--install",
            "--lang",
            "EN",
            "--use-current-python",
            "--python-executable",
            sys.executable,
        )
        self.assertEqual(conflicting.returncode, 2)
        self.assertNotIn("Please enter the target", conflicting.stdout)


if __name__ == "__main__":
    unittest.main()
