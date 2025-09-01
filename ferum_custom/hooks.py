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

# include js in doctype views
doctype_js = {
    'article': 'public/js/article.js',
    'CustomAttachment': 'public/js/customattachment.js',
    'Invoice': 'public/js/invoice.js',
    'MaintenanceSchedule': 'public/js/maintenanceschedule.js',
    'MaintenanceScheduleItem': 'public/js/maintenancescheduleitem.js',
    'PayrollEntryCustom': 'public/js/payrollentrycustom.js',
    'PayrollEntryItem': 'public/js/payrollentryitem.js',
    'ProjectObjectItem': 'public/js/projectobjectitem.js',
    'RequestPhotoAttachmentItem': 'public/js/requestphotoattachmentitem.js',
    'ServiceObject': 'public/js/serviceobject.js',
    'ServiceProject': 'public/js/serviceproject.js',
    'ServiceReport': 'public/js/servicereport.js',
    'ServiceReportDocumentItem': 'public/js/servicereportdocumentitem.js',
    'ServiceReportWorkItem': 'public/js/servicereportworkitem.js',
    'ServiceRequest': 'public/js/servicerequest.js'
}
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
# Permissions evaluated in scripted ways

permission_query_conditions = {
    'article': 'ferum_custom.doctype.article.article.get_permission_query_conditions',
    'CustomAttachment': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.get_permission_query_conditions',
    'Invoice': 'ferum_custom.doctype.Invoice.Invoice.get_permission_query_conditions',
    'MaintenanceSchedule': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.get_permission_query_conditions',
    'MaintenanceScheduleItem': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.get_permission_query_conditions',
    'PayrollEntryCustom': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.get_permission_query_conditions',
    'PayrollEntryItem': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.get_permission_query_conditions',
    'ProjectObjectItem': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.get_permission_query_conditions',
    'RequestPhotoAttachmentItem': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.get_permission_query_conditions',
    'ServiceObject': 'ferum_custom.doctype.ServiceObject.ServiceObject.get_permission_query_conditions',
    'ServiceProject': 'ferum_custom.doctype.ServiceProject.ServiceProject.get_permission_query_conditions',
    'ServiceReport': 'ferum_custom.doctype.ServiceReport.ServiceReport.get_permission_query_conditions',
    'ServiceReportDocumentItem': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.get_permission_query_conditions',
    'ServiceReportWorkItem': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.get_permission_query_conditions',
    'ServiceRequest': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.get_permission_query_conditions'
}

