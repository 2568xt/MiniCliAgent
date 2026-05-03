# MiniCLIAgent Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first industrialized MiniCLIAgent product skeleton with a real Python package, Anthropic-first provider abstraction, ToolRegistry, base runtime loop, CLI entrypoint, and tests.

**Architecture:** Create a new `minicliagent/` package at repository root and keep the tutorial repository as reference input only. The implementation uses a layered structure (`CLI / App / Core / Infra`) and isolates Anthropic-specific API integration behind a provider adapter so the runtime and tool system stay provider-agnostic.

**Tech Stack:** Python 3.11+, Anthropic SDK, python-dotenv, pytest, dataclasses, pathlib, argparse

---

### Task 1: Create Product Skeleton and Packaging

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.env.example`
- Create: `minicliagent/__init__.py`
- Create: `minicliagent/cli/__init__.py`
- Create: `minicliagent/app/__init__.py`
- Create: `minicliagent/core/__init__.py`
- Create: `minicliagent/infra/__init__.py`
- Test: `tests/unit/test_package_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
from importlib import import_module


def test_package_modules_import() -> None:
    assert import_module("minicliagent")
    assert import_module("minicliagent.cli")
    assert import_module("minicliagent.app")
    assert import_module("minicliagent.core")
    assert import_module("minicliagent.infra")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_package_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'minicliagent'`

- [ ] **Step 3: Write minimal implementation**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "minicliagent"
version = "0.1.0"
description = "Industrial local CLI coding agent harness"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "anthropic>=0.25.0",
  "python-dotenv>=1.0.0",
]
```

```python
__all__ = ["__version__"]
__version__ = "0.1.0"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_package_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md .env.example minicliagent tests/unit/test_package_smoke.py
git commit -m "feat: scaffold minicliagent package"
```

### Task 2: Add Typed Settings and Workspace State Layout

**Files:**
- Create: `minicliagent/core/config/models.py`
- Create: `minicliagent/core/config/settings.py`
- Create: `minicliagent/infra/fs/safe_paths.py`
- Create: `tests/unit/test_settings.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from minicliagent.core.config.settings import Settings


def test_settings_build_workspace_state_paths(tmp_path: Path) -> None:
    settings = Settings.from_env({
        "MINICLIAGENT_WORKSPACE": str(tmp_path),
        "MINICLIAGENT_MODEL": "claude-test",
    })

    assert settings.workspace_root == tmp_path
    assert settings.state_root == tmp_path / ".minicliagent"
    assert settings.sessions_dir == settings.state_root / "sessions"
    assert settings.tasks_dir == settings.state_root / "tasks"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_settings.py -v`
