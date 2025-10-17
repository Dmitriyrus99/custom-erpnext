from __future__ import annotations

"""Site operations helpers for one-off maintenance tasks.

Run with:
  bench --site <site> execute ferum_custom.ferum_custom.site_ops.apply_ru_workspaces
"""

from collections.abc import Iterable

import frappe
from frappe.utils import cint

from ferum_custom.ferum_custom.settings import is_feature_enabled


def _ensure_dashboard_chart(
	name: str,
	*,
	document_type: str,
	chart_type: str = "Group By",
	type_: str = "Pie",
	group_by_type: str = "Count",
	group_by_based_on: str | None = None,
	value_based_on: str | None = None,
	module: str = "Ferum Custom",
	is_public: int = 1,
) -> None:
	if frappe.db.exists("Dashboard Chart", name):
		doc = frappe.get_doc("Dashboard Chart", name)
		changed = False
		if getattr(doc, "document_type", None) != document_type:
			doc.document_type = document_type
			changed = True
		if getattr(doc, "chart_type", None) != chart_type:
			doc.chart_type = chart_type
			changed = True
		if getattr(doc, "type", None) != type_:
			doc.type = type_
			changed = True
		if getattr(doc, "group_by_type", None) != group_by_type:
			doc.group_by_type = group_by_type
			changed = True
		if getattr(doc, "group_by_based_on", None) != group_by_based_on:
			doc.group_by_based_on = group_by_based_on
			changed = True
		if getattr(doc, "value_based_on", None) != value_based_on:
			doc.value_based_on = value_based_on
			changed = True
		if cint(getattr(doc, "is_public", 0)) != cint(is_public):
			doc.is_public = is_public
			changed = True
		if getattr(doc, "module", None) != module:
			doc.module = module
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return

	frappe.get_doc(
		{
			"doctype": "Dashboard Chart",
			"chart_name": name,
			"document_type": document_type,
			"chart_type": chart_type,
			"type": type_,
			"group_by_type": group_by_type,
			"group_by_based_on": group_by_based_on,
			"value_based_on": value_based_on,
			"aggregate_function_based_on": value_based_on,
			"filters_json": "[]",
			"is_public": is_public,
			"module": module,
		}
	).insert(ignore_permissions=True)


def _hide_workspaces(names: Iterable[str]) -> None:
	for name in names:
		if frappe.db.exists("Workspace", name):
			ws = frappe.get_cached_doc("Workspace", name)
			values = {}
			if cint(ws.public) != 0:
				values["public"] = 0
			if cint(getattr(ws, "is_hidden", 0)) != 1:
				values["is_hidden"] = 1
			if values:
				frappe.db.set_value("Workspace", name, values)


def _ensure_shortcut(
	ws, *, label: str, type_: str, url: str | None = None, link_to: str | None = None
) -> None:
	# Find existing by label
	existing = None
	for sc in ws.shortcuts:  # type: ignore[attr-defined]
		if sc.label == label:
			existing = sc
			break
	if existing:
		changed = False
		if existing.type != type_:
			existing.type = type_
			changed = True
		if (existing.url or None) != (url or None):
			existing.url = url
			changed = True
		if (existing.link_to or None) != (link_to or None):
			existing.link_to = link_to
			changed = True
		if changed:
			ws.save(ignore_permissions=True)
		return

	sc = ws.append("shortcuts", {})  # type: ignore[attr-defined]
	sc.label = label
	sc.type = type_
	sc.url = url
	sc.link_to = link_to
	ws.save(ignore_permissions=True)


