from __future__ import annotations

from datetime import datetime

from ferum_custom.ferum_custom.data_cleanup import stg_raw


def test_cleanup_stg_raw_records_skips_missing_table(monkeypatch):
	monkeypatch.setattr("frappe.db.table_exists", lambda table: False)
	assert stg_raw.cleanup_stg_raw_records() == 0


def test_cleanup_stg_raw_records_deletes_old_rows(monkeypatch):
	calls: dict[str, object] = {}

	monkeypatch.setattr("frappe.db.table_exists", lambda table: True)

	def fake_count(doctype, filters=None):
		calls["filters"] = filters
		return 5

	def fake_sql(query, values):
		calls["threshold"] = values

	monkeypatch.setattr("frappe.db.count", fake_count)
	monkeypatch.setattr("frappe.db.sql", fake_sql)

	result = stg_raw.cleanup_stg_raw_records(retention_days=7)
	assert result == 5
	assert calls["filters"]["ingested_at"][0] == "<"
	assert isinstance(calls["threshold"][0], datetime)


def test_cleanup_stg_raw_job_invokes_function(monkeypatch):
	called = {}

	def fake_cleanup(**kwargs):
		called["ran"] = True

	monkeypatch.setattr(
		"ferum_custom.ferum_custom.data_cleanup.stg_raw.cleanup_stg_raw_records",
		fake_cleanup,
	)

	from ferum_custom.ferum_custom.data_cleanup.jobs import cleanup_stg_raw_job

	cleanup_stg_raw_job()
	assert called.get("ran")