Expected: FAIL with `ModuleNotFoundError` for settings module

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    model: str
    workspace_root: Path
    state_root: Path
    sessions_dir: Path
    tasks_dir: Path
    team_dir: Path
    worktrees_dir: Path
    logs_dir: Path

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "Settings":
        workspace_root = Path(env.get("MINICLIAGENT_WORKSPACE", ".")).resolve()
        state_root = workspace_root / ".minicliagent"
        return cls(
            model=env.get("MINICLIAGENT_MODEL", "claude-3-7-sonnet-latest"),
            workspace_root=workspace_root,
            state_root=state_root,
            sessions_dir=state_root / "sessions",
            tasks_dir=state_root / "tasks",
            team_dir=state_root / "team",
            worktrees_dir=state_root / "worktrees",
            logs_dir=state_root / "logs",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_settings.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add minicliagent/core/config minicliagent/infra/fs tests/unit/test_settings.py
git commit -m "feat: add typed settings and state layout"
```

### Task 3: Build Tool Models and ToolRegistry

**Files:**
- Create: `minicliagent/core/tools/models.py`
- Create: `minicliagent/core/tools/registry.py`
- Create: `tests/unit/test_tool_registry.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest

from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.tools.registry import ToolRegistry


def test_tool_registry_registers_and_dispatches() -> None:
    registry = ToolRegistry()

    registry.register(
        ToolSpec(
            name="echo",
            description="Echo input",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            handler=lambda text: ToolResult(content=text),
            tags={"test"},
        )
    )

    result = registry.execute("echo", {"text": "hello"})

    assert result.content == "hello"


def test_tool_registry_rejects_duplicate_names() -> None:
    registry = ToolRegistry()
    spec = ToolSpec(
        name="echo",
        description="Echo input",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=lambda: ToolResult(content="ok"),
        tags=set(),
    )

    registry.register(spec)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(spec)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_tool_registry.py -v`
Expected: FAIL with missing `ToolRegistry` / `ToolSpec`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolResult:
    content: str
    is_error: bool = False


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., ToolResult]
    tags: set[str] = field(default_factory=set)
```

```python
class ToolRegistry:
    def __init__(self) -> None:
        self._tools = {}

    def register(self, spec):
        if spec.name in self._tools:
            raise ValueError(f"Tool '{spec.name}' already registered")
        self._tools[spec.name] = spec

    def execute(self, name: str, payload: dict):
        return self._tools[name].handler(**payload)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_tool_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add minicliagent/core/tools tests/unit/test_tool_registry.py
git commit -m "feat: add tool registry core"
```

### Task 4: Add Provider Abstraction and Anthropic Adapter

**Files:**
- Create: `minicliagent/core/llm/types.py`
- Create: `minicliagent/core/llm/base.py`
- Create: `minicliagent/core/llm/tool_adapter.py`
- Create: `minicliagent/core/llm/anthropic_provider.py`
- Create: `tests/unit/test_tool_adapter.py`

- [ ] **Step 1: Write the failing test**

```python
from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.llm.tool_adapter import tool_specs_to_anthropic


def test_tool_specs_to_anthropic_shape() -> None:
    specs = [
        ToolSpec(
            name="echo",
            description="Echo input",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            handler=lambda text: ToolResult(content=text),
            tags={"test"},
        )
    ]

    payload = tool_specs_to_anthropic(specs)

    assert payload == [
        {
            "name": "echo",
            "description": "Echo input",
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_tool_adapter.py -v`
Expected: FAIL with missing adapter module

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelRequest:
    system: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = field(default_factory=list)
    max_tokens: int = 4096
```

```python
def tool_specs_to_anthropic(specs):
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.input_schema,
        }
        for spec in specs
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_tool_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add minicliagent/core/llm tests/unit/test_tool_adapter.py
git commit -m "feat: add llm provider abstraction"
```

### Task 5: Implement Base Infra Tools

**Files:**
- Create: `minicliagent/infra/shell/runner.py`
- Create: `minicliagent/core/tools/builtins/files.py`
- Create: `minicliagent/core/tools/builtins/bash.py`
- Create: `tests/unit/test_safe_file_tools.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from minicliagent.core.tools.builtins.files import read_text_file


def test_read_text_file_rejects_workspace_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("bad")

    result = read_text_file(
        workspace_root=tmp_path,
        path="../outside.txt",
    )

    assert result.is_error is True
    assert "escapes workspace" in result.content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_safe_file_tools.py -v`
Expected: FAIL because `read_text_file` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path

from minicliagent.core.tools.models import ToolResult


def safe_workspace_path(workspace_root: Path, relative_path: str) -> Path:
    candidate = (workspace_root / relative_path).resolve()
    if not candidate.is_relative_to(workspace_root.resolve()):
        raise ValueError(f"Path escapes workspace: {relative_path}")
    return candidate


def read_text_file(workspace_root: Path, path: str) -> ToolResult:
    try:
        file_path = safe_workspace_path(workspace_root, path)
        return ToolResult(content=file_path.read_text())
    except Exception as exc:
        return ToolResult(content=str(exc), is_error=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_safe_file_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add minicliagent/infra/shell minicliagent/core/tools/builtins tests/unit/test_safe_file_tools.py
git commit -m "feat: add safe file and shell tools"
```

