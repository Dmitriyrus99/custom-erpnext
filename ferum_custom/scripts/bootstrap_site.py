"""Bootstrap helper for clean Ferum sites."""

from __future__ import annotations

import click
import frappe


def bootstrap() -> None:
    frappe.connect()
    try:
        _run()
        frappe.db.commit()
        frappe.logger("ferum_custom").info("Bootstrap completed")
    finally:
        frappe.destroy()


@click.command()
@click.option("--site", required=True, help="Site name")
def main(site: str) -> None:
    frappe.init(site=site)
    bootstrap()


def _run() -> None:
    bootstrap_core()
    bootstrap_ferum()


CORE_DOCTYPES = [
    ("core", "doctype", "patch_log"),
    ("desk", "doctype", "notification_settings"),
    ("desk", "doctype", "notification_subscription"),
]


def bootstrap_core() -> None:
    for module, dt, name in CORE_DOCTYPES:
        frappe.reload_doc(module, dt, name)

    ensure_patch_log("frappe.patches.v15_0.set_default_roles")


def ensure_patch_log(patch: str) -> None:
    if not frappe.db.exists("Patch Log", {"patch": patch}):
        doc = frappe.new_doc("Patch Log")
        doc.patch = patch
        doc.skipped = 0
        doc.insert(ignore_permissions=True)


def bootstrap_ferum() -> None:
    frappe.db.set_single_value("Ferum Custom Settings", "enable_jwt", 1)
    frappe.db.set_single_value("Ferum Custom Settings", "jwt_secret", "dev-secret")

    if not frappe.db.exists("Currency", "RUB"):
        cur = frappe.new_doc("Currency")
        cur.currency_name = "Russian Ruble"
        cur.name = "RUB"
        cur.insert()

    if not frappe.db.exists("Country", "Russia"):
        country = frappe.new_doc("Country")
        country.country = "Russia"
        country.country_name = "Russia"
        country.insert()

    if not frappe.db.exists("Company", "Ferum Demo"):
        company = frappe.new_doc("Company")
        company.company_name = "Ferum Demo"
        company.abbr = "FD"
        company.default_currency = "RUB"
        company.country = "Russia"
        company.flags.ignore_mandatory = False
        company.insert()


if __name__ == "__main__":
    main()
