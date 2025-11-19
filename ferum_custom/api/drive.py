from __future__ import annotations

import frappe

from ferum_custom.ferum_custom.integrations import drive


@frappe.whitelist(allow_guest=True)
def health() -> dict[str, object]:
	"""Expose Google Drive healthcheck for monitoring/CI."""

	return drive.healthcheck()
