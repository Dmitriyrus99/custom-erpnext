app_name = "ferum_custom"
app_title = "Ferum Custom"
app_publisher = "Ferum"
app_description = "Custom erp system for Ferum"
app_email = "rusakov@ferumrus.ru"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "ferum_custom",
# 		"logo": "/assets/ferum_custom/logo.png",
# 		"title": "Ferum Custom",
# 		"route": "/ferum_custom",
# 		"has_permission": "ferum_custom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ferum_custom/css/ferum_custom.css"
# app_include_js = "/assets/ferum_custom/js/ferum_custom.js"

# include js, css files in header of web template
# web_include_css = "/assets/ferum_custom/css/ferum_custom.css"
# web_include_js = "/assets/ferum_custom/js/ferum_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ferum_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views (not needed for standard doctype controllers)
# Leave empty unless you add extra client scripts in `public/js`
# doctype_js = {
# 	"Some DocType": "public/js/some_doctype.js",
# }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ferum_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ferum_custom.utils.jinja_methods",
# 	"filters": "ferum_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ferum_custom.install.before_install"
# after_install = "ferum_custom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ferum_custom.uninstall.before_uninstall"
# after_uninstall = "ferum_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ferum_custom.utils.before_app_install"
# after_app_install = "ferum_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ferum_custom.utils.before_app_uninstall"
# after_app_uninstall = "ferum_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ferum_custom.notifications.get_notification_config"

# Permissions
# -----------
# No custom permission hooks defined. Use Role Permissions and DocType-level permissions.

# DocType Class overrides
# -----------------------
# Not needed for custom DocTypes; Frappe loads each DocType's controller automatically.

# Document Events
# ---------------
# Hook on document methods and events

# Document Events
# ---------------
# Not required for methods implemented in DocType controllers.

# Scheduled Tasks
# ---------------

# Testing
# -------

# before_tests = "ferum_custom.install.before_tests"

# Doc Events

# Overriding Methods
# ------------------------------

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ferum_custom.utils.before_request"]
# after_request = ["ferum_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["ferum_custom.utils.before_job"]
# after_job = ["ferum_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ferum_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
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
	}
}

# Ship workflows as fixtures
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
				["Service Request Workflow", "Service Report Workflow", "Service Project Workflow"],
			]
		],
	},
]

# Request hooks (JWT optional)
before_request = [
	"ferum_custom.ferum_custom.api.auth.jwt_before_request",
]
