
import frappe
from frappe import _

def get_company_conditions(user: str) -> str | None:
    """Returns SQL conditions for company restrictions."""
    allowed_companies = frappe.get_all(
        "User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
    )
    if allowed_companies:
        company_list = ", ".join(frappe.db.escape(c) for c in allowed_companies)
        return f"`tabService Request`.company IN ({company_list})"
    return None

def get_department_conditions(user: str) -> str | None:
    """Returns SQL conditions for service department restrictions."""
    allowed_depts = frappe.get_all(
        "User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
    )
    if allowed_depts:
        dept_list = ", ".join(frappe.db.escape(d) for d in allowed_depts)
        return f"`tabService Request`.service_department IN ({dept_list})"
    return None

def get_project_manager_conditions(user: str) -> str:
    """Returns SQL conditions for Project Managers."""
    return f"`tabService Request`.project IN (SELECT name FROM `tabService Project` WHERE project_manager = {frappe.db.escape(user)})"

def get_service_engineer_conditions(user: str) -> str:
    """Returns SQL conditions for Service Engineers."""
    return f"`tabService Request`.assigned_to = {frappe.db.escape(user)}"

def get_client_conditions(user: str) -> str:
    """Returns SQL conditions for Clients."""
    from ferum_custom.ferum_custom.utils import get_allowed_customers

    allowed_customers = get_allowed_customers(user)
    if allowed_customers:
        customer_list = ", ".join(frappe.db.escape(c) for c in allowed_customers)
        return f"`tabService Request`.customer IN ({customer_list})"
    return f"`tabService Request`.owner = {frappe.db.escape(user)}"

def has_company_permission(doc, user: str) -> bool:
    """Checks if the user has permission for the document's company."""
    allowed_companies = set(frappe.get_all("User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"))
    if allowed_companies and doc.company not in allowed_companies:
        return False
    return True

def has_department_permission(doc, user: str) -> bool:
    """Checks if the user has permission for the document's service department."""
    allowed_depts = set(frappe.get_all("User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"))
    if not allowed_depts or doc.service_department in allowed_depts:
        return True
    return False

def has_project_manager_permission(doc, user: str) -> bool:
    """Checks if the user is the project manager for the document's project."""
    if doc.project and frappe.db.get_value("Service Project", doc.project, "project_manager") == user:
        return True
    return False

def has_service_engineer_permission(doc, user: str) -> bool:
    """Checks if the user is the assigned engineer for the document."""
    if doc.assigned_to == user:
        return True
    return False

def has_client_permission(doc, user: str) -> bool:
    """Checks if the user is the client for the document."""
    from ferum_custom.ferum_custom.utils import get_allowed_customers

    allowed_customers = set(get_allowed_customers(user))
    if allowed_customers and doc.customer in allowed_customers:
        return True
    if doc.owner == user:
        return True
    return False


# --- Project permissions ----------------------------------------------------


def _user_companies(user: str) -> list[str]:
    return frappe.get_all(
        "User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value"
    )


def _user_departments(user: str) -> list[str]:
    return frappe.get_all(
        "User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
    )


def project_get_permission_query_conditions(user: str, doctype: str | None = None) -> str | None:
    if not user or user == "Administrator":
        return None

    clauses: list[str] = []
    companies = _user_companies(user)
    if companies:
        esc = ", ".join(frappe.db.escape(c) for c in companies)
        clauses.append(f"`tabProject`.company IN ({esc})")

    departments = _user_departments(user)
    if departments:
        esc = ", ".join(frappe.db.escape(d) for d in departments)
        clauses.append(
            "`tabProject`.name in (select name from `tabService Project` where service_department in ({0}))".format(
                esc
            )
        )

    return " and ".join(f"({clause})" for clause in clauses) if clauses else None


def project_has_permission(doc, user: str) -> bool:
    if not user or user == "Administrator":
        return True

    companies = set(_user_companies(user))
    if companies and getattr(doc, "company", None) not in companies:
        return False

    departments = set(_user_departments(user))
    if departments:
        department = getattr(doc, "service_department", None)
        if not department:
            department = frappe.db.get_value("Service Project", doc.name, "service_department")
        if department and department not in departments:
            return False

    return True


# --- Timesheet permissions --------------------------------------------------


def timesheet_get_permission_query_conditions(user: str, doctype: str | None = None) -> str | None:
    """Limit Timesheets by Company for non-admin users (if user has explicit Company perms).

    If the user has User Permission entries for Company, restrict Timesheets to those companies.
    Otherwise, return None (no extra filter beyond role permissions).
    """
    if not user or user == "Administrator":
        return None

    companies = _user_companies(user)
    if companies:
        esc = ", ".join(frappe.db.escape(c) for c in companies)
        return f"`tabTimesheet`.company IN ({esc})"
    return None


def timesheet_has_permission(doc, user: str) -> bool:
    if not user or user == "Administrator":
        return True
    companies = set(_user_companies(user))
    if companies and getattr(doc, "company", None) not in companies:
        return False
    return True