def apply_ru_workspaces() -> dict:
	"""Apply RU-only alignment to Workspaces and Charts on current site.

	- Hide English workspaces (Chief Accountant, Office Manager, Project Manager, Accounting, Engineer)
	- Create/update RU charts: "Открытые заявки по статусам", "Счета по проектам"
	- Align shortcuts in "Управление проектами"
	- Ensure Department Head has issue oversight reports
	"""

	# Charts (create first to satisfy Workspace link validation)
	_ensure_dashboard_chart(
		"Открытые заявки по статусам",
		document_type="Issue",
		type_="Pie",
		group_by_type="Count",
		group_by_based_on="status",
	)
	_ensure_dashboard_chart(
		"Счета по проектам",
		document_type="Sales Invoice",
		type_="Bar",
		group_by_type="Sum",
		group_by_based_on="project",
		value_based_on="base_grand_total",
	)

	# Hide EN workspaces
	_hide_workspaces(["Chief Accountant", "Office Manager", "Project Manager", "Accounting", "Engineer"])

	# Department Head shortcuts
	if frappe.db.exists("Workspace", "Руководитель отдела"):
		ws = frappe.get_doc("Workspace", "Руководитель отдела")
		_ensure_shortcut(ws, label="Нераспределенные заявки", type_="Report", link_to="Unassigned Issues")
		_ensure_shortcut(
			ws, label="Открытые заявки по инженерам", type_="Report", link_to="Open Issues by Engineer"
		)

	# Project Management alignment
	if frappe.db.exists("Workspace", "Управление проектами"):
		ws = frappe.get_doc("Workspace", "Управление проектами")
		_ensure_shortcut(ws, label="Проекты", type_="DocType", link_to="Project")
		_ensure_shortcut(ws, label="Новый проект", type_="URL", url="/app/project/new")
		_ensure_shortcut(ws, label="Заявки", type_="URL", url="/app/issue")
		_ensure_shortcut(ws, label="Сервисные отчеты", type_="DocType", link_to="Timesheet")
		_ensure_shortcut(ws, label="Объекты", type_="DocType", link_to="Asset")
		_ensure_shortcut(ws, label="Счета", type_="URL", url="/app/sales-invoice")
		_ensure_shortcut(ws, label="Новый счет (клиент)", type_="URL", url="/app/sales-invoice/new")
		_ensure_shortcut(ws, label="Новый счет (субподрядчик)", type_="URL", url="/app/purchase-invoice/new")
		if frappe.db.exists("Report", "Issues by Project"):
			_ensure_shortcut(ws, label="Заявки по проектам", type_="Report", link_to="Issues by Project")

	# Service Operations: use standard Issue reports
	if frappe.db.exists("Workspace", "Сервисные операции"):
		ws = frappe.get_doc("Workspace", "Сервисные операции")
		_ensure_shortcut(ws, label="Нераспределенные заявки", type_="Report", link_to="Unassigned Issues")
		_ensure_shortcut(
			ws, label="Открытые заявки по инженерам", type_="Report", link_to="Open Issues by Engineer"
		)

	# Регламентное обслуживание: графики, объекты, заявки и отчёт просрочки
	try:
		if frappe.db.exists("Workspace", "Регламентное обслуживание"):
			ws = frappe.get_doc("Workspace", "Регламентное обслуживание")
		else:
			ws = frappe.get_doc(
				{
					"doctype": "Workspace",
					"name": "Регламентное обслуживание",
					"label": "Регламентное обслуживание",
					"public": 1,
					"module": "Ferum Custom",
				}
			)
		_ensure_shortcut(
			ws, label="Графики обслуживания", type_="DocType", link_to="Service Maintenance Schedule"
		)
		_ensure_shortcut(ws, label="Новый график", type_="URL", url="/app/service-maintenance-schedule/new")
		_ensure_shortcut(ws, label="Объекты", type_="DocType", link_to="Service Object")
		_ensure_shortcut(ws, label="Заявки", type_="URL", url="/app/issue")
		if frappe.db.exists("Report", "Due Service Maintenance Schedules"):
			_ensure_shortcut(
				ws, label="Просроченные графики", type_="Report", link_to="Due Service Maintenance Schedules"
			)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), "apply_ru_workspaces: Регламентное обслуживание update failed"
		)

	frappe.clear_cache()
	return {"status": "ok"}


@frappe.whitelist()
def backup_to_drive() -> dict:
	"""Создать резервную копию БД и выгрузить архив в Google Drive.

	Размещение: /<site>/Backups/<filename>.
	Использует существующую интеграцию Google Drive.
	"""
	from frappe.utils.backups import new_backup

	from ferum_custom.ferum_custom.integrations.drive import upload_bytes

	# Создаём бэкап (возвращает путь к файлу .sql.gz)
	bkp = new_backup(ignore_files=True)
	filepath = getattr(bkp, "backup_path", None) or getattr(bkp, "backup_path_db", None)
	if not filepath:
		return {"status": "skipped", "reason": "no-backup-path"}

	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "skipped", "reason": "drive-disabled"}

	try:
		with open(filepath, "rb") as f:
			content = f.read()
		site_name = frappe.local.site or frappe.utils.get_site_name(frappe.local.site_path)
		parts = [site_name, "Backups"]
		filename = filepath.split("/")[-1]
		file_id = upload_bytes(parts, filename, content)
		return {"status": "ok", "file_id": file_id, "filename": filename}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Backup to Drive failed")
		return {"status": "error", "error": str(e)}


