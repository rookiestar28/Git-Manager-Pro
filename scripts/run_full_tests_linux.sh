#!/usr/bin/env bash
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$repo_root/.venv-wsl/bin/python"
export PRE_COMMIT_HOME="$repo_root/.tmp/pre-commit-home"
mkdir -p "$PRE_COMMIT_HOME"
if [[ ! -x "$python_bin" ]]; then
  echo "ERROR: missing project-local Python at $python_bin; create .venv-wsl and install requirements-dev.txt." >&2
  exit 2
fi

run_stage() {
  local name="$1"
  shift
  echo "==> $name"
  "$@"
  local status=$?
  if [[ $status -ne 0 ]]; then
    echo "ERROR: $name failed with exit code $status." >&2
    exit "$status"
  fi
}

cd "$repo_root"
echo "==> tool availability"
"$python_bin" -c "import pre_commit, detect_secrets; print('pinned local tools available')"
tool_status=$?
if [[ $tool_status -ne 0 ]]; then
  echo "ERROR: pinned tools are missing from $python_bin; run .venv-wsl/bin/python -m pip install --require-hashes -r requirements-dev.txt, then retry." >&2
  exit 2
fi
run_stage "detect-secrets" "$python_bin" -m pre_commit run detect-secrets --all-files
run_stage "pre-commit" "$python_bin" -m pre_commit run --all-files --show-diff-on-failure
run_stage "unit tests" "$python_bin" scripts/run_unittests.py --start-dir tests --pattern 'test_*.py'
run_stage "CLI integration tests" "$python_bin" scripts/run_cli_integration_tests.py
run_stage "privacy scan" "$python_bin" scripts/check_test_privacy.py --paths tests scripts requirements-dev.txt .pre-commit-config.yaml
run_stage "worktree whitespace check" git diff --check
run_stage "candidate whitespace check" git diff --cached --check
echo "FULL_GATE=PASS"
