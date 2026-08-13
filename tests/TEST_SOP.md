# Test SOP

This document is the repository-local verification workflow for Git Manager Pro. It is required
before a roadmap item can be marked accepted.

## Required Reading Order

1. `tests/TEST_SOP.md`
2. `tests/E2E_TESTING_NOTICE.md`
3. `tests/E2E_TESTING_SOP.md`

## Repository Test Lanes

This repository is a CLI-only Python project. It has no frontend or Playwright harness. The
replacement for frontend/E2E validation is the subprocess CLI integration lane plus the authorized
platform smoke lanes described below. A missing frontend E2E run is not a pass claim.

Required order:

1. Project-local tool bootstrap, only when the pinned tool cache is absent.
2. `pre-commit run detect-secrets --all-files`.
3. `pre-commit run --all-files --show-diff-on-failure`.
4. `python scripts/run_unittests.py --start-dir tests --pattern "test_*.py"`.
5. `python scripts/run_cli_integration_tests.py`.
6. `python scripts/check_test_privacy.py --paths tests scripts requirements-dev.txt .pre-commit-config.yaml`.
7. `git diff --check` and `git diff --cached --check` in the clean implementation worktree; the
   latter validates the exact staged candidate that is being accepted.

For launcher changes, the native contract and smoke lanes are additional required checks. Run
these from the implementation worktree with a fresh ignored workspace for each run:

```powershell
python scripts/run_launcher_contract_tests.py --platform windows --workspace .tmp\gmp003-launcher-contract
python scripts/run_launcher_smoke.py --platform windows --workspace .tmp\gmp003-launcher-smoke --scenario all
```

Under WSL/Linux, run the same commands with `--platform unix` and the project-local `.venv-wsl`
interpreter. The contract runner exercises clone, current-Python, explicit interpreter, venv,
Conda name, cancellation, invalid-selection retry, metacharacter arguments, and non-zero child
status propagation. The smoke runner is bounded to native `cmd.exe` or Bash and does not prove
macOS behavior. Launcher fixtures remain inside ignored `.tmp` paths and the child receipt stores
only selector digests and argument counts.

The Windows wrapper is `powershell -File scripts/run_full_tests_windows.ps1`. The WSL/Linux wrapper
is `bash scripts/run_full_tests_linux.sh`. Both wrappers use the project-local venv, stop at the
first failed stage, print a platform-specific remediation message, and return the first failing
stage's exit status.

## Bootstrap And Offline Boundary

`requirements-dev.txt` is a complete hash-pinned lock for direct and transitive development-tool
dependencies. Network access is allowed only for installing that lock and downloading the pinned
pre-commit hook environments. After bootstrap, all unit, CLI integration, privacy, and fixture tests
must run offline. Missing tools or hook caches are explicit failures; global tool fallback is not
allowed.

## Test Design

Tests follow Reproduce -> Pin -> Sweep:

- Reproduce the failure or missing gate with a deterministic command.
- Pin the behavior with a regression test that fails when the contract breaks.
- Sweep the full repository gate on the exact candidate.

Unit tests use standard-library `unittest` and exclude `test_cli_*.py`. CLI integration tests discover
only sorted `test_cli_*.py` files. Both runners fail when zero tests are discovered and propagate
import/test failures with non-zero status.

For GMP-004 automation acceptance, run the explicit failure matrix in addition to the default all-CLI
lane:

```powershell
python scripts/run_cli_integration_tests.py --suite automation-failures
```

```bash
.venv-wsl/bin/python scripts/run_cli_integration_tests.py --suite automation-failures
```

The matrix pins prompt-free clone/install usage, exit codes `0/2/3/4/5/6`, partial and total item
failure, retry exhaustion and timeout, malformed input, JSON stdout/path output, atomic write and
serialization failure, broken pipes, stream separation, and redaction. Its subprocesses are local
fake/mocked commands with bounded timeouts; receipts contain only statuses, counts, and schema
digests. The default CLI runner remains all-CLI discovery; `--suite baseline` and `--suite all` are
explicit choices for focused or complete reruns.

Fixtures must be inside ignored workspace paths, use controlled subprocess environments, and never
contact live Git hosts, PyPI, private indexes, user/global environments, or sibling projects. If pip
is exercised, it must use local packages with `--no-index --find-links`.

Environment-target smoke commands are disposable and workspace-contained:

```powershell
python scripts/run_environment_smoke.py --kind venv --workspace .tmp\\gmp002-venv
python scripts/run_environment_smoke.py --kind conda-prefix --workspace .tmp\\gmp002-conda
```

The Conda-prefix smoke is the only runtime lane allowed to create a Conda environment, and it must
use an authorized host. Probe output is reduced to version/pip status; raw environment payloads are
never recorded.

## Evidence

Accepted work requires a repo-local command log and implementation record with date/timezone,
workspace, branch/base, exact candidate SHA, OS/shell, runtime versions, exact commands, exit status,
redacted material output, failed attempts, corrected reruns, and criterion mapping. Windows and
WSL/Linux evidence are separate; Windows-only evidence cannot satisfy a dual-platform criterion.
