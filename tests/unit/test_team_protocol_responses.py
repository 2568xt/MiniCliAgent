from minicliagent.core.team.protocols import (
    create_plan_approval_response,
    create_shutdown_response,
    create_task_claim_result,
)


def test_protocol_response_factories_preserve_request_id() -> None:
    shutdown = create_shutdown_response("worker", "lead", "ok", request_id="req-1")
    approval = create_plan_approval_response("worker", "lead", "approved", request_id="req-2")
    claim = create_task_claim_result("lead", "worker", "claimed", request_id="req-3")

    assert shutdown.request_id == "req-1"
    assert approval.request_id == "req-2"
    assert claim.request_id == "req-3"
