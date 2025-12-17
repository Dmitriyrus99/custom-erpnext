from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from types import ModuleType

try:
    __version__ = version("ferum_custom")
except PackageNotFoundError:
    __version__ = "0.0.0"

_report_overrides: ModuleType | None
try:
    from .api import reports as _report_overrides_mod
except ModuleNotFoundError as exc:
    # `flit` imports this module while building metadata in an isolated env where
    # Frappe isn't installed, so gracefully skip optional integrations there.
    if exc.name != "frappe":
        raise
    _report_overrides = None
else:
    _report_overrides = _report_overrides_mod

# Backward compatibility: historical imports expect `ferum_custom.ferum_custom.*`.
_self = sys.modules[__name__]
_self.ferum_custom = _self
sys.modules.setdefault(f"{__name__}.ferum_custom", _self)

__all__ = ["__version__"]
