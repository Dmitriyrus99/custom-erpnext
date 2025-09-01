import frappe
from frappe import _
from frappe.model.document import Document


class ServiceReport(Document):
	def validate(self):
		self.calculate_total_amount()
		self.validate_attachments()
		self.validate_workflow_transitions()
		self.validate_work_items()

	def on_submit(self):
		self.update_service_request_on_submit()

	def calculate_total_amount(self):
		self.total_amount = 0
		for item in self.work_items:
			item.total = item.hours * item.rate
			self.total_amount += item.total

	def validate_attachments(self):
		for item in self.documents:
			if not item.custom_attachment:
				frappe.throw(_("Attachment is required for all Document Items."))

	def validate_workflow_transitions(self):
		old_status = frappe.db.get_value("ServiceReport", self.name, "status") if not self.is_new() else None

		if old_status == "Draft" and self.status == "Submitted":
			# Draft to Submitted is allowed
			pass
		elif old_status == "Submitted" and self.status == "Approved":
			# Submitted to Approved is allowed (e.g., by Dept Head)
			pass
		elif old_status == "Approved" and self.status == "Archived":
			# Approved to Archived is allowed
			pass
		elif old_status == "Submitted" and self.status == "Draft":
			# Submitted to Draft (Amend) is allowed
			pass
		elif self.status == "Cancelled":
			# Cancelled is allowed from Draft or Submitted
			if old_status not in ["Draft", "Submitted"]:
				frappe.throw(_("Service Report can only be Cancelled from Draft or Submitted status."))
		elif old_status and old_status != self.status:  # Prevent invalid transitions
			frappe.throw(_(f"Invalid status transition from {old_status} to {self.status}."))

	def update_service_request_on_submit(self):
		if self.service_request:
			frappe.db.set_value(
				"ServiceRequest", self.service_request, {"linked_report": self.name, "status": "Completed"}
			)
			frappe.msgprint(_(f"Service Request {self.service_request} updated and marked as Completed."))

	def validate_work_items(self):
		if not self.work_items:
			frappe.throw(_("At least one Work Item is required before submitting a Service Report."))
