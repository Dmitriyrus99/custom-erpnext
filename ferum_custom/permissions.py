
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
