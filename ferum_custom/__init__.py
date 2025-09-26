from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
	__version__ = version("ferum_custom")
except PackageNotFoundError:
	__version__ = "0.0.0"

from ferum_custom.api import reports as _report_overrides

__all__ = ["__version__"]
