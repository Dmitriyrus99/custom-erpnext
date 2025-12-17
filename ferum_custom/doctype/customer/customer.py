"""Lightweight Customer DocType used for tests and demo data.

This app is designed to run without the full ERPNext dependency tree, but
several doctypes - such as Service Object and Service Request - link to a
Customer record.  The frappe test runner instantiates Customer documents in the
fixtures and automated tests, so we provide a minimal implementation here that
covers the required fields and permissions without introducing heavy upstream
coupling.
"""

from __future__ import annotations

from frappe.model.document import Document


class Customer(Document):
    """Simple customer master used across custom doctypes."""

    customer_name: str
    email: str | None
    phone: str | None
    address: str | None
    notes: str | None
    customer_group: str | None
    territory: str | None
