from __future__ import annotations

"""Utilities for the nested ``ferum_custom.ferum_custom`` package.

Historically some modules imported APIs via ``ferum_custom.ferum_custom`` even
though most public modules (``api``, ``hooks`` and friends) live directly next to
this package inside the app root.  Earlier we tried to support those imports by
manipulating ``__path__`` which confused :mod:`pkgutil.walk_packages` and caused
it to recurse indefinitely during the test runner setup.

To keep backward compatibility without mutating ``__path__`` we register a small
set of alias modules in :mod:`sys.modules`.  This allows dotted imports such as
``ferum_custom.ferum_custom.api`` to resolve to the real package
``ferum_custom.api`` while keeping the package tree acyclic.
"""

from importlib import import_module
import sys
from types import ModuleType
from typing import Dict

_LEGACY_ALIASES: Dict[str, str] = {
        "api": "ferum_custom.api",
}

for alias, target in _LEGACY_ALIASES.items():
        try:
                module: ModuleType = import_module(target)
        except Exception:
                # Import failures should not prevent the app from loading; simply
                # skip the alias if the target cannot be imported (for example
                # during partial installs or optional dependencies).
                continue
        sys.modules.setdefault(f"{__name__}.{alias}", module)
        globals()[alias] = module

__all__ = ["_LEGACY_ALIASES"]
