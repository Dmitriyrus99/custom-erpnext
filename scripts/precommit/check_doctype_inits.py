#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    base = Path("apps/ferum_custom/ferum_custom/ferum_custom/doctype")
    if not base.exists():
        return 0
    missing: list[str] = []
    for child in base.iterdir():
        if child.is_dir():
            init_py = child / "__init__.py"
            if not init_py.exists():
                missing.append(str(init_py))
    if missing:
        print("Missing __init__.py in doctype packages:")
        for p in missing:
            print(" -", p)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
