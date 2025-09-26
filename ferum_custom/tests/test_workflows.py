from __future__ import annotations

import json
import os


def _load_fixture(relpath: str):
    base = os.path.dirname(__file__)
    path = os.path.normpath(os.path.join(base, "..", "fixtures", relpath))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_workflow(data: list[dict], name: str) -> dict:
    for wf in data:
        if wf.get("name") == name:
            return wf
    raise AssertionError(f"Workflow not found: {name}")


def test_service_request_workflow_smoke():
    data = _load_fixture("workflow.json")
    wf = _find_workflow(data, "Service Request Workflow")

    trans = {(t["state"], t["action"], t["next_state"]): t for t in wf.get("transitions", [])}

    assert ("Open", "Start Work", "In Progress") in trans
    assert trans[("Open", "Start Work", "In Progress")]["condition"] == "doc.assigned_to"

    assert ("In Progress", "Complete", "Completed") in trans
    assert trans[("In Progress", "Complete", "Completed")]["condition"] == "doc.linked_report"

    assert ("Completed", "Close", "Closed") in trans
    assert trans[("Completed", "Close", "Closed")]["allowed"] == "System Manager"


def test_service_report_workflow_smoke():
    data = _load_fixture("workflow.json")
    wf = _find_workflow(data, "Service Report Workflow")
    actions = {(t["state"], t["action"], t["next_state"]) for t in wf.get("transitions", [])}

    assert ("Draft", "Submit", "Submitted") in actions
    assert ("Submitted", "Approve", "Approved") in actions
    assert ("Approved", "Archive", "Archived") in actions
    assert ("Submitted", "Cancel", "Cancelled") in actions


def test_service_project_workflow_smoke():
    data = _load_fixture("workflow.json")
    wf = _find_workflow(data, "Service Project Workflow")
    trans = {(t["state"], t["action"], t["next_state"]): t for t in wf.get("transitions", [])}

    assert ("Planned", "Submit", "Pending Approval") in trans
    assert ("Pending Approval", "Approve", "Active") in trans
    assert trans[("Pending Approval", "Approve", "Active")]["allowed"] == "General Director"
    assert ("Active", "Complete", "Completed") in trans


def test_invoice_workflow_smoke():
    data = _load_fixture("workflow.json")
    wf = _find_workflow(data, "Invoice Workflow")
    trans = {(t["state"], t["action"], t["next_state"]): t for t in wf.get("transitions", [])}

    assert ("Draft", "Send", "Sent") in trans
    assert ("Sent", "Mark Paid", "Paid") in trans
    assert trans[("Sent", "Mark Paid", "Paid")]["allowed"] == "Chief Accountant"

