from __future__ import annotations

"""Lightweight app metrics helpers (no external deps).

Stores counters in frappe.cache() and exposes them via the API endpoint
`ferum_custom.api.metrics.prometheus`.
"""

from typing import Dict, Iterable, Iterator, Tuple

import frappe


_REGISTRY_KEY = "ferum:metrics:registry"
_PREFIX = "ferum:metrics:counters:"


def _labels_key(labels: Dict[str, str] | None) -> str:
    if not labels:
        return ""
    parts = [f"{k}={labels[k]}" for k in sorted(labels.keys())]
    return "|".join(parts)


def inc(name: str, labels: Dict[str, str] | None = None, amount: int = 1) -> None:
    """Increment a named counter with optional labelset.

    Keys are stored as: ``ferum:metrics:counters:<name>|k1=v1|k2=v2``.
    A simple registry list is maintained at ``ferum:metrics:registry``.
    """
    try:
        cache = frappe.cache()
        lbl = _labels_key(labels)
        key = _PREFIX + name + ("|" + lbl if lbl else "")
        current = cache.get_value(key) or 0
        try:
            current_val = int(current) if current is not None else 0
        except Exception:
            current_val = 0
        cache.set_value(key, current_val + max(1, int(amount)))
        # Maintain registry
        reg = cache.get_value(_REGISTRY_KEY) or []
        if not isinstance(reg, list):
            reg = []
        if key not in reg:
            reg.append(key)
            cache.set_value(_REGISTRY_KEY, reg)
    except Exception:
        # Never break business logic due to metrics
        pass


def iter_counters() -> Iterator[Tuple[str, Dict[str, str], int]]:
    """Yield (name, labels, value) for all recorded counters."""
    try:
        cache = frappe.cache()
        reg = cache.get_value(_REGISTRY_KEY) or []
        if not isinstance(reg, list):
            return iter(())
        result: list[Tuple[str, Dict[str, str], int]] = []
        for key in reg:
            if not isinstance(key, str) or not key.startswith(_PREFIX):
                continue
            rest = key[len(_PREFIX) :]
            if "|" in rest:
                name, lbls = rest.split("|", 1)
                labels: Dict[str, str] = {}
                for chunk in lbls.split("|"):
                    if "=" in chunk:
                        k, v = chunk.split("=", 1)
                        labels[k] = v
            else:
                name, labels = rest, {}
            val = cache.get_value(key) or 0
            try:
                val_int = int(val) if val is not None else 0
            except Exception:
                val_int = 0
            result.append((name, labels, val_int))
        return iter(result)
    except Exception:
        return iter(())

