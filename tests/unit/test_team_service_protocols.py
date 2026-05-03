from pathlib import Path

from minicliagent.app.team_service import TeamService
from minicliagent.core.team.bus import MessageBus


def test_team_service_protocol_requests_have_request_ids(tmp_path: Path) -> None:
    service = TeamService(bus=MessageBus(tmp_path))

    shutdown = service.send_shutdown_request("lead", "worker", "stop")
    approval = service.send_plan_approval_request("lead", "worker", "approve")
    claim = service.send_task_claim("worker", "lead", "claim")

    assert shutdown.request_id.startswith("req-")
    assert approval.request_id.startswith("req-")
    assert claim.request_id.startswith("req-")
