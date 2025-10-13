from __future__ import annotations

"""Site operations helpers for one-off maintenance tasks.

Run with:
  bench --site <site> execute ferum_custom.ferum_custom.site_ops.apply_ru_workspaces
"""

from typing import Iterable

import frappe
from frappe.utils import cint
from ferum_custom.ferum_custom.settings import is_feature_enabled


def _ensure_dashboard_chart(
    name: str,
    *,
    document_type: str,
    chart_type: str = "Group By",
    type_: str = "Pie",
    group_by_type: str = "Count",
    group_by_based_on: str | None = None,
    value_based_on: str | None = None,
    module: str = "Ferum Custom",
    is_public: int = 1,
) -> None:
    if frappe.db.exists("Dashboard Chart", name):
        doc = frappe.get_doc("Dashboard Chart", name)
        changed = False
        if getattr(doc, "document_type", None) != document_type:
            doc.document_type = document_type
            changed = True
        if getattr(doc, "chart_type", None) != chart_type:
            doc.chart_type = chart_type
            changed = True
        if getattr(doc, "type", None) != type_:
            doc.type = type_
            changed = True
        if getattr(doc, "group_by_type", None) != group_by_type:
            doc.group_by_type = group_by_type
            changed = True
        if getattr(doc, "group_by_based_on", None) != group_by_based_on:
            doc.group_by_based_on = group_by_based_on
            changed = True
        if getattr(doc, "value_based_on", None) != value_based_on:
            doc.value_based_on = value_based_on
            changed = True
        if cint(getattr(doc, "is_public", 0)) != cint(is_public):
            doc.is_public = is_public
            changed = True
        if getattr(doc, "module", None) != module:
            doc.module = module
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return

    frappe.get_doc(
        {
            "doctype": "Dashboard Chart",
            "chart_name": name,
            "document_type": document_type,
            "chart_type": chart_type,
            "type": type_,
            "group_by_type": group_by_type,
            "group_by_based_on": group_by_based_on,
            "value_based_on": value_based_on,
            "aggregate_function_based_on": value_based_on,
            "filters_json": "[]",
            "is_public": is_public,
            "module": module,
        }
    ).insert(ignore_permissions=True)


def _hide_workspaces(names: Iterable[str]) -> None:
    for name in names:
        if frappe.db.exists("Workspace", name):
            ws = frappe.get_cached_doc("Workspace", name)
            values = {}
            if cint(ws.public) != 0:
                values["public"] = 0
            if cint(getattr(ws, "is_hidden", 0)) != 1:
                values["is_hidden"] = 1
            if values:
                frappe.db.set_value("Workspace", name, values)


def _ensure_shortcut(ws, *, label: str, type_: str, url: str | None = None, link_to: str | None = None) -> None:
    # Find existing by label
    existing = None
    for sc in ws.shortcuts:  # type: ignore[attr-defined]
        if sc.label == label:
            existing = sc
            break
    if existing:
        changed = False
        if existing.type != type_:
            existing.type = type_
            changed = True
        if (existing.url or None) != (url or None):
            existing.url = url
            changed = True
        if (existing.link_to or None) != (link_to or None):
            existing.link_to = link_to
            changed = True
        if changed:
            ws.save(ignore_permissions=True)
        return

    sc = ws.append("shortcuts", {})  # type: ignore[attr-defined]
    sc.label = label
    sc.type = type_
    sc.url = url
    sc.link_to = link_to
    ws.save(ignore_permissions=True)


