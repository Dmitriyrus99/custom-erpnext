from ferum_custom.ferum_custom import security_pqc_rules as sr


def _set_roles(monkeypatch, roles):
    monkeypatch.setattr("frappe.get_roles", lambda user: roles)


def _set_companies(monkeypatch, companies):
    monkeypatch.setattr("ferum_custom.security_pqc_rules._companies", lambda user: companies)


def test_service_request_pqc_engineer(monkeypatch):
    _set_roles(monkeypatch, ["Service Engineer"])
    _set_companies(monkeypatch, ["Ferum Co"])
    cond = sr.service_request_pqc("engineer@example.com")
    assert cond is not None
    assert "assigned_to" in cond


def test_invoice_pqc_chief_accountant(monkeypatch):
    _set_roles(monkeypatch, ["Chief Accountant"])
    _set_companies(monkeypatch, ["Ferum Co"])
    cond = sr.invoice_pqc("acct@example.com")
    assert cond and "`tabInvoice`.company" in cond


def test_service_request_pqc_client(monkeypatch):
    _set_roles(monkeypatch, ["Client"])
    monkeypatch.setattr(
        "ferum_custom.security_pqc_rules.get_allowed_customers",
        lambda user: ["Cust Inc"],
    )
    cond = sr.service_request_pqc("client@example.com")
    assert cond
    assert "`tabService Request`.customer" in cond


def test_data_issue_pqc_security_role(monkeypatch):
    _set_roles(monkeypatch, ["Security Engineer"])
    cond = sr.data_issue_pqc("security@example.com")
    assert cond is None


def test_data_issue_pqc_other_user(monkeypatch):
    _set_roles(monkeypatch, ["Service Engineer"])
    cond = sr.data_issue_pqc("engineer@example.com")
    assert cond == "FALSE"
