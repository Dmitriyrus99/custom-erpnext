"""High-level application services for service-domain flows."""

from __future__ import annotations

import typing as t

import frappe
from frappe import _


def create_issue(
	*,
	title: str,
	description: str | None = None,
	asset: str | None = None,
	company: str | None = None,
	project: str | None = None,
	customer: str | None = None,
	priority: str | None = None,
	request_type: str | None = None,
) -> str:
	"""Create a Service Request (via standard Issue) with company isolation."""

	issue = frappe.new_doc("Issue")
	issue.subject = title
	issue.description = description
	issue.asset = asset
	issue.company = company
	issue.project = project
	issue.customer = customer
	issue.priority = priority
	issue.issue_type = request_type
	issue.insert(ignore_permissions=False)
	return issue.name


def confirm_issue_completion(name: str) -> None:
	doc = frappe.get_doc("Issue", name)
	doc.add_comment("Comment", _("Client confirmed completion via portal (domain)"))


def confirm_timesheet_report(name: str) -> None:
	doc = frappe.get_doc("Timesheet", name)
	doc.add_comment("Comment", _("Client confirmed Timesheet Report via portal (domain)"))


def fetch_issue(name: str) -> dict:
	doc = frappe.get_doc("Issue", name)
	data = doc.as_dict()
	# Map 'subject' to 'title' for API compatibility
	data["title"] = data.get("subject")

	safe_fields = {
		"name": data.get("name"),
		"title": data.get("title"),
		"status": data.get("status"),
		"description": data.get("description"),
		# 'linked_report' is likely custom or not in standard Issue yet, handle gracefully if missing
		"priority": data.get("priority"),
		"customer": data.get("customer"),
		"asset": data.get("asset"),
	}
	return safe_fields


def list_issues(
	*,
	filters: dict[str, t.Any],
	start: int = 0,
	page_length: int = 20,
) -> list[dict[str, t.Any]]:
	# Query standard Issue, but alias subject -> title for compatibility
	return frappe.get_list(
		"Issue",
		filters=filters,
		fields=[
			"name",
			"subject as title",
			"status",
			"priority",
			"customer",
			"project",
			"asset",
			"modified",
		],
		start=start,
		page_length=page_length,
		order_by="modified desc",
	)