def apply_ru_workspaces() -> dict:
    """Apply RU-only alignment to Workspaces and Charts on current site.

    - Hide English workspaces (Chief Accountant, Office Manager, Project Manager, Accounting, Engineer)
    - Create/update RU charts: "Открытые заявки по статусам", "Счета по проектам"
    - Align shortcuts in "Управление проектами"
    - Ensure Department Head has issue oversight reports
    """

    # Charts (create first to satisfy Workspace link validation)
    _ensure_dashboard_chart(
        "Открытые заявки по статусам",
        document_type="Issue",
        type_="Pie",
        group_by_type="Count",
        group_by_based_on="status",
    )
    _ensure_dashboard_chart(
        "Счета по проектам",
        document_type="Sales Invoice",
        type_="Bar",
        group_by_type="Sum",
        group_by_based_on="project",
        value_based_on="base_grand_total",
    )

    # Hide EN workspaces
    _hide_workspaces(["Chief Accountant", "Office Manager", "Project Manager", "Accounting", "Engineer"])

    # Department Head shortcuts
    if frappe.db.exists("Workspace", "Руководитель отдела"):
        ws = frappe.get_doc("Workspace", "Руководитель отдела")
        _ensure_shortcut(ws, label="Нераспределенные заявки", type_="Report", link_to="Unassigned Issues")
        _ensure_shortcut(ws, label="Открытые заявки по инженерам", type_="Report", link_to="Open Issues by Engineer")

    # Project Management alignment
    if frappe.db.exists("Workspace", "Управление проектами"):
        ws = frappe.get_doc("Workspace", "Управление проектами")
        _ensure_shortcut(ws, label="Проекты", type_="DocType", link_to="Project")
        _ensure_shortcut(ws, label="Новый проект", type_="URL", url="/app/project/new")
        _ensure_shortcut(ws, label="Заявки", type_="URL", url="/app/issue")
        _ensure_shortcut(ws, label="Сервисные отчеты", type_="DocType", link_to="Timesheet")
        _ensure_shortcut(ws, label="Объекты", type_="DocType", link_to="Asset")
        _ensure_shortcut(ws, label="Счета", type_="URL", url="/app/sales-invoice")
        _ensure_shortcut(ws, label="Новый счет (клиент)", type_="URL", url="/app/sales-invoice/new")
        _ensure_shortcut(ws, label="Новый счет (субподрядчик)", type_="URL", url="/app/purchase-invoice/new")
        if frappe.db.exists("Report", "Issues by Project"):
            _ensure_shortcut(ws, label="Заявки по проектам", type_="Report", link_to="Issues by Project")

    # Service Operations: use standard Issue reports
    if frappe.db.exists("Workspace", "Сервисные операции"):
        ws = frappe.get_doc("Workspace", "Сервисные операции")
        _ensure_shortcut(ws, label="Нераспределенные заявки", type_="Report", link_to="Unassigned Issues")
        _ensure_shortcut(ws, label="Открытые заявки по инженерам", type_="Report", link_to="Open Issues by Engineer")

    frappe.clear_cache()
    return {"status": "ok"}


@frappe.whitelist()
def backup_to_drive() -> dict:
    """Создать резервную копию БД и выгрузить архив в Google Drive.

    Размещение: /<site>/Backups/<filename>.
    Использует существующую интеграцию Google Drive.
    """
    from frappe.utils.backups import new_backup
    from ferum_custom.ferum_custom.integrations.drive import upload_bytes

    # Создаём бэкап (возвращает путь к файлу .sql.gz)
    bkp = new_backup(ignore_files=True)
    filepath = getattr(bkp, "backup_path", None) or getattr(bkp, "backup_path_db", None)
    if not filepath:
        return {"status": "skipped", "reason": "no-backup-path"}

    if not is_feature_enabled("enable_google_drive_sync"):
        return {"status": "skipped", "reason": "drive-disabled"}

    try:
        with open(filepath, "rb") as f:
            content = f.read()
        site_name = frappe.local.site or frappe.utils.get_site_name(frappe.local.site_path)
        parts = [site_name, "Backups"]
        filename = filepath.split("/")[-1]
        file_id = upload_bytes(parts, filename, content)
        return {"status": "ok", "file_id": file_id, "filename": filename}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Backup to Drive failed")
        return {"status": "error", "error": str(e)}
