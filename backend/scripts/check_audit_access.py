"""Guard direct AuditEvent creation outside the audit layer.

Read-side tests and migrations may query ``AuditEvent.objects`` directly, but
production code must create audit rows through ``apps.audit.services`` so MCP
agent attribution can correlate rows by request_id.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APPS = REPO / "backend" / "apps"

ALLOWED_CREATE_FILES = {
    Path("audit/services.py"),
}
ALLOWED_DIR_PARTS = {"migrations", "tests"}


def _is_allowed(path: Path) -> bool:
    rel = path.relative_to(APPS)
    if rel in ALLOWED_CREATE_FILES:
        return True
    return any(part in ALLOWED_DIR_PARTS for part in rel.parts)


def _is_auditevent_objects_create(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute) or func.attr != "create":
        return False
    objects_attr = func.value
    if not isinstance(objects_attr, ast.Attribute) or objects_attr.attr != "objects":
        return False
    model_name = objects_attr.value
    return isinstance(model_name, ast.Name) and model_name.id == "AuditEvent"


def main() -> int:
    offenders: list[tuple[Path, int]] = []
    for path in APPS.rglob("*.py"):
        if _is_allowed(path):
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            print(f"Could not parse {path.relative_to(REPO)}: {exc}", file=sys.stderr)
            return 1
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_auditevent_objects_create(node):
                offenders.append((path.relative_to(REPO), node.lineno))

    if not offenders:
        print("OK: AuditEvent creation goes through apps.audit.services")
        return 0

    print("AuditEvent.objects.create is restricted to apps.audit.services:", file=sys.stderr)
    for path, line in offenders:
        print(f"  {path}:{line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
