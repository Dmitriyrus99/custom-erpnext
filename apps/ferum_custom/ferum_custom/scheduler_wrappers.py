from __future__ import annotations

import frappe


def _is_enabled(flag: str, default: bool = True) -> bool:
    """Check feature flag in site config (frappe.conf)."""
    try:
        return bool(frappe.get_conf().get(flag, default))
    except Exception:
        return default


def _enqueue(path: str, *, job_name: str, timeout: int = 900):
    """Enqueue helper on long queue with sane timeout."""
    frappe.enqueue(path, queue="long", job_name=job_name, timeout=timeout)


def daily_drive_backfill():
    """Safe wrapper for incremental Drive backfill."""
    if not _is_enabled("enable_drive_jobs", True):
        return
    _enqueue(
        "ferum_custom.ferum_custom.automation.enqueue_daily_drive_backfill_small",
        job_name="daily_drive_backfill",
        timeout=1200,
    )


def nightly_backup_to_gdrive():
    """Wrapper to push backups to GDrive on long queue."""
    if not _is_enabled("enable_backups", True):
        return
    _enqueue(
        "ferum_custom.ferum_custom.automation.run_nightly_backup_to_gdrive",
        job_name="nightly_backup_to_gdrive",
        timeout=1800,
    )


def refresh_materialized_views():
    """Refresh analytics materialized views on long queue."""
    if not _is_enabled("enable_mv_refresh", True):
        return
    _enqueue(
        "ferum_custom.ferum_custom.domain.analytics.application.refresh_all_materialized_views",
        job_name="refresh_materialized_views",
        timeout=1200,
    )


def cleanup_stg_raw():
    """Cleanup staging raw tables on long queue."""
    if not _is_enabled("enable_data_cleanup", True):
        return
    _enqueue(
        "ferum_custom.ferum_custom.data_cleanup.jobs.cleanup_stg_raw_job",
        job_name="cleanup_stg_raw",
        timeout=900,
    )


def weekly_full_backup():
    """Weekly full backup enqueued to long queue."""
    if not _is_enabled("enable_backups", True):
        return
    _enqueue(
        "ferum_custom.ferum_custom.automation.enqueue_weekly_full_backup",
        job_name="weekly_full_backup",
        timeout=1800,
    )


def test_restore_latest_backup():
    """Optional staging restore test."""
    if not _is_enabled("enable_test_restore", False):
        return
    _enqueue(
        "ferum_custom.ferum_custom.site_ops.test_restore_latest_backup",
        job_name="test_restore_latest_backup",
        timeout=1800,
    )
