"""
Finance migration helpers.

Goal: phase out custom Invoice/Payment Allocation in favour of ERPNext
Sales Invoice / Payment Entry. This module centralises feature flag
checks and mapping helpers so we can gradually switch without breaking
callers.
"""

from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.settings import is_feature_enabled


def standard_finance_enabled() -> bool:
	"""
	Feature flag: enable use of standard Sales Invoice/Payment Entry as primary.

	Controlled by setting/environment ``enable_standard_finance``.
	"""

	return is_feature_enabled("enable_standard_finance")


def prefer_sales_invoice() -> bool:
	"""Alias for readability."""

	return standard_finance_enabled()
