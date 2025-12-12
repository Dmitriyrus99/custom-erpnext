import frappe


def execute():
	"""Map Contract.customer_ref from Counterparty.customer when available."""
	for ctr in frappe.get_all(
		"Contract",
		fields=["name", "customer", "customer_ref"],
	):
		if ctr.customer_ref:
			continue
		if not ctr.customer:
			continue
		cust = frappe.db.get_value("Counterparty", ctr.customer, "customer")
		if cust:
			frappe.db.set_value("Contract", ctr.name, "customer_ref", cust, update_modified=False)