has_permission = {
    'article': 'ferum_custom.doctype.article.article.has_permission',
    'CustomAttachment': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.has_permission',
    'Invoice': 'ferum_custom.doctype.Invoice.Invoice.has_permission',
    'MaintenanceSchedule': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.has_permission',
    'MaintenanceScheduleItem': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.has_permission',
    'PayrollEntryCustom': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.has_permission',
    'PayrollEntryItem': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.has_permission',
    'ProjectObjectItem': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.has_permission',
    'RequestPhotoAttachmentItem': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.has_permission',
    'ServiceObject': 'ferum_custom.doctype.ServiceObject.ServiceObject.has_permission',
    'ServiceProject': 'ferum_custom.doctype.ServiceProject.ServiceProject.has_permission',
    'ServiceReport': 'ferum_custom.doctype.ServiceReport.ServiceReport.has_permission',
    'ServiceReportDocumentItem': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.has_permission',
    'ServiceReportWorkItem': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.has_permission',
    'ServiceRequest': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.has_permission'
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    'article': 'ferum_custom.doctype.article.article.article',
    'CustomAttachment': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.CustomAttachment',
    'Invoice': 'ferum_custom.doctype.Invoice.Invoice.Invoice',
    'MaintenanceSchedule': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.MaintenanceSchedule',
    'MaintenanceScheduleItem': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.MaintenanceScheduleItem',
    'PayrollEntryCustom': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.PayrollEntryCustom',
    'PayrollEntryItem': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.PayrollEntryItem',
    'ProjectObjectItem': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.ProjectObjectItem',
    'RequestPhotoAttachmentItem': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem',
    'ServiceObject': 'ferum_custom.doctype.ServiceObject.ServiceObject.ServiceObject',
    'ServiceProject': 'ferum_custom.doctype.ServiceProject.ServiceProject.ServiceProject',
    'ServiceReport': 'ferum_custom.doctype.ServiceReport.ServiceReport.ServiceReport',
    'ServiceReportDocumentItem': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.ServiceReportDocumentItem',
    'ServiceReportWorkItem': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.ServiceReportWorkItem',
    'ServiceRequest': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.ServiceRequest'
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    'article': {
        'on_update': 'ferum_custom.doctype.article.article.on_update',
        'on_submit': 'ferum_custom.doctype.article.article.on_submit',
        'on_cancel': 'ferum_custom.doctype.article.article.on_cancel',
        'on_trash': 'ferum_custom.doctype.article.article.on_trash'
    },
    'CustomAttachment': {
        'on_update': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.on_update',
        'on_submit': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.on_submit',
        'on_cancel': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.on_cancel',
        'on_trash': 'ferum_custom.doctype.CustomAttachment.CustomAttachment.on_trash'
    },
    'Invoice': {
        'on_update': 'ferum_custom.doctype.Invoice.Invoice.on_update',
        'on_submit': 'ferum_custom.doctype.Invoice.Invoice.on_submit',
        'on_cancel': 'ferum_custom.doctype.Invoice.Invoice.on_cancel',
        'on_trash': 'ferum_custom.doctype.Invoice.Invoice.on_trash'
    },
    'MaintenanceSchedule': {
        'on_update': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.on_update',
        'on_submit': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.on_submit',
        'on_cancel': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.on_cancel',
        'on_trash': 'ferum_custom.doctype.MaintenanceSchedule.MaintenanceSchedule.on_trash'
    },
    'MaintenanceScheduleItem': {
        'on_update': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.on_update',
        'on_submit': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.on_submit',
        'on_cancel': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.on_cancel',
        'on_trash': 'ferum_custom.doctype.MaintenanceScheduleItem.MaintenanceScheduleItem.on_trash'
    },
    'PayrollEntryCustom': {
        'on_update': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.on_update',
        'on_submit': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.on_submit',
        'on_cancel': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.on_cancel',
        'on_trash': 'ferum_custom.doctype.PayrollEntryCustom.PayrollEntryCustom.on_trash'
    },
    'PayrollEntryItem': {
        'on_update': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.on_update',
        'on_submit': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.on_submit',
        'on_cancel': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.on_cancel',
        'on_trash': 'ferum_custom.doctype.PayrollEntryItem.PayrollEntryItem.on_trash'
    },
    'ProjectObjectItem': {
        'on_update': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.on_update',
        'on_submit': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.on_submit',
        'on_cancel': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.on_cancel',
        'on_trash': 'ferum_custom.doctype.ProjectObjectItem.ProjectObjectItem.on_trash'
    },
    'RequestPhotoAttachmentItem': {
        'on_update': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.on_update',
        'on_submit': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.on_submit',
        'on_cancel': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.on_cancel',
        'on_trash': 'ferum_custom.doctype.RequestPhotoAttachmentItem.RequestPhotoAttachmentItem.on_trash'
    },
    'ServiceObject': {
        'on_update': 'ferum_custom.doctype.ServiceObject.ServiceObject.on_update',
        'on_submit': 'ferum_custom.doctype.ServiceObject.ServiceObject.on_submit',
        'on_cancel': 'ferum_custom.doctype.ServiceObject.ServiceObject.on_cancel',
        'on_trash': 'ferum_custom.doctype.ServiceObject.ServiceObject.on_trash'
    },
    'ServiceProject': {
        'on_update': 'ferum_custom.doctype.ServiceProject.ServiceProject.on_update',
        'on_submit': 'ferum_custom.doctype.ServiceProject.ServiceProject.on_submit',
        'on_cancel': 'ferum_custom.doctype.ServiceProject.ServiceProject.on_cancel',
        'on_trash': 'ferum_custom.doctype.ServiceProject.ServiceProject.on_trash'
    },
    'ServiceReport': {
        'on_update': 'ferum_custom.doctype.ServiceReport.ServiceReport.on_update',
        'on_submit': 'ferum_custom.doctype.ServiceReport.ServiceReport.on_submit',
        'on_cancel': 'ferum_custom.doctype.ServiceReport.ServiceReport.on_cancel',
        'on_trash': 'ferum_custom.doctype.ServiceReport.ServiceReport.on_trash'
    },
    'ServiceReportDocumentItem': {
        'on_update': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.on_update',
        'on_submit': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.on_submit',
        'on_cancel': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.on_cancel',
        'on_trash': 'ferum_custom.doctype.ServiceReportDocumentItem.ServiceReportDocumentItem.on_trash'
    },
    'ServiceReportWorkItem': {
        'on_update': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.on_update',
        'on_submit': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.on_submit',
        'on_cancel': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.on_cancel',
        'on_trash': 'ferum_custom.doctype.ServiceReportWorkItem.ServiceReportWorkItem.on_trash'
    },
    'ServiceRequest': {
        'on_update': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.on_update',
        'on_submit': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.on_submit',
        'on_cancel': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.on_cancel',
        'on_trash': 'ferum_custom.doctype.ServiceRequest.ServiceRequest.on_trash'
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ferum_custom.tasks.all"
# 	],
# 	"daily": [
# 		"ferum_custom.tasks.daily"
# 	],
# 	"hourly": [
# 		"ferum_custom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ferum_custom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ferum_custom.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ferum_custom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ferum_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ferum_custom.task.get_dashboard_data"
# }

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