@frappe.whitelist()
def backfill_drive_ids(limit: int | None = 200) -> dict:
	"""Backfill missing Drive IDs for Custom Attachments and File docs.

	- For Custom Attachment without `drive_file_id` and with ERP-hosted `file_url`,
	  reuse the existing upload helper to push to Drive and store IDs.
	- For File without `drive_file_id`, invoke the on_update handler to upload.

	Returns a summary dict with processed counts.
	"""
	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "skipped", "reason": "drive-disabled"}

	from ferum_custom.ferum_custom.doctype.custom_attachment.custom_attachment import (
		_upload_to_drive as _upload_custom_attachment,
	)
	from ferum_custom.ferum_custom.integrations import drive_file as drive_file_hook

	lim = int(limit) if (limit is not None and str(limit).isdigit()) else 200
	att_ok = att_skip = file_ok = file_skip = 0

	# Custom Attachments first
	try:
		atts = frappe.get_all(
			"Custom Attachment",
			filters={"drive_file_id": ["in", ["", None]], "file_url": ["like", "/%"]},
			fields=["name"],
			limit=lim,
		)
		for a in atts:
			try:
				_upload_custom_attachment(a["name"])  # idempotent
				att_ok += 1
			except Exception:
				att_skip += 1
	except Exception:
		frappe.log_error(frappe.get_traceback(), "backfill_drive_ids: list attachments failed")

	# Files next (public only to avoid private file perms)
	try:
		files = frappe.get_all(
			"File",
			filters={"drive_file_id": ["in", ["", None]], "is_private": 0},
			fields=["name"],
			limit=max(0, lim - att_ok),
		)
		for f in files:
			try:
				doc = frappe.get_doc("File", f["name"])
				drive_file_hook.on_file_update(doc, method="backfill")
				file_ok += 1
			except Exception:
				file_skip += 1
	except Exception:
		frappe.log_error(frappe.get_traceback(), "backfill_drive_ids: list files failed")

		return {
			"status": "ok",
			"attachments_processed": att_ok,
			"attachments_failed": att_skip,
			"files_processed": file_ok,
			"files_failed": file_skip,
		}


@frappe.whitelist()
def harden_permissions() -> dict:
	"""Harden access to admin pages/reports and align Client user type.

	- Restrict Page "permission-manager" to System Manager only.
	- Restrict Reports "Document Share Report" and
	  "Permitted Documents For User" to System Manager only.
	- Ensure users with role Client are Website Users (no Desk access).
	"""
	changed = {"rppr": 0, "clients": 0}

	# Role Permission for Page and Report tightening
	try:

		def _ensure_only_sm(filter_key: str, name: str) -> None:
			rows = frappe.get_all(
				"Role Permission for Page and Report",
				filters={filter_key: name},
				fields=["name", "role"],
			)
			for r in rows:
				if r["role"] != "System Manager":
					frappe.delete_doc("Role Permission for Page and Report", r["name"], force=1)
					changed["rppr"] += 1
			exists = frappe.db.exists(
				"Role Permission for Page and Report", {filter_key: name, "role": "System Manager"}
			)
			if not exists:
				doc = frappe.get_doc(
					{
						"doctype": "Role Permission for Page and Report",
						filter_key: name,
						"role": "System Manager",
					}
				)
				doc.insert(ignore_permissions=True)
				changed["rppr"] += 1

		_ensure_only_sm("page", "permission-manager")
		_ensure_only_sm("report", "Document Share Report")
		_ensure_only_sm("report", "Permitted Documents For User")
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "harden_permissions: rppr tighten failed")

	# Ensure Client users are Website Users
	try:
		users = frappe.get_all(
			"Has Role",
			filters={"role": "Client"},
			pluck="parent",
		)
		for u in set(users or []):
			try:
				user_doc = frappe.get_doc("User", u)
				if user_doc.user_type != "Website User":
					user_doc.user_type = "Website User"
					user_doc.save(ignore_permissions=True)
					changed["clients"] += 1
			except Exception:
				pass
		if changed["clients"]:
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "harden_permissions: client alignment failed")

	return {"status": "ok", **changed}


