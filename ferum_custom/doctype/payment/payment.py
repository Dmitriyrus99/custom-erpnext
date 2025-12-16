import frappe
from frappe import _
from frappe.model.document import Document

from ferum_custom.ferum_custom.domain.finance import standard_finance_enabled
from ferum_custom.ferum_custom.domain.finance.payments import ensure_payment_entry_from_custom


class Payment(Document):
	def validate(self):
		# Align company from Sales Invoice if linked
		if getattr(self, "sales_invoice", None) and not getattr(self, "company", None):
			self.company = frappe.db.get_value("Sales Invoice", self.sales_invoice, "company")

		# Prefer Customer field; derive from Counterparty if needed
		if not getattr(self, "customer", None) and getattr(self, "counterparty", None):
			customer = frappe.db.get_value("Counterparty", self.counterparty, "customer")
			if customer:
				self.customer = customer

		if self.direction == "in" and not getattr(self, "customer", None):
			frappe.throw(_("Customer is required for incoming payments"))


@frappe.whitelist()
def create_payment_entry_from_payment(payment_name: str) -> str:
	"""Create ERPNext Payment Entry from custom Payment + Payment Allocation.

	- direction 'in' -> Receive (Customer)
	- direction 'out' -> Pay (Supplier) — currently unsupported, will throw
	- allocations map to Sales Invoice if present; otherwise skipped
	"""

	if standard_finance_enabled():
		pe = ensure_payment_entry_from_custom(payment_name)
		if pe:
			return pe

	# fallback: original custom Payment Entry logic
	pay = frappe.get_doc("Payment", payment_name)

	if pay.direction not in ("in", "out"):
		frappe.throw(_("Payment {0}: direction must be 'in' or 'out'").format(payment_name))

	if pay.direction == "out":
		frappe.throw(_("Payment {0}: supplier payouts not supported in automation yet").format(payment_name))

	customer = pay.customer
	if not customer and pay.counterparty:
		customer = frappe.db.get_value("Counterparty", pay.counterparty, "customer")
	if not customer:
		frappe.throw(_("Payment {0}: customer is required to create Payment Entry").format(payment_name))

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.company = pay.company
	pe.party_type = "Customer"
	pe.party = customer
	pe.posting_date = pay.trx_date
	pe.paid_amount = pay.amount
	pe.received_amount = pay.amount

	# Map allocations to Sales Invoice where possible
	allocations = frappe.get_all(
		"Payment Allocation",
		filters={"payment": pay.name},
		fields=["invoice", "amount"],
	)
	for alloc in allocations:
		si = None
		if alloc.invoice:
			si = frappe.db.get_value("Invoice", alloc.invoice, "sales_invoice")
		if not si and getattr(pay, "sales_invoice", None):
			si = pay.sales_invoice
		if si:
			row = pe.append("references", {})
			row.reference_doctype = "Sales Invoice"
			row.reference_name = si
			row.total_amount = frappe.db.get_value("Sales Invoice", si, "grand_total") or 0
			row.allocated_amount = alloc.amount or pay.amount

	# Optional link back to SR
	if getattr(pay, "service_request", None):
		pe.references = pe.references or []
		pe.custom_service_request = pay.service_request

	pe.insert(ignore_permissions=True, ignore_mandatory=True)
	pe.submit()
	pay.db_set("doc_ref", f"Payment Entry {pe.name}", update_modified=False)
	return pe.name
