from ferum_custom.ferum_custom.api import service
from ferum_custom.ferum_custom.constants import statuses as status_consts


def test_resolve_target_status_issue_actions():
    target = service._resolve_target_status("Issue", action="start")  # type: ignore[attr-defined]
    assert target == "Replied"
    target = service._resolve_target_status("Issue", action="done")  # type: ignore[attr-defined]
    assert target == "Resolved"


def test_resolve_target_status_service_actions():
    target = service._resolve_target_status("Service Request", action="start")  # type: ignore[attr-defined]
    assert target == "In Progress"
    target = service._resolve_target_status("Service Request", action="done")  # type: ignore[attr-defined]
    assert target == "Completed"


def test_final_statuses_constant():
    assert "Resolved" in status_consts.FINAL_STATUSES
    assert "Open" not in status_consts.FINAL_STATUSES
