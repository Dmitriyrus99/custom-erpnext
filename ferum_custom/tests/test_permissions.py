from ferum_custom.ferum_custom import security_pqc_rules


def _set_roles(monkeypatch, roles):
    monkeypatch.setattr("frappe.get_roles", lambda user: roles)


def _set_companies(monkeypatch, companies):
    monkeypatch.setattr("ferum_custom.ferum_custom.security_pqc_rules._companies", lambda user: companies)



def test_invoice_pqc_chief_accountant(monkeypatch):
    _set_roles(monkeypatch, ["Chief Accountant"])
    _set_companies(monkeypatch, ["Ferum Co"])
    cond = security_pqc_rules.invoice_pqc("acct@example.com")
    assert cond and "`tabInvoice`.company" in cond



def test_data_issue_pqc_security_role(monkeypatch):
    _set_roles(monkeypatch, ["Security Engineer"])
    cond = security_pqc_rules.data_issue_pqc("security@example.com")
    assert cond is None


def test_data_issue_pqc_other_user(monkeypatch):
    _set_roles(monkeypatch, ["Service Engineer"])
    cond = security_pqc_rules.data_issue_pqc("engineer@example.com")
    assert cond == "FALSE"
