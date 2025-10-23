import frappe
from frappe.utils import now, get_backups_path, get_url_to_form
import os

# List of roles that are expected to have wide-ranging permissions.
# We will alert if any other role gets access to system pages/reports.
ALLOWED_ADMIN_ROLES = ["System Manager", "Administrator"]

def send_daily_overdue_report():
    """
    Scans for overdue Service Requests (past SLA) and emails a summary report
    to Project Managers and Department Heads.
    """
    overdue_requests = frappe.get_list(
        "Service Request",
        filters={"status": ["not in", ["Closed", "Cancelled"]], "sla_deadline": ["<", now()]},
        fields=["name", "title", "project", "assigned_to", "sla_deadline", "customer"],
        order_by="sla_deadline asc",
    )

    if not overdue_requests:
        frappe.log_info("No overdue service requests found.", "Daily Overdue Report")
        return

    recipients = get_report_recipients(["Project Manager", "Department Head"])
    if not recipients:
        frappe.log_error("No recipients found for Overdue Report (Roles: Project Manager, Department Head).", "Daily Overdue Report")
        return

    subject = "Ежедневный отчёт: Просроченные заявки на обслуживание"
    message = build_report_html("Просроченные заявки на обслуживание", overdue_requests)

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        doctype="Service Request",
    )
    frappe.log_info(f"Sent daily overdue report to {len(recipients)} recipients.", "Daily Overdue Report")


def send_weekly_overdue_maintenance_report():
    """
    Scans for overdue routine maintenance Service Requests and emails a summary
    to relevant managers.
    """
    overdue_maintenance = frappe.get_list(
        "Service Request",
        filters={
            "status": ["not in", ["Closed", "Cancelled"]],
            "sla_deadline": ["<", now()],
            "type": "Routine Maintenance",
        },
        fields=["name", "title", "project", "assigned_to", "sla_deadline", "customer"],
        order_by="sla_deadline asc",
    )

    if not overdue_maintenance:
        frappe.log_info("No overdue routine maintenance tasks found.", "Weekly Maintenance Report")
        return

    recipients = get_report_recipients(["Project Manager", "Department Head"])
    if not recipients:
        frappe.log_error("No recipients found for Weekly Maintenance Report (Roles: Project Manager, Department Head).", "Weekly Maintenance Report")
        return

    subject = "Еженедельный отчёт: Просроченное плановое обслуживание"
    message = build_report_html("Просроченное плановое обслуживание", overdue_maintenance)

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        message=message,
        doctype="Service Request",
    )
    frappe.log_info(f"Sent weekly overdue maintenance report to {len(recipients)} recipients.", "Weekly Maintenance Report")

def run_nightly_backup_to_gdrive():
    """
    Runs a standard bench backup and uploads the resulting file to Google Drive.
    """
    # 1. Run bench backup
    try:
        # Using --with-files to include private files as well
        backup_command = f"bench --site {frappe.local.site} backup --with-files"
        # We execute from the bench directory
        bench_path = frappe.utils.get_bench_path()
        result = frappe.utils.execute_in_shell(backup_command, cwd=bench_path, check_exit_code=True)
        frappe.log_info(f"Backup created successfully.\n{result}", "Nightly Backup")
    except Exception as e:
        frappe.log_error(f"Backup creation failed: {e}", "Nightly Backup")
        return

    # 2. Find the latest backup file
    try:
        backups_path = get_backups_path()
        files = os.listdir(backups_path)
        # Filter for .sql.gz files and find the newest one
        backup_files = [f for f in files if f.endswith("-database.sql.gz")]
        if not backup_files:
            frappe.log_error("No backup file found after running bench backup.", "Nightly Backup")
            return
        
        latest_backup_file = max(backup_files, key=lambda f: os.path.getmtime(os.path.join(backups_path, f)))
        latest_backup_path = os.path.join(backups_path, latest_backup_file)
        frappe.log_info(f"Found latest backup file: {latest_backup_path}", "Nightly Backup")
    except Exception as e:
        frappe.log_error(f"Failed to find latest backup file: {e}", "Nightly Backup")
        return

    # 3. Upload to Google Drive
    try:
        from ferum_custom.ferum_custom.integrations.drive import upload_bytes

        with open(latest_backup_path, "rb") as f:
            file_data = f.read()

        # Define a path structure in Google Drive
        drive_path_parts = ["Backups", frappe.local.site]
        
        file_id = upload_bytes(
            path_parts=drive_path_parts,
            filename=latest_backup_file,
            data=file_data,
            mime_type="application/gzip",
        )

        if file_id:
            frappe.log_info(f"Successfully uploaded backup {latest_backup_file} to Google Drive. File ID: {file_id}", "Nightly Backup")
        else:
            raise Exception("Upload function returned no file ID.")

    except Exception as e:
        frappe.log_error(f"Google Drive upload failed: {e}", "Nightly Backup")

