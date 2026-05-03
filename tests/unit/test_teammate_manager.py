from minicliagent.core.team.teammate_manager import TeammateManager


def test_teammate_manager_add_and_update_member() -> None:
    manager = TeammateManager()

    manager.add_member("worker", "coder")
    manager.set_status("worker", "working")
    members = manager.list_members()

    assert len(members) == 1
    assert members[0].name == "worker"
    assert members[0].role == "coder"
    assert members[0].status == "working"
