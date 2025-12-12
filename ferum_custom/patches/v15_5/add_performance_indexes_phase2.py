import frappe


def execute():
	"""
	Add performance indexes for high-volume doctypes.
	Targets:
	- Service Request: company/status, service_object, assigned_to, sla_deadline
	- Service Report: service_request, company/report_date
	- Invoice: company/service_project, sales_invoice
	- Payment Allocation: invoice, payment
	- Service Maintenance Schedule Item: service_object
	"""

	indexes = [
		("Service Request", ["company", "status"], "idx_sr_company_status"),
		("Service Request", ["service_object"], "idx_sr_object"),
		("Service Request", ["assigned_to"], "idx_sr_assigned"),
		("Service Request", ["sla_deadline"], "idx_sr_sla_deadline"),
		("Service Report", ["service_request"], "idx_srp_request"),
		("Service Report", ["company", "report_date"], "idx_srp_company_date"),
		("Invoice", ["company", "service_project"], "idx_inv_company_project"),
		("Invoice", ["sales_invoice"], "idx_inv_sales_invoice"),
		("Payment Allocation", ["invoice"], "idx_payalloc_invoice"),
		("Payment Allocation", ["payment"], "idx_payalloc_payment"),
		("Service Maintenance Schedule Item", ["service_object"], "idx_smsi_object"),
	]

	for doctype, fields, name in indexes:
		try:
			frappe.db.add_index(doctype, fields, index_name=name)
		except Exception:
			# ignore if table/fields missing in this site
			frappe.log_error(frappe.get_traceback(), f"Add index failed: {doctype} {name}")
