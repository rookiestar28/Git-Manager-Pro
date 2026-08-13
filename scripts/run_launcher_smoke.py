"""Run a bounded native launcher smoke scenario from a caller directory."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from run_launcher_contract_tests import _assert_static_contract, _run_case, _workspace


def run(platform_name: str, workspace: Path, scenario: str) -> int:
    expected_platform = "windows" if os.name == "nt" else "unix"
    if platform_name != expected_platform:
        raise ValueError(f"requested {platform_name} runner on {expected_platform} host")
    _assert_static_contract(platform_name)
    workspace.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"gmp003-smoke-{platform_name}-", dir=workspace) as raw:
        base = Path(raw) / "caller directory with spaces"
        base.mkdir(parents=True)
        metachar = (
            "smoke !bang%percent&pipe|caret^paren()"
            if platform_name == "windows"
            else "smoke spaces;$(no_exec) 'quote' \"$dollar\""
        )
        if scenario in {"all", "clone"}:
            _run_case(base, platform_name, "clone", language="CHT")
        if scenario in {"all", "install"}:
            _run_case(base, platform_name, "conda-prefix", value=metachar, language="CHT")
        if scenario == "all":
            _run_case(base, platform_name, "python", value=metachar, exit_code=2)
    print(f"SMOKE_PASS platform={platform_name} scenario={scenario}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("windows", "unix"), required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--scenario", choices=("all", "clone", "install"), default="all")
    args = parser.parse_args(argv)
    try:
        return run(args.platform, _workspace(args.workspace), args.scenario)
    except Exception as exc:
        print(f"SMOKE_FAIL platform={args.platform} scenario={args.scenario} reason={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
