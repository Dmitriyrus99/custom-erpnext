from frappe import _


def get_data():
	return {
		"fieldname": "service_request",
		"transactions": [
			{
				"label": _("Related"),
				"items": ["Service Report"],
			}
		],
	}
