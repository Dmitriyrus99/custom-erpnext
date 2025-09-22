"""Pytest configuration for the repository tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root (which contains the lightweight ``frappe`` test
# double) is on ``sys.path`` even when pytest is executed via the shim entry
# point that lives outside of the project directory.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

