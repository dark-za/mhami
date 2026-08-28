"""Cyclomatic complexity guard.

Runs ``radon cc`` against the platform's ``apps/`` tree and exits with
a non-zero status if any function has a grade worse than the configured
threshold. The default threshold is ``C`` (the minimum acceptable).
The script accepts ``--min-grade`` to relax or tighten the bar:

* ``A`` (1-5)  — strict, almost always a refactoring signal
* ``B`` (6-10) — pragmatic for business logic
* ``C`` (11-20) — warning zone
* ``D`` (21-30) — refactor required
* ``F`` (31+)  — untestable

Usage::

    python scripts/check_complexity.py
    python scripts/check_complexity.py --min-grade B
    python scripts/check_complexity.py --report
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APPS = REPO / "backend" / "apps"

# Radon grade → inclusive upper bound on complexity value.
GRADE_THRESHOLDS = {
    "A": 5,
    "B": 10,
    "C": 20,
    "D": 30,
    "F": 10**9,
}

# Map a grade letter to the worst acceptable grade. Used as a string
# comparison fallback when radon formats output without the value.
GRADE_ORDER = ["A", "B", "C", "D", "F"]

# ``radon cc`` formats a function's grade as ``<kind> <line>:<col> <name>
# - <grade> (<complexity>)``. We match the last column to extract the
# grade letter and the complexity score.
LINE_RE = re.compile(r"-\s*([A-F])\s*\((\d+)\)")


def _run_radon(apps_dir: Path) -> str:
    completed = subprocess.run(
        ["python", "-m", "radon", "cc", str(apps_dir), "-s", "-a"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout


def _parse(output: str) -> list[tuple[str, str, int, int]]:
    """Return ``(file, name, line, complexity)`` for every function/method."""
    parsed: list[tuple[str, str, int, int]] = []
    current_file: str | None = None
    for raw_line in output.splitlines():
        stripped = raw_line.rstrip()
        if not stripped:
            continue
        # Filenames appear as their own indented header line ending in a
        # recognised extension. We treat any line whose stripped form is
        # just a path with that extension as a file header.
        if (
            stripped
            and not stripped.startswith(" ")
            and (
                stripped.endswith(".py")
                or stripped.endswith(".ts")
                or stripped.endswith(".tsx")
            )
        ):
            current_file = stripped.strip()
            continue
        match = LINE_RE.search(stripped)
        if not match or current_file is None:
            continue
        complexity = int(match.group(2))
        # The first character on the line (after indentation) is the
        # radon kind: M (method), F (function), C (class).
        first_word = stripped.lstrip().split(None, 1)[0]
        if first_word not in {"M", "F", "C"}:
            continue
        # Name segment format: ``<kind> <line>:<col> <name> - <grade> (<cc>)``
        name_segment = stripped[: match.start()].strip()
        parts = name_segment.split(None, 2)
        if len(parts) < 3:
            continue
        line_no = int(parts[1].split(":")[0])
        name = parts[2]
        parsed.append((current_file, name, line_no, complexity))
    return parsed


def _grade_for(complexity: int) -> str:
    """Return the radon letter grade for a complexity value."""
    for letter in ("A", "B", "C", "D"):
        if complexity <= GRADE_THRESHOLDS[letter]:
            return letter
    return "F"


def main() -> int:
    parser = argparse.ArgumentParser(description="Cyclomatic complexity guard")
    parser.add_argument(
        "--min-grade",
        choices=GRADE_ORDER,
        default="C",
        help="Worst acceptable grade (default C)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print the full report without failing",
    )
    args = parser.parse_args()

    output = _run_radon(APPS)
    if not output:
        print("radon produced no output — is it installed?")
        return 1

    parsed = _parse(output)
    if not parsed:
        print("No functions found — radon output may have changed format.")
        return 1

    threshold_value = GRADE_THRESHOLDS[args.min_grade]
    offenders: list[tuple[str, str, int, int]] = []
    distribution: Counter[str] = Counter()
    for file_path, name, line_no, complexity in parsed:
        grade_letter = _grade_for(complexity)
        distribution[grade_letter] += 1
        if complexity >= threshold_value:
            offenders.append((file_path, name, line_no, complexity))

    print(f"Total functions analysed: {len(parsed)}")
    for grade in GRADE_ORDER:
        count = distribution.get(grade, 0)
        print(f"  Grade {grade}: {count}")
    print()

    if args.report:
        for file_path, name, line_no, complexity in sorted(
            offenders, key=lambda x: x[3], reverse=True
        ):
            print(f"  {complexity:>3}  {file_path}:{line_no}  {name}")
        return 0

    if offenders:
        print(f"{len(offenders)} function(s) at or above grade {args.min_grade}:")
        for file_path, name, line_no, complexity in sorted(
            offenders, key=lambda x: x[3], reverse=True
        ):
            print(f"  {complexity:>3}  {file_path}:{line_no}  {name}")
        return 1

    print(f"OK: all functions below grade {args.min_grade}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
