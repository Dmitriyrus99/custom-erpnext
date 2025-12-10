import re

import frappe


def try_allocate_by_doc_ref(payment_name: str):
	"""Auto-allocate входящий Payment по номеру счета в doc_ref."""
	pay = frappe.get_doc("Payment", payment_name)
	if getattr(pay, "direction", None) != "in":
		return

	text = pay.doc_ref or ""
	# Извлекаем номера вида "счёт №123" или "№ 123"
	nums = re.findall(r"(?:сч[её]т[ау]?\s*№?\s*|№\s*)(\d+)", text, re.I)
	if not nums:
		return

	remaining = float(pay.amount or 0)
	for n in nums:
		invoice = frappe.get_all(
			"Invoice",
			filters={"company": pay.company, "invoice_no": n},
			fields=["name", "amount"],
			limit=1,
		)
		if not invoice:
			continue
		inv = invoice[0]

		alloc_sum = frappe.get_all(
			"Payment Allocation",
			filters={"invoice": inv.name},
			fields=["sum(amount) as total"],
			limit=1,
		)
		already_allocated = float(alloc_sum[0].total or 0) if alloc_sum else 0.0
		due_amt = max(float(inv.amount) - already_allocated, 0.0)

		alloc = min(remaining, due_amt)
		if alloc > 0:
			frappe.get_doc(
				{
					"doctype": "Payment Allocation",
					"payment": pay.name,
					"invoice": inv.name,
					"amount": alloc,
				}
			).insert(ignore_permissions=True)
			remaining -= alloc

		if remaining <= 0:
			break
