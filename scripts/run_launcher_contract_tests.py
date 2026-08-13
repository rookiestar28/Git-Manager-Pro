"""Run native launcher contract scenarios against a content-limited fake child."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


FORBIDDEN = ("call ", "call\t", "eval ", "eval\t", "cmd /c", "sh -c", "source ")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _workspace(raw: str) -> Path:
    root = REPO_ROOT
    candidate = Path(raw).expanduser().resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise ValueError("workspace must remain inside the repository")
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def _python_path(platform_name: str) -> str:
    if platform_name == "windows":
        candidate = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = REPO_ROOT / ".venv-wsl" / "bin" / "python"
    if not candidate.is_file():
        raise RuntimeError(f"missing project-local bootstrap interpreter: {candidate}")
    return str(candidate)


def _controlled_env(workspace: Path, platform_name: str, receipt: Path, child_exit: int) -> dict[str, str]:
    allowed = {"PATH", "SYSTEMROOT", "SystemRoot", "LANG", "LC_ALL", "PYTHONUTF8"}
    environment = {key: os.environ[key] for key in allowed if os.environ.get(key)}
    python_parent = str(Path(_python_path(platform_name)).parent)
    if platform_name == "windows":
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        environment["PATH"] = python_parent + ";" + str(Path(system_root) / "System32")
        environment["SYSTEMROOT"] = system_root
        environment["SystemRoot"] = system_root
    else:
        environment["PATH"] = python_parent + ":/usr/bin:/bin"
    environment.update(
        {
            "PYTHONNOUSERSITE": "1",
            "GMP003_FAKE_CHILD_RECEIPT": str(receipt),
            "GMP003_FAKE_CHILD_EXIT": str(child_exit),
        }
    )
    return environment


def _write_fake_core(path: Path) -> None:
    path.write_text(
        '''import hashlib
import json
import os
import sys

args = sys.argv[1:]
language = ""
if "--lang" in args and args.index("--lang") + 1 < len(args):
    language = args[args.index("--lang") + 1]
known = ("--use-current-python", "--python-executable", "--venv", "--conda-env", "--conda-prefix")
selectors = []
for flag in known:
    if flag in args:
        index = args.index(flag)
        value = "" if flag == "--use-current-python" else args[index + 1] if index + 1 < len(args) else ""
        selectors.append({"flag": flag, "value_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()})
receipt = {"argc": len(args), "language": language, "selectors": selectors}
with open(os.environ["GMP003_FAKE_CHILD_RECEIPT"], "w", encoding="utf-8") as stream:
    json.dump(receipt, stream, sort_keys=True)
raise SystemExit(int(os.environ.get("GMP003_FAKE_CHILD_EXIT", "0")))
''',
        encoding="utf-8",
        newline="\n",
    )


def _prepare_fixture(workspace: Path, platform_name: str) -> tuple[Path, Path]:
    fixture = workspace / f"fixture {platform_name} with spaces"
    fixture.mkdir(parents=True, exist_ok=True)
    source = REPO_ROOT / ("Auto_Installer.bat" if platform_name == "windows" else "Auto_Installer.sh")
    launcher = fixture / source.name
    shutil.copy2(source, launcher)
    if platform_name != "windows":
        launcher.chmod(0o755)
    core = fixture / "auto_installer.py"
    _write_fake_core(core)
    return fixture, launcher


def _run_native(
    launcher: Path,
    fixture: Path,
    platform_name: str,
    transcript: str,
    receipt: Path,
    child_exit: int,
) -> subprocess.CompletedProcess[str]:
    env = _controlled_env(fixture, platform_name, receipt, child_exit)
    if platform_name == "windows":
        # `call` is used only by this disposable harness to enter a batch file with
        # spaces in its path; the launcher under test contains no call/reparse boundary.
        # cmd.exe set /p reads multiple prompts reliably from a redirected CRLF file,
        # whereas a direct pipe is consumed after the first prompt on this host.
        transcript_path = fixture / "gmp003-input.txt"
        transcript_path.write_text(transcript.replace("\n", "\r\n"), encoding="utf-8", newline="")
        command = ["cmd.exe", "/d", "/s", "/c", f"call {launcher.name} < {transcript_path.name}"]
        input_data = None
    else:
        command = ["bash", launcher.name]
        input_data = transcript
    return subprocess.run(
        command,
        cwd=fixture,
        env=env,
        input=input_data,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _assert_receipt(receipt: Path, flag: str, value: str | None, language: str) -> None:
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["language"] == language, payload
    if flag == "":
        assert payload["selectors"] == [], payload
        return
    expected_value = "" if value is None else value
    assert payload["selectors"] == [{"flag": flag, "value_sha256": _digest(expected_value)}], payload


def _static_check(platform_name: str) -> None:
    source = (REPO_ROOT / ("Auto_Installer.bat" if platform_name == "windows" else "Auto_Installer.sh")).read_text(
        encoding="utf-8"
    ).lower()
    for token in FORBIDDEN:
        assert token not in source, f"forbidden launcher boundary: {token}"


def _assert_static_contract(platform_name: str) -> None:
    """Compatibility entry point used by the smoke runner."""

    _static_check(platform_name)


def _run_case(
    caller_root: Path,
    platform_name: str,
    mode: str,
    *,
    value: str | None = None,
    language: str = "EN",
    exit_code: int = 0,
) -> None:
    """Run one native launcher scenario from a caller directory outside the repo."""

    fixture, launcher = _prepare_fixture(caller_root / f"case-{mode}", platform_name)
    language_choice = "2" if language == "CHT" else "1"
    if mode == "clone":
        transcript = f"{language_choice}\n1\n\n3\n"
        expected_flag, expected_value = "", None
    elif mode in {"cancel", "invalid-cancel"}:
        invalid_choice = "9\n" if mode == "invalid-cancel" else ""
        transcript = f"{language_choice}\n2\n{invalid_choice}6\n3\n"
        receipt = fixture / "receipt.json"
        result = _run_native(launcher, fixture, platform_name, transcript, receipt, exit_code)
        assert result.returncode == 0, (mode, result.returncode, result.stderr[-400:])
        assert not receipt.exists(), (mode, result.stdout[-400:])
        return
    else:
        target_choice = {
            "python": "2",
            "venv": "3",
            "conda-env": "4",
            "conda-prefix": "5",
            "current": "1",
        }.get(mode)
        if target_choice is None:
            raise ValueError(f"unknown launcher scenario: {mode}")
        if mode == "current":
            transcript = f"{language_choice}\n2\n{target_choice}\n\n3\n"
            expected_flag, expected_value = "--use-current-python", ""
        else:
            if value is None:
                raise ValueError(f"scenario {mode} requires a value")
            transcript = f"{language_choice}\n2\n{target_choice}\n{value}\n"
            if exit_code == 0:
                transcript += "\n3\n"
            expected_flag = {
                "python": "--python-executable",
                "venv": "--venv",
                "conda-env": "--conda-env",
                "conda-prefix": "--conda-prefix",
            }[mode]
            expected_value = value
    receipt = fixture / "receipt.json"
    result = _run_native(launcher, fixture, platform_name, transcript, receipt, exit_code)
    assert result.returncode == exit_code, (mode, result.returncode, result.stderr[-400:])
    if mode == "clone" and exit_code == 0:
        _assert_receipt(receipt, "", None, language)
    else:
        _assert_receipt(receipt, expected_flag, expected_value, language)


def run(platform_name: str, workspace: Path) -> None:
    if platform_name == "windows" and os.name != "nt":
        raise RuntimeError("windows contract lane requires native Windows cmd.exe")
    if platform_name == "unix" and os.name == "nt":
        raise RuntimeError("unix contract lane must run under WSL/Linux Bash")
    _static_check(platform_name)
    fixture, launcher = _prepare_fixture(workspace, platform_name)
    cases = (
        ("clone", "1\n1\n\n3\n", "", None, 0),
        ("current", "1\n2\n1\n\n3\n", "--use-current-python", "", 0),
        ("interpreter", "1\n2\n2\n" + str(REPO_ROOT / "path with ! % & | ^ ( ) ; value") + "\n", "--python-executable", str(REPO_ROOT / "path with ! % & | ^ ( ) ; value"), 2),
        # Successful install returns to the menu after consuming a pause line;
        # feed an empty pause response and an explicit exit choice.
        ("venv", "1\n2\n3\n" + str(REPO_ROOT / "venv with spaces") + "\n\n3\n", "--venv", str(REPO_ROOT / "venv with spaces"), 0),
        (
            "conda-name",
            "2\n2\n4\n" + "name ; $() " + "\\\n" + "\n3\n",
            "--conda-env",
            "name ; $() \\",
            0,
        ),
        ("cancel", "1\n2\n6\n3\n", "", None, 0),
        ("invalid-cancel", "2\n2\n9\n6\n3\n", "", None, 0),
        ("control-tab", "1\n2\n2\nabc\tdef\n6\n3\n", "", None, 0),
        ("control-bell", "1\n2\n2\nabc\x07def\n6\n3\n", "", None, 0),
        ("control-escape", "1\n2\n2\nabc\x1bdef\n6\n3\n", "", None, 0),
        ("control-delete", "1\n2\n2\nabc\x7fdef\n6\n3\n", "", None, 0),
    )
    for name, transcript, flag, value, child_exit in cases:
        receipt = fixture / f"receipt-{name}.json"
        if receipt.exists():
            receipt.unlink()
        result = _run_native(launcher, fixture, platform_name, transcript, receipt, child_exit)
        if name in {"cancel", "invalid-cancel"} or name.startswith("control-"):
            assert not receipt.exists(), (name, result.stdout, result.stderr)
            assert result.returncode == 0, (name, result.returncode, result.stderr)
        elif child_exit:
            assert result.returncode == child_exit, (name, result.returncode, result.stderr)
            _assert_receipt(receipt, flag, value, "EN")
        else:
            assert result.returncode == 0, (name, result.returncode, result.stderr)
            _assert_receipt(receipt, flag, value, "CHT" if name == "conda-name" else "EN")
    print(f"CONTRACT_PASS platform={platform_name} cases={len(cases)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("windows", "unix"), required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)
    try:
        run(args.platform, _workspace(args.workspace))
    except (AssertionError, OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"CONTRACT_FAIL platform={args.platform} reason={exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