@frappe.whitelist()
def audit_fix_tasks() -> dict:
	"""End-to-end smoke: ensure schedule item exists, run generator, create portal SR.

	Returns summary with keys: service_object, schedule, issues_created, issues_today, portal_sr.
	"""
	out: dict[str, object] = {}
	from frappe.utils import nowdate

	# Ensure there is a Service Object to use
	so = frappe.get_all("Service Object", pluck="name", limit=1)
	if not so:
		cust = frappe.get_all("Customer", pluck="name", limit=1)
		if not cust:
			c = frappe.new_doc("Customer")
			c.customer_name = "Portal Client"
			c.insert(ignore_permissions=True)
			cust = [c.name]
		so_doc = frappe.new_doc("Service Object")
		so_doc.company = frappe.get_all("Company", pluck="name", limit=1)[0]
		so_doc.customer = cust[0]
		so_doc.object_name = "SO-AUDIT-1"
		so_doc.insert(ignore_permissions=True)
		so = [so_doc.name]
	out["service_object"] = so[0]

	# Ensure schedule exists and has an item
	sch = frappe.db.get_value("Service Maintenance Schedule", {"schedule_name": ["like", "Smoke %"]}, "name")
	if not sch:
		ms = frappe.new_doc("Service Maintenance Schedule")
		ms.company = frappe.get_all("Company", pluck="name", limit=1)[0]
		ms.customer = frappe.get_all("Customer", pluck="name", limit=1)[0]
		ms.schedule_name = "Smoke " + frappe.generate_hash(length=6)
		ms.frequency = "Monthly"
		ms.start_date = nowdate()
		ms.next_due_date = nowdate()
		ms.insert(ignore_permissions=True)
		sch = ms.name
	doc = frappe.get_doc("Service Maintenance Schedule", sch)
	if not doc.items:
		doc.append("items", {"service_object": so[0], "description": "Routine check (audit)"})
		doc.save(ignore_permissions=True)
	out["schedule"] = doc.name

	# Run generator and collect delta
	before = frappe.db.count("Issue")
	from ferum_custom.ferum_custom.doctype.service_maintenance_schedule.service_maintenance_schedule import (
		generate_service_requests_from_schedule,
	)

	generate_service_requests_from_schedule()
	after = frappe.db.count("Issue")
	issues = frappe.get_all(
		"Issue", filters={"modified": (">=", nowdate())}, fields=["name", "subject"], limit=5
	)
	out["issues_created"] = after - before
	out["issues_today"] = issues

	# Create a test portal client and create SR
	uname = "portal.client@example.com"
	if not frappe.db.exists("User", uname):
		u = frappe.new_doc("User")
		u.email = uname
		u.first_name = "Portal"
		u.last_name = "Client"
		u.user_type = "Website User"
		u.insert(ignore_permissions=True)
		u.add_roles("Client")
	cust = frappe.db.get_value("Customer", {"customer_name": "Portal Client"}, "name")
	if not cust:
		c = frappe.new_doc("Customer")
		c.customer_name = "Portal Client"
		c.insert(ignore_permissions=True)
		cust = c.name
		if not frappe.db.exists("User Permission", {"user": uname, "allow": "Customer", "for_value": cust}):
			up = frappe.new_doc("User Permission")
			up.user = uname
			up.allow = "Customer"
			up.for_value = cust
			up.insert(ignore_permissions=True)
		# Create via API under Administrator context (portal UI проверяется отдельно)
		from ferum_custom.ferum_custom.api.service import create_service_request

		sr_name = create_service_request(
			title="Portal API Audit", description="from audit", service_object=None
		)
		out["portal_sr"] = sr_name
		return out


