from types import SimpleNamespace

import frappe

from ferum_custom.ferum_custom.services.usecases import maintenance


def test_generate_issues_from_schedules_creates_issue(monkeypatch):
	inserted = []

	class DummySchedule:
		name = "SMSCH-0001"
		frequency = "Daily"
		next_due_date = "2025-01-01"
		schedule_name = "Pump upkeep"
		customer = "Cust A"
		service_project = None
		company = "Ferum"
		end_date = None
		items = [SimpleNamespace(service_object="SO-001", description="Inspect pump")]

		def save(self):
			self.saved = True

	dummy_schedule = DummySchedule()

	monkeypatch.setattr(
		frappe,
		"get_list",
		lambda *args, **kwargs: [frappe._dict(name=dummy_schedule.name)],
	)

	def fake_get_doc(arg1, arg2=None):
		if isinstance(arg1, dict):
			data = arg1.copy()

			class DummyIssue:
				def __init__(self):
					self.data = data
					self.name = data.get("name") or f"ISS-{len(inserted) + 1:05d}"

				def insert(self, ignore_permissions=True):
					inserted.append(self)
					return self

			return DummyIssue()
		if arg1 == "System Settings":
			return SimpleNamespace(time_zone="UTC")
		assert arg1 == "Service Maintenance Schedule"
		assert arg2 == dummy_schedule.name
		return dummy_schedule

	monkeypatch.setattr(frappe, "get_doc", fake_get_doc)
	monkeypatch.setattr(frappe, "logger", lambda *args, **kwargs: SimpleNamespace(info=lambda *a, **k: None))
	monkeypatch.setattr(
		"ferum_custom.ferum_custom.services.audit.log_event", lambda **kwargs: None, raising=False
	)

	result = maintenance.generate_issues_from_schedules()
	assert result == {"created": 1, "skipped": 0}
	assert inserted and inserted[0].data["service_maintenance_schedule"] == dummy_schedule.name
	assert dummy_schedule.next_due_date == "2025-01-02"


def test_generate_issues_handles_no_due_schedules(monkeypatch):
	monkeypatch.setattr(frappe, "get_list", lambda *a, **k: [])
	result = maintenance.generate_issues_from_schedules()
	assert result == {"created": 0, "skipped": 0}
