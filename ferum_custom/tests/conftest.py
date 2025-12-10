"""Pytest configuration for the repository tests."""

from __future__ import annotations

import contextlib
import importlib
import os
import sys
from pathlib import Path

import frappe
import pytest
from frappe.utils.fixtures import sync_fixtures

# Ensure the repository root (which contains the lightweight ``frappe`` test
# double) is on ``sys.path`` even when pytest is executed via the shim entry
# point that lives outside of the project directory.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

os.environ.setdefault("FERUM_ENABLE_JWT", "1")

# Keep module aliases consistent regardless of import path depth
_security_module = importlib.import_module("ferum_custom.security_pqc_rules")
sys.modules["ferum_custom.security_pqc_rules"] = _security_module
sys.modules["ferum_custom.ferum_custom.security_pqc_rules"] = _security_module
importlib.import_module("frappe.auth")
with contextlib.suppress(Exception):
	import ferum_custom as _fc  # type: ignore
	_fc.security_pqc_rules = _security_module
	nested_pkg = importlib.import_module("ferum_custom.ferum_custom")
	setattr(nested_pkg, "security_pqc_rules", _security_module)

BENCH_PATH = Path(__file__).resolve().parents[4]
SITES_PATH = BENCH_PATH / "sites"


def _init_frappe_site() -> None:
	if getattr(frappe.local, "site", None):
		frappe.flags.in_test = True
		return

	site = os.environ.get("TEST_SITE") or os.environ.get("SITE_NAME") or "test_site"
	frappe.init(site=site, sites_path=str(SITES_PATH))
	frappe.connect()
	frappe.setup_module_map(include_all_apps=True)
	frappe.flags.in_test = True
	frappe.local.lang = "en"
	with contextlib.suppress(Exception):
		if not getattr(frappe.local.conf, "enable_jwt", None):
			frappe.local.conf.enable_jwt = 1
		frappe.conf.enable_jwt = frappe.local.conf.enable_jwt
	frappe.set_user("Administrator")
	with contextlib.suppress(Exception):
		sync_fixtures("ferum_custom")


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_frappe():
	_init_frappe_site()
	yield
	frappe.destroy()


def pytest_configure(config):
	import importlib

	import frappe

	for module in [
		"ferum_custom.ferum_custom.ferum_custom.doctype.customer.customer",
		"ferum_custom.ferum_custom.ferum_custom.doctype.service_request.service_request",
		"ferum_custom.ferum_custom.ferum_custom.doctype.service_report.service_report",
	]:
		with contextlib.suppress(ModuleNotFoundError):
			importlib.import_module(module)
