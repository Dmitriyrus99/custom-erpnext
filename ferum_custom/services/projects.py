from __future__ import annotations

"""Utilities related to Service Project ownership and participants."""


import frappe


def get_project_manager_email(project: str | None) -> str | None:
    """Return the best-effort email address of the project's manager."""

    if not project:
        return None
    info = frappe.db.get_value(
        "Service Project",
        project,
        ["project_manager", "project_manager.email"],
        as_dict=True,
    )
    if not info:
        return None
    return info.get("project_manager.email") or info.get("project_manager")
