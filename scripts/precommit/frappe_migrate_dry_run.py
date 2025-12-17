#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    # Best-effort dry-run: this is staged as `manual` hook; run only in CI if needed.
    try:
        cmd = ["bench", "--site", "all", "migrate", "--dry-run"]
        res = subprocess.run(cmd, check=False, capture_output=True, text=True)
        # Do not fail local dev if bench not available
        if res.returncode != 0 and "bench" in (res.stderr or ""):
            return 0
        return 0 if res.returncode == 0 else 1
    except FileNotFoundError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
