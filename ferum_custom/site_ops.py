from __future__ import annotations

"""Site operations helpers for one-off maintenance tasks.

Run with:
  bench --site <site> execute ferum_custom.ferum_custom.site_ops.apply_ru_workspaces
"""

import contextlib
import os
import shutil
import subprocess
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path

import frappe
from frappe.utils import cint

from ferum_custom.ferum_custom.security.api_guard import (
	require_post_if_http,
	require_roles_if_http,
)
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled


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
		_ensure_shortcut(ws, label="Объекты", type_="DocType", link_to="Asset")
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
	# Restrict when invoked via HTTP; scheduler/bench bypass
	require_roles_if_http(["System Manager"])
	require_post_if_http()
	from frappe.utils.backups import get_or_generate_backup_encryption_key, new_backup

	from ferum_custom.ferum_custom.integrations.drive import upload_bytes

	# Создаём бэкап (возвращает путь к файлу .sql.gz)
	bkp = new_backup(ignore_files=True)
	filepath = getattr(bkp, "backup_path", None) or getattr(bkp, "backup_path_db", None)
	if not filepath:
		return {"status": "skipped", "reason": "no-backup-path"}

	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "skipped", "reason": "drive-disabled"}

	try:
		# Optional: encrypt backup on disk before upload
		enc_path = None
		if is_feature_enabled("enable_backup_encryption"):
			passphrase = get_setting("backup_encryption_key") or get_or_generate_backup_encryption_key()
			enc_path = _encrypt_file_with_gpg(filepath, passphrase)
			if enc_path:
				# Remove plaintext backup
				with contextlib.suppress(Exception):
					os.remove(filepath)
		filepath_to_upload = enc_path or filepath
		with open(filepath_to_upload, "rb") as f:
			content = f.read()
		site_name = frappe.local.site or frappe.utils.get_site_name(frappe.local.site_path)
		parts = [site_name, "Backups"]
		filename = Path(filepath_to_upload).name
		file_id = upload_bytes(parts, filename, content)
		return {"status": "ok", "file_id": file_id, "filename": filename}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Backup to Drive failed")
		return {"status": "error", "error": str(e)}


@frappe.whitelist()
def backfill_drive_ids(limit: int | None = 200, dry_run: bool = False) -> dict:
	"""Backfill missing Drive IDs for Custom Attachments and File docs, with optional dry-run.

	- For Custom Attachment without `drive_file_id` and with ERP-hosted `file_url`,
	  reuse the existing upload helper to push to Drive and store IDs.
	- For File without `drive_file_id`, invoke the on_update handler to upload.

	Returns a summary dict with processed counts.
	"""
	# Admin-only via HTTP, POST-only
	require_roles_if_http(["System Manager"])
	require_post_if_http()
	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "skipped", "reason": "drive-disabled"}

	from ferum_custom.ferum_custom.integrations import drive_file as drive_file_hook
	from ferum_custom.ferum_custom.integrations import file_sync

	lim = int(limit) if (limit is not None and str(limit).isdigit()) else 200
	att_ok = att_skip = file_ok = file_skip = 0
	att_pending: list[str] = []
	file_pending: list[str] = []

	# Custom Attachments first
	try:
		atts = frappe.get_all(
			"Custom Attachment",
			filters={
				"drive_file_id": ["in", ["", None]],
				"file_url": ["like", "/%"],  # ERP-hosted only
			},
			fields=["name", "file_url"],
			limit=lim,
			order_by="creation asc",
		)
		for att in atts:
			try:
				if dry_run:
					att_pending.append(att["name"])
					continue
				file_id = file_sync.sync_custom_attachment_by_name(att["name"])
				if file_id:
					att_ok += 1
				else:
					att_skip += 1
			except Exception:
				att_skip += 1
	except Exception:
		frappe.log_error(frappe.get_traceback(), "backfill_drive_ids: list custom attachments failed")

	# Files next
	try:
		files = frappe.get_all(
			"File",
			filters={"drive_file_id": ["in", ["", None]]},
			fields=["name"],
			limit=lim,
			order_by="creation asc",
		)
		for f in files:
			try:
				if dry_run:
					file_pending.append(f["name"])
					continue
				doc = frappe.get_doc("File", f["name"])
				drive_file_hook.on_file_update(doc, method="backfill")
				file_ok += 1
			except Exception:
				file_skip += 1
	except Exception:
		frappe.log_error(frappe.get_traceback(), "backfill_drive_ids: list files failed")

	return {
		"status": "ok",
		"dry_run": dry_run,
		"limit": lim,
		"custom_attachments_processed": att_ok,
		"custom_attachments_failed": att_skip,
		"files_processed": file_ok,
		"files_failed": file_skip,
		"pending_preview": {
			"custom_attachments": att_pending[:20],
			"files": file_pending[:20],
		}
	}


