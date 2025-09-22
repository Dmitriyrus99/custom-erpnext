import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf

from ferum_custom.ferum_custom.integrations.drive import upload_bytes


class ServiceReport(Document):
	def before_insert(self):
		if not self.report_date:
			self.report_date = frappe.utils.today()

	def validate(self):
		self.calculate_total_amount()
		self.validate_attachments()
		self.validate_workflow_transitions()
		self.validate_work_items()

	def on_submit(self):
		self.update_service_request_on_submit()
		self.enqueue_drive_upload()

	def on_update(self):
		# Audit: log status changes
		try:
			if self.has_value_changed("status"):
				self.add_comment(
					"Info",
					_("Status changed to {status}").format(status=self.status or "-"),
				)
		except Exception:
			pass

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
		"""Validate allowed status transitions.

		The Service Report workflow currently does not require any side
		effects when moving between statuses.  This method simply
		ensures that the transition from ``old_status`` to ``self.status``
		is permitted by the workflow definition.
		"""
		old_status = frappe.db.get_value("Service Report", self.name, "status") if not self.is_new() else None

		allowed_transitions = {
			("Draft", "Submitted"),
			("Submitted", "Approved"),
			("Approved", "Archived"),
		}

		if self.status == "Cancelled":
			if old_status != "Submitted":
				frappe.throw(_("Service Report can only be Cancelled from Submitted status."))
			return

		if not old_status or old_status == self.status:
			return

		if (old_status, self.status) not in allowed_transitions:
			frappe.throw(_(f"Invalid status transition from {old_status} to {self.status}."))

	def update_service_request_on_submit(self):
		if self.service_request:
			frappe.db.set_value(
				"Service Request",
				self.service_request,
				{"linked_report": self.name, "status": "Completed"},
			)
			frappe.msgprint(_(f"Service Request {self.service_request} updated and marked as Completed."))

	def validate_work_items(self):
		if not self.work_items:
			frappe.throw(_("At least one Work Item is required before submitting a Service Report."))

	def enqueue_drive_upload(self):
		"""Generate PDF and upload to Google Drive in structured folders.

		Folders: /Customer/Project/Reports, filename: ServiceReport-{name}.pdf
		"""
		try:
			frappe.enqueue(
				"ferum_custom.ferum_custom.doctype.service_report.service_report._upload_report_pdf",
				queue="short",
				docname=self.name,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Enqueue Drive Upload failed")


def _upload_report_pdf(docname: str) -> None:
	doc = frappe.get_doc("Service Report", docname)
	# Build path parts
	customer = None
	project = None
	if doc.service_request:
		customer = frappe.db.get_value("Service Request", doc.service_request, "customer")
		project = frappe.db.get_value("Service Request", doc.service_request, "project")
	parts = [p for p in [customer or "Customer", project or "Project", "Reports"] if p]
	# Render PDF
	html = frappe.get_print("Service Report", docname)
	pdf = get_pdf(html)
	filename = f"ServiceReport-{docname}.pdf"
	upload_bytes(parts, filename, pdf, mime_type="application/pdf")


def get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return None
	# Join via Service Request or Project
	conds = []
	if "Project Manager" in frappe.get_roles(user):
		conds.append(
			"exists(select 1 from `tabService Request` sr join `tabService Project` sp on sp.name=sr.project where sr.name=`tabService Report`.service_request and sp.project_manager=%(user)s)"
		)
	if "Service Engineer" in frappe.get_roles(user):
		conds.append(
			"exists(select 1 from `tabService Request` sr where sr.name=`tabService Report`.service_request and sr.assigned_to=%(user)s)"
		)
	if not conds:
		return None
	return "(" + ") or (".join(conds) + ")"


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return True
	pm = None
	assigned = None
	if doc.service_request:
		pm = frappe.db.sql(
			"select sp.project_manager from `tabService Request` sr left join `tabService Project` sp on sp.name=sr.project where sr.name=%s",
			(doc.service_request,),
		)
		assigned = frappe.db.get_value("Service Request", doc.service_request, "assigned_to")
	if assigned == user:
		return True
	if pm and pm[0][0] == user:
		return True
	return False
