import frappe

TARGETS = {
    "Service Request": "Service Request Workflow",
    "Service Report": "Service Report Workflow",
    "Service Project": "Service Project Workflow",
    "Invoice": "Invoice Workflow",
}


def execute():
    # Ensure only our workflows are active for target doctypes
    for doctype, wf_name in TARGETS.items():
        others = frappe.get_all(
            "Workflow",
            filters={"document_type": doctype, "name": ("!=", wf_name)},
            pluck="name",
        )
        for name in others:
            try:
                frappe.db.set_value("Workflow", name, "is_active", 0, update_modified=False)
            except Exception:
                pass
        # ensure our workflow exists and is active + state field is 'status'
        if frappe.db.exists("Workflow", wf_name):
            try:
                frappe.db.set_value("Workflow", wf_name, "is_active", 1, update_modified=False)
                frappe.db.set_value("Workflow", wf_name, "workflow_state_field", "status", update_modified=False)
            except Exception:
                pass

