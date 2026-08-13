$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$env:PRE_COMMIT_HOME = Join-Path $repoRoot ".tmp\pre-commit-home"
New-Item -ItemType Directory -Force $env:PRE_COMMIT_HOME | Out-Null
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-Error "Missing project-local Python at $python. Create .venv and install requirements-dev.txt."
    exit 2
}

function Invoke-Stage {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Host "==> $Name"
    & $Executable @Arguments
    $status = $LASTEXITCODE
    if ($status -ne 0) {
        Write-Error "$Name failed with exit code $status."
        exit $status
    }
}

Push-Location $repoRoot
try {
    Write-Host "==> tool availability"
    & $python -c "import pre_commit, detect_secrets; print('pinned local tools available')"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Pinned tools are missing from $python. Run .venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.txt, then retry."
        exit 2
    }
    Invoke-Stage "detect-secrets" $python @("-m", "pre_commit", "run", "detect-secrets", "--all-files")
    Invoke-Stage "pre-commit" $python @("-m", "pre_commit", "run", "--all-files", "--show-diff-on-failure")
    Invoke-Stage "unit tests" $python @("scripts\run_unittests.py", "--start-dir", "tests", "--pattern", "test_*.py")
    Invoke-Stage "CLI integration tests" $python @("scripts\run_cli_integration_tests.py")
    Invoke-Stage "privacy scan" $python @(
        "scripts\check_test_privacy.py", "--paths", "tests", "scripts", "requirements-dev.txt", ".pre-commit-config.yaml"
    )
    Invoke-Stage "worktree whitespace check" "git" @("diff", "--check")
    Invoke-Stage "candidate whitespace check" "git" @("diff", "--cached", "--check")
    Write-Host "FULL_GATE=PASS"
    exit 0
}
finally {
    Pop-Location
}
