"""Target-selection and probe-contract regression tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.environment_target import (
    TargetValidationError,
    build_pip_install_command,
    resolve_environment_target,
)


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / ".tmp" / "test-fixtures"


def local_tempdir() -> tempfile.TemporaryDirectory[str]:
    workspace = FIXTURE_ROOT.parents[1].resolve()
    fixture_root = FIXTURE_ROOT.resolve()
    if not fixture_root.is_relative_to(workspace):
        raise RuntimeError("fixture root escaped workspace")
    fixture_root.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(dir=fixture_root)
    if not Path(temporary.name).resolve().is_relative_to(fixture_root):
        temporary.cleanup()
        raise RuntimeError("temporary fixture escaped workspace")
    return temporary


def probe_result(
    executable: str,
    prefix: str,
    *,
    pip_available: bool = True,
    conda_prefix: str = "",
    conda_default_env: str = "",
) -> subprocess.CompletedProcess[str]:
    payload = {
        "executable": executable,
        "version": "3.13.9",
        "prefix": prefix,
        "base_prefix": prefix,
        "pip_available": pip_available,
        "conda_prefix": conda_prefix,
        "conda_default_env": conda_default_env,
    }
    return subprocess.CompletedProcess([], 0, json.dumps(payload), "")


class EnvironmentTargetTests(unittest.TestCase):
    def test_selector_is_required_and_mutually_exclusive_without_running_probe(self) -> None:
        calls: list[list[str]] = []

        def runner(command, **kwargs):
            calls.append(command)
            return probe_result(sys.executable, sys.prefix)

        with self.assertRaises(TargetValidationError):
            resolve_environment_target(runner=runner)
        with self.assertRaises(TargetValidationError):
            resolve_environment_target(use_current_python=True, python_executable=sys.executable, runner=runner)
        self.assertEqual(calls, [])

    def test_current_python_probe_validates_identity_and_pip(self) -> None:
        target = resolve_environment_target(use_current_python=True)
        self.assertEqual(target.kind, "current")
        self.assertTrue(target.identity.pip_available)
        self.assertEqual(target.command_prefix[0], os.path.abspath(sys.executable))

    def test_probe_uses_workspace_contained_allowlisted_environment(self) -> None:
        with local_tempdir() as directory:
            workspace = Path(directory)
            calls: list[dict] = []

            def runner(command, **kwargs):
                calls.append(kwargs)
                return probe_result(sys.executable, sys.prefix)

            resolve_environment_target(
                use_current_python=True,
                runner=runner,
                probe_workspace=workspace,
            )
            environment = calls[0]["env"]
            self.assertNotIn("PYTHONPATH", environment)
            self.assertTrue(Path(environment["TMPDIR"]).resolve().is_relative_to(workspace.resolve()))
            self.assertTrue(Path(environment["PIP_CACHE_DIR"]).resolve().is_relative_to(workspace.resolve()))
            self.assertTrue(Path(environment["CONDA_PKGS_DIRS"]).resolve().is_relative_to(workspace.resolve()))
            self.assertTrue(Path(environment["CONDA_ENVS_PATH"]).resolve().is_relative_to(workspace.resolve()))
            self.assertTrue(Path(environment["CONDARC"]).resolve().is_relative_to(workspace.resolve()))

    def test_explicit_interpreter_and_venv_use_single_structured_argument(self) -> None:
        with local_tempdir() as directory:
            root = Path(directory)
            executable = root / "python with spaces.exe"
            executable.write_text("fixture", encoding="utf-8")
            calls: list[tuple[list[str], dict]] = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                executable_arg = command[0]
                if executable_arg == str(executable.resolve()):
                    return probe_result(str(executable), str(root))
                return probe_result(executable_arg, str(venv_root))

            target = resolve_environment_target(
                python_executable=str(executable), runner=runner
            )
            self.assertEqual(target.command_prefix, (str(executable.resolve()),))
            self.assertIs(calls[0][1]["shell"], False)
            self.assertIn("python with spaces.exe", calls[0][0][0])

            venv_root = root / "venv with spaces"
            executable_path = venv_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            executable_path.parent.mkdir(parents=True)
            executable_path.write_text("fixture", encoding="utf-8")
            venv_target = resolve_environment_target(venv=str(venv_root), runner=runner)
            self.assertEqual(venv_target.kind, "venv")
            self.assertEqual(venv_target.identity.prefix, str(venv_root.resolve()))

    def test_conda_name_and_prefix_preserve_selector_as_data(self) -> None:
        with local_tempdir() as directory:
            root = Path(directory)
            conda = root / "conda with spaces.exe"
            conda.write_text("fixture", encoding="utf-8")
            prefix = root / "conda-prefix"
            prefix.mkdir()
            calls: list[list[str]] = []

            def runner(command, **kwargs):
                calls.append(command)
                if "-n" in command:
                    return probe_result(
                        str(prefix / "python.exe"), str(prefix), conda_default_env="env with spaces"
                    )
                return probe_result(
                    str(prefix / "python.exe"),
                    str(prefix),
                    conda_prefix=str(prefix),
                )

            with mock.patch.dict(os.environ, {"CONDA_EXE": str(conda)}, clear=False):
                named = resolve_environment_target(conda_env="env with spaces", runner=runner)
                prefixed = resolve_environment_target(conda_prefix=str(prefix), runner=runner)

            self.assertEqual(named.command_prefix[3:5], ("-n", "env with spaces"))
            self.assertEqual(prefixed.command_prefix[3:5], ("-p", str(prefix.resolve())))
            self.assertTrue(all(command[0] == str(conda.resolve()) for command in calls))

    def test_probe_rejection_happens_before_install_command_construction(self) -> None:
        with local_tempdir() as directory:
            executable = Path(directory) / "python.exe"
            executable.write_text("fixture", encoding="utf-8")

            def malformed(command, **kwargs):
                return subprocess.CompletedProcess(command, 0, "not-json", "")

            with self.assertRaises(TargetValidationError):
                resolve_environment_target(python_executable=str(executable), runner=malformed)

            def no_pip(command, **kwargs):
                return probe_result(str(executable), directory, pip_available=False)

            with self.assertRaises(TargetValidationError):
                resolve_environment_target(python_executable=str(executable), runner=no_pip)

            def mismatch(command, **kwargs):
                return probe_result(str(Path(directory) / "other.exe"), directory)

            with self.assertRaises(TargetValidationError):
                resolve_environment_target(python_executable=str(executable), runner=mismatch)

    def test_probe_timeout_is_content_limited(self) -> None:
        def timeout(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 15)

        with self.assertRaisesRegex(TargetValidationError, "timed out"):
            resolve_environment_target(use_current_python=True, runner=timeout)

    def test_pip_command_is_structured_and_keeps_metacharacters_in_one_argument(self) -> None:
        target = resolve_environment_target(use_current_python=True)
        requirements = Path("requirements [local];.txt")
        command = build_pip_install_command(target, requirements)
        self.assertEqual(command[:3], [target.command_prefix[0], "-m", "pip"])
        self.assertIn(str(requirements), command)


if __name__ == "__main__":
    unittest.main()
