from minicliagent.core.team.protocols import (
    create_plan_approval_request,
    create_shutdown_request,
    create_task_claim,
)


def test_protocol_factories_generate_request_ids() -> None:
    shutdown = create_shutdown_request("lead", "worker", "stop")
    approval = create_plan_approval_request("lead", "worker", "approve plan")
    claim = create_task_claim("worker", "lead", "claim task")

    assert shutdown.request_id.startswith("req-")
    assert approval.request_id.startswith("req-")
    assert claim.request_id.startswith("req-")
