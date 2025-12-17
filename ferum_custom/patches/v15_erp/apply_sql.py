"""Execute ordered raw SQL patches for ERP data model refactor.

Adds company scoping, constraints, triggers, indexes, and performance helpers.
Idempotent and safe on reruns.
"""

from __future__ import annotations

from pathlib import Path

import frappe


def _read_sql(relpath: str) -> str:
    base = Path(frappe.get_app_path("ferum_custom"))  # apps/ferum_custom/ferum_custom
    sql_path = base / "patches" / "v15_erp" / relpath
    if not sql_path.exists():
        return ""
    return sql_path.read_text(encoding="utf-8")


def execute():
    # Only run on PostgreSQL-backed sites. Skip gracefully on MariaDB/MySQL.
    db_type = getattr(getattr(frappe, "db", None), "db_type", None) or getattr(
        frappe.conf, "db_type", None
    )
    if str(db_type).lower() not in {"postgres", "postgresql"}:
        # Avoid hard failure on non-Postgres sites
        try:
            # Log to patches output if available
            frappe.logger().info(
                "ferum_custom.v15_erp.apply_sql: skipping SQL patches on non-Postgres db_type=%s",
                db_type,
            )
        except Exception:
            pass
        return

    files = [
        "001_multi_company.sql",
        "002_rls.sql",
        "010_counterparty_constraints.sql",
        "011_project_constraints.sql",
        "020_contract_constraints.sql",
        "021_contract_stage_constraints.sql",
        "022_service_act_constraints.sql",
        "030_service_constraints.sql",
        "040_invoice_constraints.sql",
        "041_payment_constraints.sql",
        "042_triggers.sql",
        "043_partitions.sql",
        "050_quality_helpers.sql",
        "060_performance.sql",
    ]
    for fname in files:
        sql = _read_sql(fname)
        if not sql:
            continue
        for stmt in [sql]:
            frappe.db.sql(stmt)
