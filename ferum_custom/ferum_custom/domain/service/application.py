"""High-level application services for service-domain flows."""

from __future__ import annotations

import typing as t

import frappe
from frappe import _


def create_service_request(
    *,
    title: str,
    description: str | None = None,
    service_object: str | None = None,
    company: str | None = None,
    project: str | None = None,
    customer: str | None = None,
    priority: str | None = None,
    request_type: str | None = None,
) -> str:
    """Create a Service Request (Issue proxy) with company isolation."""

    issue = frappe.new_doc("Service Request")
    issue.title = title
    issue.description = description
    issue.service_object = service_object
    issue.company = company
    issue.project = project
    issue.customer = customer
    issue.priority = priority
    issue.type = request_type
    issue.insert(ignore_permissions=False)
    return issue.name


def confirm_service_request(name: str) -> None:
    doc = frappe.get_doc("Service Request", name)
    doc.add_comment("Comment", _("Client confirmed completion via portal (domain)"))


def confirm_service_report(name: str) -> None:
    doc = frappe.get_doc("Service Report", name)
    doc.add_comment("Comment", _("Client confirmed Service Report via portal (domain)"))


def fetch_service_request(name: str) -> dict:
    doc = frappe.get_doc("Service Request", name)
    data = doc.as_dict()
    data.setdefault("title", data.get("subject"))
    safe_fields = {
        "name": data.get("name"),
        "title": data.get("title"),
        "status": data.get("status"),
        "description": data.get("description"),
        "linked_report": data.get("linked_report"),
        "priority": data.get("priority"),
        "customer": data.get("customer"),
    }
    return safe_fields


def list_service_requests(
    *,
    filters: dict[str, t.Any],
    start: int = 0,
    page_length: int = 20,
) -> list[dict[str, t.Any]]:
    return frappe.get_list(
        "Service Request",
        filters=filters,
        fields=[
            "name",
            "title",
            "status",
            "priority",
            "customer",
            "project",
            "modified",
        ],
        start=start,
        page_length=page_length,
        order_by="modified desc",
    )
