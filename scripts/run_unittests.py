"""Run the non-CLI unit-test lane with deterministic discovery and exit status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from test_runner_common import discover_test_files, load_suite, run_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-dir", default="tests", help="test directory")
    parser.add_argument("--pattern", default="test_*.py", help="filename pattern")
    args = parser.parse_args(argv)

    start_dir = Path(args.start_dir).resolve()
    if not start_dir.is_dir():
        print(f"ERROR: test directory does not exist: {start_dir}", file=sys.stderr)
        return 2
    try:
        files = discover_test_files(start_dir, args.pattern, exclude_cli=True)
        suite = load_suite(files, start_dir.parent)
    except Exception as exc:
        print(f"ERROR: unable to load unit tests: {exc}", file=sys.stderr)
        return 1
    return run_suite(suite)


if __name__ == "__main__":
    raise SystemExit(main())
