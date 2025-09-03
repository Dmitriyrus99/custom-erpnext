from frappe import _


def get_data():
	return {
		"fieldname": "service_object",
		"transactions": [
			{
				"label": _("Related"),
				"items": ["Service Request"],
			}
		],
	}
