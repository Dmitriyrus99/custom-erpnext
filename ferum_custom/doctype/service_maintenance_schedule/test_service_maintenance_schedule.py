from ferum_custom.ferum_custom.doctype.service_maintenance_schedule import (
    service_maintenance_schedule as sms,
)


def test_generate_service_requests_delegates(monkeypatch):
    called = {}

    def fake_generate():
        called["hit"] = True
        return [{"name": "ISS-0001"}]

    monkeypatch.setattr(
        "ferum_custom.ferum_custom.services.usecases.maintenance.generate_issues_from_schedules",
        fake_generate,
    )

    result = sms.generate_service_requests_from_schedule()
    assert called.get("hit") is True
    assert result == [{"name": "ISS-0001"}]


def test_service_maintenance_schedule_document_is_subclass():
    from frappe.model.document import Document

    assert issubclass(sms.ServiceMaintenanceSchedule, Document)
