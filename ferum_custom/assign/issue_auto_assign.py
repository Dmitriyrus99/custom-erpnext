from __future__ import annotations

import re

import frappe


def _project_default_engineer(project: str | None) -> str | None:
	if not project:
		return None
	try:
		# custom field on Project (Link/User)
		return frappe.db.get_value("Project", project, "default_engineer")
	except Exception:
		return None


def _parse_asset_from_text(text: str | None) -> str | None:
	if not text:
		return None
	# Look for "Service Object: NAME" pattern
	m = re.search(r"Service Object:\s*([\w\-\.\s]+)", text)
	return m.group(1).strip() if m else None


def _asset_default_engineer_from_issue(doc) -> str | None:
	# Try to resolve from subject (Scheduled Maintenance: <SO>)
	try:
		if doc.subject and doc.subject.startswith("Scheduled Maintenance:"):
			parts = doc.subject.split(":", 1)[1].strip()
			so_name = parts.split("(")[0].strip()
			# Accept either Service Object name or object_name
			if frappe.db.exists("Asset", so_name):
				return frappe.db.get_value("Asset", so_name, "default_engineer")
			obj = frappe.db.get_value("Asset", {"object_name": so_name}, "name")
			if obj:
				return frappe.db.get_value("Asset", obj, "default_engineer")
	except Exception:
		pass

	# Try from description "Service Object: ..."
	try:
		so = _parse_service_object_from_text(getattr(doc, "description", None))
		if so:
			if frappe.db.exists("Asset", so):
				return frappe.db.get_value("Asset", so, "default_engineer")
			obj = frappe.db.get_value("Asset", {"object_name": so}, "name")
			if obj:
				return frappe.db.get_value("Asset", obj, "default_engineer")
	except Exception:
		pass
	return None


def before_insert(doc, method=None):  # called via hooks
	"""Populate Issue.assigned_engineer from Asset/Project/Service Object context.

	Assignment Rule (Based on Field) will pick up `assigned_engineer` and create ToDo.
	"""
	try:
		if getattr(doc, "assigned_engineer", None):
			return
		# From Project
		eng = _project_default_engineer(getattr(doc, "project", None))
		if eng:
			doc.assigned_engineer = eng
			return
		# From Service Object inferred from subject/description
		eng = _asset_default_engineer_from_issue(doc)
		if eng:
			doc.assigned_engineer = eng
			return
	except Exception:
		pass
