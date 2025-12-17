from __future__ import annotations

from ferum_custom.ferum_custom.data_cleanup import contracts as contracts_cleanup


class DummyCache:
    pass


def test_normalize_contracts_creates_normalized(monkeypatch):
    calls = {}

    def fake_get_all(doctype, fields):
        assert doctype == "Contract"
        return [
            {
                "name": "C-1",
                "contract_no": "123/А",
                "contract_year": "2024",
                "company": "Ferum",
                "status": "Open",
                "contract_no_normalized": None,
            }
        ]

    def fake_set_value(doctype, docname, fieldname, value):
        calls["set"] = (doctype, docname, fieldname, value)

    def fake_exists(doctype, filters):
        return False

    monkeypatch.setattr("frappe.get_all", fake_get_all)
    monkeypatch.setattr("frappe.db.set_value", fake_set_value)

    contracts_cleanup.normalize_contracts()

    assert calls["set"][3] == "123А2024"


def test_normalize_contracts_logs_duplicate(monkeypatch):
    created = []

    def fake_get_all(*args, **kwargs):
        return [
            {
                "name": "C-1",
                "contract_no": "123",
                "contract_year": "2024",
                "company": "Ferum",
                "status": "Open",
                "contract_no_normalized": "1232024",
            },
            {
                "name": "C-2",
                "contract_no": "123",
                "contract_year": "2024",
                "company": "Ferum",
                "status": "Open",
                "contract_no_normalized": None,
            },
        ]

    class DummyIssue:
        def __init__(self, doc):
            self.doc = doc

        def insert(self, ignore_permissions=False):
            created.append(self.doc)

    def fake_get_doc(doc):
        return DummyIssue(doc)

    monkeypatch.setattr("frappe.get_all", fake_get_all)
    monkeypatch.setattr("frappe.db.set_value", lambda *args, **kwargs: None)
    monkeypatch.setattr("frappe.db.exists", lambda *args, **kwargs: False)
    monkeypatch.setattr("frappe.get_doc", lambda *args, **kwargs: DummyIssue({"doc": args}))

    contracts_cleanup.normalize_contracts()

    assert created, "Data Issue should be created for duplicate normalized numbers"
