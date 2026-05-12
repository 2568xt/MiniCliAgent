from __future__ import annotations

import re as _re
import subprocess
from pathlib import Path

from minicliagent.core.tools.models import ToolResult
from minicliagent.infra.sandbox.backend import detect_backend, get_backend
from minicliagent.infra.sandbox.config import SandboxConfig

DANGEROUS_PATTERNS = [
    _re.compile(r'rm\s+-rf\s+/'),
    _re.compile(r':\s*\(\s*\)\s*\{\s*:\s*\|'),
    _re.compile(r'\bmkfs\b'),
    _re.compile(r'dd\s+if=.*\bof=/dev/(?!null\b)'),
]
DANGEROUS_SUBSTRINGS_PATTERNS = [
    _re.compile(r'\b' + w + r'\b') for w in ['sudo', 'shutdown', 'reboot']
]

def is_dangerous(command: str) -> bool:
    for pattern in DANGEROUS_SUBSTRINGS_PATTERNS:
        if pattern.search(command):
            return True
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return True
    if _re.search(r'>\s*/dev/(?:sda|sdb|sdc|nvme|disk|fd\d)', command):
        return True
    return False

class ShellRunner:
    def __init__(
        self,
        workspace_root: Path,
        timeout_seconds: int = 120,
        sandbox_config: SandboxConfig | None = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.timeout_seconds = timeout_seconds
        self.sandbox_config = sandbox_config or SandboxConfig(enabled=False)
        self._sandbox_backend = self._init_sandbox_backend()

    def _init_sandbox_backend(self):
        if not self.sandbox_config.enabled:
            return get_backend("disabled")
        backend_name = self.sandbox_config.backend or detect_backend()
        try:
            return get_backend(backend_name)
        except KeyError:
            return get_backend("disabled")

    def run(self, command: str) -> ToolResult:
        if is_dangerous(command):
            return ToolResult(content="Error: Dangerous command blocked", is_error=True)

        if self._sandbox_backend.name != "disabled":
            return self._run_sandboxed(command)
        return self._run_unsandboxed(command)

    def _run_sandboxed(self, command: str) -> ToolResult:
        wrapped = self._sandbox_backend.wrap(command, self.sandbox_config)
        try:
            result = subprocess.run(
                wrapped,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(content=f"Error: Timeout ({self.timeout_seconds}s)", is_error=True)
        finally:
            self._sandbox_backend.cleanup()

        output = (result.stdout + result.stderr).strip() or "(no output)"
        return ToolResult(content=output[:50000], is_error=result.returncode != 0)

    def _run_unsandboxed(self, command: str) -> ToolResult:
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