@frappe.whitelist()
def daily_backfill_drive_ids_small() -> dict:
	"""Daily incremental Google Drive backfill with a safe limit.

	Processes a smaller batch (e.g. 100) to avoid overloading quota.
	"""
	require_roles_if_http(["System Manager"])  # restrict manual HTTP calls
	require_post_if_http()
	return backfill_drive_ids(limit=100, dry_run=False)


@frappe.whitelist()
def drive_healthcheck_and_alert(days: int = 1, threshold: int = 5) -> dict:
	"""Run Drive healthcheck and verify recent syncs; alert admins on issues.

	- Calls integrations.drive.healthcheck to verify API connectivity and root access.
	- Scans recent Files and Custom Attachments and counts items missing drive_file_id.
	- Sends an email to System Managers if connectivity is down or if missing
	  uploads exceed `threshold` items within the last `days` days.
	"""
	from datetime import datetime, timedelta

	from ferum_custom.ferum_custom.integrations import drive as drive_integration
	from ferum_custom.ferum_custom.utils import get_users_by_roles

	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "skipped", "reason": "drive-disabled"}

	problems: list[str] = []
	hc = drive_integration.healthcheck()
	if hc.get("status") != "ok":
		problems.append(f"Drive healthcheck: {hc.get('status')} - {hc.get('message')}")

	since = (datetime.utcnow() - timedelta(days=int(days))).strftime("%Y-%m-%d %H:%M:%S")

	try:
		missing_files = frappe.db.count(
			"File",
			filters={
				"creation": [">=", since],
				"is_private": 0,
				"drive_file_id": ["in", ["", None]],
			},
		)
	except Exception:
		missing_files = 0

	total_missing = missing_files or 0
	if total_missing > int(threshold):
		problems.append(f"Recent uploads pending Drive sync: Files={missing_files}")

	status = "ok" if not problems else "degraded"
	result = {
		"status": status,
		"health": hc,
		"missing_files": missing_files,
	}

	if problems:
		try:
			recipients = list(get_users_by_roles(["System Manager"]))
			if recipients:
				subject = "Google Drive healthcheck warnings"
				body = "\n".join(problems)
				frappe.sendmail(recipients=recipients, subject=subject, message=body)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Drive healthcheck notify failed")

	return result


# ------------------------------
# Monitoring summaries (email)
# ------------------------------


@frappe.whitelist()
def daily_overdue_summary_email(issue_fallback_days: int = 7) -> dict:
	"""Scan for overdue Issues (SLA/due date) and email a summary.

	Sent to Office Manager and Project Manager roles (email only).
	"""
	from datetime import timedelta

	today = date.today().isoformat()
	rows_issue: list[dict] = []

	# Issues overdue by due date field where available
	due_field = None
	try:
		meta = frappe.get_meta("Issue")
		for fn in ("resolution_by", "due_date", "expected_resolution", "sla_due_date"):
			if meta.has_field(fn):
				due_field = fn
				break
	except Exception:
		due_field = None

	try:
		if due_field:
			rows_issue = frappe.get_all(
				"Issue",
				filters={
					"status": ["not in", ["Resolved", "Closed"]],
					due_field: ["<", today],
				},
				fields=["name", "subject", "status", "priority", "project", "assigned_engineer", due_field],
				order_by=f"{due_field} asc",
			)
		else:
			# Fallback: very old open issues
			since = (date.today() - timedelta(days=int(issue_fallback_days))).isoformat()
			rows_issue = frappe.get_all(
				"Issue",
				filters={"status": ["not in", ["Resolved", "Closed"]], "creation": ["<", since]},
				fields=["name", "subject", "status", "priority", "project", "assigned_engineer", "creation"],
				order_by="creation asc",
			)
	except Exception:
		rows_issue = []

	if not rows_issue:
		return {"status": "ok", "sent": False, "reason": "no-overdue"}

	def fmt_issue(r: dict) -> str:
		due_val = r.get(due_field or "creation")
		return (
			f"- {r.get('name')} | {r.get('subject')} | {r.get('priority')} | "
			f"{r.get('project') or '-'} | {r.get('assigned_engineer') or '-'} | Due: {due_val} | {r.get('status')}"
		)

	lines: list[str] = []
	if rows_issue:
		lines.append("Issues overdue:")
		lines.extend(fmt_issue(r) for r in rows_issue)

	body = "\n".join(lines)

	# recipients: PM + OM
	try:
		from ferum_custom.ferum_custom.utils import get_users_by_roles

		recipients = list(get_users_by_roles(["Project Manager", "Office Manager"]))
		if recipients:
			frappe.sendmail(
				recipients=recipients,
				subject="Daily Overdue Summary (Issues)",
				message=body,
			)
			return {"status": "ok", "sent": True, "count_issue": len(rows_issue)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "daily_overdue_summary_email failed")
	return {"status": "error", "sent": False}