def run_permission_audit():
    """Weekly job to audit Page and Report permissions for non-admin roles."""
    suspicious_page_perms = frappe.get_all(
        "Role Permission for Page",
        filters={"role": ["notin", ALLOWED_ADMIN_ROLES]},
        fields=["parent", "role", "page"]
    )
    
    suspicious_report_perms = frappe.get_all(
        "Role Permission for Report",
        filters={"role": ["notin", ALLOWED_ADMIN_ROLES]},
        fields=["parent", "role", "report"]
    )

    if not suspicious_page_perms and not suspicious_report_perms:
        frappe.log_info("Permission audit completed. No issues found.", "Permission Audit")
        return

    # Build the report
    message_html = "<h3>Обнаружены потенциально небезопасные права доступа</h3>"
    message_html += "<p>Следующим ролям предоставлен доступ к системным страницам или отчетам, что может быть нежелательно:</p>"

    if suspicious_page_perms:
        message_html += "<h4>Доступы к страницам:</h4><ul>"
        for perm in suspicious_page_perms:
            message_html += f"<li>Роль <b>{perm.role}</b> имеет доступ к странице <b>{perm.page}</b></li>"
        message_html += "</ul>"

    if suspicious_report_perms:
        message_html += "<h4>Доступы к отчетам:</h4><ul>"
        for perm in suspicious_report_perms:
            message_html += f"<li>Роль <b>{perm.role}</b> имеет доступ к отчету <b>{perm.report}</b></li>"
        message_html += "</ul>"
    
    message_html += "<p>Пожалуйста, проверьте эти права в разделе 'Role Permissions Manager'.</p>"

    admin_recipients = get_report_recipients(["System Manager"])
    if not admin_recipients:
        frappe.log_error("No System Manager found to send permission audit report.", "Permission Audit")
        return

    frappe.sendmail(
        recipients=admin_recipients,
        subject="[Security Audit] Обнаружены небезопасные права доступа",
        message=message_html
    )

def on_role_update_audit(doc, method):
    """Hook that triggers on Role save to check who is making the change."""
    current_user = frappe.session.user
    if current_user == "Administrator": # Often the user for scheduler actions
        return

    user_roles = frappe.get_roles(current_user)
    
    # If the user is not an admin, send an alert.
    if not set(user_roles).intersection(set(ALLOWED_ADMIN_ROLES)):
        admin_recipients = get_report_recipients(["System Manager"])
        if not admin_recipients:
            return

        subject = f"[Security Alert] Пользователь {current_user} изменил права для роли {doc.name}"
        message = f"""
            <p>Пользователь <b>{current_user}</b>, не являющийся администратором, изменил настройки для роли <b>{doc.name}</b>.</p>
            <p>Пожалуйста, проверьте внесенные изменения на соответствие политикам безопасности.</p>
            <p>Вы можете просмотреть роль по <a href=\"{get_url_to_form('Role', doc.name)}\">этой ссылке</a>.</p>
        """
        frappe.sendmail(recipients=admin_recipients, subject=subject, message=message)


# Helper Functions

def get_report_recipients(roles: list) -> list:
    """Fetch email addresses for all active users with the given roles."""
    user_names = frappe.get_users_with_role(roles)
    
    if not user_names:
        return []

    recipients = frappe.get_all(
        "User",
        filters={"name": ["in", user_names], "enabled": 1},
        fields=["email"],
        pluck="email",
    )
    return list(set(recipients)) # Return unique emails


def build_report_html(title: str, items: list) -> str:
    """Builds an HTML email body with a table of items."""
    
    header_row = "".join(f"<th>{key.replace('_', ' ').title()}</th>" for key in items[0].keys())

    body_rows = ""
    for item in items:
        row_html = "<tr>"
        for key, value in item.items():
            if key == "name":
                # Link to the document in the desk
                url = get_url_to_form(item.doctype or "Service Request", item.name)
                row_html += f'<td><a href="{url}">{value}</a></td>'
            else:
                row_html += f"<td>{frappe.utils.escape_html(str(value or ''))}</td>"
        row_html += "</tr>"
        body_rows += row_html

    return f"""
        <h3>{title}</h3>
        <p>Найдено {len(items)} просроченных задач на {now()}.</p>
        <table class="table table-bordered">
            <thead>
                <tr>{header_row}</tr>
            </thead>
            <tbody>
                {body_rows}
            </tbody>
        </table>
    """