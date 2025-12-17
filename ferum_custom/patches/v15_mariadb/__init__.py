"""Shared helpers for MariaDB SQL patches."""

from __future__ import annotations

import os
from collections.abc import Iterable

import frappe
from pymysql.err import OperationalError


def iter_sql_files(filenames: Iterable[str] | None = None):
    """Yield (filename, sql_text) tuples for requested files or all .sql files."""
    base_path = frappe.get_app_path("ferum_custom", "patches", "v15_mariadb")

    if filenames is None:
        items = sorted(name for name in os.listdir(base_path) if name.endswith(".sql"))
    else:
        items = filenames

    for name in items:
        path = os.path.join(base_path, name)
        if not os.path.isfile(path):
            continue

        with open(path, encoding="utf-8") as handle:
            sql = handle.read().strip()

        if sql:
            yield name, sql


def run_sql_file(filename: str) -> None:
    """Execute a single SQL patch file."""
    for _, sql in iter_sql_files([filename]):
        execute_sql_block(sql)


def execute_sql_block(sql: str) -> None:
    """Execute a block of SQL statements separated by semicolons."""
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    for statement in statements:
        try:
            frappe.db.sql(statement)
        except OperationalError as exc:
            message = exc.args[1] if len(exc.args) > 1 else ""
            message_l = message.lower()
            if "already exists" in message_l or "duplicate" in message_l:
                continue
            raise
