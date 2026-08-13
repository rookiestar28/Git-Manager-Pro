"""Git clone and dependency installation automation with stable CLI contracts."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, TextIO
from urllib.parse import urlsplit

from scripts.environment_target import (
    EnvironmentTarget,
    TargetValidationError,
    add_target_arguments,
    build_pip_install_command,
    parse_target_arguments,
    resolve_environment_target,
)

IGNORE_LIST = ["__pycache__", ".git", ".vscode", "venv", "env", ".idea", "python_embeded"]
MAX_RETRIES = 3
PIP_TIMEOUT = 60
MAX_CAPTURE_LINES = 80
MAX_CAPTURE_BYTES = 16 * 1024

EXIT_SUCCESS = 0
EXIT_USAGE = 2
EXIT_ENVIRONMENT = 3
EXIT_OPERATION = 4
EXIT_CANCELLED = 5
EXIT_OUTPUT = 6

_OUTPUT_STREAM: Optional[TextIO] = None
_OUTPUT_FAILURE = False


class OperationCancelled(Exception):
    """Raised when an interactive operator cancels before a child starts."""


class CliUsageError(ValueError):
    """Raised when non-interactive inputs fail preflight."""


class EnvironmentFailure(ValueError):
    """Raised when a syntactically valid target cannot be validated."""


class OutputFailure(OSError):
    """Raised when a requested machine-readable output cannot be emitted."""


@dataclass(frozen=True)
class OperationItem:
    item_id: str
    label: str
    state: str
    attempts: int
    error_category: Optional[str] = None


@dataclass(frozen=True)
class OperationResult:
    operation: str
    status: str
    exit_code: int
    items: tuple[OperationItem, ...] = ()

    @property
    def counts(self) -> dict[str, int]:
        return {
            "attempted": sum(item.state != "skipped" for item in self.items),
            "succeeded": sum(item.state == "succeeded" for item in self.items),
            "failed": sum(item.state == "failed" for item in self.items),
            "skipped": sum(item.state == "skipped" for item in self.items),
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "operation": self.operation,
            "status": self.status,
            "exit_code": self.exit_code,
            "counts": self.counts,
            "items": [
                {
                    "item_id": item.item_id,
                    "label": item.label,
                    "state": item.state,
                    "attempts": item.attempts,
                    "error_category": item.error_category,
                }
                for item in self.items
            ],
        }


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


if sys.platform == "win32":
    os.system("color")


TEXT: Dict[str, Dict[str, str]] = {
    "EN": {
        "menu_header": " AIGC Project Manager ",
        "menu_1": "1. Batch Git Clone (from list)",
        "menu_2": "2. Batch Install Dependencies (requirements.txt)",
        "menu_prompt": "Please select a mode (1 or 2): ",
        "path_prompt": "Please enter the target ABSOLUTE PATH (e.g., D:\\ComfyUI\\custom_nodes): ",
        "path_invalid": "Directory does not exist. Create it? (y/n): ",
        "path_created": "Directory created: {}",
        "op_cancel": "Operation cancelled.",
        "done": "All tasks completed.",
        "list_prompt": "Please enter the path to the URL list file, or drag and drop it to here (.txt): ",
        "list_err": "File not found.",
        "cloning": "  [*] Cloning: {}",
        "clone_success": "    -> [Success] Cloned '{}'",
        "clone_fail": "    -> [Failed] Error cloning '{}'",
        "clone_exists": "    -> [Skip] Folder '{}' already exists.",
        "scanning": "Scanning directory: ",
        "found_req": "  [*] Found 'requirements.txt' in: ",
        "installing": "    -> Installing dependencies (Attempt {}/{})...",
        "success": "    -> [Success] Dependencies installed for '{}'.",
        "fail": "    -> [Failed] Error installing dependencies for '{}' after retries.",
        "skip": "    -> [Skipped] No requirements.txt found.",
        "summary_header": " Execution Summary ",
        "conflict_header": " Error Report ",
    },
    "CHT": {
        "menu_header": " AIGC 專案管理工具 ",
        "menu_1": "1. 批次複製專案 (Git Clone)",
        "menu_2": "2. 批次安裝依賴 (Install Dependencies)",
        "menu_prompt": "請選擇模式 (1 或 2): ",
        "path_prompt": "請輸入目標資料夾的「絕對路徑」 (例如 D:\\ComfyUI\\custom_nodes): ",
        "path_invalid": "目錄不存在，是否建立？(y/n): ",
        "path_created": "已建立目錄: {}",
        "op_cancel": "作業已取消。",
        "done": "所有作業執行完畢。",
        "list_prompt": "請輸入 URL 清單文件的路徑，或直接拖移檔案加入此處 (.txt): ",
        "list_err": "找不到檔案，請重新輸入。",
        "cloning": "  [*] 正在複製專案: {}",
        "clone_success": "    -> [成功] 已複製 '{}'",
        "clone_fail": "    -> [失敗] 複製 '{}' 時發生錯誤",
        "clone_exists": "    -> [略過] 資料夾 '{}' 已存在。",
        "scanning": "正在掃描目錄: ",
        "found_req": "  [*] 在目錄中找到 'requirements.txt': ",
        "installing": "    -> 正在安裝依賴 (第 {}/{} 次嘗試)...",
        "success": "    -> [成功] 已安裝 '{}' 的依賴。",
        "fail": "    -> [失敗] 經重試後，安裝 '{}' 的依賴仍然失敗。",
        "skip": "    -> [略過] 未找到 requirements.txt。",
        "summary_header": " 執行結果統計 ",
        "conflict_header": " 錯誤報告 ",
    },
}

current_lang = "EN"


def t(key: str) -> str:
    return str(TEXT.get(current_lang, TEXT["EN"]).get(key, key))


def _human_stream() -> TextIO:
    return _OUTPUT_STREAM or sys.stdout


def _emit(text: str, *, end: str = "\n") -> None:
    global _OUTPUT_FAILURE
    try:
        stream = _human_stream()
        stream.write(text + end)
        stream.flush()
    except (BrokenPipeError, OSError):
        _OUTPUT_FAILURE = True
        raise OutputFailure("human output pipe closed")


def print_color(color: str, message: str) -> None:
    _emit(f"{color}{message}{Colors.RESET}")


def _sanitize_text(value: object) -> str:
    """Keep child diagnostics useful without preserving URLs, credentials, or absolute paths."""

    text = str(value)
    text = re.sub(r"(?i)\b(?:https?|ssh|git)://[^\s]+", "[REDACTED_URL]", text)
    text = re.sub(r"(?i)\b[^\s@]+@[^\s:]+:[^\s]+", "[REDACTED_URL]", text)
    text = re.sub(
        r"(?i)\b(token|password|passwd|api[_-]?key|authorization|cookie|pip_[a-z_]+)\s*[:=]\s*[^\s]+",
        r"\1=[REDACTED_SECRET]",
        text,
    )
    text = re.sub(
        r"(?i)(?:[A-Z]:[\\/]\S+|\\\\\S+|/(?:home|mnt|tmp|Users|var|opt|workspace)/\S+)",
        "[REDACTED_PATH]",
        text,
    )
    return text


def _bounded_lines(log: str) -> list[str]:
    retained: list[str] = []
    total = 0
    for raw_line in _sanitize_text(log).splitlines():
        line = raw_line[:512]
        encoded = len(line.encode("utf-8", errors="replace"))
        if len(retained) >= MAX_CAPTURE_LINES or total + encoded > MAX_CAPTURE_BYTES:
            retained.append("[output truncated]")
            break
        retained.append(line)
        total += encoded
    return retained


def read_file_safe(filepath: str | Path) -> list[str]:
    encodings = ["utf-8", "utf-8-sig", "utf-16", "cp950", "gbk", "latin-1"]
    for enc in encodings:
        try:
            lines: list[str] = []
            with open(filepath, "r", encoding=enc) as file:
                for line in file:
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith("#"):
                        continue
                    if "http" in clean_line and not clean_line.startswith("http"):
                        clean_line = clean_line[clean_line.find("http") :]
                    lines.append(clean_line)
            return lines
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            print_color(Colors.RED, f"Read Error: {_sanitize_text(exc)}")
            return []
    print_color(Colors.RED, "Failed to read file with known encodings.")
    return []


def set_language_interactive() -> None:
    global current_lang
    lang_c = input("Select Language / 語言選擇 (1: EN, 2: CHT): ").strip()
    if lang_c == "2":
        current_lang = "CHT"
    else:
        current_lang = "EN"


def get_target_directory(allow_create: bool = False) -> Path:
    while True:
        user_path = input(t("path_prompt")).strip().strip('"').strip("'")
        if not user_path:
            continue
        path_obj = Path(user_path)
        if path_obj.is_dir():
            return path_obj
        if allow_create:
            confirm = input(t("path_invalid")).lower()
            if confirm == "y":
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    _emit(t("path_created").format(_sanitize_text(path_obj)))
                    return path_obj
                except Exception as exc:
                    print_color(Colors.RED, f"Error: {_sanitize_text(exc)}")
            else:
                _emit(t("op_cancel"))
                raise OperationCancelled
        else:
            print_color(Colors.RED, "Invalid path.")


def run_command_stream(
    command: list[str], cwd: str | Path, timeout: float = PIP_TIMEOUT
) -> tuple[int, str]:
    """Run a child with shell=False, bounded streaming, and a hard wall-clock timeout."""

    captured: list[str] = []
    captured_bytes = 0
    emitted_truncation = False
    events: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=MAX_CAPTURE_LINES + 4)
    process: subprocess.Popen[str] | None = None
    reader_thread: threading.Thread | None = None
    overflow_sent = False

    def enqueue_event(event: tuple[str, object]) -> None:
        """Keep a non-blocking bounded queue while reserving delivery for EOF/errors."""

        nonlocal overflow_sent
        kind = event[0]
        if kind == "overflow":
            if overflow_sent:
                return
            overflow_sent = True
        if kind == "line":
            try:
                events.put_nowait(event)
            except queue.Full:
                if overflow_sent:
                    return
                overflow_sent = True
                while True:
                    try:
                        events.get_nowait()
                    except queue.Empty:
                        break
                    if not events.full():
                        break
                try:
                    events.put_nowait(("overflow", None))
                except queue.Full:
                    pass
            return
        while events.full():
            try:
                events.get_nowait()
            except queue.Empty:
                return
        try:
            events.put_nowait(event)
        except queue.Full:
            return

    def capture_line(line: str) -> None:
        nonlocal captured_bytes, emitted_truncation
        safe_line = _sanitize_text(line.rstrip("\r\n"))
        if safe_line == "[output truncated]":
            if not emitted_truncation:
                emitted_truncation = True
                captured.append(safe_line)
                _emit(safe_line, end="\n")
            return
        encoded = len(safe_line.encode("utf-8", errors="replace"))
        if len(captured) < MAX_CAPTURE_LINES and captured_bytes + encoded <= MAX_CAPTURE_BYTES:
            captured.append(safe_line)
            captured_bytes += encoded
            _emit(safe_line, end="\n")
        elif not emitted_truncation:
            emitted_truncation = True
            captured.append("[output truncated]")
            _emit("[output truncated]", end="\n")

    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            shell=False,
        )
        if process.stdout is None:
            return -1, "spawn_failed"

        def reader() -> None:
            try:
                for line in process.stdout:  # type: ignore[union-attr]
                    try:
                        enqueue_event(("line", line))
                    except Exception:
                        enqueue_event(("overflow", None))
            except Exception as exc:  # pragma: no cover - platform pipe edge
                enqueue_event(("error", exc))
            finally:
                enqueue_event(("eof", None))

        reader_thread = threading.Thread(target=reader, name="gmp-output-reader", daemon=True)
        reader_thread.start()
        started = time.monotonic()
        saw_eof = False
        while not saw_eof:
            if time.monotonic() - started > timeout:
                _terminate_process(process, reader_thread)
                return -1, "timeout"
            try:
                kind, payload = events.get(timeout=0.05)
            except queue.Empty:
                if time.monotonic() - started > timeout:
                    _terminate_process(process, reader_thread)
                    return -1, "timeout"
                continue
            if kind == "line":
                capture_line(str(payload))
            elif kind == "overflow":
                capture_line("[output truncated]")
            elif kind == "error":
                raise OSError("child output could not be read") from payload
            else:
                saw_eof = True
        process.wait(timeout=max(0.0, timeout - (time.monotonic() - started)))
        if reader_thread is not None:
            reader_thread.join(timeout=1)
        process.stdout.close()
        return process.returncode, "\n".join(captured)
    except subprocess.TimeoutExpired:
        if process is not None:
            _terminate_process(process, reader_thread)
        return -1, "timeout"
    except OutputFailure:
        if process is not None:
            _terminate_process(process, reader_thread)
        return -1, "output_failed"
    except (FileNotFoundError, OSError) as exc:
        if process is not None:
            _terminate_process(process, reader_thread)
        safe = _sanitize_text(exc)
        try:
            print_color(Colors.RED, f"Execution Error: {safe}")
        except OutputFailure:
            return -1, "[output truncated]"
        return -1, "spawn_failed"


def _terminate_process(
    process: subprocess.Popen[str], reader_thread: threading.Thread | None = None
) -> None:
    """Best-effort child cleanup that never leaks a second timeout/traceback."""

    try:
        process.kill()
    except OSError:
        pass
    try:
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        pass
    if reader_thread is not None:
        reader_thread.join(timeout=5)
    try:
        if process.stdout is not None:
            process.stdout.close()
    except (OSError, ValueError):
        pass


def _failure_category(log: str, default: str) -> str:
    if log in {"timeout", "spawn_failed", "output_failed"}:
        return log
    return default


def extract_error_info(full_log: str) -> list[str]:
    keywords = ("ERROR:", "conflict", "Conflict", "Incompatible", "ResolutionImpossible")
    lines = _bounded_lines(full_log)
    selected = [line for line in lines if line.startswith("ERROR:") or any(k in line for k in keywords)]
    return selected or lines[-3:]


def _safe_label(value: object) -> str:
    text = str(value).rstrip("/\\")
    parsed = urlsplit(text)
    if parsed.scheme and parsed.path:
        text = parsed.path.rstrip("/\\")
    else:
        text = re.split(r"[?#]", text, maxsplit=1)[0].rstrip("/\\")
        scp_match = re.match(r"^[^@/\\\s]+@[^:\s]+:(.+)$", text)
        if scp_match:
            text = scp_match.group(1).rstrip("/\\")
    tail = re.split(r"[/\\]", text)[-1]
    if tail.lower().endswith(".git"):
        tail = tail[:-4]
    label = re.sub(r"[^A-Za-z0-9._-]+", "_", tail).strip("._-")
    return (label or "item")[:64]


def _item_id(index: int) -> str:
    return f"item-{index:04d}"


def _result_from_items(operation: str, items: Iterable[OperationItem]) -> OperationResult:
    frozen = tuple(items)
    failed = any(item.state == "failed" for item in frozen)
    if failed:
        status = "partial_failure" if any(item.state in {"succeeded", "skipped"} for item in frozen) else "failure"
        return OperationResult(operation, status, EXIT_OPERATION, frozen)
    return OperationResult(operation, "success", EXIT_SUCCESS, frozen)


def _terminal_result(operation: str, status: str, code: int) -> OperationResult:
    return OperationResult(operation, status, code, ())


def _render_summary(result: OperationResult, error_details: dict[str, list[str]] | None = None) -> None:
    counts = result.counts
    _emit("\n" + "=" * 20 + t("summary_header") + "=" * 20)
    _emit(
        f"Success: {counts['succeeded']} | Failed: {counts['failed']} | Skipped: {counts['skipped']}"
    )
    if result.items and counts["failed"]:
        _emit("\n" + "=" * 20 + t("conflict_header") + "=" * 20)
        for item in result.items:
            if item.state != "failed":
                continue
            _emit(f"\n[ {item.label} ]")
            _emit(f"    category: {item.error_category or 'operation_failed'}")
            for error in (error_details or {}).get(item.item_id, []):
                print_color(Colors.YELLOW, error)
    _emit("\n" + t("done"))


def mode_git_clone(
    *,
    target_directory: str | Path | None = None,
    list_path: str | Path | None = None,
    non_interactive: bool = False,
    git_command: Sequence[str] | None = None,
) -> OperationResult:
    try:
        if target_directory is None:
            target_dir = get_target_directory(allow_create=True)
        else:
            target_dir = Path(target_directory).expanduser()
            if not target_dir.is_dir():
                raise CliUsageError("target directory must already exist")
        if list_path is None:
            while True:
                candidate = Path(input(t("list_prompt")).strip().strip('"').strip("'"))
                if candidate.is_file():
                    list_path = candidate
                    break
                print_color(Colors.RED, t("list_err"))
        elif not Path(list_path).is_file():
            raise CliUsageError("clone list does not exist")
        urls = read_file_safe(Path(list_path))
        if non_interactive and not urls:
            raise CliUsageError("clone list is empty or unreadable")
    except (EOFError, OperationCancelled):
        _emit(t("op_cancel"))
        result = _terminal_result("clone", "cancelled", EXIT_CANCELLED)
        return result

    _emit("\n" + "-" * 50)
    _emit(f"Target: {_sanitize_text(target_dir)}")
    _emit(f"Total URLs: {len(urls)}")
    _emit("-" * 50)
    items: list[OperationItem] = []
    details: dict[str, list[str]] = {}
    for index, url in enumerate(urls, 1):
        item_id = _item_id(index)
        label = _safe_label(url)
        destination = target_dir / label
        print_color(Colors.CYAN, t("cloning").format(label))
        if destination.exists():
            print_color(Colors.YELLOW, t("clone_exists").format(label))
            items.append(OperationItem(item_id, label, "skipped", 0, "already_exists"))
            continue
        try:
            command = [*(git_command or ("git",)), "clone", url]
            return_code, log = run_command_stream(command, cwd=target_dir)
        except subprocess.TimeoutExpired:
            return_code, log = -1, "timeout"
        if return_code == 0:
            print_color(Colors.GREEN, t("clone_success").format(label))
            items.append(OperationItem(item_id, label, "succeeded", 1))
        else:
            print_color(Colors.RED, t("clone_fail").format(label))
            items.append(OperationItem(item_id, label, "failed", 1, _failure_category(log, "clone_failed")))
            details[item_id] = extract_error_info(log)
        _emit("-" * 30)
    result = _result_from_items("clone", items)
    _render_summary(result, details)
    return result


def mode_install_dependencies(
    target: Optional[EnvironmentTarget] = None,
    *,
    target_directory: str | Path | None = None,
    non_interactive: bool = False,
) -> OperationResult:
    try:
        if target_directory is None:
            target_dir = get_target_directory(allow_create=False)
        else:
            target_dir = Path(target_directory).expanduser()
            if not target_dir.is_dir():
                raise CliUsageError("target directory must already exist")
        if target is None:
            if non_interactive:
                raise CliUsageError("an explicit environment selector is required")
            target = resolve_environment_target(use_current_python=True)
    except (EOFError, OperationCancelled):
        _emit(t("op_cancel"))
        return _terminal_result("install", "cancelled", EXIT_CANCELLED)
    except TargetValidationError as exc:
        raise EnvironmentFailure(str(exc)) from exc

    _emit("\n" + "-" * 50)
    _emit(f"{t('scanning')}{_sanitize_text(target_dir)}")
    _emit("-" * 50)
    print_color(Colors.YELLOW, f"Using Python Interpreter: {_sanitize_text(target.python_executable)}")
    _emit("-" * 50)

    items: list[OperationItem] = []
    details: dict[str, list[str]] = {}
    candidates = sorted((item for item in target_dir.iterdir() if item.is_dir()), key=lambda item: item.name)
    visible_index = 0
    for item in candidates:
        if item.name in IGNORE_LIST:
            continue
        visible_index += 1
        item_id = _item_id(visible_index)
        label = _safe_label(item.name)
        req_file = item / "requirements.txt"
        if not req_file.exists():
            print_color(Colors.YELLOW, t("skip").format(label))
            items.append(OperationItem(item_id, label, "skipped", 0, "requirements_missing"))
            continue

        print_color(Colors.CYAN, f"{t('found_req')}{label}")
        success = False
        last_log = ""
        attempts = 0
        timed_out = False
        for attempt in range(1, MAX_RETRIES + 1):
            attempts = attempt
            _emit(t("installing").format(attempt, MAX_RETRIES))
            _emit("-" * 20 + f" PIP LOG (Try {attempt}) " + "-" * 20)
            command = build_pip_install_command(target, req_file, timeout=PIP_TIMEOUT)
            try:
                return_code, full_log = run_command_stream(command, cwd=item)
            except subprocess.TimeoutExpired:
                return_code, full_log = -1, "timeout"
                timed_out = True
            last_log = full_log
            if return_code == 0:
                success = True
                break
            print_color(Colors.YELLOW, f"    [Warning] Attempt {attempt} failed. Retrying...")
            if attempt < MAX_RETRIES:
                time.sleep(2)
        _emit("-" * 20 + " END LOG " + "-" * 20)
        if success:
            print_color(Colors.GREEN, t("success").format(label))
            items.append(OperationItem(item_id, label, "succeeded", attempts))
        else:
            print_color(Colors.RED, t("fail").format(label))
            items.append(
                OperationItem(
                    item_id,
                    label,
                    "failed",
                    attempts,
                    _failure_category(last_log, "install_failed"),
                )
            )
            details[item_id] = extract_error_info(last_log)
        _emit("=" * 50 + "\n")

    result = _result_from_items("install", items)
    _render_summary(result, details)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Git clone and dependency installation automation")
    parser.add_argument("--clone", action="store_true", help="clone mode")
    parser.add_argument("--install", action="store_true", help="dependency installation mode")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--target-directory")
    parser.add_argument("--clone-list")
    parser.add_argument("--lang", choices=("EN", "CHT"))
    parser.add_argument("--json", dest="json_output", action="append", metavar="PATH|-" )
    add_target_arguments(parser, required=False)
    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Optional[str]:
    mode_count = int(args.clone) + int(args.install)
    json_values = args.json_output or []
    if len(json_values) > 1:
        parser.error("--json may be specified only once")
    if args.target_directory and not args.non_interactive:
        parser.error("--target-directory requires --non-interactive")
    if args.clone_list and not args.non_interactive:
        parser.error("--clone-list requires --non-interactive")
    if not mode_count:
        if args.non_interactive or args.target_directory or args.clone_list or json_values:
            parser.error("a mode flag is required")
        return None
    if mode_count != 1:
        parser.error("--clone and --install are mutually exclusive")
    if args.clone:
        if any(getattr(args, name) is not None for name in ("python_executable", "venv", "conda_env", "conda_prefix")) or args.use_current_python:
            parser.error("environment selectors are valid only with --install")
        if args.non_interactive:
            if not args.target_directory:
                parser.error("--target-directory is required with --non-interactive")
            if not args.clone_list:
                parser.error("--clone-list is required with non-interactive --clone")
    if args.install:
        if args.clone_list:
            parser.error("--clone-list is valid only with --clone")
        selector_count = int(args.use_current_python) + sum(
            getattr(args, name) is not None for name in ("python_executable", "venv", "conda_env", "conda_prefix")
        )
        if selector_count != 1:
            parser.error("one of the arguments --use-current-python --python-executable --venv --conda-env --conda-prefix is required")
        if args.non_interactive and not args.target_directory:
            parser.error("--target-directory is required with --non-interactive")
    return "clone" if args.clone else "install"


def _validate_clone_list(path: Path) -> None:
    if not path.is_file():
        raise CliUsageError("clone list does not exist")
    try:
        encoded = path.read_bytes()
    except OSError as exc:
        raise CliUsageError("clone list is unreadable") from exc
    raw: Optional[str] = None
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "cp950", "gbk", "latin-1"):
        try:
            raw = encoded.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        raise CliUsageError("clone list is unreadable")
    if any((ord(char) < 32 and char not in "\r\n") or ord(char) == 127 for char in raw):
        raise CliUsageError("clone list contains control characters")
    urls = read_file_safe(path)
    if not urls:
        raise CliUsageError("clone list is empty or unreadable")
    for value in urls:
        if any(char.isspace() for char in value):
            raise CliUsageError("clone list contains a malformed URL")
        if value.startswith("git@") and ":" in value:
            continue
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https", "ssh", "git", "file"} or (
            parsed.scheme != "file" and not parsed.netloc
        ):
            raise CliUsageError("clone list contains a malformed URL")


def _resolve_cli_target(args: argparse.Namespace) -> EnvironmentTarget:
    target_args: list[str] = []
    if args.use_current_python:
        target_args.append("--use-current-python")
    for flag, value in (
        ("--python-executable", args.python_executable),
        ("--venv", args.venv),
        ("--conda-env", args.conda_env),
        ("--conda-prefix", args.conda_prefix),
    ):
        if value is not None:
            target_args.extend((flag, value))
    try:
        return parse_target_arguments(target_args)
    except TargetValidationError as exc:
        raise EnvironmentFailure(str(exc)) from exc


def _json_payload(result: OperationResult) -> str:
    try:
        return json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    except (TypeError, ValueError) as exc:
        raise OutputFailure("result serialization failed") from exc


def _write_json_path(destination: str, payload: str) -> None:
    path = Path(destination).expanduser()
    if path.is_symlink():
        raise OutputFailure("JSON destination must not be a symlink")
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise OutputFailure("JSON destination parent must be an existing directory")
    if path.exists() and not path.is_file():
        raise OutputFailure("JSON destination is not a regular file")
    temporary_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    except (OSError, UnicodeError) as exc:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
        raise OutputFailure("JSON destination could not be replaced") from exc


def _execute_cli(args: argparse.Namespace, mode: str) -> OperationResult:
    global current_lang
    if args.lang:
        current_lang = args.lang
    if mode == "clone":
        if args.non_interactive:
            target_directory = Path(args.target_directory).expanduser()
            if not target_directory.is_dir():
                raise CliUsageError("target directory must already exist")
            list_path = Path(args.clone_list).expanduser()
            _validate_clone_list(list_path)
            return mode_git_clone(
                target_directory=target_directory, list_path=list_path, non_interactive=True
            )
        return mode_git_clone()

    if args.non_interactive:
        target_directory = Path(args.target_directory).expanduser()
        if not target_directory.is_dir():
            raise CliUsageError("target directory must already exist")
        target = _resolve_cli_target(args)
        return mode_install_dependencies(target, target_directory=target_directory, non_interactive=True)
    target = _resolve_cli_target(args)
    return mode_install_dependencies(target)


def main() -> int:
    try:
        set_language_interactive()
        _emit(f"\n{t('menu_header')}")
        _emit(t("menu_1"))
        _emit(t("menu_2"))
        choice = input(t("menu_prompt")).strip()
        if choice == "1":
            return mode_git_clone().exit_code
        if choice == "2":
            return mode_install_dependencies().exit_code
        print_color(Colors.RED, "Invalid mode selection.")
        return EXIT_USAGE
    except EOFError:
        _emit(t("op_cancel"))
        return EXIT_CANCELLED
    except EnvironmentFailure as exc:
        try:
            print_color(Colors.RED, f"Environment target rejected: {_sanitize_text(exc)}")
        except OutputFailure:
            return EXIT_OUTPUT
        return EXIT_ENVIRONMENT
    except OutputFailure:
        return EXIT_OUTPUT
    except OSError as exc:
        try:
            print_color(Colors.RED, f"Operation error: {_sanitize_text(exc)}")
        except OutputFailure:
            return EXIT_OUTPUT
        return EXIT_OPERATION


def cli_entry(argv: Optional[list[str]] = None) -> int:
    global _OUTPUT_FAILURE
    _OUTPUT_FAILURE = False
    parser = _parser()
    args = parser.parse_args(argv)
    mode = _validate_args(parser, args)
    if mode is None:
        return main()
    json_values = args.json_output or []
    json_destination = json_values[0] if json_values else None
    original_stdout = sys.stdout
    def run_with_errors() -> OperationResult:
        global _OUTPUT_FAILURE
        try:
            return _execute_cli(args, mode)
        except CliUsageError as exc:
            print_color(Colors.RED, f"Usage error: {_sanitize_text(exc)}")
            return _terminal_result(mode, "usage_error", EXIT_USAGE)
        except EnvironmentFailure as exc:
            print_color(Colors.RED, f"Environment target rejected: {_sanitize_text(exc)}")
            return _terminal_result(mode, "environment_error", EXIT_ENVIRONMENT)
        except OperationCancelled:
            _emit(t("op_cancel"))
            return _terminal_result(mode, "cancelled", EXIT_CANCELLED)
        except OutputFailure:
            _OUTPUT_FAILURE = True
            return _terminal_result(mode, "output_error", EXIT_OUTPUT)
        except OSError:
            return _terminal_result(mode, "failure", EXIT_OPERATION)

    if json_destination == "-":
        with contextlib.redirect_stdout(sys.stderr):
            result = run_with_errors()
    else:
        result = run_with_errors()

    if _OUTPUT_FAILURE:
        return EXIT_OUTPUT
    if json_destination is not None:
        try:
            payload = _json_payload(result)
            if json_destination == "-":
                original_stdout.write(payload)
                original_stdout.flush()
            else:
                _write_json_path(json_destination, payload)
        except (OutputFailure, BrokenPipeError, OSError):
            try:
                sys.stderr.write("Output error: machine-readable result was not emitted.\n")
                sys.stderr.flush()
            except (BrokenPipeError, OSError):
                pass
            return EXIT_OUTPUT
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(cli_entry())