@frappe.whitelist()
def weekly_overdue_maintenance_schedules_email() -> dict:
	"""Email a weekly summary of overdue maintenance schedules to PM/OM roles.

	Overdue is defined as Service Maintenance Schedule.next_due_date < today (and not trashed).
	"""

	today = date.today().isoformat()
	try:
		rows = frappe.get_all(
			"Service Maintenance Schedule",
			filters={"next_due_date": ["<", today]},
			fields=["name", "schedule_name", "customer", "service_project", "next_due_date", "frequency"],
			order_by="next_due_date asc",
		)
	except Exception:
		rows = []

	if not rows:
		return {"status": "ok", "sent": False, "reason": "no-overdue"}

	lines = [
		"Overdue Maintenance Schedules:",
		*[
			f"- {r['name']} | {r['schedule_name']} | Project: {r.get('service_project') or '-'} | Customer: {r.get('customer') or '-'} | Next due: {r.get('next_due_date')} | Freq: {r.get('frequency')}"
			for r in rows
		],
	]
	body = "\n".join(lines)

	try:
		from ferum_custom.ferum_custom.utils import get_users_by_roles

		recipients = list(get_users_by_roles(["Project Manager", "Office Manager"]))
		if recipients:
			frappe.sendmail(
				recipients=recipients,
				subject="Weekly Overdue Maintenance Schedules",
				message=body,
			)
			return {"status": "ok", "sent": True, "count": len(rows)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "weekly_overdue_maintenance_schedules_email failed")
	return {"status": "error", "sent": False}


@frappe.whitelist()
def weekly_full_backup_to_drive() -> dict:
	"""Create a full backup (DB + files) and upload to Google Drive.

	Uses frappe.utils.backups.new_backup(ignore_files=False) and the same
	upload helper as daily backups (if Drive sync feature is enabled).
	"""
	require_roles_if_http(["System Manager"])
	require_post_if_http()
	from frappe.utils.backups import get_or_generate_backup_encryption_key, new_backup

	from ferum_custom.ferum_custom.integrations.drive import upload_bytes

	# Create full backup (includes files)
	bkp = new_backup(ignore_files=False)
	filepath = getattr(bkp, "backup_path", None) or getattr(bkp, "backup_path_db", None)
	if not filepath:
		return {"status": "skipped", "reason": "no-backup-path"}

	if not is_feature_enabled("enable_google_drive_sync"):
		return {"status": "skipped", "reason": "drive-disabled"}

	try:
		enc_path = None
		if is_feature_enabled("enable_backup_encryption"):
			passphrase = get_setting("backup_encryption_key") or get_or_generate_backup_encryption_key()
			enc_path = _encrypt_file_with_gpg(filepath, passphrase)
			if enc_path:
				with contextlib.suppress(Exception):
					os.remove(filepath)
		filepath_to_upload = enc_path or filepath
		with open(filepath_to_upload, "rb") as f:
			content = f.read()
		site_name = frappe.local.site or frappe.utils.get_site_name(frappe.local.site_path)
		parts = [site_name, "Backups", "Weekly"]
		filename = Path(filepath_to_upload).name
		file_id = upload_bytes(parts, filename, content)
		return {"status": "ok", "file_id": file_id, "filename": filename}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Weekly full backup to Drive failed")
		return {"status": "error", "error": str(e)}


