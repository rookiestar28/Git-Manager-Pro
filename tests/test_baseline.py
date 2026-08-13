"""Offline baseline tests for the existing script behavior."""

from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import auto_installer
import manage_git_pro


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / ".tmp" / "test-fixtures"


def local_tempdir() -> tempfile.TemporaryDirectory[str]:
    workspace = Path(__file__).resolve().parents[1]
    fixture_root = FIXTURE_ROOT.resolve()
    if not fixture_root.is_relative_to(workspace.resolve()):
        raise RuntimeError(f"fixture root escaped workspace: {fixture_root}")
    fixture_root.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(dir=fixture_root)
    if not Path(temporary.name).resolve().is_relative_to(fixture_root):
        temporary.cleanup()
        raise RuntimeError("temporary fixture escaped workspace fixture root")
    return temporary


class BaselineUtilityTests(unittest.TestCase):
    def test_language_catalog_and_timestamp_contract(self) -> None:
        self.assertEqual(set(auto_installer.TEXT), {"EN", "CHT"})
        self.assertTrue(manage_git_pro.validate_timestamp("2025-11-27 12:00:00"))
        self.assertFalse(manage_git_pro.validate_timestamp("not-a-timestamp"))

    def test_read_file_safe_ignores_comments_and_extracts_url(self) -> None:
        with local_tempdir() as directory:
            path = Path(directory) / "repos.txt"
            path.write_text(
                "# comment\n copied from note: https://example.invalid/node.git \n",
                encoding="utf-8",
            )
            self.assertEqual(
                auto_installer.read_file_safe(path),
                ["https://example.invalid/node.git"],
            )

    def test_streaming_command_captures_local_output(self) -> None:
        code = "print('local-stream-check')"
        FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
        with mock.patch.dict(
            os.environ,
            {"PATH": os.environ.get("PATH", ""), "PYTHONNOUSERSITE": "1"},
            clear=True,
        ):
            return_code, log = auto_installer.run_command_stream(
                [auto_installer.sys.executable, "-c", code], cwd=str(FIXTURE_ROOT)
            )
        self.assertEqual(return_code, 0)
        self.assertIn("local-stream-check", log)

    def test_git_update_adds_recursive_submodule_flag(self) -> None:
        with local_tempdir() as directory:
            project = Path(directory)
            (project / ".gitmodules").write_text("[submodule]\n", encoding="utf-8")
            commands: list[tuple[list[str], bool]] = []

            def fake_run(command: list[str], cwd: str, capture_output: bool = True):
                commands.append((command, capture_output))
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(manage_git_pro, "run_command", side_effect=fake_run):
                result = manage_git_pro.update_repo(
                    manage_git_pro.RepoInfo(project), mode="auto"
                )

            self.assertEqual(result, ("success", project.name))
            self.assertEqual(commands[0][0][:3], ["git", "rev-parse", "--abbrev-ref"])
            self.assertEqual(commands[1][0], ["git", "pull", "--recurse-submodules"])
            self.assertFalse(commands[1][1])


class BaselineInstallerTests(unittest.TestCase):
    def _run_install_mode(self, target: Path, fake_runner) -> str:
        output = io.StringIO()
        with (
            mock.patch("builtins.input", return_value=str(target)),
            mock.patch.object(auto_installer, "run_command_stream", side_effect=fake_runner),
            mock.patch.object(auto_installer.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            auto_installer.mode_install_dependencies()
        return output.getvalue()

    def test_requirements_discovery_is_sorted_and_skips_missing_files(self) -> None:
        with local_tempdir() as directory:
            target = Path(directory)
            (target / "z_node").mkdir()
            (target / "a_node").mkdir()
            (target / "a_node" / "requirements.txt").write_text("local-demo\n", encoding="utf-8")
            calls: list[tuple[list[str], Path]] = []

            def fake_runner(command, cwd):
                calls.append((command, Path(cwd)))
                return 0, "Requirement already satisfied: local-demo"

            output = self._run_install_mode(target, fake_runner)

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][1], target / "a_node")
            self.assertEqual(calls[0][0][0], auto_installer.sys.executable)
            self.assertIn("Success: 1 | Failed: 0 | Skipped: 1", output)

    def test_install_retries_then_succeeds(self) -> None:
        with local_tempdir() as directory:
            target = Path(directory)
            node = target / "retry_node"
            node.mkdir()
            (node / "requirements.txt").write_text("local-demo\n", encoding="utf-8")
            attempts: list[int] = []

            def fake_runner(command, cwd):
                attempts.append(1)
                if len(attempts) == 1:
                    return 1, "temporary local failure"
                return 0, "local success"

            output = self._run_install_mode(target, fake_runner)

            self.assertEqual(len(attempts), 2)
            self.assertIn("Success: 1 | Failed: 0 | Skipped: 0", output)


if __name__ == "__main__":
    unittest.main()
