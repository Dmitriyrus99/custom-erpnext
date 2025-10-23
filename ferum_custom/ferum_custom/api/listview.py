from __future__ import annotations

import frappe


@frappe.whitelist()
def get_projects_for_pm(user: str | None = None, doctype: str = "Project") -> list[str]:
    """Return a list of project names where the given user is the Project Manager.

    Args:
        user: User name (defaults to session user).
        doctype: Either "Project" (standard) or "Service Project" (custom).

    Returns:
        List of project names.
    """
    user = user or frappe.session.user
    if not user:
        return []

    if doctype not in ("Project", "Service Project"):
        return []

    try:
        return [
            d.name
            for d in frappe.get_all(
                doctype, filters={"project_manager": user}, pluck="name"
            )
        ]
    except Exception:
        return []

