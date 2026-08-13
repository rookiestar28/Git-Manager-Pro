"""Contract tests for deterministic unit and CLI runner behavior."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE_ROOT = REPO_ROOT / ".tmp" / "test-fixtures"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from run_cli_integration_tests import main as cli_runner_main  # noqa: E402
from run_unittests import main as unit_runner_main  # noqa: E402
from test_runner_common import discover_test_files, run_suite  # noqa: E402


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


class RunnerContractTests(unittest.TestCase):
    def test_discovery_is_sorted_and_lanes_are_disjoint(self) -> None:
        with local_tempdir() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            for name in ("test_z.py", "test_cli_b.py", "test_a.py"):
                (root / name).write_text("", encoding="utf-8")
            (root / "nested" / "test_cli_a.py").write_text("", encoding="utf-8")

            all_files = discover_test_files(root, "test_*.py")
            cli_files = discover_test_files(root, "test_*.py", cli_only=True)
            unit_files = discover_test_files(root, "test_*.py", exclude_cli=True)

            self.assertEqual(
                [item.relative_to(root).as_posix() for item in all_files],
                ["nested/test_cli_a.py", "test_a.py", "test_cli_b.py", "test_z.py"],
            )
            self.assertEqual(
                {item.name for item in cli_files}, {"test_cli_a.py", "test_cli_b.py"}
            )
            self.assertEqual({item.name for item in unit_files}, {"test_a.py", "test_z.py"})
            self.assertTrue(set(cli_files).isdisjoint(unit_files))

    def test_shared_suite_returns_distinct_empty_and_failure_statuses(self) -> None:
        self.assertEqual(run_suite(unittest.TestSuite()), 2)

        failing = unittest.FunctionTestCase(
            lambda: self.fail("controlled local failure")
        )
        self.assertEqual(run_suite(unittest.TestSuite([failing])), 1)

    def test_unit_runner_reports_missing_directory_empty_suite_and_failure(self) -> None:
        with local_tempdir() as directory:
            root = Path(directory)
            self.assertEqual(
                unit_runner_main(["--start-dir", str(root / "missing")]), 2
            )

            (root / "test_empty.py").write_text("value = 1\n", encoding="utf-8")
            self.assertEqual(unit_runner_main(["--start-dir", str(root)]), 2)

            (root / "test_failure.py").write_text(
                "import unittest\n"
                "class Failure(unittest.TestCase):\n"
                "    def test_failure(self):\n"
                "        self.fail('controlled local failure')\n",
                encoding="utf-8",
            )
            self.assertEqual(unit_runner_main(["--start-dir", str(root)]), 1)

            (root / "test_import_error.py").write_text(
                "raise RuntimeError('controlled import failure')\n", encoding="utf-8"
            )
            self.assertEqual(unit_runner_main(["--start-dir", str(root)]), 1)

    def test_cli_runner_only_executes_cli_files_and_propagates_failure(self) -> None:
        with local_tempdir() as directory:
            root = Path(directory)
            self.assertEqual(cli_runner_main(["--start-dir", str(root)]), 2)
            (root / "test_regular.py").write_text(
                "raise RuntimeError('must not be imported by CLI lane')\n",
                encoding="utf-8",
            )
            (root / "test_cli_pass.py").write_text(
                "import unittest\n"
                "class Pass(unittest.TestCase):\n"
                "    def test_pass(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            self.assertEqual(cli_runner_main(["--start-dir", str(root)]), 0)

            (root / "test_cli_failure.py").write_text(
                "import unittest\n"
                "class Failure(unittest.TestCase):\n"
                "    def test_failure(self):\n"
                "        self.fail('controlled CLI failure')\n",
                encoding="utf-8",
            )
            self.assertEqual(cli_runner_main(["--start-dir", str(root)]), 1)

            (root / "test_cli_import_error.py").write_text(
                "raise RuntimeError('controlled CLI import failure')\n", encoding="utf-8"
            )
            self.assertEqual(cli_runner_main(["--start-dir", str(root)]), 1)


if __name__ == "__main__":
    unittest.main()
