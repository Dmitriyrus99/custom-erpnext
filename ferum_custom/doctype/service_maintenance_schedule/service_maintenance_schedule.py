import contextlib

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_months, add_years, getdate, nowdate

try:
	# optional helper to map custom Service Project -> standard Project
	from ferum_custom.patches.utils_migration import find_or_create_project  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional in CI
	find_or_create_project = None  # type: ignore[assignment]


def generate_service_requests_from_schedule():
	"""Thin controller: delegate maintenance Issue generation to service layer."""
	from ferum_custom.ferum_custom.services.usecases.maintenance import (
		generate_issues_from_schedules,
	)

	return generate_issues_from_schedules()


class ServiceMaintenanceSchedule(Document):
	pass
