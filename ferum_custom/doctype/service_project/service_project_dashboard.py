from frappe import _


def get_data():
    return {
        "fieldname": "project",
        "transactions": [
            {
                "label": _("Related"),
                "items": ["Service Request", "Invoice", "Service Object"],
            }
        ],
    }
