from __future__ import annotations

# Compatibility shim: ensure `ferum_custom.ferum_custom.*` resolves to the
# standard app package at `apps/ferum_custom/ferum_custom` even if this nested
# package is on sys.path first in Bench environments.
import os
import sys

_this_dir = os.path.dirname(__file__)
_parent_pkg_dir = os.path.dirname(_this_dir)

# Ensure subpackages are discoverable from the parent app directory
try:
	__path__  # type: ignore[name-defined]
except Exception:
	__path__ = [_this_dir]  # type: ignore[assignment]

if _parent_pkg_dir not in __path__:  # type: ignore[operator]
	# let python look for subpackages (e.g., `doctype`) in the parent app dir
	__path__.append(_parent_pkg_dir)  # type: ignore[attr-defined]
