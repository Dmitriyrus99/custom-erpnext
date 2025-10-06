import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf

from ferum_custom.ferum_custom.integrations.drive import upload_bytes
from ferum_custom.ferum_custom.utils import get_allowed_customers, user_roles


class ServiceReport(Document):
	def before_insert(self):
		if not self.report_date:
			self.report_date = frappe.utils.today()

	def validate(self):
		self.ensure_company_from_request()
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
				# Notify clients on approval
				if self.status == "Approved" and getattr(self, "service_request", None):
					cust = frappe.db.get_value("Service Request", self.service_request, "customer")
					if cust:
						_notify_clients(
							cust,
							_("Service Report {0} approved").format(self.name),
							_("Your service report {0} was approved and is available.").format(self.name),
						)
		except Exception:
			pass

	def calculate_total_amount(self):
		self.total_amount = 0
		for item in self.work_items:
			item.total = item.hours * item.rate
			self.total_amount += item.total
		# For now, payable equals total; can adjust for discounts/taxes later
		try:
			self.total_payable = self.total_amount
		except Exception:
			pass

	def validate_attachments(self):
		if not self.documents:
			frappe.throw(_("At least one attachment is required."))
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

	def ensure_company_from_request(self):
		try:
			if getattr(self, "service_request", None):
				req_company, req_dept = frappe.db.get_value(
					"Service Request", self.service_request, ["company", "service_department"]
				)
				if req_company:
					self.company = req_company
				if req_dept:
					self.service_department = req_dept
		except Exception:
			pass

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
	# Upload to Google Drive
	upload_bytes(parts, filename, pdf, mime_type="application/pdf")
	# Also attach PDF as ERP File + register as Custom Attachment for consistency
	try:
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": filename,
				"content": pdf,
				"is_private": 0,
				"attached_to_doctype": "Service Report",
				"attached_to_name": docname,
			}
		)
		file_doc.insert(ignore_permissions=True)
		att = frappe.get_doc(
			{
				"doctype": "Custom Attachment",
				"file_name": filename,
				"file_url": file_doc.file_url,
				"file_type": "application/pdf",
				"linked_doctype": "Service Report",
				"linked_docname": docname,
			}
		)
		att.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Attach Service Report PDF failed")


def _user_companies(user: str) -> list[str]:
	try:
		return frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Company"},
			pluck="for_value",
		)
	except Exception:
		return []


def _company_cond_for(user: str, table: str) -> str | None:
	try:
		user_type = frappe.get_cached_value("User", user, "user_type")
		if user_type == "Website User":
			return None
		companies = _user_companies(user)
		if not companies:
			return None
		vals = ", ".join(frappe.db.escape(x) for x in companies)
		return f"`{table}`.company in ({vals})"
	except Exception:
		return None


def get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	roles = set(frappe.get_roles(user))
	if "System Manager" in roles:
		return None
	# Join via Service Request or Project
	conds = []
	base = _company_cond_for(user, "tabService Report")
	if base:
		conds.append(base)
	# Office Manager and Department Head: broad access within companies
	if "Office Manager" in roles:
		return " and ".join(f"({c})" for c in conds) if conds else None
	if "Department Head" in roles:
		depts = frappe.get_all(
			"User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
		)
		if depts:
			vals = ", ".join(frappe.db.escape(x) for x in depts)
			conds.append(f"`tabService Report`.service_department in ({vals})")
			return " and ".join(f"({c})" for c in conds)
		# fallback: broad within company
		return " and ".join(f"({c})" for c in conds) if conds else None
	if "Project Manager" in roles:
		conds.append(
			"exists(select 1 from `tabService Request` sr join `tabService Project` sp on sp.name=sr.project where sr.name=`tabService Report`.service_request and sp.project_manager=%(user)s)"
		)
	if "Service Engineer" in roles:
		conds.append(
			"exists(select 1 from `tabService Request` sr where sr.name=`tabService Report`.service_request and sr.assigned_to=%(user)s)"
		)
	if "Client" in roles:
		customers = get_allowed_customers(user)
		if customers:
			vals = ", ".join(frappe.db.escape(x) for x in customers)
			conds.append(
				"exists(select 1 from `tabService Request` sr where sr.name=`tabService Report`.service_request and sr.customer in ("
				+ vals
				+ "))"
			)
	if not conds:
		return None
	# Combine: company AND (role-based OR)
	if base:
		role_conds = conds[1:]  # after base
		if role_conds:
			return f"({base}) and ((" + ") or (".join(role_conds) + "))"
		return base
	return "(" + ") or (".join(conds) + ")"


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	roles = user_roles(user)
	if "System Manager" in roles or "Office Manager" in roles:
		return True
	if "Department Head" in roles:
		allowed = set(
			frappe.get_all(
				"User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
			)
		)
		if allowed:
			dept = getattr(doc, "service_department", None)
			if not dept and getattr(doc, "service_request", None):
				dept = frappe.db.get_value("Service Request", doc.service_request, "service_department")
			if dept in allowed:
				return True
		else:
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
	if "Client" in roles and getattr(doc, "service_request", None):
		customers = set(get_allowed_customers(user))
		if customers:
			cust = frappe.db.get_value("Service Request", doc.service_request, "customer")
			if cust in customers:
				return True
	return False


def _notify_clients(customer: str, subject: str, message: str) -> None:
	try:
		users = frappe.get_all(
			"User Permission", filters={"allow": "Customer", "for_value": customer}, pluck="user"
		)
		if not users:
			return
		emails = [u.email for u in frappe.get_all("User", filters={"name": ["in", users]}, fields=["email"]) if u.email]
		if emails:
			frappe.sendmail(recipients=emails, subject=subject, message=message)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Notify clients failed (report)")
