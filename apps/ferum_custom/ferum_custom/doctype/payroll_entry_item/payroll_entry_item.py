import frappe
from frappe import _
from frappe.model.document import Document


class PayrollEntryItem(Document):
    def validate(self):
        self.net_salary = self.base_salary - self.advance
        if self.net_salary < 0:
            frappe.throw(_("Net Salary cannot be negative. Advance amount exceeds Base Salary."))
