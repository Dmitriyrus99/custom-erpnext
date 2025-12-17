from __future__ import annotations

import frappe

DOCTYPES_TO_MODULES: dict[str, str] = {
    # These doctypes are provided by ERPNext. If they were previously “shadowed” by ferum_custom,
    # restore their canonical module to avoid loading wrong controller modules.
    "Customer": "Selling",
    "Contract": "CRM",
}


def execute() -> None:
    for doctype, expected_module in DOCTYPES_TO_MODULES.items():
        if not frappe.db.exists("DocType", doctype):
            continue

        current_module = frappe.db.get_value("DocType", doctype, "module")
        if current_module != "Ferum Custom":
            continue

        frappe.db.set_value("DocType", doctype, "module", expected_module, update_modified=False)
        frappe.clear_cache(doctype=doctype)
