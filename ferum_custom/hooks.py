app_name = "ferum_custom"
app_title = "Ferum Custom"
app_publisher = "Ferum"
app_description = "Custom erp system for Ferum"
app_email = "rusakov@ferumrus.ru"
app_license = "mit"

doctype_js = {
	# Keep User.user_type consistent with assigned roles (Desk vs Website)
	"User": "public/js/user.js",
}

scheduler_events = {
	"daily": [
		"ferum_custom.ferum_custom.doctype.service_maintenance_schedule.service_maintenance_schedule.generate_service_requests_from_schedule",
	],
	"hourly": [
		"ferum_custom.ferum_custom.doctype.service_request.service_request.check_all_slas",
	],
}

doc_events = {
	"Invoice": {
		"on_update": "ferum_custom.ferum_custom.doctype.invoice.invoice.on_invoice_update",
		"on_cancel": "ferum_custom.ferum_custom.doctype.invoice.invoice.on_invoice_update",
	}
}

fixtures = [
	{
		"doctype": "Workflow Action Master",
		"filters": [
			[
				"workflow_action_name",
				"in",
				[
					"Start Work",
					"Complete",
					"Close",
					"Cancel",
					"Submit",
					"Approve",
					"Archive",
					"Reopen",
					"Activate",
					"Reject",
					"Send",
					"Mark Paid",
				],
			]
		],
	},
	{
		"doctype": "Workflow",
		"filters": [
			[
				"name",
				"in",
				[
					"Service Request Workflow",
					"Service Report Workflow",
					"Service Project Workflow",
					"Invoice Workflow",
				],
			]
		],
	},
	{
		"doctype": "Role",
		"filters": [
			[
				"role_name",
				"in",
				[
					"Office Manager",
					"Chief Accountant",
					"Service Engineer",
					"Project Manager",
					"Client",
				],
			]
		],
	},
	{
		"doctype": "Print Format",
		"filters": [["module", "=", "Ferum Custom"]],
	},
	{
		"doctype": "Notification",
		"filters": [["module", "=", "Ferum Custom"]],
	},
	{
		"doctype": "Report",
		"filters": [["module", "=", "Ferum Custom"]],
	},
	{
		"doctype": "Module Profile",
		"filters": [["module_profile_name", "=", "Ferum Admin"]],
	},
	{
		"doctype": "Workspace",
		"filters": [["module", "=", "Ferum Custom"]],
	},
	{
		"doctype": "Module Def",
		"filters": [["name", "=", "Ferum Custom"]],
	},
	{
		"doctype": "Role Profile",
		"filters": [
			[
				"role_profile",
				"in",
				[
					"Project Manager",
					"Office Manager",
					"Service Engineer",
					"Chief Accountant",
					"Client",
				],
			]
		],
	},
]

# Request hooks (JWT optional)
before_request = [
	"ferum_custom.api.auth.jwt_before_request",
]