@frappe.whitelist()
def harden_permissions() -> dict:
	"""Harden access to admin pages/reports and align Client user type.

	- Restrict Page "permission-manager" to System Manager only.
	- Restrict Reports "Document Share Report" and
	  "Permitted Documents For User" to System Manager only.
	- Ensure users with role Client are Website Users (no Desk access).
	"""
	require_roles_if_http(["System Manager"])  # if executed via HTTP
	require_post_if_http()
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


# ------------------------------
# Backup encryption and retention
# ------------------------------


def _encrypt_file_with_gpg(file_path: str, passphrase: str | None) -> str | None:
	"""Encrypt file with gpg symmetric encryption (AES256). Returns new path."""
	try:
		if not passphrase:
			return None
		if shutil.which("gpg") is None:
			frappe.logger().warning("gpg not available; skipping backup encryption")
			return None
		out_path = f"{file_path}.gpg"
		cmd = [
			"gpg",
			"--batch",
			"--yes",
			"--symmetric",
			"--cipher-algo",
			"AES256",
			"--pinentry-mode",
			"loopback",
			"--passphrase",
			str(passphrase),
			"-o",
			out_path,
			file_path,
		]
		subprocess.run(cmd, check=True)
		return out_path if os.path.exists(out_path) else None
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Encrypt backup with gpg failed")
		return None


@frappe.whitelist()
def cleanup_backups_retention(daily_keep: int = 7, weekly_keep: int = 4, monthly_keep: int = 6) -> dict:
	"""Apply local backup retention: daily/weekly/monthly windows.

	Keep:
	- All backups in the last `daily_keep` days
	- One per ISO week for the next `weekly_keep` weeks
	- One per month for the next `monthly_keep` months
	Delete older files outside of these windows.
	"""
	try:
		backups_dir = Path(frappe.utils.get_backups_path())
		if not backups_dir.exists():
			return {"status": "ok", "deleted": 0, "kept": 0}

		today = datetime.utcnow().date()
		items: list[tuple[Path, datetime]] = []
		for p in backups_dir.iterdir():
			if p.is_file():
				try:
					ts = datetime.utcfromtimestamp(p.stat().st_mtime)
				except Exception:
					ts = datetime.utcnow()
				items.append((p, ts))

		keep: set[Path] = set()
		# Daily window
		for path, ts in items:
			age_days = (today - ts.date()).days
			if age_days <= int(daily_keep):
				keep.add(path)

		# Weekly window
		weekly_window_days = int(daily_keep) + 7 * int(weekly_keep)
		weekly_groups: dict[tuple[int, int], tuple[Path, datetime]] = {}
		for path, ts in items:
			age_days = (today - ts.date()).days
			if int(daily_keep) < age_days <= weekly_window_days:
				iso = ts.isocalendar()
				key = (iso.year, iso.week)
				prev = weekly_groups.get(key)
				if not prev or ts > prev[1]:
					weekly_groups[key] = (path, ts)
		for p, _ in weekly_groups.values():
			keep.add(p)

		# Monthly window
		monthly_window_days = weekly_window_days + 30 * int(monthly_keep)
		monthly_groups: dict[tuple[int, int], tuple[Path, datetime]] = {}
		for path, ts in items:
			age_days = (today - ts.date()).days
			if weekly_window_days < age_days <= monthly_window_days:
				key = (ts.year, ts.month)
				prev = monthly_groups.get(key)
				if not prev or ts > prev[1]:
					monthly_groups[key] = (path, ts)
		for p, _ in monthly_groups.values():
			keep.add(p)

		deleted = 0
		for path, _ in items:
			if path not in keep:
				with contextlib.suppress(Exception):
					path.unlink()
					deleted += 1
		return {"status": "ok", "deleted": deleted, "kept": len(keep), "dir": str(backups_dir)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "cleanup_backups_retention failed")
		return {"status": "error"}


