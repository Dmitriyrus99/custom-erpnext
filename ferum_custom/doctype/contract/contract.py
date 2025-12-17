import re

import frappe
from frappe.model.document import Document


def _normalize(contract_no: str) -> str:
    """Stable normalization to keep unique index (company, contract_no_normalized) filled."""
    contract_no = contract_no or ""
    contract_no = contract_no.strip()
    contract_no = re.sub(r"[ \u00A0]+", "", contract_no)  # collapse spaces
    contract_no = contract_no.replace("—", "-").replace("–", "-")  # unify dashes
    contract_no = contract_no.replace("\\", "/")  # unify slashes
    return contract_no.lower()


class Contract(Document):
    def validate(self):
        # Prefer ERP Customer; derive from Counterparty if provided
        if not getattr(self, "customer_ref", None) and getattr(self, "customer", None):
            cust = frappe.db.get_value("Counterparty", self.customer, "customer")
            if cust:
                self.customer_ref = cust

        if not getattr(self, "company", None) and getattr(self, "project", None):
            self.company = frappe.db.get_value("Project", self.project, "company")

        # Maintain normalized number and basic date sanity
        self.contract_no_normalized = _normalize(self.contract_no)
        if self.date_start and self.date_end and self.date_start > self.date_end:
            frappe.throw("date_start must be <= date_end")
