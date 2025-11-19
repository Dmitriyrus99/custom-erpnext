import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf

from ferum_custom.ferum_custom.integrations.file_sync import sync_file_by_name
from ferum_custom.ferum_custom.settings import is_feature_enabled
from ferum_custom.ferum_custom.utils import get_allowed_customers, user_roles


class ServiceReport(Document):
	def before_insert(self):
		if not self.report_date:
			self.report_date = frappe.utils.today()

	def validate(self):
		self.ensure_company_from_request()
		self.calculate_total_amount()
		self.validate_attachments()
		self._sync_document_links_to_attachments()
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
		"""Validate presence and types of required attachments.

		Business rule:
		- At least one attachment must be present.
		- Must include at least one photo (image/*).
		- Must include an act/report (PDF), treated as the mandatory "акт".
		"""
		if not self.documents:
			frappe.throw(_("At least one attachment is required."))

		from mimetypes import guess_type

		has_photo = False
		has_act_pdf = False
		missing = []
		for item in self.documents:
			if not item.custom_attachment:
				missing.append(item.name)
				continue
			try:
				att = frappe.get_doc("Custom Attachment", item.custom_attachment)
				mime = (att.file_type or "").lower().strip()
				if not mime:
					# derive from filename or URL
					name_or_url = att.file_name or att.file_url or ""
					m2, enc = guess_type(name_or_url)
					mime = (m2 or "").lower()
				if mime.startswith("image/"):
					has_photo = True
				# consider any PDF as an acceptable Act/Report
				if mime == "application/pdf" or (att.file_name or "").lower().endswith(".pdf"):
					has_act_pdf = True
			except Exception:
				# if attachment can't be loaded, treat as missing
				missing.append(item.custom_attachment)

		if missing:
			frappe.throw(
				_("Attachment is required for all Document Items. Missing: {0}").format(", ".join(missing))
			)
		if not has_photo:
			frappe.throw(_("At least one photo (image) attachment is required."))
		if not has_act_pdf:
			frappe.throw(_("An Act (PDF) attachment is required."))

	def _sync_document_links_to_attachments(self) -> None:
		"""Ensure CustomAttachment records referenced in documents table are linked to this Service Report.

		This guarantees Google Drive synchronization places files under the Service Report context.
		Idempotent: only updates records where link differs or is missing.
		"""
		for item in self.documents or []:
			if not getattr(item, "custom_attachment", None):
				continue
			try:
				att = frappe.get_doc("Custom Attachment", item.custom_attachment)
				if att.linked_doctype != "Service Report" or att.linked_docname != self.name:
					att.db_set(
						{
							"linked_doctype": "Service Report",
							"linked_docname": self.name,
						},
						commit=False,
					)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(), f"Failed to sync attachment link for {item.custom_attachment}"
				)

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
			try:
				# Add an audit comment on the Service Request
				req = frappe.get_doc("Service Request", self.service_request)
				req.add_comment("Info", _("Linked Service Report {0}").format(self.name))
			except Exception:
				pass

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
		if not is_feature_enabled("enable_google_drive_sync"):
			return
		try:
			frappe.enqueue(
				"ferum_custom.ferum_custom.doctype.service_report.service_report._upload_report_pdf",
				queue="short",
				docname=self.name,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Enqueue Drive Upload failed")


def _upload_report_pdf(docname: str) -> None:
	# Render PDF
	html = frappe.get_print("Service Report", docname)
	pdf = get_pdf(html)
	filename = f"ServiceReport-{docname}.pdf"

	# Attach PDF as ERP File (on_update hook will handle Drive sync via FileSyncService)
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

		# Force immediate sync to avoid race (optional; idempotent)
		sync_file_by_name(file_doc.name)

		# Reload to fetch drive ids if available
		try:
			file_doc = frappe.get_doc("File", file_doc.name)
			file_drive_id = getattr(file_doc, "drive_file_id", None)
			file_web = getattr(file_doc, "drive_web_link", None)
		except Exception:
			file_drive_id = None
			file_web = None

		# Register as Custom Attachment for unified handling and references
		att_data = {
			"doctype": "Custom Attachment",
			"file_name": filename,
			"file_url": file_doc.file_url,
			"file_type": "application/pdf",
			"linked_doctype": "Service Report",
			"linked_docname": docname,
		}
		if file_drive_id:
			att_data["drive_file_id"] = file_drive_id
		if file_web:
			att_data["drive_web_link"] = file_web
		att = frappe.get_doc(att_data)
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

	service_department = getattr(doc, "service_department", None)
	service_request_info: dict[str, object] | None = None
	if doc.service_request:
		info = frappe.db.sql(
			"""
			select sr.assigned_to, sr.project, sr.service_department, sr.customer,
				sp.project_manager
			from `tabService Request` sr
			left join `tabService Project` sp on sp.name=sr.project
			where sr.name=%s
			""",
			(doc.service_request,),
			as_dict=True,
		)
		if info:
			service_request_info = info[0]
			service_department = service_department or service_request_info.get("service_department")

	if "Department Head" in roles:
		allowed = set(
			frappe.get_all(
				"User Permission", filters={"user": user, "allow": "Service Department"}, pluck="for_value"
			)
		)
		if allowed:
			dept = service_department or (service_request_info or {}).get("service_department")
			if dept in allowed:
				return True
		else:
			return True

	assigned = (service_request_info or {}).get("assigned_to")
	project_manager = (service_request_info or {}).get("project_manager")
	customer = (service_request_info or {}).get("customer")

	if assigned == user:
		return True
	if project_manager == user:
		return True
	if "Client" in roles and getattr(doc, "service_request", None):
		customers = set(get_allowed_customers(user))
		if customers and customer in customers:
			return True
	return False


def _notify_clients(customer: str, subject: str, message: str) -> None:
	try:
		users = frappe.get_all(
			"User Permission", filters={"allow": "Customer", "for_value": customer}, pluck="user"
		)
		if not users:
			return
		emails = [
			u.email
			for u in frappe.get_all("User", filters={"name": ["in", users]}, fields=["email"])
			if u.email
		]
		if emails:
			frappe.sendmail(recipients=emails, subject=subject, message=message)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Notify clients failed (report)")
