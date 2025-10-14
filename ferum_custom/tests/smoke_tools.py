from __future__ import annotations

import json
from typing import Any

import frappe


def create_test_service_request() -> str:
	"""Create a minimal test Service Request using first available Company.

	Returns the docname.
	"""
	companies = frappe.get_all("Company", pluck="name")
	if not companies:
		raise RuntimeError("No Company found; create a Company first")
	doc = frappe.get_doc(
		{
			"doctype": "Service Request",
			"company": companies[0],
			"title": "Smoke Test Request",
			"status": "Open",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def assign_request(name: str, user: str = "Administrator") -> None:
	doc = frappe.get_doc("Service Request", name)
	doc.assigned_to = user
	doc.save(ignore_permissions=True)


def update_request_status_via_api(name: str, status: str) -> dict[str, Any]:
	from ferum_custom.ferum_custom.api.service import update_service_request_status

	return update_service_request_status(name=name, status=status)


def get_telegram_secret() -> str:
	from ferum_custom.ferum_custom.settings import get_setting

	return (get_setting("telegram_webhook_secret") or "").strip()


def call_webhook_with_secret(secret: str) -> dict[str, Any]:
	from ferum_custom.ferum_custom.api.telegram_bot import handle_update

	# minimal update payload that should be rejected by allowlist but processed
	update = {
		"message": {
			"text": "/ping",
			"from": {"username": "smoke_user"},
			"chat": {"id": "0"},
		}
	}
	return handle_update(secret=secret, update=json.dumps(update))
