"""Local-only GMP-004 automation and failure-contract matrix."""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import auto_installer
from scripts.environment_target import EnvironmentIdentity, EnvironmentTarget, TargetValidationError


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / ".tmp" / "test-fixtures" / "automation-failures"


def local_tempdir() -> tempfile.TemporaryDirectory[str]:
    root = FIXTURE_ROOT.resolve()
    if not root.is_relative_to(REPO_ROOT.resolve()):
        raise RuntimeError("fixture root escaped workspace")
    root.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(dir=root)
    if not Path(temporary.name).resolve().is_relative_to(root):
        temporary.cleanup()
        raise RuntimeError("temporary fixture escaped workspace fixture root")
    return temporary


class CliAutomationFailureTests(unittest.TestCase):
    def _clone_fixture(self, *, count: int = 1) -> tuple[Path, Path]:
        temporary = local_tempdir()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        target = root / "target"
        target.mkdir()
        list_path = root / "urls.txt"
        authenticated_prefix = "https://" + "user" + ":" + "credential" + "@"
        list_path.write_text(
            "\n".join(f"{authenticated_prefix}example.invalid/repo-{index}.git" for index in range(count)) + "\n",
            encoding="utf-8",
        )
        return target, list_path

    def _run_clone(self, target: Path, list_path: Path, *extra: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(auto_installer, "run_command_stream", return_value=(0, "")),
            mock.patch("builtins.input", side_effect=AssertionError("non-interactive prompt")),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                    "--lang",
                    "EN",
                    *extra,
                ]
            )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_partial_clone_failure_returns_operation_code_and_preserves_items(self) -> None:
        target, list_path = self._clone_fixture(count=2)
        calls: list[list[str]] = []

        def fake_runner(command, cwd):
            calls.append(command)
            return (0 if command[-1].endswith("repo-1.git") else 1), "token=secret https://private.invalid/index"

        stdout = io.StringIO()
        with (
            mock.patch.object(auto_installer, "run_command_stream", side_effect=fake_runner),
            mock.patch("builtins.input", side_effect=AssertionError("non-interactive prompt")),
            mock.patch("sys.stdout", stdout),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_OPERATION)
        self.assertEqual(len(calls), 2)
        self.assertIn("Success: 1 | Failed: 1 | Skipped: 0", stdout.getvalue())
        self.assertNotIn("secret", stdout.getvalue())
        self.assertNotIn("private.invalid", stdout.getvalue())

    def test_json_stdout_is_the_only_stdout_and_matches_summary(self) -> None:
        target, list_path = self._clone_fixture()
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(auto_installer, "run_command_stream", return_value=(0, "")),
            mock.patch("sys.stdout", stdout),
            mock.patch("sys.stderr", stderr),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                    "--json",
                    "-",
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_SUCCESS)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            set(payload),
            {"schema_version", "operation", "status", "exit_code", "counts", "items"},
        )
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["counts"], {"attempted": 1, "succeeded": 1, "failed": 0, "skipped": 0})
        self.assertIn("Execution Summary", stderr.getvalue())
        self.assertNotIn("https://", stdout.getvalue())
        self.assertNotIn("secret", stdout.getvalue())

    def test_public_schema_docs_match_machine_contract(self) -> None:
        english = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (REPO_ROOT / "README.zh-TW.md").read_text(encoding="utf-8")
        for document in (english, chinese):
            self.assertIn("schema_version", document)
            self.assertIn("error_category", document)
            self.assertIn("partial_failure", document)

    def test_json_file_redacts_child_output_and_replaces_atomically(self) -> None:
        target, list_path = self._clone_fixture()
        output_path = target.parent / "result.json"
        output_path.write_text('{"old": true}\n', encoding="utf-8")
        with (
            mock.patch.object(
                auto_installer,
                "run_command_stream",
                return_value=(
                    1,
                    "ERROR: "
                    + "https://"
                    + "user"
                    + ":"
                    + "credential"
                    + "@private.invalid/x token="
                    + "credential",
                ),
            ),
            mock.patch("sys.stdout", io.StringIO()),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                    "--json",
                    str(output_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_OPERATION)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["exit_code"], auto_installer.EXIT_OPERATION)
        self.assertNotIn("secret", output_path.read_text(encoding="utf-8"))
        self.assertNotIn("private.invalid", output_path.read_text(encoding="utf-8"))
        self.assertFalse(list(target.parent.glob(".result.json.*.tmp")))

    def test_missing_noninteractive_values_are_usage_error_without_prompt(self) -> None:
        with mock.patch("builtins.input", side_effect=AssertionError("prompted")):
            with self.assertRaises(SystemExit) as raised:
                auto_installer.cli_entry(["--install", "--non-interactive"])
        self.assertEqual(raised.exception.code, auto_installer.EXIT_USAGE)

    def test_environment_validation_is_distinct_from_usage(self) -> None:
        with mock.patch.object(
            auto_installer,
            "parse_target_arguments",
            side_effect=TargetValidationError("controlled target rejection"),
        ), mock.patch("sys.stdout", io.StringIO()):
            code = auto_installer.cli_entry(["--install", "--use-current-python"])
        self.assertEqual(code, auto_installer.EXIT_ENVIRONMENT)

    def test_retry_exhaustion_returns_nonzero_and_keeps_three_attempts(self) -> None:
        with local_tempdir() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            node = target / "node"
            node.mkdir()
            (node / "requirements.txt").write_text("local-only\n", encoding="utf-8")
            calls: list[int] = []

            def fake_runner(command, cwd):
                calls.append(1)
                return 1, "ERROR: local failure"

            with (
                mock.patch.object(auto_installer, "run_command_stream", side_effect=fake_runner),
                mock.patch.object(auto_installer.time, "sleep"),
                mock.patch.object(auto_installer, "resolve_environment_target", return_value=mock.Mock(python_executable="python")),
                mock.patch("sys.stdout", io.StringIO()),
            ):
                fake_target = mock.Mock(python_executable="python", command_prefix=("python",))
                result = auto_installer.mode_install_dependencies(
                    target_directory=target,
                    target=fake_target,
                    non_interactive=True,
                )
        self.assertEqual(result.exit_code, auto_installer.EXIT_OPERATION)
        self.assertEqual(len(calls), auto_installer.MAX_RETRIES)
        self.assertEqual(result.items[0].attempts, auto_installer.MAX_RETRIES)

    def test_timeout_is_bounded_error_category(self) -> None:
        with local_tempdir() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            node = target / "node"
            node.mkdir()
            (node / "requirements.txt").write_text("local-only\n", encoding="utf-8")
            with (
                mock.patch.object(
                    auto_installer,
                    "run_command_stream",
                    side_effect=subprocess.TimeoutExpired(["fake-pip"], timeout=1),
                ),
                mock.patch.object(auto_installer.time, "sleep"),
                mock.patch("sys.stdout", io.StringIO()),
            ):
                result = auto_installer.mode_install_dependencies(
                    target_directory=target,
                    target=mock.Mock(python_executable="python", command_prefix=("python",)),
                    non_interactive=True,
                )
        self.assertEqual(result.exit_code, auto_installer.EXIT_OPERATION)
        self.assertEqual(result.items[0].error_category, "timeout")

    def test_real_child_stream_timeout_and_spawn_failure_are_bounded(self) -> None:
        with local_tempdir() as temporary:
            root = Path(temporary)
            output = io.StringIO()
            with mock.patch.object(auto_installer, "_OUTPUT_STREAM", output):
                started = auto_installer.time.monotonic()
                timeout_code, timeout_log = auto_installer.run_command_stream(
                    [
                        auto_installer.sys.executable,
                        "-c",
                        "import time; time.sleep(2)",
                    ],
                    cwd=root,
                    timeout=0.2,
                )
                elapsed = auto_installer.time.monotonic() - started
                spawn_code, spawn_log = auto_installer.run_command_stream(
                    [str(root / "missing-child.exe")], cwd=root, timeout=0.2
                )
            self.assertEqual(timeout_code, -1)
            self.assertEqual(timeout_log, "timeout")
            self.assertLess(elapsed, 1.5)
            self.assertEqual(spawn_code, -1)
            self.assertEqual(spawn_log, "spawn_failed")

    def test_real_child_continuous_output_still_hits_wall_clock_timeout(self) -> None:
        with local_tempdir() as temporary:
            output = io.StringIO()
            child_code = "import time; [print('x' * 200, flush=True) for _ in iter(int, 1)]"
            with mock.patch.object(auto_installer, "_OUTPUT_STREAM", output):
                started = auto_installer.time.monotonic()
                code, log = auto_installer.run_command_stream(
                    [auto_installer.sys.executable, "-c", child_code],
                    cwd=Path(temporary),
                    timeout=0.2,
                )
                elapsed = auto_installer.time.monotonic() - started
            self.assertEqual(code, -1)
            self.assertEqual(log, "timeout")
            self.assertLess(elapsed, 1.5)
            self.assertLessEqual(output.getvalue().count("x"), auto_installer.MAX_CAPTURE_BYTES)
            self.assertIn("[output truncated]", output.getvalue())

    def test_finite_high_output_child_reaches_eof_without_false_timeout(self) -> None:
        with local_tempdir() as temporary:
            output = io.StringIO()
            child_code = "import sys; [print('x' * 200) for _ in range(5000)]"
            with mock.patch.object(auto_installer, "_OUTPUT_STREAM", output):
                code, log = auto_installer.run_command_stream(
                    [auto_installer.sys.executable, "-c", child_code],
                    cwd=Path(temporary),
                    timeout=5,
                )
            self.assertEqual(code, 0)
            self.assertIn("[output truncated]", log)

    def test_real_child_output_is_bounded_and_redacted(self) -> None:
        with local_tempdir() as temporary:
            output = io.StringIO()
            child_code = (
                "import sys; "
                "print('token=credential https://private.invalid/repo'); "
                "print(r'C:/private/file /tmp/private /Users/private', file=sys.stderr)"
            )
            with mock.patch.object(auto_installer, "_OUTPUT_STREAM", output):
                code, log = auto_installer.run_command_stream(
                    [auto_installer.sys.executable, "-c", child_code],
                    cwd=Path(temporary),
                    timeout=2,
                )
            self.assertEqual(code, 0)
            self.assertNotIn("private.invalid", log)
            self.assertNotIn("credential", log)
            self.assertNotIn("C:/private", log)
            self.assertNotIn("/tmp/private", log)
            self.assertNotIn("/Users/private", log)
            self.assertIn("[REDACTED_URL]", log)
            self.assertIn("[REDACTED_PATH]", log)

    def test_real_child_human_output_failure_maps_to_output_category(self) -> None:
        with local_tempdir() as temporary:
            class ClosedStream:
                def write(self, value: str) -> int:
                    raise OSError("controlled output closure")

                def flush(self) -> None:
                    return None

            with mock.patch.object(auto_installer, "_OUTPUT_STREAM", ClosedStream()):
                code, log = auto_installer.run_command_stream(
                    [auto_installer.sys.executable, "-c", "print('child output', flush=True)"],
                    cwd=Path(temporary),
                    timeout=2,
                )
            self.assertEqual(code, -1)
            self.assertEqual(log, "output_failed")

    def test_real_fake_git_and_pip_commands_use_local_fixture_only(self) -> None:
        with local_tempdir() as temporary:
            root = Path(temporary)
            target_dir = root / "target"
            target_dir.mkdir()
            list_path = root / "urls.txt"
            list_path.write_text("https://example.invalid/local.git\n", encoding="utf-8")
            git_script = root / "fake_git.py"
            git_script.write_text(
                "import pathlib,sys; "
                "pathlib.Path(sys.argv[-1].split('/')[-1].removesuffix('.git')).mkdir(); "
                "print('local fake git success')\n",
                encoding="utf-8",
            )
            with mock.patch.object(auto_installer, "_OUTPUT_STREAM", io.StringIO()):
                clone_result = auto_installer.mode_git_clone(
                    target_directory=target_dir,
                    list_path=list_path,
                    non_interactive=True,
                    git_command=(auto_installer.sys.executable, str(git_script)),
                )
            self.assertEqual(clone_result.exit_code, auto_installer.EXIT_SUCCESS)
            self.assertTrue((target_dir / "local").is_dir())

            pip_script = root / "fake_python.py"
            pip_script.write_text(
                "import pathlib,sys; "
                "assert sys.argv[1:3] == ['-m','pip']; "
                "pathlib.Path('pip-receipt.txt').write_text('ok', encoding='utf-8')\n",
                encoding="utf-8",
            )
            install_target_dir = root / "install-target"
            install_target_dir.mkdir()
            node = install_target_dir / "node"
            node.mkdir()
            (node / "requirements.txt").write_text("local-only\n", encoding="utf-8")
            identity = EnvironmentIdentity(
                executable=str(Path(auto_installer.sys.executable).resolve()),
                version="3.13.9",
                prefix=str(root),
                base_prefix=str(root),
                pip_available=True,
            )
            fake_target = EnvironmentTarget(
                "fake-python",
                str(pip_script),
                (auto_installer.sys.executable, str(pip_script)),
                identity,
            )
            with (
                mock.patch.object(auto_installer, "_OUTPUT_STREAM", io.StringIO()),
                mock.patch.object(auto_installer.time, "sleep"),
            ):
                install_result = auto_installer.mode_install_dependencies(
                    target=fake_target,
                    target_directory=install_target_dir,
                    non_interactive=True,
                )
            self.assertEqual(install_result.exit_code, auto_installer.EXIT_SUCCESS)
            self.assertTrue((node / "pip-receipt.txt").is_file())

    def test_malformed_list_is_rejected_before_child(self) -> None:
        target, list_path = self._clone_fixture()
        list_path.write_text("bad\x07value\n", encoding="utf-8")
        with mock.patch.object(auto_installer, "run_command_stream") as runner:
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_USAGE)
        runner.assert_not_called()

    def test_malformed_url_is_rejected_before_child(self) -> None:
        target, list_path = self._clone_fixture()
        list_path.write_text("not-a-clone-url\n", encoding="utf-8")
        with mock.patch.object(auto_installer, "run_command_stream") as runner:
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_USAGE)
        runner.assert_not_called()

    def test_legacy_utf16_clone_list_is_supported(self) -> None:
        target, list_path = self._clone_fixture()
        list_path.write_text("https://example.invalid/utf16.git\n", encoding="utf-16")
        with mock.patch.object(auto_installer, "run_command_stream", return_value=(0, "")) as runner:
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_SUCCESS)
        runner.assert_called_once()

    def test_del_character_is_rejected_before_child(self) -> None:
        target, list_path = self._clone_fixture()
        list_path.write_bytes(b"https://example.invalid/repo.git\x7f\n")
        with mock.patch.object(auto_installer, "run_command_stream") as runner:
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_USAGE)
        runner.assert_not_called()

    def test_json_output_failure_preserves_previous_file(self) -> None:
        target, list_path = self._clone_fixture()
        previous = target.parent / "result.json"
        previous.write_text('{"previous": true}\n', encoding="utf-8")
        with (
            mock.patch.object(auto_installer, "run_command_stream", return_value=(0, "")),
            mock.patch.object(auto_installer.os, "replace", side_effect=OSError("controlled replace failure")),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                    "--json",
                    str(previous),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_OUTPUT)
        self.assertEqual(previous.read_text(encoding="utf-8"), '{"previous": true}\n')

    def test_safe_label_drops_query_fragment_and_userinfo(self) -> None:
        value = (
            "https://" + "user" + ":" + "credential" + "@example.invalid/repo.git?"
            + "token=secret#fragment"
        )
        self.assertEqual(auto_installer._safe_label(value), "repo")

    def test_broken_human_pipe_is_output_failure_without_traceback(self) -> None:
        target, list_path = self._clone_fixture()

        class BrokenStream:
            def write(self, value: str) -> int:
                raise BrokenPipeError("controlled pipe closure")

            def flush(self) -> None:
                return None

        with (
            mock.patch.object(auto_installer, "run_command_stream", return_value=(0, "")),
            mock.patch("sys.stdout", BrokenStream()),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_OUTPUT)

    def test_json_serialization_failure_is_output_failure(self) -> None:
        target, list_path = self._clone_fixture()
        with (
            mock.patch.object(auto_installer, "run_command_stream", return_value=(0, "")),
            mock.patch.object(auto_installer, "_json_payload", side_effect=auto_installer.OutputFailure("controlled serialization")),
            mock.patch("sys.stdout", io.StringIO()),
        ):
            code = auto_installer.cli_entry(
                [
                    "--clone",
                    "--non-interactive",
                    "--target-directory",
                    str(target),
                    "--clone-list",
                    str(list_path),
                    "--json",
                    str(target.parent / "result.json"),
                ]
            )
        self.assertEqual(code, auto_installer.EXIT_OUTPUT)


if __name__ == "__main__":
    unittest.main()