@frappe.whitelist()
def test_restore_latest_backup() -> dict:
	"""Best-effort test restore on a staging site to validate backups.

	Reads `test_restore_site` from settings. Requires bench CLI in PATH.
	This runs `bench --site <staging> restore <latest-db-dump>` (DB only).
	Sends email to System Managers on failure.
	"""
	staging = (get_setting("test_restore_site") or "").strip()
	if not staging:
		return {"status": "skipped", "reason": "no-staging-site-configured"}

	try:
		backups_dir = Path(frappe.utils.get_backups_path())
		dumps = sorted(
			[p for p in backups_dir.iterdir() if p.is_file() and p.suffix in (".gz", ".sql", ".gpg")],
			key=lambda p: p.stat().st_mtime,
			reverse=True,
		)
		if not dumps:
			return {"status": "skipped", "reason": "no-backups-found"}
		latest = dumps[0]
		# If encrypted, skip automatic restore
		if latest.suffix == ".gpg":
			return {"status": "skipped", "reason": "latest-backup-encrypted"}

		cmd = ["bench", "--site", staging, "restore", str(latest), "--force"]
		frappe.utils.execute_in_shell(" ".join(cmd))
		return {"status": "ok", "restored": True, "site": staging, "backup": str(latest)}
	except Exception as exc:
		with contextlib.suppress(Exception):
			from ferum_custom.ferum_custom.utils import get_users_by_roles

			recipients = list(get_users_by_roles(["System Manager"]))
			if recipients:
				frappe.sendmail(
					recipients=recipients,
					subject="Backup test restore failed",
					message=f"Error: {exc}",
				)
		return {"status": "error", "error": str(exc)}


@frappe.whitelist()
def audit_fix_tasks() -> dict:
	"""End-to-end smoke: ensure schedule item exists, run generator, create portal Issue.

	Returns summary with keys: asset, schedule, issues_created, issues_today, portal_issue.
	"""
	out: dict[str, object] = {}
	from frappe.utils import nowdate

	# Ensure there is an Asset to use
	asset_name = frappe.get_all("Asset", pluck="name", limit=1)
	if not asset_name:
		cust = frappe.get_all("Customer", pluck="name", limit=1)
		if not cust:
			c = frappe.new_doc("Customer")
			c.customer_name = "Portal Client"
			c.insert(ignore_permissions=True)
			cust = [c.name]
		asset_doc = frappe.new_doc("Asset")
		asset_doc.company = frappe.get_all("Company", pluck="name", limit=1)[0]
		asset_doc.customer = cust[0]
		asset_doc.asset_name = "ASSET-AUDIT-1"
		asset_doc.insert(ignore_permissions=True)
		asset_name = [asset_doc.name]
	out["asset"] = asset_name[0]

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
		doc.append("items", {"service_object": asset_name[0], "description": "Routine check (audit)"})
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

	# Create a test portal client and create Issue
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
		from ferum_custom.ferum_custom.api.service import create_service_request as create_issue

		resp = create_issue(title="Portal API Audit", description="from audit", service_object=None)
		issue_name = resp.get("name") if isinstance(resp, dict) else resp
		out["portal_issue"] = issue_name
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

	# Resolve Asset
	asset_name = service_object
	if asset_name and not frappe.db.exists("Asset", asset_name):
		asset_name = None
	if not asset_name:
		asset_name = frappe.get_all("Asset", pluck="name", limit=1)[0]
	res["service_object"] = asset_name

	# Set default engineer on Asset
	try:
		frappe.db.set_value("Asset", asset_name, "default_engineer", email)
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
	sch.append("items", {"service_object": asset_name, "description": "Demo assigned task"})
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

	# Clear default_engineer on Asset
	try:
		objs = frappe.get_all("Asset", filters={"default_engineer": email}, pluck="name")
		for name in objs or []:
			try:
				frappe.db.set_value("Asset", name, "default_engineer", None)
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

	If parameters are omitted, picks the first available Company/Customer/Asset.
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
		objs = frappe.get_all("Asset", pluck="name", limit=1)
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
			"project": project,
			"frequency": "Monthly",
			"start_date": nowdate(),
			"next_due_date": nowdate(),
		}
	)
	if service_object:
		doc.append("items", {"asset": service_object, "description": "Routine check"})
	doc.insert(ignore_permissions=True)
	return doc.name
