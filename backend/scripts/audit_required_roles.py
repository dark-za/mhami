"""Static audit for ``required_roles`` on every ``TenantAPIView`` subclass.

This script is the single source of truth for BE-01 ("Audit required_roles on
every view"). It walks every ``views.py`` under ``backend/apps`` and reports
any class that inherits from ``TenantAPIView`` but does not declare a
``required_roles`` tuple. CI invokes the script in non-zero-exit mode so the
build fails if a new view lands without an explicit role contract.

Usage::

    python backend/scripts/audit_required_roles.py          # warn only
    python backend/scripts/audit_required_roles.py --strict # exit 1 on miss
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from typing import Iterable


SKIP_DIRS = {"tests", "migrations", "__pycache__"}


def iter_view_files(root: str) -> Iterable[str]:
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            if filename == "views.py":
                yield os.path.join(current, filename)


def inherits_tenant_api_view(node: ast.ClassDef) -> bool:
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "TenantAPIView":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "TenantAPIView":
            return True
    return False


def declares_required_roles(node: ast.ClassDef) -> bool:
    for stmt in node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == "required_roles":
                return True
    return False


def audit(root: str) -> list[str]:
    findings: list[str] = []
    for path in iter_view_files(root):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except SyntaxError as exc:  # pragma: no cover - defensive
            findings.append(f"{path}: SyntaxError: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and inherits_tenant_api_view(node):
                if not declares_required_roles(node):
                    findings.append(f"{path}:{node.lineno} {node.name}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apps-root",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps"),
        help="Root directory containing the Django apps (default: ../apps).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any view is missing required_roles.",
    )
    args = parser.parse_args(argv)

    apps_root = os.path.abspath(args.apps_root)
    findings = audit(apps_root)
    if findings:
        for finding in findings:
            print(f"❌ missing required_roles: {finding}")
        print(f"\nTotal views without required_roles: {len(findings)}")
    else:
        print("✅ Every TenantAPIView subclass declares required_roles.")
    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