### Task 6: Implement Runtime Loop with Fake-Provider Test

**Files:**
- Create: `minicliagent/core/runtime/message_store.py`
- Create: `minicliagent/core/runtime/agent_runtime.py`
- Create: `tests/integration/test_agent_runtime_loop.py`

- [ ] **Step 1: Write the failing test**

```python
from minicliagent.core.llm.types import ModelRequest, ModelResponse, TextBlock, ToolCall
from minicliagent.core.runtime.agent_runtime import AgentRuntime
from minicliagent.core.tools.models import ToolResult, ToolSpec
from minicliagent.core.tools.registry import ToolRegistry


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def create_response(self, request: ModelRequest) -> ModelResponse:
        self.calls += 1
        if self.calls == 1:
            return ModelResponse(
                stop_reason="tool_use",
                text="",
                tool_calls=[ToolCall(id="tool-1", name="echo", input={"text": "hello"})],
            )
        return ModelResponse(
            stop_reason="end_turn",
            text="done",
            tool_calls=[],
        )


def test_agent_runtime_executes_tool_calls_until_end_turn() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo",
            description="Echo input",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
            handler=lambda text: ToolResult(content=text),
            tags={"test"},
        )
    )

    runtime = AgentRuntime(provider=FakeProvider(), tool_registry=registry, system_prompt="system")
    result = runtime.run_turn(session_id="s1", user_input="say hello")

    assert result.output_text == "done"
    assert len(result.messages) >= 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_agent_runtime_loop.py -v`
Expected: FAIL with missing runtime or model response types

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class ModelResponse:
    stop_reason: str
    text: str
    tool_calls: list[ToolCall]
```

```python
class AgentRuntime:
    def __init__(self, provider, tool_registry, system_prompt: str) -> None:
        self.provider = provider
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self._messages = {}

    def run_turn(self, session_id: str, user_input: str | None = None):
        messages = self._messages.setdefault(session_id, [])
        if user_input:
            messages.append({"role": "user", "content": user_input})
        while True:
            response = self.provider.create_response(
                ModelRequest(system=self.system_prompt, messages=list(messages), tools=[], max_tokens=4096)
            )
            messages.append({"role": "assistant", "content": response.text})
            if response.stop_reason != "tool_use":
                return RuntimeTurnResult(output_text=response.text, messages=list(messages))
            for call in response.tool_calls:
                result = self.tool_registry.execute(call.name, call.input)
                messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id, "content": result.content}]})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_agent_runtime_loop.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add minicliagent/core/runtime minicliagent/core/llm/tests tests/integration/test_agent_runtime_loop.py
git commit -m "feat: add base agent runtime loop"
```

### Task 7: Add CLI Entry for Interactive Prompting

**Files:**
- Create: `minicliagent/cli/main.py`
- Create: `tests/integration/test_cli_smoke.py`

- [ ] **Step 1: Write the failing test**

```python
from minicliagent.cli.main import build_parser


def test_cli_parser_accepts_prompt_argument() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--prompt", "hello"])

    assert args.command == "run"
    assert args.prompt == "hello"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_cli_smoke.py -v`
Expected: FAIL with missing CLI parser

- [ ] **Step 3: Write minimal implementation**

```python
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="minicliagent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--prompt", required=True)
    return parser
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_cli_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add minicliagent/cli/main.py tests/integration/test_cli_smoke.py
git commit -m "feat: add CLI entrypoint"
```

### Task 8: Run Full Foundation Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add usage documentation**

```md
## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pytest
python -m minicliagent.cli.main run --prompt "hello"
```
```

- [ ] **Step 2: Run focused verification**

Run: `pytest tests/unit tests/integration -v`
Expected: PASS with all new tests green

- [ ] **Step 3: Run packaging verification**

Run: `python -m minicliagent.cli.main run --prompt "hello" --help`
Expected: exit code 0 and CLI usage output

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add foundation usage guide"
```

