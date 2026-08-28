"""File-size guard for the platform's source tree.

The refinement plan caps production source files at 500 lines. Test
files and Django migrations are exempt because they grow
proportionally to the schema and feature surface they cover.

The script exits with a non-zero status when at least one file exceeds
``MAX_LINES``. Use ``--max-lines`` to override the cap for ad-hoc
runs, or ``--report`` to print the sorted top offenders without
failing.

Usage::

    python scripts/check_file_sizes.py
    python scripts/check_file_sizes.py --max-lines 300
    python scripts/check_file_sizes.py --report
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND_APPS = REPO / "backend" / "apps"
FRONTEND_SRC = REPO / "frontend" / "src"
DEFAULT_MAX_LINES = 500

EXEMPT_DIR_NAMES = ("migrations", "tests", "vendored", "node_modules", "dist")
EXEMPT_FILE_NAMES = ("generated-types.ts",)


def _line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))


def _is_exempt(path: Path) -> bool:
    if any(part in EXEMPT_DIR_NAMES for part in path.parts):
        return True
    if path.name in EXEMPT_FILE_NAMES:
        return True
    return False


def _gather_backend(max_lines: int) -> list[tuple[int, Path]]:
    offenders: list[tuple[int, Path]] = []
    for py_file in BACKEND_APPS.rglob("*.py"):
        if _is_exempt(py_file):
            continue
        n = _line_count(py_file)
        if n > max_lines:
            offenders.append((n, py_file))
    return offenders


def _gather_frontend(max_lines: int) -> list[tuple[int, Path]]:
    offenders: list[tuple[int, Path]] = []
    for ext in ("*.ts", "*.tsx"):
        for ts_file in FRONTEND_SRC.rglob(ext):
            if _is_exempt(ts_file):
                continue
            n = _line_count(ts_file)
            if n > max_lines:
                offenders.append((n, ts_file))
    return offenders


def main() -> int:
    parser = argparse.ArgumentParser(description="Check file sizes against a cap")
    parser.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=f"Maximum lines per file (default {DEFAULT_MAX_LINES})",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print the top offenders sorted by size, do not fail",
    )
    args = parser.parse_args()

    backend_offenders = _gather_backend(args.max_lines)
    frontend_offenders = _gather_frontend(args.max_lines)
    all_offenders = sorted(
        backend_offenders + frontend_offenders, key=lambda x: x[0], reverse=True
    )

    if not all_offenders:
        print(f"OK: all files under {args.max_lines} lines")
        return 0

    if args.report:
        for n, path in all_offenders:
            rel = path.relative_to(REPO)
            print(f"  {n:>4}  {rel}")
        return 0

    print(f"\n{len(all_offenders)} file(s) exceed {args.max_lines} lines:")
    for n, path in all_offenders:
        rel = path.relative_to(REPO)
        print(f"  {n:>4}  {rel}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
