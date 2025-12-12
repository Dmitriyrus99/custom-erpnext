import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_to_date, getdate, nowdate

try:
	from ferum_custom.ferum_custom.integrations.telegram import send_message as tg_send
except Exception:
	# During migrate/import, telegram module may not be importable; use no-op
	def tg_send(*args, **kwargs):  # type: ignore
		return False


from ferum_custom.notifications.dispatcher import notify as notify_dispatch
from ferum_custom.ferum_custom.services import get_project_manager_email
from ferum_custom.ferum_custom.utils import (
	get_allowed_customers,
	get_users_by_roles,
	user_roles,
)


class ServiceRequest(Document):
	def before_insert(self) -> None:
		if not self.status:
			self.status = "Open"
		# Auto-assign engineer if not set
		try:
			if not getattr(self, "assigned_to", None):
				# prefer Service Object default, then Project default
				if getattr(self, "service_object", None):
					eng = frappe.db.get_value("Service Object", self.service_object, "default_engineer")
					if eng:
						self.assigned_to = eng
				if not getattr(self, "assigned_to", None) and getattr(self, "project", None):
					eng = frappe.db.get_value("Service Project", self.project, "default_engineer")
					if eng:
						self.assigned_to = eng
		except Exception:
			pass

	def after_insert(self) -> None:
		"""Notify stakeholders about the new request (PM, Office Managers, assigned engineer)."""
		self.notify_on_create()

	def validate(self):
		self.set_customer_and_project()
		self.calculate_sla_deadline()

	def on_update(self):
		self.update_timestamps()
		# Audit: log status changes
		try:
			if self.has_value_changed("status"):
				old_status = frappe.db.get_value("Service Request", self.name, "status") or "-"
				self.add_comment(
					"Info",
					_("Status changed to {status}").format(status=self.status or "-"),
				)
				from ferum_custom.ferum_custom.services.audit import log_event

				log_event(
					event_type="status_change",
					ref_doctype="Service Request",
					ref_docname=self.name,
					message=f"Status: {old_status} -> {self.status}",
					details={
						"old_status": old_status,
						"new_status": self.status,
						"linked_report": getattr(self, "linked_report", None),
					},
				)
				# Notify clients on close
				if self.status == "Closed" and getattr(self, "customer", None):
					_notify_clients(
						self.customer,
						_("Service Request {0} closed").format(self.name),
						_("Your service request {0} has been closed.").format(self.name),
					)
		except Exception:
			pass

	def set_customer_and_project(self):
		"""Cache derived fields from Service Object / Service Project to reduce joins."""
		needs_sync = self.is_new() or self.has_value_changed("service_object") or self.has_value_changed("project")

		if not needs_sync:
			return

		if self.service_object:
			service_object_doc = frappe.get_doc("Service Object", self.service_object)
			self.customer = service_object_doc.customer
			# Respect explicitly provided project if already set; otherwise use object's default
			if not getattr(self, "project", None) and getattr(service_object_doc, "project", None):
				self.project = service_object_doc.project
			# Align company from Service Object or linked Project
			self.company = getattr(service_object_doc, "company", None)
			if not self.company and self.project:
				self.company = frappe.db.get_value("Service Project", self.project, "company")
			# Align department from Project
			if self.project:
				dept, default_eng = frappe.db.get_value(
					"Service Project", self.project, ["service_department", "default_engineer"]
				)
				if dept:
					self.service_department = dept
				if not getattr(self, "assigned_to", None) and default_eng:
					self.assigned_to = default_eng
		elif self.project:
			# Derive from project only
			dept, company, customer, default_eng = frappe.db.get_value(
				"Service Project", self.project, ["service_department", "company", "customer", "default_engineer"]
			)
			self.service_department = self.service_department or dept
			self.company = self.company or company
			self.customer = self.customer or customer
			if not getattr(self, "assigned_to", None) and default_eng:
				self.assigned_to = default_eng
		else:
			# No object/project supplied
			self.customer = None
			self.project = None
			# keep company unchanged unless explicitly cleared elsewhere

	def calculate_sla_deadline(self):
		"""Calculate SLA deadline based on matching SLA policies."""
		hours = None
		# 1) explicit selection
		if getattr(self, "sla_policy", None):
			hours = frappe.db.get_value("SLA Policy", self.sla_policy, "duration_hours")
		# 2) fallback: pick by priority/type
		if hours is None and self.priority and getattr(self, "type", None):
			hours = frappe.db.get_value(
				"SLA Policy",
				filters={
					"priority": self.priority,
					"type": self.type,
					"enabled": 1,
				},
				fieldname="duration_hours",
				order_by="creation DESC",
			)
		# normalize to float
		if hours is not None:
			hours = float(hours)

		if hours is not None:
			self.sla_deadline = add_to_date(self.creation, hours=hours)
		else:
			# Default SLA if no policy matches
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
			try:
				from ferum_custom.ferum_custom.services.audit import log_event

				log_event(
					event_type="sla_breach",
					ref_doctype="Service Request",
					ref_docname=self.name,
					message=message,
					details={
						"priority": self.priority,
						"due": str(self.sla_deadline),
						"status": self.status,
					},
				)
			except Exception:
				pass
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
		# update duration if possible
		try:
			from frappe.utils import get_datetime

			if self.reported_datetime and self.actual_end_datetime:
				start = get_datetime(self.reported_datetime)
				end = get_datetime(self.actual_end_datetime)
				delta = (end - start).total_seconds() / 3600.0
				self.db_set("duration_hours", round(delta, 2), commit=False)
		except Exception:
			pass
		return updated

	def notify_on_create(self) -> None:
		"""Send notifications on new request creation to PM, Office Managers and assigned engineer."""
		try:
			recipients: set[str] = set()
			# PM by email
			if getattr(self, "project", None):
				pm_email = get_project_manager_email(self.project)
				if pm_email:
					recipients.add(pm_email)
			# Office Managers by role
			try:
				oms = frappe.get_all("Has Role", filters={"role": "Office Manager"}, pluck="parent")
				recipients.update(oms)
			except Exception:
				pass
			# Assigned engineer (user id)
			if getattr(self, "assigned_to", None):
				recipients.add(self.assigned_to)

			if recipients:
				notify_dispatch(
					"new_service_request",
					recipients=list(recipients),
					context={
						"name": self.name,
						"title": self.title,
						"priority": self.priority,
						"project": self.project,
					},
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Service Request notification failed")


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
			pm_email = get_project_manager_email(sr.project)
			if pm_email:
				recipients.add(pm_email)
		try:
			oms = frappe.get_all("Has Role", filters={"role": "Office Manager"}, pluck="parent")
			recipients.update(oms)
		except Exception:
			pass
		if recipients:
			notify_dispatch(
				"sla_breach",
				recipients=list(recipients),
				context={
					"name": sr.name,
					"title": sr.title,
					"priority": sr.priority,
					"due": str(sr.sla_deadline or ""),
				},
			)
		else:
			frappe.logger().warning(
				f"No recipients found for SLA breach notification on {service_request_name}"
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Failed to send SLA breach notification")


from ferum_custom.ferum_custom.permissions import (
	get_company_conditions,
	get_department_conditions,
	get_project_manager_conditions,
	get_service_engineer_conditions,
	get_client_conditions,
	has_company_permission,
	has_department_permission,
	has_project_manager_permission,
	has_service_engineer_permission,
	has_client_permission,
)


def has_permission(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user

	roles = set(user_roles(user))

	if "System Manager" in roles:
		return True

	if not has_company_permission(doc, user):
		return False

	if "Office Manager" in roles:
		return True

	if "Department Head" in roles:
		if has_department_permission(doc, user):
			return True

	if "Project Manager" in roles:
		if has_project_manager_permission(doc, user):
			return True

	if "Service Engineer" in roles:
		if has_service_engineer_permission(doc, user):
			return True

	if "Client" in roles:
		if has_client_permission(doc, user):
			return True

	return False


def _notify_clients(customer: str, subject: str, message: str) -> None:
	try:
		# Find users with Client role and explicit permission to this Customer
		users = frappe.get_all(
			"User Permission",
			filters={"allow": "Customer", "for_value": customer},
			pluck="user",
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
		frappe.log_error(frappe.get_traceback(), "Notify clients failed")
