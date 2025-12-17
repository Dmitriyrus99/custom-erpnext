from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "File": [
            {
                "fieldname": "drive_file_id",
                "label": "Drive File ID",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "file_url",
            },
            {
                "fieldname": "drive_web_link",
                "label": "Drive Web Link",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "drive_file_id",
            },
        ]
    }
    try:
        create_custom_fields(fields, ignore_validate=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Create File.drive_* fields failed")
