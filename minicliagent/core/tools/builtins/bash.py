from __future__ import annotations

from pathlib import Path

from minicliagent.core.tools.models import ToolResult
from minicliagent.infra.shell.runner import ShellRunner


def run_bash_command(workspace_root: Path, command: str) -> ToolResult:
    runner = ShellRunner(workspace_root=workspace_root)
    return runner.run(command)
