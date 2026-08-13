"""Scan declared test/tool paths for common secret and private-config patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


IGNORED_DIR_NAMES = frozenset({".git", ".tmp", ".venv", ".venv-wsl", "__pycache__"})


PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|private[_-]?key)\b\s*[:=]\s*['\"](?!\[REDACTED_SECRET\]|CHANGE_ME|EXAMPLE)[^'\"]+['\"]"
        ),
    ),
    (
        "authenticated-url",
        re.compile(r"(?i)https?://[^\s/@:]+:[^\s/@]+@"),
    ),
    (
        "private-index",
        re.compile(r"(?i)\b(?:extra-)?index-url\s*[=:]\s*(?:https?://|[^#\s]+@)"),
    ),
    (
        "environment-dump",
        re.compile(r"(?i)\b(?:print|pprint|json\.dump)\s*\([^\n]*(?:environ|os\.environ)"),
    ),
)


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_file():
            if not any(part in IGNORED_DIR_NAMES for part in path.parts):
                files.append(path)
        elif path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file()
                and not any(part in IGNORED_DIR_NAMES for part in item.relative_to(path).parts)
            )
        else:
            raise FileNotFoundError(path)
    return sorted(set(files), key=lambda item: item.as_posix().casefold())


def scan(paths: list[str]) -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    for path in iter_files(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for category, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append((path, line_number, category))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="+", required=True)
    args = parser.parse_args(argv)
    try:
        findings = scan(args.paths)
    except (FileNotFoundError, OSError) as exc:
        print(f"ERROR: privacy scan path failure: {exc}", file=sys.stderr)
        return 2
    for path, line_number, category in findings:
        print(f"{path}:{line_number}:{category}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
