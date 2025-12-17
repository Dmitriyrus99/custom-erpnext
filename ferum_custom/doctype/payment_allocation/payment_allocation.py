import frappe
from frappe.model.document import Document


class PaymentAllocation(Document):
    def validate(self):
        # Derive company/customer from Payment for consistency
        try:
            payment_company = frappe.db.get_value("Payment", self.payment, "company")
            if payment_company:
                self.db_set("company", payment_company, commit=False)
        except Exception:
            pass
