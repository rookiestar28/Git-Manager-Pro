"""Validated Python and Conda target resolution for dependency installation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


PROBE_TIMEOUT_SECONDS = 15
PIP_TIMEOUT_SECONDS = 60
CONTROLLED_ENV_DIR = Path(__file__).resolve().parents[1] / ".tmp" / "environment-target"
PROBE_CODE = (
    "import importlib.util,json,os,sys;"
    "print(json.dumps({"
    "'executable':sys.executable,"
    "'version':'.'.join(str(x) for x in sys.version_info[:3]),"
    "'prefix':sys.prefix,"
    "'base_prefix':sys.base_prefix,"
    "'pip_available':importlib.util.find_spec('pip') is not None,"
    "'conda_prefix':os.environ.get('CONDA_PREFIX',''),"
    "'conda_default_env':os.environ.get('CONDA_DEFAULT_ENV','')"
    "},sort_keys=True))"
)


class TargetValidationError(ValueError):
    """Raised when a requested interpreter cannot be safely validated."""


@dataclass(frozen=True)
class EnvironmentIdentity:
    executable: str
    version: str
    prefix: str
    base_prefix: str
    pip_available: bool
    conda_prefix: str = ""
    conda_default_env: str = ""


@dataclass(frozen=True)
class EnvironmentTarget:
    kind: str
    selector: str
    command_prefix: tuple[str, ...]
    identity: EnvironmentIdentity

    @property
    def python_executable(self) -> str:
        return self.identity.executable


RunFunction = Callable[..., subprocess.CompletedProcess[str]]


def build_controlled_environment(workspace: Path | None = None) -> dict[str, str]:
    """Return an allowlisted subprocess environment with workspace-local state paths."""

    root = (workspace or CONTROLLED_ENV_DIR).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    temp_root = root / "tmp"
    home_root = root / "home"
    pip_cache = root / "pip-cache"
    conda_packages = root / "conda-pkgs"
    conda_envs = root / "conda-envs"
    for path in (temp_root, home_root, pip_cache, conda_packages, conda_envs):
        path.mkdir(parents=True, exist_ok=True)

    allowed = {
        "PATH",
        "SYSTEMROOT",
        "SystemRoot",
        "LANG",
        "LC_ALL",
        "PYTHONNOUSERSITE",
        "PYTHONUTF8",
    }
    environment = {key: os.environ[key] for key in allowed if os.environ.get(key)}
    environment.update(
        {
            "HOME": str(home_root),
            "USERPROFILE": str(home_root),
            "TMPDIR": str(temp_root),
            "TMP": str(temp_root),
            "TEMP": str(temp_root),
            "PIP_CACHE_DIR": str(pip_cache),
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INPUT": "1",
            "PIP_NO_INDEX": "1",
            "CONDA_PKGS_DIRS": str(conda_packages),
            "CONDA_ENVS_PATH": str(conda_envs),
            "CONDA_BLD_PATH": str(root / "conda-build"),
            "CONDARC": str(root / "condarc"),
        }
    )
    return environment


def _canonical_path(value: str | Path) -> str:
    return str(Path(value).expanduser().resolve(strict=False))


def _absolute_path(value: str | Path) -> str:
    """Make a command path absolute without resolving a venv's interpreter symlink."""

    return os.path.abspath(os.path.expanduser(os.fspath(value)))


def _same_path(left: str, right: str) -> bool:
    if os.name == "nt":
        return os.path.normcase(_canonical_path(left)) == os.path.normcase(_canonical_path(right))
    return _canonical_path(left) == _canonical_path(right)


def _require_file(path: Path, label: str) -> str:
    if not path.is_file():
        raise TargetValidationError(f"{label} does not exist: {path}")
    return _absolute_path(path)


def _conda_executable() -> str:
    configured = os.environ.get("CONDA_EXE", "").strip()
    candidate = configured or shutil.which("conda")
    if not candidate:
        raise TargetValidationError("conda executable was not found")
    return _require_file(Path(candidate), "conda executable")


