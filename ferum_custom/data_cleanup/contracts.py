from __future__ import annotations

from typing import Iterable

import frappe

from ferum_custom.ferum_custom.utils import get_logger

LOGGER = get_logger(__name__)


def _normalized_number(contract_no: str, year: str | None) -> str:
    clean = "".join(ch for ch in (contract_no or "") if str(ch).isalnum())
    if year:
        clean = f"{clean}{year}"
    return clean.upper()


def _log_issue(entity: str, entity_id: str, severity: str, message: str) -> None:
    try:
        if frappe.db.exists(
            "Data Issue",
            {
                "entity": entity,
                "entity_id": entity_id,
                "severity": severity,
                "message": message,
            },
        ):
            return
        issue = frappe.get_doc(
            {
                "doctype": "Data Issue",
                "entity": entity,
                "entity_id": entity_id,
                "severity": severity,
                "message": message,
                "detected_at": frappe.utils.now_datetime(),
            }
        )
        issue.insert(ignore_permissions=True)
    except Exception:
        LOGGER.error("Failed to log Data Issue for %s %s", entity, entity_id)


def normalize_contracts() -> None:
    """Idempotent normalization of contract numbers and statuses."""
    contracts = frappe.get_all(
        "Contract",
        fields=["name", "contract_no", "contract_year", "company", "status", "contract_no_normalized"],
    )
    seen: dict[tuple[str, str], str] = {}
    for c in contracts:
        company = c.get("company")
        number = c.get("contract_no") or ""
        year = c.get("contract_year") or ""
        normalized = _normalized_number(number, year)
        if not normalized:
            continue
        key = (company or "", normalized)
        if seen.get(key):
            _log_issue(
                "Contract",
                c["name"],
                "Medium",
                f"Duplicate normalized contract number {normalized} for {company}",
            )
        else:
            seen[key] = c["name"]
        if c.get("contract_no_normalized") != normalized:
            frappe.db.set_value("Contract", c["name"], "contract_no_normalized", normalized)
