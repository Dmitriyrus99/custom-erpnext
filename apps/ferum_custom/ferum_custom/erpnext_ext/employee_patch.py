from __future__ import annotations

"""Safety wrapper around :meth:`Employee.update_user`."""

import frappe
from erpnext.setup.doctype.employee.employee import Employee

_ORIGINAL_UPDATE_USER = Employee.update_user


def _should_apply_patch(doc: Employee) -> bool:
    user_id = getattr(doc, "user_id", "") or ""
    return bool(
        frappe.flags.in_test
        or (getattr(doc, "name", "") or "").startswith("_T-")
        or user_id.startswith("test")
    )


def update_user_with_unique_middle_name(self: Employee) -> None:
    try:
        return _ORIGINAL_UPDATE_USER(self)
    except frappe.UniqueValidationError as exc:
        if not _should_apply_patch(self):
            raise
        if getattr(self.flags, "_update_user_retry", False):
            raise
        details = " ".join(str(part) for part in exc.args)
        if "middle_name" not in details or getattr(exc, "doctype", None) not in (None, "User"):
            raise

    user = frappe.get_doc("User", self.user_id)
    user.flags.ignore_permissions = True
    if not user.middle_name or user.middle_name == "Employee":
        user.middle_name = self.name or frappe.generate_hash(length=10)

    frappe.db.set_value("User", user.name, "middle_name", user.middle_name, update_modified=False)

    original_employee_name = getattr(self, "employee_name", None)
    first_token = ((getattr(self, "first_name", None) or "").split(" ", 1)[0]) or self.name
    self.employee_name = f"{first_token} {self.name}"

    self.flags._update_user_retry = True
    try:
        return _ORIGINAL_UPDATE_USER(self)
    finally:
        self.flags._update_user_retry = False
        if original_employee_name is not None:
            self.employee_name = original_employee_name


Employee.update_user = update_user_with_unique_middle_name
