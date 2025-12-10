from __future__ import annotations

import json

import pandas as pd

from ferum_custom.ferum_custom.etl.ingest_staging import ingest_excel_to_staging


def test_ingest_excel_to_staging(monkeypatch):
	df = pd.DataFrame([{"a": 1, "b": 2}, {"a": 3, "b": 4}])

	inserted: list[dict[str, object]] = []

	class StubDoc:
		def __init__(self, payload: dict[str, object]):
			self.payload = payload

		def insert(self, ignore_permissions: bool = False) -> None:
			inserted.append(self.payload)

	monkeypatch.setattr(
		"ferum_custom.ferum_custom.etl.ingest_staging.pd.read_excel",
		lambda path, sheet_name=None: df,
	)
	monkeypatch.setattr("frappe.get_doc", lambda payload: StubDoc(payload))

	ingest_excel_to_staging("data.xlsx", company="Ferum", sheet="Sheet1", source_name="upload.csv")

	assert len(inserted) == 2
	for payload in inserted:
		assert payload["company"] == "Ferum"
		assert payload["sheet"] == "Sheet1"
		assert payload["source_file"] == "upload.csv"
		parsed = json.loads(payload["row_json"])
		assert "a" in parsed
