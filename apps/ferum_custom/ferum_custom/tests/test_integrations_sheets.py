from __future__ import annotations

from unittest import mock

import frappe
import pytest
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

try:
    from ferum_custom.ferum_custom.doctype.invoice import invoice as invoice_module
except ModuleNotFoundError:  # pragma: no cover - gracefully skip when module removed
    invoice_module = None  # type: ignore[assignment]

from ferum_custom.ferum_custom.tests import smoke_tools

pytestmark = pytest.mark.skipif(
    invoice_module is None, reason="Invoice Google Sheets sync module not present in this build."
)


class _DummySheet:
    def __init__(self):
        self.rows: list[list[object]] = []

    def find(self, value):
        raise invoice_module.CellNotFound

    def append_row(self, row):
        self.rows.append(row)


class TestGoogleSheetsSync(FrappeTestCase):
    def test_append_row_on_missing_cell(self):
        company = smoke_tools.ensure_company()

        doc = frappe.get_doc(
            {
                "doctype": "Invoice",
                "company": company,
                "counterparty_type": "Customer",
                "counterparty_name": "Dummy Client",
                "amount": 100,
                "invoice_date": getdate(),
            }
        )
        doc.insert()

        sheet = _DummySheet()
        with (
            mock.patch.object(
                invoice_module,
                "get_google_sheet",
                return_value=sheet,
            ),
            mock.patch.object(invoice_module, "metrics_inc", lambda *args, **kwargs: None),
        ):
            invoice_module.sync_to_google_sheets(doc.name)

        self.assertEqual(sheet.rows[0][0], doc.name)
        doc.delete()
