from __future__ import annotations

from ferum_custom.ferum_custom.domain.service import application as service_app


class DummyDoc:
    def __init__(self, doctype: str):
        self.doctype = doctype
        self.name = f"{doctype}-1"
        self.data: dict[str, object] = {}

    def insert(self, ignore_permissions: bool = False) -> None:
        self.inserted = True

    def as_dict(self) -> dict[str, object]:
        return self.data


def test_create_service_request_sets_fields(monkeypatch):
    captured = {}

    def fake_new_doc(doctype: str):
        doc = DummyDoc(doctype)
        captured["doc"] = doc
        return doc

    monkeypatch.setattr("frappe.new_doc", fake_new_doc)

    name = service_app.create_service_request(
        title="Test",
        description="desc",
        service_object="SO-1",
        company="Ferum",
        project="Proj-1",
        customer="Customer A",
        priority="High",
        request_type="Issue",
    )

    doc = captured["doc"]
    assert doc.doctype == "Service Request"
    assert doc.service_object == "SO-1"
    assert doc.company == "Ferum"
    assert doc.customer == "Customer A"
    assert doc.priority == "High"
    assert doc.type == "Issue"
    assert name == doc.name


def test_list_service_requests_passes_filters(monkeypatch):
    recorded = {}

    def fake_get_list(doctype, **kwargs):
        recorded["doctype"] = doctype
        recorded["filters"] = kwargs.get("filters")
        return [{"name": "SR-1"}]

    monkeypatch.setattr("frappe.get_list", fake_get_list)

    data = service_app.list_service_requests(filters={"status": "Open"}, start=0, page_length=5)

    assert recorded["doctype"] == "Service Request"
    assert recorded["filters"] == {"status": "Open"}
    assert data == [{"name": "SR-1"}]
