"""Run the subprocess-oriented CLI integration lane."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from test_runner_common import discover_test_files, load_suite, run_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-dir", default="tests", help="test directory")
    parser.add_argument(
        "--suite",
        choices=("baseline", "automation-failures", "all"),
        default="all",
        help="CLI suite to run (default: all; baseline remains available explicitly)",
    )
    args = parser.parse_args(argv)

    start_dir = Path(args.start_dir).resolve()
    if not start_dir.is_dir():
        print(f"ERROR: test directory does not exist: {start_dir}", file=sys.stderr)
        return 2
    try:
        all_files = discover_test_files(start_dir, "test_cli_*.py", cli_only=True)
        if args.suite == "baseline":
            files = [path for path in all_files if path.name == "test_cli_baseline.py"]
        elif args.suite == "automation-failures":
            files = [path for path in all_files if path.name == "test_cli_automation_failures.py"]
        else:
            files = all_files
        suite = load_suite(files, start_dir.parent)
    except Exception as exc:
        print(f"ERROR: unable to load CLI integration tests: {exc}", file=sys.stderr)
        return 1
    return run_suite(suite)


if __name__ == "__main__":
    raise SystemExit(main())
