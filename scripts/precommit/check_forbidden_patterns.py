#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


PRINT_RE = re.compile(r"\bprint\(\s*[^)]+\)")
SQL_RE = re.compile(r"frappe\.db\.sql\(")


def allow_path(path: Path) -> bool:
    s = str(path)
    return any(
        seg in s
        for seg in (
            "/patches/",
            "/tests/",
            "/scripts/",
            "/migrations/",
        )
    )


def sql_is_unsafe(line: str) -> bool:
    # Heuristic: if call has only one argument (no comma inside parentheses) -- unsafe
    try:
        open_idx = line.index("frappe.db.sql(") + len("frappe.db.sql(")
        close_idx = line.index(")", open_idx)
        inside = line[open_idx:close_idx]
        return "," not in inside
    except ValueError:
        return False


def main(argv: list[str]) -> int:
    failed = []
    files = [Path(p) for p in argv if p.endswith(".py")]
    for f in files:
        if not f.exists():
            continue
        allow = allow_path(f)
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(txt.splitlines(), start=1):
            if PRINT_RE.search(line) and not allow:
                failed.append((f, i, "print() is forbidden"))
            if SQL_RE.search(line) and not allow and sql_is_unsafe(line):
                failed.append((f, i, "Unsafe frappe.db.sql() without parameters"))
    if failed:
        for f, i, msg in failed:
            print(f"{f}:{i}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
