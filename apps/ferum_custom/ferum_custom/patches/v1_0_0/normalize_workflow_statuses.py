import frappe


def _normalize_single(doctype: str, allowed: list[str], fallback: str):
    # Trim whitespace and fix case where possible
    # Update rows where status not in allowed
    placeholders = ", ".join(["%s"] * len(allowed))
    invalid = frappe.db.sql(
        f"""
        select name, status, docstatus from `tab{doctype}`
        where coalesce(status, '') not in ({placeholders})
        """,
        allowed,
        as_dict=True,
    )
    for row in invalid:
        frappe.db.set_value(doctype, row.name, "status", fallback, update_modified=False)


def _normalize_submittable_by_docstatus(doctype: str, mapping: dict[int, str], allowed: list[str]):
    # For submittable doctypes, map invalid statuses based on docstatus
    placeholders = ", ".join(["%s"] * len(allowed))
    rows = frappe.db.sql(
        f"""
        select name, status, docstatus from `tab{doctype}`
        where coalesce(status, '') not in ({placeholders})
        """,
        allowed,
        as_dict=True,
    )
    for row in rows:
        fallback = mapping.get(int(row.docstatus), allowed[0])
        frappe.db.set_value(doctype, row.name, "status", fallback, update_modified=False)


def execute():
    # Service Project: replace legacy/invalid statuses (e.g., 'Draft') with 'Planned'
    _normalize_single(
        doctype="Service Project",
        allowed=["Planned", "Active", "Completed", "Cancelled"],
        fallback="Planned",
    )

    # Service Request: fallback to 'Open'
    _normalize_single(
        doctype="Service Request",
        allowed=["Open", "In Progress", "Completed", "Closed", "Cancelled"],
        fallback="Open",
    )

    # Service Report (submittable): map by docstatus
    _normalize_submittable_by_docstatus(
        doctype="Service Report",
        mapping={0: "Draft", 1: "Submitted", 2: "Cancelled"},
        allowed=["Draft", "Submitted", "Approved", "Archived", "Cancelled"],
    )

    # Invoice (submittable): map by docstatus
    _normalize_submittable_by_docstatus(
        doctype="Invoice",
        mapping={0: "Draft", 1: "Paid", 2: "Cancelled"},
        allowed=["Draft", "Sent", "Paid", "Cancelled"],
    )
