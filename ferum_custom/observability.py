from __future__ import annotations

"""Observability hooks: Sentry init and other runtime instrumentation."""

from typing import Any

import frappe

from ferum_custom.ferum_custom.settings import get_setting

_sentry_initialized = False


def _init_sentry_sdk() -> None:
	global _sentry_initialized
	if _sentry_initialized:
		return
	dsn = get_setting("sentry_dsn")
	if not dsn:
		return
	try:
		import sentry_sdk  # type: ignore[import-untyped]

		traces = get_setting("sentry_traces_sample_rate")
		try:
			traces_sample_rate = float(traces) if traces is not None else 0.0
		except Exception:
			traces_sample_rate = 0.0
		sentry_sdk.init(dsn=dsn, traces_sample_rate=traces_sample_rate or 0.0)
		_sentry_initialized = True
	except Exception:
		# Avoid breaking requests due to sentry setup
		pass


def before_request() -> None:
	"""Hooked from hooks.py: initialize Sentry lazily per worker."""
	_init_sentry_sdk()
