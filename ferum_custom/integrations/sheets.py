from __future__ import annotations

from typing import Any

import frappe

from ferum_custom.ferum_custom.integrations.google import (
    SERVICE_ACCOUNT_SCOPE_SHEETS,
    build_service_account_credentials,
)
from ferum_custom.ferum_custom.metrics import inc as metrics_inc
from ferum_custom.ferum_custom.settings import get_setting, is_feature_enabled
from ferum_custom.ferum_custom.utils import get_users_by_roles

try:
    from googleapiclient.discovery import build  # type: ignore[import-untyped]
    from googleapiclient.errors import HttpError  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    build = None  # type: ignore[assignment]
    HttpError = None  # type: ignore[assignment]

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
FATAL_STATUS_CODES = {401, 403, 404}


def _notify_admins(subject: str, message: str) -> None:
    try:
        recipients = list(get_users_by_roles(["System Manager", "Chief Accountant"]))
        if recipients:
            frappe.sendmail(recipients=recipients, subject=subject, message=message)
    except Exception:
        pass


def _sheets_service():
    if build is None:
        return None
    try:
        creds = build_service_account_credentials([SERVICE_ACCOUNT_SCOPE_SHEETS])
        if not creds:
            return None
        return build("sheets", "v4", credentials=creds)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Sheets service init failed")
        _notify_admins(
            "Sheets service init failed",
            "Google Sheets service initialization failed. Check Ferum Custom settings and credentials.",
        )
        return None


def _http_status(exc: Exception) -> int | None:
    if HttpError and isinstance(exc, HttpError):
        resp = getattr(exc, "resp", None)
        if resp:
            return getattr(resp, "status", None)
    return None


def _classify_failure(exc: Exception) -> tuple[str, str]:
    status = _http_status(exc)
    if status in RETRYABLE_STATUS_CODES:
        return "retry", f"HTTP {status}"
    if status in FATAL_STATUS_CODES:
        return "fatal", f"HTTP {status}"
    return "unknown", str(exc)


def append_rows(
    spreadsheet_id: str, range_name: str, values: list[list[Any]]
) -> dict[str, Any] | None:
    """Appends rows to a Google Sheet. Returns response on success."""
    if not is_feature_enabled("enable_google_sheets_sync"):
        return None
    service = _sheets_service()
    if not service:
        return None

    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )
        metrics_inc("ferum_integration_sheets_append_total", {"result": "success"})
        return result
    except Exception as exc:
        frappe.log_error(frappe.get_traceback(), f"Sheets append failed: {exc}")
        category, context = _classify_failure(exc)
        _notify_admins(
            "Sheets append failed",
            f"Failed to append rows to Google Sheet {spreadsheet_id}. Error: {context}",
        )
        metrics_inc(
            "ferum_integration_sheets_append_total", {"result": "error", "category": category}
        )
        return None


def update_rows(
    spreadsheet_id: str, range_name: str, values: list[list[Any]]
) -> dict[str, Any] | None:
    """Updates rows in a Google Sheet. Returns response on success."""
    if not is_feature_enabled("enable_google_sheets_sync"):
        return None
    service = _sheets_service()
    if not service:
        return None

    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )
        metrics_inc("ferum_integration_sheets_update_total", {"result": "success"})
        return result
    except Exception as exc:
        frappe.log_error(frappe.get_traceback(), f"Sheets update failed: {exc}")
        category, context = _classify_failure(exc)
        _notify_admins(
            "Sheets update failed",
            f"Failed to update rows in Google Sheet {spreadsheet_id}. Error: {context}",
        )
        metrics_inc(
            "ferum_integration_sheets_update_total", {"result": "error", "category": category}
        )
        return None


def read_range(spreadsheet_id: str, range_name: str) -> list[list[Any]] | None:
    """Reads a range of data from a Google Sheet. Returns values on success."""
    if not is_feature_enabled("enable_google_sheets_sync"):
        return None
    service = _sheets_service()
    if not service:
        return None

    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        metrics_inc("ferum_integration_sheets_read_total", {"result": "success"})
        return result.get("values")
    except Exception as exc:
        frappe.log_error(frappe.get_traceback(), f"Sheets read failed: {exc}")
        category, context = _classify_failure(exc)
        _notify_admins(
            "Sheets read failed",
            f"Failed to read range {range_name} from Google Sheet {spreadsheet_id}. Error: {context}",
        )
        metrics_inc(
            "ferum_integration_sheets_read_total", {"result": "error", "category": category}
        )
        return None


def healthcheck() -> dict[str, Any]:
    """Return health information for the Sheets integration, including read/write verification (if sheet is configured)."""
    if not is_feature_enabled("enable_google_sheets_sync"):
        try:
            metrics_inc("ferum_integration_sheets_health_total", {"result": "disabled"})
        except Exception:
            pass
        return {"status": "disabled", "message": "Sheets sync feature flag disabled"}

    if build is None:
        try:
            metrics_inc(
                "ferum_integration_sheets_health_total",
                {"result": "error", "reason": "missing_client"},
            )
        except Exception:
            pass
        return {"status": "error", "message": "google-api-python-client is not installed"}

    spreadsheet_id = get_setting("google_sheet_id")  # Assuming a setting for sheet ID
    if not spreadsheet_id:
        try:
            metrics_inc(
                "ferum_integration_sheets_health_total",
                {"result": "warning", "reason": "no_sheet_id_configured"},
            )
        except Exception:
            pass
        return {
            "status": "warning",
            "message": "Google Sheet ID is not configured. Basic connectivity only.",
        }

    service = _sheets_service()
    if not service:
        try:
            metrics_inc(
                "ferum_integration_sheets_health_total",
                {"result": "error", "reason": "init_failed"},
            )
        except Exception:
            pass
        return {"status": "error", "message": "Failed to initialise Sheets client"}

    # Attempt to read a small range to verify connectivity and permissions
    test_range = "Sheet1!A1"
    try:
        service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=test_range
        ).execute()
        try:
            metrics_inc("ferum_integration_sheets_health_total", {"result": "ok"})
        except Exception:
            pass
        return {"status": "ok", "message": "Successfully connected to Google Sheets."}
    except Exception as exc:
        category, context = _classify_failure(exc)
        _notify_admins(
            "Sheets healthcheck failed",
            f"Failed to access Google Sheet {spreadsheet_id} for health check. Error: {context}",
        )
        try:
            metrics_inc(
                "ferum_integration_sheets_health_total",
                {"result": "error", "reason": category or "exception"},
            )
        except Exception:
            pass
        return {
            "status": "error",
            "message": f"Unable to access Google Sheet {spreadsheet_id} ({context})",
            "category": category,
        }
