from __future__ import annotations

import importlib
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
	__version__ = version("ferum_custom")
except PackageNotFoundError:
	__version__ = "0.0.0"

try:
	from .api import reports as _report_overrides
except ModuleNotFoundError as exc:
	# `flit` imports this module while building metadata in an isolated env where
	# Frappe isn't installed, so gracefully skip optional integrations there.
	if exc.name != "frappe":
		raise
	_report_overrides = None

# Extend __path__ through nested ferum_custom directories so deep imports resolve.
current_dir = Path(__file__).resolve().parent
while True:
	next_dir = current_dir / "ferum_custom"
	if not next_dir.exists():
		break
	__path__.append(str(next_dir))
	current_dir = next_dir

subpkg_name = f"{__name__}.ferum_custom"
if subpkg_name not in sys.modules:
	sys.modules[subpkg_name] = importlib.import_module(__name__)

__all__ = ["__version__"]
