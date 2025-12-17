import frappe


def execute():
    # Rename custom doctypes if they exist under our module
    try:
        ms = frappe.db.get_value(
            "DocType", {"name": "Maintenance Schedule", "module": "Ferum Custom"}, "name"
        )
        if ms:
            frappe.rename_doc(
                "DocType", "Maintenance Schedule", "Service Maintenance Schedule", force=True
            )
    except Exception:
        pass
    try:
        msi = frappe.db.get_value(
            "DocType", {"name": "Maintenance Schedule Item", "module": "Ferum Custom"}, "name"
        )
        if msi:
            frappe.rename_doc(
                "DocType",
                "Maintenance Schedule Item",
                "Service Maintenance Schedule Item",
                force=True,
            )
    except Exception:
        pass
