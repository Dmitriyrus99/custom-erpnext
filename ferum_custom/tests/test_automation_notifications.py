import frappe

from ferum_custom.ferum_custom import automation


def test_get_report_recipients_handles_multiple_roles(monkeypatch):
	calls = []

	def fake_get_users_with_role(role):
		calls.append(role)
		return {
			"Project Manager": ["pm1@example.com"],
			"Department Head": ["pm1@example.com", "lead@example.com"],
		}.get(role, [])

	def fake_get_all(doctype, **kwargs):
		assert doctype == "User"
		names = sorted(kwargs["filters"]["name"][1])
		assert names == sorted(["pm1@example.com", "lead@example.com"])
		return ["pm1@ferum.test", "lead@ferum.test"]

	monkeypatch.setattr(automation.frappe, "get_users_with_role", fake_get_users_with_role, raising=False)
	monkeypatch.setattr(automation.frappe, "get_all", fake_get_all)

	recipients = automation.get_report_recipients(["Project Manager", "Department Head"])
	assert set(recipients) == {"pm1@ferum.test", "lead@ferum.test"}
	assert calls == ["Project Manager", "Department Head"]


def test_run_permission_audit_queries_combined_doctype(monkeypatch):
	filters_seen = []

	def fake_get_all(doctype, **kwargs):
		assert doctype == "Role Permission for Page and Report"
		filters_seen.append(kwargs["filters"])
		if kwargs["filters"].get("page"):
			return [frappe._dict(role="Employee", page="permission-manager")]
		if kwargs["filters"].get("report"):
			return [frappe._dict(role="Employee", report="System Report")]
		return []

	sent = {}

	monkeypatch.setattr(automation.frappe, "get_all", fake_get_all)
	monkeypatch.setattr(
		"ferum_custom.ferum_custom.automation.get_report_recipients", lambda roles: ["admin@example.com"]
	)
	monkeypatch.setattr(
		automation.frappe, "sendmail", lambda **kwargs: sent.setdefault("calls", []).append(kwargs)
	)
	monkeypatch.setattr(automation.frappe, "log_info", lambda *args, **kwargs: None, raising=False)

	automation.run_permission_audit()

	assert len(filters_seen) == 2
	assert filters_seen[0]["page"] == ["is", "set"]
	assert filters_seen[1]["report"] == ["is", "set"]
	assert sent["calls"][0]["recipients"] == ["admin@example.com"]
