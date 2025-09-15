import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_to_date, getdate, nowdate

from ferum_custom.ferum_custom.utils import get_users_by_roles


def _get_pm_email(project: str) -> str | None:
	pm_info = frappe.db.get_value(
		"Service Project",
		project,
		["project_manager", "project_manager.email"],
		as_dict=True,
	)
	if not pm_info:
		return None
	return pm_info.get("project_manager.email") or pm_info.get("project_manager")


class ServiceRequest(Document):
	def after_insert(self) -> None:
		"""Notify the project manager about the new request.

		Using server-side logic ensures that only the manager of the
		linked project receives the email instead of broadcasting to all
		users with the Project Manager role.
		"""
		self.notify_project_manager()

	def validate(self):
		self.set_customer_and_project()
		self.validate_workflow_transitions()
		self.calculate_sla_deadline()

	def on_update(self):
		self.check_sla_breach()
		self.update_timestamps()
		# Audit: log status changes
		try:
			if self.has_value_changed("status"):
				self.add_comment(
					"Info",
					_("Status changed to {status}").format(status=self.status or "-"),
				)
		except Exception:
			pass

	def set_customer_and_project(self):
		if self.is_new() or self.has_value_changed("service_object"):
			if self.service_object:
				service_object_doc = frappe.get_doc("Service Object", self.service_object)
				self.customer = service_object_doc.customer
				self.project = service_object_doc.project
			else:
				self.customer = None
				self.project = None

	def validate_workflow_transitions(self):
		old_status = (
			frappe.db.get_value("Service Request", self.name, "status") if not self.is_new() else None
		)

		if old_status == "Open" and self.status == "In Progress" and not self.assigned_to:
			frappe.throw(_("Cannot set status to 'In Progress' without assigning an engineer."))
		elif old_status == "In Progress" and self.status == "Completed" and not self.linked_report:
			frappe.throw(_("Cannot set status to 'Completed' without linking a Service Report."))
		elif (
			old_status == "Completed"
			and self.status == "Closed"
			and "System Manager" not in frappe.get_roles()
		):
			frappe.throw(_("Only a Manager can close a Service Request."))

	def calculate_sla_deadline(self):
		if self.type == "Emergency" and self.priority == "High":
			self.sla_deadline = add_to_date(self.creation, hours=4)
		elif self.type == "Emergency" and self.priority == "Medium":
			self.sla_deadline = add_to_date(self.creation, hours=8)
		elif self.type == "Routine Maintenance" and self.priority == "High":
			self.sla_deadline = add_days(self.creation, 1)
		else:
			self.sla_deadline = add_days(self.creation, 3)

	def check_sla_breach(self):
		if (
			self.status not in ["Completed", "Closed"]
			and self.sla_deadline
			and getdate(nowdate()) > getdate(self.sla_deadline)
		):
			message = f"SLA for Service Request {self.name} has been breached! Title: {self.title}. Priority: {self.priority}. Due: {self.sla_deadline}"
			frappe.msgprint(_(message))
			frappe.log_error(message, "SLA Breach Alert")
			frappe.enqueue(
				"ferum_custom.ferum_custom.doctype.service_request.service_request.send_sla_breach_notifications",
				service_request_name=self.name,
				message=message,
			)

	def update_timestamps(self):
		updated = False
		if self.status == "In Progress" and not self.actual_start_datetime:
			self.db_set("actual_start_datetime", frappe.utils.now(), commit=False)
			updated = True
		elif self.status == "Completed" and not self.actual_end_datetime:
			self.db_set("actual_end_datetime", frappe.utils.now(), commit=False)
			updated = True
		return updated

	def notify_project_manager(self) -> None:
		"""Send an email to the project manager for the linked project."""
		if not self.project:
			return

		try:
			email = _get_pm_email(self.project)
			if not email:
				return
			frappe.sendmail(
				recipients=[email],
				subject=_("New Service Request {0}").format(self.name),
				message=_("A new service request {0} was created for your project.").format(self.name),
			)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				"Service Request notification failed",
			)


@frappe.whitelist()
def check_all_slas():
	open_requests = frappe.get_all("Service Request", filters={"status": ["not in", ["Completed", "Closed"]]})
	for req in open_requests:
		doc = frappe.get_doc("Service Request", req.name)
		doc.check_sla_breach()


def send_sla_breach_notifications(service_request_name: str, message: str) -> None:
	"""Notify responsible users about an SLA breach.

	This helper is triggered via :pyfunc:`check_sla_breach` either during a
	document update or from the hourly scheduler job (see ``check_all_slas``).
	The previous implementation only logged a warning which meant that no one
	was actually alerted about the overdue service request. Here we collect a
	set of recipients (project manager and all office managers) and dispatch an
	email.

	Args:
	    service_request_name: Name of the :doctype:`Service Request`.
	    message: Human-readable breach message.
	"""

	try:
		sr = frappe.get_doc("Service Request", service_request_name)
		recipients: set[str] = set()

		if sr.project:
			pm_email = _get_pm_email(sr.project)
			if pm_email:
				recipients.add(pm_email)

			recipients.update(get_users_by_roles(["Office Manager"]))

		if recipients:
			frappe.sendmail(
				recipients=list(recipients),
				subject=_("SLA breached for Service Request {0}").format(service_request_name),
				message=message,
			)
		else:
			# Fallback to logging if no recipients resolved
			frappe.logger().warning(
				f"No recipients found for SLA breach notification on {service_request_name}"
			)

	except Exception:
		frappe.log_error(frappe.get_traceback(), "Failed to send SLA breach notification")


def get_permission_query_conditions(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return None
	conds = []
	roles = set(frappe.get_roles(user))
	if "Project Manager" in roles:
		conds.append(
			"exists(select 1 from `tabService Project` sp where sp.name = `tabService Request`.project and sp.project_manager=%(user)s)"
		)
	if "Service Engineer" in roles:
		conds.append("`tabService Request`.assigned_to=%(user)s")
	if "Client" in roles:
		conds.append("`tabService Request`.owner=%(user)s")
	if not conds:
		return None
	return "(" + ") or (".join(conds) + ")"


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if "System Manager" in frappe.get_roles(user):
		return True
	if doc.assigned_to == user:
		return True
	if doc.project and frappe.db.get_value("Service Project", doc.project, "project_manager") == user:
		return True
	if doc.owner == user:
		return True
	return False
