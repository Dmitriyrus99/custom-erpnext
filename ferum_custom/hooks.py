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

# List view customizations
doctype_list_js = {
	"Invoice": "ferum_custom/doctype/invoice/invoice_list.js",
}

scheduler_events = {
	"daily": [
		"ferum_custom.ferum_custom.doctype.service_maintenance_schedule.service_maintenance_schedule.generate_service_requests_from_schedule",
		"ferum_custom.ferum_custom.site_ops.backup_to_drive",
	],
	"hourly": [
		"ferum_custom.ferum_custom.doctype.service_request.service_request.check_all_slas",
	],
}

doc_events = {
    "Invoice": {
        "on_update": "ferum_custom.ferum_custom.doctype.invoice.invoice.on_invoice_update",
        "on_cancel": "ferum_custom.ferum_custom.doctype.invoice.invoice.on_invoice_update",
    },
    "File": {
        "on_trash": "ferum_custom.cleanup.on_file_trash",
        "on_update": "ferum_custom.ferum_custom.integrations.drive_file.on_file_update",
    },
    "Project": {
        "after_insert": "ferum_custom.ferum_custom.autodoc.on_project_created",
    },
    "Task": {
        "on_update": "ferum_custom.ferum_custom.autodoc.on_task_update",
    },
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
					"General Director",
					"Department Head",
				],
			]
		],
	},
	{
		"doctype": "Print Format",
		"filters": [["module", "=", "Ferum Custom"]],
	},
	{
		"doctype": "Module Profile",
		"filters": [["module_profile_name", "=", "Ferum Admin"]],
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
					"General Director",
					"Department Head",
				],
			]
		],
	},
	{
		"doctype": "Dashboard Chart",
		"filters": [
			[
				"chart_name",
				"in",
				[
					"Открытые заявки по статусам",
					"Счета по проектам",
				],
			]
		],
	},
	{
		"doctype": "Workflow State",
		"filters": [
			[
				"workflow_state_name",
				"in",
				[
					"Draft",
					"Submitted",
					"Approved",
					"Archived",
					"Cancelled",
					"Open",
					"In Progress",
					"Completed",
					"Closed",
					"Sent",
					"Paid",
					"Planned",
					"Active",
					"Pending Approval",
				],
			]
		],
	},
]

before_request = [
	"ferum_custom.ferum_custom.observability.before_request",
	"ferum_custom.api.auth.jwt_before_request",
]

override_whitelisted_methods = {
	"frappe.desk.query_report.run": "ferum_custom.api.reports.run_with_defaults",
}
