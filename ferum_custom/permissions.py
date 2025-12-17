import frappe


def company_guard(user):
    if frappe.session.user == "Administrator":
        return ""

    companies = frappe.get_all(
        "User Permission",
        filters={
            "user": frappe.session.user,
            "allow": "Company",
        },
        pluck="for_value",
    )

    if not companies:
        return "1=0"  # Deny access if no company permissions are found

    # Ensure companies are properly quoted for SQL
    escaped_companies = [frappe.db.escape(c) for c in companies]

    return f"`tab{{doctype}}`.company in ({', '.join(escaped_companies)})"


def has_company_permission(doc, user: str | None = None) -> bool:
    """Return True if `user` is permitted to access `doc` by Company."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True

    company = getattr(doc, "company", None)
    if not company:
        return True

    try:
        companies = frappe.get_all(
            "User Permission",
            filters={"user": user, "allow": "Company"},
            pluck="for_value",
        )
    except Exception:
        companies = []
    return bool(companies and company in companies)


def has_department_permission(doc, user: str | None = None) -> bool:
    """Return True if `user` has explicit permission for doc's department-like field."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True

    department = getattr(doc, "department", None) or getattr(doc, "service_department", None)
    if not department:
        return False

    for allow in ("Department", "Service Department"):
        try:
            if frappe.db.exists(
                "User Permission", {"user": user, "allow": allow, "for_value": department}
            ):
                return True
        except Exception:
            continue
    return False


def has_project_manager_permission(doc, user: str | None = None) -> bool:
    """Return True if `user` is the project manager for the linked Service Project."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True

    project = getattr(doc, "project", None)
    if not project:
        return False
    try:
        pm = frappe.db.get_value("Service Project", project, "project_manager")
        return pm == user
    except Exception:
        return False


def has_service_engineer_permission(doc, user: str | None = None) -> bool:
    """Return True if `user` is the assigned engineer or default engineer for the linked object."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True

    if getattr(doc, "assigned_to", None) == user or getattr(doc, "assigned_engineer", None) == user:
        return True

    service_object = getattr(doc, "service_object", None)
    if service_object:
        try:
            eng = frappe.db.get_value("Service Object", service_object, "default_engineer")
            return eng == user
        except Exception:
            return False

    return False


def has_client_permission(doc, user: str | None = None) -> bool:
    """Return True if client `user` is allowed for doc.customer via User Permission."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True

    if getattr(doc, "owner", None) == user:
        return True

    customer = getattr(doc, "customer", None)
    if not customer:
        return False
    try:
        return bool(
            frappe.db.exists(
                "User Permission", {"user": user, "allow": "Customer", "for_value": customer}
            )
        )
    except Exception:
        return False