def _run_probe(
    command_prefix: Sequence[str],
    *,
    runner: RunFunction = subprocess.run,
    timeout: float = PROBE_TIMEOUT_SECONDS,
    workspace: Path | None = None,
) -> EnvironmentIdentity:
    command = [*command_prefix, "-c", PROBE_CODE]
    environment = build_controlled_environment(workspace)
    try:
        result = runner(
            command,
            shell=False,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TargetValidationError("environment probe timed out") from exc
    except (FileNotFoundError, OSError) as exc:
        raise TargetValidationError("environment probe could not start") from exc
    if result.returncode != 0:
        raise TargetValidationError("environment probe failed")
    try:
        payload = json.loads(result.stdout.strip())
    except (TypeError, json.JSONDecodeError) as exc:
        raise TargetValidationError("environment probe returned malformed identity") from exc
    required = ("executable", "version", "prefix", "base_prefix", "pip_available")
    if any(key not in payload for key in required) or not isinstance(payload["pip_available"], bool):
        raise TargetValidationError("environment probe returned incomplete identity")
    identity = EnvironmentIdentity(
        executable=_canonical_path(str(payload["executable"])),
        version=str(payload["version"]),
        prefix=_canonical_path(str(payload["prefix"])),
        base_prefix=_canonical_path(str(payload["base_prefix"])),
        pip_available=payload["pip_available"],
        conda_prefix=_canonical_path(str(payload.get("conda_prefix", "")))
        if payload.get("conda_prefix")
        else "",
        conda_default_env=str(payload.get("conda_default_env", "")),
    )
    if not identity.pip_available:
        raise TargetValidationError("target Python does not provide pip")
    return identity


def _validate_identity(
    target: EnvironmentTarget,
    *,
    expected_executable: str | None = None,
    expected_prefix: str | None = None,
) -> EnvironmentTarget:
    if expected_executable and not _same_path(target.identity.executable, expected_executable):
        raise TargetValidationError("target Python identity did not match requested executable")
    if expected_prefix and not _same_path(target.identity.prefix, expected_prefix):
        raise TargetValidationError("target Python identity did not match requested venv/prefix")
    if target.kind == "conda-env":
        if target.identity.conda_default_env != target.selector:
            raise TargetValidationError("Conda environment identity did not match requested name")
    if target.kind == "conda-prefix":
        if not target.identity.conda_prefix or not _same_path(
            target.identity.conda_prefix, target.selector
        ):
            raise TargetValidationError("Conda prefix identity did not match requested prefix")
    return target


def _direct_target(
    kind: str,
    selector: str,
    executable: str,
    *,
    runner: RunFunction,
    workspace: Path | None = None,
) -> EnvironmentTarget:
    identity = _run_probe((executable,), runner=runner, workspace=workspace)
    target = EnvironmentTarget(kind, selector, (executable,), identity)
    return _validate_identity(target, expected_executable=executable)


def resolve_environment_target(
    *,
    use_current_python: bool = False,
    python_executable: str | None = None,
    venv: str | None = None,
    conda_env: str | None = None,
    conda_prefix: str | None = None,
    runner: RunFunction = subprocess.run,
    probe_workspace: Path | None = None,
) -> EnvironmentTarget:
    selectors = [use_current_python, python_executable, venv, conda_env, conda_prefix]
    if sum(value is not False and value is not None for value in selectors) != 1:
        raise TargetValidationError("exactly one environment target selector is required")

    if use_current_python:
        return _direct_target(
            "current",
            "current",
            _require_file(Path(sys.executable), "current Python"),
            runner=runner,
            workspace=probe_workspace,
        )
    if python_executable is not None:
        executable = _require_file(Path(python_executable), "Python executable")
        return _direct_target(
            "interpreter", executable, executable, runner=runner, workspace=probe_workspace
        )
    if venv is not None:
        root = Path(venv).expanduser()
        executable = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        executable = _require_file(executable, "venv Python")
        target = _direct_target(
            "venv", _canonical_path(root), executable, runner=runner, workspace=probe_workspace
        )
        return _validate_identity(target, expected_prefix=_canonical_path(root))

    conda = _conda_executable()
    if conda_env is not None:
        if not conda_env.strip() or any(char in conda_env for char in "\r\n"):
            raise TargetValidationError("Conda environment name is invalid")
        prefix = (conda, "run", "--no-capture-output", "-n", conda_env, "python")
        identity = _run_probe(prefix, runner=runner, workspace=probe_workspace)
        target = EnvironmentTarget("conda-env", conda_env, prefix, identity)
        return _validate_identity(target)

    prefix_path = Path(conda_prefix).expanduser() if conda_prefix is not None else None
    if prefix_path is None or not prefix_path.is_dir():
        raise TargetValidationError(f"Conda prefix does not exist: {conda_prefix}")
    canonical_prefix = _canonical_path(prefix_path)
    command_prefix = (conda, "run", "--no-capture-output", "-p", canonical_prefix, "python")
    identity = _run_probe(command_prefix, runner=runner, workspace=probe_workspace)
    target = EnvironmentTarget("conda-prefix", canonical_prefix, command_prefix, identity)
    return _validate_identity(target, expected_prefix=canonical_prefix)


def add_target_arguments(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--use-current-python", action="store_true")
    group.add_argument("--python-executable")
    group.add_argument("--venv")
    group.add_argument("--conda-env")
    group.add_argument("--conda-prefix")


def parse_target_arguments(argv: Sequence[str]) -> EnvironmentTarget:
    parser = argparse.ArgumentParser(description="Select and validate the install environment")
    parser.add_argument("--lang", choices=("EN", "CHT"))
    add_target_arguments(parser)
    args = parser.parse_args(list(argv))
    return resolve_environment_target(
        use_current_python=args.use_current_python,
        python_executable=args.python_executable,
        venv=args.venv,
        conda_env=args.conda_env,
        conda_prefix=args.conda_prefix,
    )


def build_pip_install_command(
    target: EnvironmentTarget, requirements_file: Path, *, timeout: int = PIP_TIMEOUT_SECONDS
) -> list[str]:
    return [
        *target.command_prefix,
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements_file),
        "--no-cache-dir",
        f"--default-timeout={timeout}",
    ]
