"""Top-level package entrypoint that exposes the internal Ferum Custom module."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Extend __path__ by walking down nested `ferum_custom` directories so imports like
# `ferum_custom.ferum_custom...` resolve.
current_dir = Path(__file__).resolve().parent
while True:
	next_dir = current_dir / "ferum_custom"
	if not next_dir.exists():
		break
	__path__.append(str(next_dir))
	current_dir = next_dir

from . import ferum_custom  # noqa: F401

subpkg_name = f"{__name__}.ferum_custom"
if subpkg_name not in sys.modules:
	sys.modules[subpkg_name] = ferum_custom

__all__ = ["ferum_custom"]
