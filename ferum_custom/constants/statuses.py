"""Shared status constants for Issue and Service Request flows."""

from __future__ import annotations

# Canonical statuses for standard ERPNext Issue
ISSUE_STATUSES: set[str] = {"Open", "Replied", "On Hold", "Resolved", "Closed"}

# Canonical statuses for Service Request (custom)
SERVICE_REQUEST_STATUSES: set[str] = {"Open", "In Progress", "Completed", "Closed", "Cancelled"}

# Active statuses used in the Telegram bot lists
ACTIVE_STATUSES: set[str] = {"Open", "Replied", "In Progress"}

# Final/terminal statuses where actions (start/done) should be hidden
FINAL_STATUSES: set[str] = {"Resolved", "Closed", "Completed", "Cancelled"}

# Mapping of friendly actions to target statuses per doctype
ACTION_TO_STATUS_ISSUE = {
    "start": "Replied",
    "accept": "Replied",
    "in_progress": "Replied",
    "done": "Resolved",
    "complete": "Resolved",
    "finish": "Resolved",
    "close": "Closed",
}

ACTION_TO_STATUS_SERVICE = {
    "start": "In Progress",
    "accept": "In Progress",
    "in_progress": "In Progress",
    "done": "Completed",
    "complete": "Completed",
    "finish": "Completed",
    "close": "Closed",
}

