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
    "Issue": "ferum_custom/doctype/issue/issue_list.js",
}

scheduler_events = {
    "daily": [
        # Generate Issues from due maintenance schedules
        "ferum_custom.ferum_custom.doctype.service_maintenance_schedule.service_maintenance_schedule.generate_service_requests_from_schedule",
        # Incremental Google Drive backfill (long queue)
        "ferum_custom.ferum_custom.scheduler_wrappers.daily_drive_backfill",
        # Drive healthcheck + alert to admins
        "ferum_custom.ferum_custom.site_ops.drive_healthcheck_and_alert",
        # Daily report on overdue service requests
        "ferum_custom.ferum_custom.automation.send_daily_overdue_report",
        # Contract normalization data cleanup
        "ferum_custom.ferum_custom.data_cleanup.jobs.normalize_contracts_job",
        # Apply backup retention locally (7 daily, 4 weekly, 6 monthly)
        "ferum_custom.ferum_custom.site_ops.cleanup_backups_retention",
        # Refresh materialized views (long queue)
        "ferum_custom.ferum_custom.scheduler_wrappers.refresh_materialized_views",
        # Cleanup staging raw data (long queue)
        "ferum_custom.ferum_custom.scheduler_wrappers.cleanup_stg_raw",
    ],
    "weekly": [
        # Enforce permissions/roles and lock admin pages/reports
        "ferum_custom.ferum_custom.site_ops.harden_permissions",
        # Weekly report on overdue routine maintenance tasks
        "ferum_custom.ferum_custom.automation.send_weekly_overdue_maintenance_report",
        # Weekly audit of risky permissions
        "ferum_custom.ferum_custom.automation.run_permission_audit",
        # Weekly test restore on staging (if configured)
        "ferum_custom.ferum_custom.scheduler_wrappers.test_restore_latest_backup",
        # Weekly full backup (DB+files) to long queue
        "ferum_custom.ferum_custom.scheduler_wrappers.weekly_full_backup",
    ],
    "hourly": [

    ],
    "cron": {
        # Nightly backup to Google Drive at 2 AM
        "0 2 * * *": ["ferum_custom.ferum_custom.scheduler_wrappers.nightly_backup_to_gdrive"],
    },
}

doc_events = {
    "File": {
        "on_trash": "ferum_custom.cleanup.on_file_trash",
        # Private-by-default for sensitive doctypes
        "validate": "ferum_custom.ferum_custom.integrations.file_security.on_file_validate",
        # Antivirus + Drive sync
        "on_update": "ferum_custom.ferum_custom.integrations.drive_file.on_file_update",
    },
    "Project": {
        "after_insert": "ferum_custom.ferum_custom.autodoc.on_project_created",
    },
    "Task": {
        "on_update": "ferum_custom.ferum_custom.autodoc.on_task_update",
    },
    "Issue": {
        "before_insert": "ferum_custom.assign.issue_auto_assign.before_insert",
        "after_insert": "ferum_custom.notifications_module.on_issue_after_insert",
    },
    "Employee": {
        "before_save": "ferum_custom.ferum_custom.hr.employee.ensure_unique_middle_name_for_tests",
        "on_update": "ferum_custom.ferum_custom.hr.employee.sync_user_middle_name",
    },
    "Role": {
        "on_update": "ferum_custom.ferum_custom.automation.on_role_update_audit",
    },
    "Role Permission for Page and Report": {
        "after_insert": "ferum_custom.ferum_custom.automation.on_rppr_after_insert",
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
        "filters": [
            [
                "name",
                "in",
                [
                    "Ferum Custom",
                    "Project & Contract Management",
                    "Service Request Management",
                    "Work Reporting",
                    "Invoicing",
                    "HR & Payroll",
                    "Document Management",
                    "Notifications",
                    "Analytics",
                ],
            ]
        ],
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
                    "Ferum Admin",
                    "Ferum Management",
                    "Ferum Operations",
                    "Ferum Accounting",
                    "Ferum Client",
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

# Optional: set role-tailored home pages (Desk) to relevant workspaces
role_home_page = {
    "Project Manager": "/app/workspace/Управление проектами",
    "Office Manager": "/app/workspace/Сервисные операции",
    "Service Engineer": "/app/workspace/Инженер",
}

# Permission hooks to unify access rules across key DocTypes
permission_query_conditions = {
    "Project": "ferum_custom.ferum_custom.permissions.project_get_permission_query_conditions",
    "Timesheet": "ferum_custom.ferum_custom.permissions.timesheet_get_permission_query_conditions",

    "Invoice": "ferum_custom.security_pqc_rules.invoice_pqc",
    "Payment": "ferum_custom.security_pqc_rules.payment_pqc",
    "Counterparty": "ferum_custom.security_pqc_rules.counterparty_pqc",
    "Contract": "ferum_custom.security_pqc_rules.contract_pqc",
    "Service Report": "ferum_custom.security_pqc_rules.service_report_pqc",
    "Service Act": "ferum_custom.security_pqc_rules.service_act_pqc",
    "Payment Allocation": "ferum_custom.security_pqc_rules.payment_allocation_pqc",
    "Data Issue": "ferum_custom.security_pqc_rules.data_issue_pqc",
}

has_permission = {
    "Project": "ferum_custom.ferum_custom.permissions.project_has_permission",
    "Timesheet": "ferum_custom.ferum_custom.permissions.timesheet_has_permission",

    "Invoice": "ferum_custom.security_pqc_rules.default_has_permission",
    "Payment": "ferum_custom.security_pqc_rules.default_has_permission",
    "Counterparty": "ferum_custom.security_pqc_rules.default_has_permission",
    "Contract": "ferum_custom.security_pqc_rules.default_has_permission",
    "Service Report": "ferum_custom.security_pqc_rules.default_has_permission",
    "Service Act": "ferum_custom.security_pqc_rules.default_has_permission",
    "Data Issue": "ferum_custom.security_pqc_rules.default_has_permission",
}
