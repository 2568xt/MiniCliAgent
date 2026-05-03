from importlib import import_module


def test_package_modules_import() -> None:
    assert import_module("minicliagent")
    assert import_module("minicliagent.cli")
    assert import_module("minicliagent.app")
    assert import_module("minicliagent.core")
    assert import_module("minicliagent.infra")
