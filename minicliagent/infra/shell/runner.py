from __future__ import annotations

import subprocess
from pathlib import Path

from minicliagent.core.tools.models import ToolResult


class ShellRunner:
    def __init__(self, workspace_root: Path, timeout_seconds: int = 120) -> None:
        self.workspace_root = workspace_root
        self.timeout_seconds = timeout_seconds

    def run(self, command: str) -> ToolResult:
        dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
        if any(token in command for token in dangerous):
            return ToolResult(content="Error: Dangerous command blocked", is_error=True)
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(content=f"Error: Timeout ({self.timeout_seconds}s)", is_error=True)

        output = (result.stdout + result.stderr).strip() or "(no output)"
        return ToolResult(content=output[:50000], is_error=result.returncode != 0)
