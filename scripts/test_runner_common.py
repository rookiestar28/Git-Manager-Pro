"""Shared deterministic unittest discovery for repository-local test runners."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Iterable


def discover_test_files(
    start_dir: Path,
    pattern: str,
    *,
    cli_only: bool = False,
    exclude_cli: bool = False,
) -> list[Path]:
    """Return sorted test files with an explicit CLI-lane boundary."""

    files = [
        path
        for path in start_dir.rglob(pattern)
        if path.is_file() and path.suffix == ".py"
    ]
    if cli_only:
        files = [path for path in files if path.name.startswith("test_cli_")]
    if exclude_cli:
        files = [path for path in files if not path.name.startswith("test_cli_")]
    return sorted(files, key=lambda path: path.relative_to(start_dir).as_posix().casefold())


def load_suite(files: Iterable[Path], repo_root: Path) -> unittest.TestSuite:
    """Load files in caller-supplied order without relying on filesystem ordering."""

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for index, path in enumerate(files):
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16]
        module_name = f"gmp_local_test_{index}_{digest}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load test module: {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


def run_suite(suite: unittest.TestSuite, *, verbosity: int = 2) -> int:
    """Run a suite and return 0 only when tests were discovered and passed."""

    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    if result.testsRun == 0:
        print("ERROR: no tests discovered", file=sys.stderr)
        return 2
    return 0 if result.wasSuccessful() else 1
