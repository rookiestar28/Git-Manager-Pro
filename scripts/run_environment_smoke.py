"""Create a disposable environment and verify the GMP-002 target contract."""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import shutil
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

from environment_target import (
    TargetValidationError,
    build_controlled_environment,
    resolve_environment_target,
)


def _workspace_path(raw: str) -> Path:
    workspace = Path.cwd().resolve()
    candidate = Path(raw).expanduser().resolve(strict=False)
    if not candidate.is_relative_to(workspace):
        raise TargetValidationError("smoke workspace must remain inside the current repository")
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def _run(
    command: list[str],
    *,
    workspace: Path,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=False,
        env=build_controlled_environment(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _write_local_wheel(workspace: Path) -> Path:
    """Create a tiny pure-Python wheel so smoke installation never needs an index."""

    distribution = "gmp002_smoke_package"
    version = "0.0.1"
    normalized = distribution.replace("-", "_")
    dist_info = f"{normalized}-{version}.dist-info"
    files = {
        f"{distribution}/__init__.py": b"SMOKE_MARKER = 'gmp002'\n",
        f"{dist_info}/METADATA": (
            f"Metadata-Version: 2.1\nName: {distribution}\nVersion: {version}\n\n"
        ).encode("utf-8"),
        f"{dist_info}/WHEEL": b"Wheel-Version: 1.0\nGenerator: gmp002\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    record_lines = []
    for name, content in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode("ascii")
        record_lines.append(f"{name},sha256={digest},{len(content)}")
    files[f"{dist_info}/RECORD"] = ("\n".join(record_lines) + f"\n{dist_info}/RECORD,,\n").encode("utf-8")
    wheel = workspace / f"{normalized}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return wheel


def _offline_local_install(target, workspace: Path) -> None:
    wheel = _write_local_wheel(workspace)
    install = _run(
        [
            *target.command_prefix,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-cache-dir",
            str(wheel),
        ],
        workspace=workspace,
        timeout=120,
    )
    if install.returncode != 0:
        raise TargetValidationError("offline local-package pip smoke failed")
    import_check = _run(
        [*target.command_prefix, "-c", "import gmp002_smoke_package"],
        workspace=workspace,
        timeout=60,
    )
    if import_check.returncode != 0:
        raise TargetValidationError("offline local-package import smoke failed")


def _venv_smoke(workspace: Path) -> int:
    venv_root = workspace / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_root)
    target = resolve_environment_target(venv=str(venv_root), probe_workspace=workspace)
    result = _run([*target.command_prefix, "-m", "pip", "--version"], workspace=workspace, timeout=60)
    if result.returncode != 0:
        raise TargetValidationError("venv pip smoke failed")
    _offline_local_install(target, workspace)
    print(f"SMOKE_PASS kind=venv python={target.identity.version} pip={target.identity.pip_available}")
    return 0


def _conda_smoke(workspace: Path) -> int:
    conda = os.environ.get("CONDA_EXE") or shutil.which("conda")
    if not conda:
        raise TargetValidationError("conda executable was not found")
    prefix = workspace / "conda-prefix"
    create = _run(
        [str(conda), "create", "--yes", "--prefix", str(prefix), "python", "pip"],
        workspace=workspace,
        timeout=600,
    )
    if create.returncode != 0:
        raise TargetValidationError("disposable Conda prefix creation failed")
    target = resolve_environment_target(conda_prefix=str(prefix), probe_workspace=workspace)
    result = _run([*target.command_prefix, "-m", "pip", "--version"], workspace=workspace, timeout=60)
    if result.returncode != 0:
        raise TargetValidationError("Conda-prefix pip smoke failed")
    _offline_local_install(target, workspace)
    print(f"SMOKE_PASS kind=conda-prefix python={target.identity.version} pip={target.identity.pip_available}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("venv", "conda-prefix"), required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)
    try:
        workspace = _workspace_path(args.workspace)
        return _venv_smoke(workspace) if args.kind == "venv" else _conda_smoke(workspace)
    except (TargetValidationError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"SMOKE_FAIL kind={args.kind} reason={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