@frappe.whitelist()
def setup_demo_assigned_schedule(
	engineer_email: str | None = None, service_object: str | None = None
) -> dict:
	"""Create a demo maintenance schedule that assigns Issues to an engineer.

	- Ensures a System User with role "Service Engineer" exists (engineer_email).
	- Sets this engineer as default on the provided or first Service Object.
	- Creates a schedule due today and runs the generator.

	Returns: dict with keys user, service_object, schedule, issue, assigned_to.
	"""
	res: dict[str, object] = {}

	# Ensure engineer user
	email = engineer_email or "engineer.demo@ferumrus.ru"
	if not frappe.db.exists("User", email):
		u = frappe.new_doc("User")
		u.email = email
		u.first_name = "Engineer"
		u.last_name = "Demo"
		u.user_type = "System User"
		u.insert(ignore_permissions=True)
		u.add_roles("Service Engineer")
	res["user"] = email

	# Resolve Service Object
	so = service_object
	if so and not frappe.db.exists("Service Object", so):
		so = None
	if not so:
		so = frappe.get_all("Service Object", pluck="name", limit=1)[0]
	res["service_object"] = so

	# Set default engineer on Service Object
	try:
		frappe.db.set_value("Service Object", so, "default_engineer", email)
	except Exception:
		pass

	# Create schedule due today
	from frappe.utils import nowdate

	sch = frappe.get_doc(
		{
			"doctype": "Service Maintenance Schedule",
			"company": frappe.get_all("Company", pluck="name", limit=1)[0],
			"customer": frappe.get_all("Customer", pluck="name", limit=1)[0],
			"schedule_name": f"DEMO-AUTO-{frappe.generate_hash(length=6)}",
			"frequency": "Monthly",
			"start_date": nowdate(),
			"next_due_date": nowdate(),
		}
	)
	sch.append("items", {"service_object": so, "description": "Demo assigned task"})
	sch.insert(ignore_permissions=True)
	res["schedule"] = sch.name

	# Run generator
	before = frappe.db.count("Issue")
	from ferum_custom.ferum_custom.doctype.service_maintenance_schedule.service_maintenance_schedule import (
		generate_service_requests_from_schedule,
	)

	generate_service_requests_from_schedule()
	after = frappe.db.count("Issue")
	created = after - before

	# Find newest issue and check assignment
	issue = None
	assigned = []
	try:
		last = frappe.get_all("Issue", fields=["name"], order_by="creation desc", limit=1)
		if last:
			issue = last[0]["name"]
			assigned = [
				r["allocated_to"]
				for r in frappe.get_all(
					"ToDo",
					filters={
						"reference_type": "Issue",
						"reference_name": issue,
					},
					fields=["allocated_to"],
				)
			]
	except Exception:
		pass

	res.update({"issues_created": created, "issue": issue, "assigned_to": assigned})
	return res


@frappe.whitelist()
def cleanup_users(keep_emails: list[str] | None = None, company: str | None = None) -> dict:
	"""Disable all non-essential users and align the primary user's company scope.

	Args:
	    keep_emails: List of user emails to keep enabled in addition to Administrator.
	    company: Optional company to grant as User Permission to kept users.

	Returns a summary of actions.
	"""
	keep = set(keep_emails or [])
	# Normalize and always keep Administrator and Guest intact
	keep.update({"Administrator"})

	changed = {"disabled": 0, "kept": [], "granted_company": 0}

	# Disable everyone except keep and Administrator/Guest
	users = frappe.get_all("User", fields=["name", "email", "enabled"], filters={})
	for u in users:
		name = u["name"]
		email = (u.get("email") or "").strip()
		if name in {"Guest", "Administrator"}:
			continue
		if email in keep:
			changed["kept"].append(email)
			# Ensure System User type for kept users
			try:
				user_doc = frappe.get_doc("User", name)
				if user_doc.user_type != "System User":
					user_doc.user_type = "System User"
					user_doc.save(ignore_permissions=True)
			except Exception:
				pass
			continue
		# disable
		if int(u.get("enabled") or 0) != 0:
			try:
				frappe.db.set_value("User", name, "enabled", 0)
				changed["disabled"] += 1
			except Exception:
				pass

	# Grant company user permission to kept users if requested
	if company:
		for email in keep:
			if email == "Administrator":
				continue
			if not frappe.db.exists("User", email):
				continue
			try:
				if not frappe.db.exists(
					"User Permission",
					{"user": email, "allow": "Company", "for_value": company},
				):
					up = frappe.new_doc("User Permission")
					up.user = email
					up.allow = "Company"
					up.for_value = company
					up.insert(ignore_permissions=True)
					changed["granted_company"] += 1
			except Exception:
				pass

	frappe.db.commit()
	return {"status": "ok", **changed}


