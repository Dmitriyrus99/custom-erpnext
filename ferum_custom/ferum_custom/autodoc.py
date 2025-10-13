from __future__ import annotations

import contextlib
from typing import Any

import frappe
from frappe.utils.pdf import get_pdf


def _render_template(template_body: str, ctx: dict[str, Any]) -> str:
    return frappe.render_template(template_body, ctx)


def _ctx_for_project(project_name: str) -> dict[str, Any]:
    proj = frappe.get_doc("Project", project_name)
    customer = None
    with contextlib.suppress(Exception):
        if getattr(proj, "customer", None):
            customer = frappe.get_doc("Customer", proj.customer)
    # Optional: try primary address
    address = None
    try:
        address = frappe.get_all(
            "Address",
            filters={"is_primary_address": 1},
            fields=["*"],
            limit=1,
        )
        address = address[0] if address else None
    except Exception:
        address = None
    return {"doc": proj, "customer": customer, "address": address}


def _ctx_for_task(task_name: str) -> dict[str, Any]:
    task = frappe.get_doc("Task", task_name)
    project = None
    customer = None
    with contextlib.suppress(Exception):
        if getattr(task, "project", None):
            project = frappe.get_doc("Project", task.project)
            if getattr(project, "customer", None):
                customer = frappe.get_doc("Customer", project.customer)
    return {"doc": task, "project": project, "customer": customer}


def generate_from_template(template_name: str, attach_to_doctype: str, attach_to_name: str) -> str:
    """Render template to PDF/HTML and create a File attached to given doc.

    Returns File.name
    """
    tpl = frappe.get_doc("Document Template", template_name)
    if attach_to_doctype not in {"Project", "Task", "Timesheet", "Custom"}:
        frappe.throw("Unsupported target doctype for generation")

    ctx = (
        _ctx_for_project(attach_to_name)
        if attach_to_doctype == "Project"
        else _ctx_for_task(attach_to_name) if attach_to_doctype == "Task" else {"doc": frappe.get_doc(attach_to_doctype, attach_to_name)}
    )

    html = _render_template(tpl.template_body, ctx)
    content: bytes
    file_name = frappe.render_template(tpl.file_name_pattern or "{{ doc.name }}.pdf" if tpl.output == "PDF" else "{{ doc.name }}.html", ctx)
    if tpl.output == "PDF":
        content = get_pdf(html)
    else:
        content = html.encode("utf-8")

    file_doc = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": attach_to_doctype,
            "attached_to_name": attach_to_name,
            "is_private": 0,
            "content": content,
        }
    )
    file_doc.insert(ignore_permissions=True)
    return file_doc.name


def _active_templates(target: str, when: str) -> list[str]:
    try:
        return frappe.get_all(
            "Document Template",
            filters={"active": 1, "target": target, "when": when},
            pluck="name",
        )
    except Exception:
        return []


def on_project_created(doc, method: str | None = None) -> None:
    for name in _active_templates("Project", "on_project_create"):
        with contextlib.suppress(Exception):
            generate_from_template(name, "Project", doc.name)


def on_task_update(doc, method: str | None = None) -> None:
    try:
        changed = bool(getattr(doc, "has_value_changed") and doc.has_value_changed("status"))
    except Exception:
        changed = False
    if not changed or getattr(doc, "status", None) != "Completed":
        return
    for name in _active_templates("Task", "on_task_completed"):
        with contextlib.suppress(Exception):
            generate_from_template(name, "Task", doc.name)