@frappe.whitelist()
def purge_user(email: str) -> dict:
	"""Hard-delete a user by email and cleanup references.

	- Clears Service Object.default_engineer for this user
	- Deletes User Permissions and ToDo assignments
	- Deletes the User document (force)
	"""
	res = {
		"cleared_service_objects": 0,
		"deleted_user_permissions": 0,
		"deleted_todos": 0,
		"deleted_user": False,
	}
	if not frappe.db.exists("User", email):
		return {"status": "skipped", **res}

	# Clear default_engineer on Service Object
	try:
		objs = frappe.get_all("Service Object", filters={"default_engineer": email}, pluck="name")
		for name in objs or []:
			try:
				frappe.db.set_value("Service Object", name, "default_engineer", None)
				res["cleared_service_objects"] += 1
			except Exception:
				pass
	except Exception:
		pass

	# Delete User Permissions
	try:
		ups = frappe.get_all("User Permission", filters={"user": email}, pluck="name")
		for name in ups or []:
			try:
				frappe.delete_doc("User Permission", name, force=1)
				res["deleted_user_permissions"] += 1
			except Exception:
				pass
	except Exception:
		pass

	# Delete ToDo assignments (allocated_to is Data)
	try:
		todos = frappe.get_all("ToDo", filters={"allocated_to": email}, pluck="name")
		for name in todos or []:
			try:
				frappe.delete_doc("ToDo", name, force=1)
				res["deleted_todos"] += 1
			except Exception:
				pass
	except Exception:
		pass

	# Delete the user
	try:
		frappe.delete_doc("User", email, force=1)
		res["deleted_user"] = True
	except Exception:
		pass

	frappe.db.commit()
	return {"status": "ok", **res}


@frappe.whitelist()
def ensure_user_roles(email: str, roles: list[str]) -> dict:
	"""Ensure the given User has all roles from the list (idempotent)."""
	if not frappe.db.exists("User", email):
		return {"status": "not-found", "email": email}
	user = frappe.get_doc("User", email)
	current = {r.role for r in (user.roles or [])}
	added: list[str] = []
	for role in roles or []:
		if role not in current:
			try:
				user.add_roles(role)
				added.append(role)
			except Exception:
				pass
	# ensure System User if granting desk roles
	if added and user.user_type != "System User":
		try:
			user.user_type = "System User"
			user.save(ignore_permissions=True)
		except Exception:
			pass
	return {"status": "ok", "email": email, "added": added}


@frappe.whitelist()
def purge_nonessential_users(keep_emails: list[str] | None = None) -> dict:
	"""Delete all users except Administrator/Guest and those in keep_emails.

	Also clears basic references (default_engineer, ToDo, User Permissions).
	"""
	keep = set(keep_emails or [])
	keep.update({"Administrator", "Guest"})
	users = frappe.get_all("User", fields=["name", "email"], filters={})
	deleted = 0
	skipped: list[str] = []
	for u in users:
		name = u["name"]
		email = u.get("email") or name
		if name in keep or email in keep:
			skipped.append(email)
			continue
		try:
			# reuse purge_user for cleanup
			purge_user(email)
			deleted += 1
		except Exception:
			pass
	frappe.db.commit()
	return {"status": "ok", "deleted": deleted, "kept": list(sorted(skipped))}


@frappe.whitelist()
def create_test_schedule(
	customer: str | None = None,
	company: str | None = None,
	service_object: str | None = None,
	project: str | None = None,
) -> str:
	"""Create a simple Service Maintenance Schedule for smoke testing.

	If parameters are omitted, picks the first available Company/Customer/Service Object.
	Returns the created document name.
	"""
	# Resolve defaults
	if not company:
		companies = frappe.get_all("Company", pluck="name", limit=1)
		company = companies[0] if companies else None
	if not customer:
		customers = frappe.get_all("Customer", pluck="name", limit=1)
		customer = customers[0] if customers else None
	if not service_object:
		objs = frappe.get_all("Service Object", pluck="name", limit=1)
		service_object = objs[0] if objs else None

	if not (company and customer):
		raise frappe.ValidationError("Need at least Company and Customer to create schedule")

	from frappe.utils import nowdate

	doc = frappe.get_doc(
		{
			"doctype": "Service Maintenance Schedule",
			"company": company,
			"schedule_name": f"Smoke {frappe.generate_hash(length=6)}",
			"customer": customer,
			"service_project": project,
			"frequency": "Monthly",
			"start_date": nowdate(),
			"next_due_date": nowdate(),
		}
	)
	if service_object:
		doc.append("items", {"service_object": service_object, "description": "Routine check"})
	doc.insert(ignore_permissions=True)
	return doc.name
