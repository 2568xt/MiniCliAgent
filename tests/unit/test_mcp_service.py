import json
import subprocess
import threading
from queue import Empty, Queue

from minicliagent.core.config.settings import Settings
from minicliagent.core.mcp.models import MCPServerConfig, MCPToolDefinition
from minicliagent.core.mcp.service import MCPToolRuntime, MCPService
from minicliagent.core.mcp.transport import MCPStdioSession
from minicliagent.core.tools.models import ToolSpec
from minicliagent.core.tools.registry import ToolRegistry


# ── Settings parsing ──────────────────────────────────────────────

def test_settings_parses_mcp_servers() -> None:
    settings = Settings.from_env({
        'MINICLIAGENT_WORKSPACE': '/tmp/work',
        'MINICLIAGENT_MCP_SERVERS': 'demo,python demo.py,prefix,timeout=7,max_return_chars=128,enabled=1,env.FOO=bar',
    })
    assert len(settings.mcp_servers) == 1
    server = settings.mcp_servers[0]
    assert server.name == 'demo'
    assert server.command == ['python', 'demo.py']
    assert server.tool_prefix == 'prefix'
    assert server.timeout_seconds == 7.0
    assert server.max_return_chars == 128
    assert server.env['FOO'] == 'bar'


def test_settings_parses_multiple_mcp_servers() -> None:
    settings = Settings.from_env({
        'MINICLIAGENT_WORKSPACE': '/tmp/work',
        'MINICLIAGENT_MCP_SERVERS': 's1,cmd1; s2,cmd2 arg,tool_s2,enabled=0',
    })
    assert len(settings.mcp_servers) == 2
    assert settings.mcp_servers[0].name == 's1'
    assert settings.mcp_servers[0].enabled is True
    assert settings.mcp_servers[1].name == 's2'
    assert settings.mcp_servers[1].enabled is False
    assert settings.mcp_servers[1].tool_prefix == 'tool_s2'


def test_settings_empty_mcp_servers() -> None:
    settings = Settings.from_env({'MINICLIAGENT_WORKSPACE': '/tmp/work'})
    assert settings.mcp_servers == []


# ── MCP Tool Spec conversion ──────────────────────────────────────

def test_tool_spec_prefixed_naming() -> None:
    server = MCPServerConfig(name='echo', command=['echo'])
    tool = MCPToolDefinition(name='say', description='say something', input_schema={'type': 'object', 'properties': {'msg': {'type': 'string'}}})
    service = MCPService([server])
    session = MCPStdioSession(server)
    spec = service._to_tool_spec(server, tool, session)
    assert spec.name == 'echo.say'
    assert spec.description == 'say something'
    assert 'mcp' in spec.tags
    assert 'echo' in spec.tags


def test_tool_spec_uses_explicit_prefix() -> None:
    server = MCPServerConfig(name='echo', command=['echo'], tool_prefix='my_prefix')
    tool = MCPToolDefinition(name='say', description='desc', input_schema={'type': 'object', 'properties': {}})
    service = MCPService([server])
    session = MCPStdioSession(server)
    spec = service._to_tool_spec(server, tool, session)
    assert spec.name == 'my_prefix.say'


# ── Conflict detection ────────────────────────────────────────────

def test_register_tools_skips_builtin_conflicts() -> None:
    server = MCPServerConfig(name='srv', command=['cmd'])
    service = MCPService([server])
    service._runtimes = [
        MCPToolRuntime(
            server=server,
            healthy=True,
            tools=[
                ToolSpec(name='bash', description='MCP bash', input_schema={}, handler=lambda: None, tags={'mcp'}),
                ToolSpec(name='srv.ok', description='no conflict', input_schema={}, handler=lambda: None, tags={'mcp'}),
            ],
        )
    ]
    registry = ToolRegistry()
    registry.register(ToolSpec(name='bash', description='builtin bash', input_schema={}, handler=lambda: None, tags={'builtin'}))

    registered = service.register_tools(registry)

    tool_names = {spec.name for spec in registry.list_specs()}
    assert 'bash' in tool_names
    assert 'srv.ok' in tool_names
    assert registered == {'srv': ['srv.ok']}


def test_register_tools_no_conflicts_when_prefix_matches() -> None:
    server = MCPServerConfig(name='srv', command=['cmd'])
    service = MCPService([server])
    service._runtimes = [
        MCPToolRuntime(
            server=server,
            healthy=True,
            tools=[
                ToolSpec(name='srv.echo', description='echo', input_schema={}, handler=lambda: None, tags={'mcp'}),
            ],
        )
    ]
    registry = ToolRegistry()

    registered = service.register_tools(registry)

    assert 'srv.echo' in {s.name for s in registry.list_specs()}
    assert registered == {'srv': ['srv.echo']}


# ── Diagnostics ───────────────────────────────────────────────────

def test_diagnostics_healthy_server() -> None:
    server = MCPServerConfig(name='demo', command=['cmd'])
    service = MCPService([server])
    service._runtimes = [
        MCPToolRuntime(
            server=server,
            healthy=True,
            tools=[ToolSpec(name='demo.t1', description='d', input_schema={}, handler=lambda: None, tags={'mcp'})],
        )
    ]
    diags = service.diagnostics()
    assert len(diags) == 1
    assert diags[0].name == 'demo'
    assert diags[0].healthy is True
    assert diags[0].tool_count == 1
    assert diags[0].error is None


def test_diagnostics_unhealthy_server() -> None:
    server = MCPServerConfig(name='broken', command=['bad'])
    service = MCPService([server])
    service._runtimes = [
        MCPToolRuntime(server=server, healthy=False, error='connection refused')
    ]
    diags = service.diagnostics()
    assert diags[0].healthy is False
    assert diags[0].error == 'connection refused'
    assert diags[0].tool_count == 0


def test_diagnostics_disabled_server() -> None:
    server = MCPServerConfig(name='off', command=['cmd'], enabled=False)
    service = MCPService([server])
    service._runtimes = [MCPToolRuntime(server=server, healthy=False)]
    diags = service.diagnostics()
    assert diags[0].enabled is False


# ── Health check ──────────────────────────────────────────────────

def test_health_check_disabled_always_false() -> None:
    server = MCPServerConfig(name='off', command=['cmd'], enabled=False)
    service = MCPService([server])
    service._runtimes = [MCPToolRuntime(server=server, healthy=False)]
    result = service.health_check()
    assert result == {'off': False}


# ── MCPService with retry ─────────────────────────────────────────

class FailingConnectService(MCPService):
    def _connect_runtime(self, runtime: MCPToolRuntime) -> None:
        runtime.healthy = False
        runtime.error = 'simulated connect failure'
        runtime.connect_retries = self.max_connect_retries


def test_mcp_service_marks_server_unhealthy_after_retries() -> None:
    service = FailingConnectService(
        [MCPServerConfig(name='fail', command=['noop'])],
        max_connect_retries=1,
    )
    assert len(service._runtimes) == 1
    assert service._runtimes[0].healthy is False
    assert service._runtimes[0].error == 'simulated connect failure'
    assert service._runtimes[0].connect_retries == 1


def test_mcp_service_registers_no_tools_on_failed_connect() -> None:
    service = FailingConnectService(
        [MCPServerConfig(name='fail', command=['noop'])],
        max_connect_retries=1,
    )
    registry = ToolRegistry()
    registered = service.register_tools(registry)
    assert registered == {'fail': []}


# ── Tool list ─────────────────────────────────────────────────────

def test_tool_list_filters_unhealthy_servers() -> None:
    service = MCPService([])
    service._runtimes = [
        MCPToolRuntime(
            server=MCPServerConfig(name='good', command=['ok']),
            healthy=True,
            tools=[ToolSpec(name='good.t1', description='d', input_schema={}, handler=lambda: None, tags={'mcp'})],
        ),
        MCPToolRuntime(
            server=MCPServerConfig(name='bad', command=['nope']),
            healthy=False,
            tools=[ToolSpec(name='bad.t1', description='d', input_schema={}, handler=lambda: None, tags={'mcp'})],
        ),
    ]
    tools = service.tool_list()
    assert len(tools) == 1
    assert tools[0].name == 'good.t1'


# ── MCPStdioSession integration tests ─────────────────────────────

class MCPResponder:
    """A fake MCP stdio server that responds to incoming requests."""

    def __init__(self):
        self.stdin_queue: Queue = Queue()
        self.stdout_queue: Queue = Queue()
        self._next_id = 0
        self._responses: dict[int, dict] = {}
        self._lock = threading.Lock()

    def add_response(self, method: str, result: dict):
        """Queue a response that will be returned when a matching request arrives."""
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
        self._responses[req_id] = result
        return req_id

    def write(self, text: str):
        """Called when the client writes to stdin. Triggers response processing."""
        self.stdin_queue.put(text)
        # Parse the request and find matching response
        try:
            request = json.loads(text.strip())
            req_id = request.get("id")
            if req_id is not None and req_id in self._responses:
                result = self._responses.pop(req_id)
                response = json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}) + '\n'
                self.stdout_queue.put(response)
        except json.JSONDecodeError:
            pass

    def readline(self) -> str:
        try:
            return self.stdout_queue.get(timeout=5)
        except Empty:
            return ''


class SyncedFakePopen:
    """Fake Popen where stdin.write triggers stdout responses via MCPResponder."""

    def __init__(self, *args, **kwargs):
        self.responder = MCPResponder()
        self.stdin = _ResponderStdin(self.responder)
        self.stdout = _ResponderStdout(self.responder)
        self.stderr = _DummyFile()
        self.returncode = None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def kill(self):
        self.returncode = -9


class _ResponderStdin:
    def __init__(self, responder: MCPResponder):
        self._responder = responder
        self.lines: list[str] = []

    def write(self, text: str):
        self.lines.append(text)
        self._responder.write(text)

    def flush(self):
        pass

    def close(self):
        pass


class _ResponderStdout:
    def __init__(self, responder: MCPResponder):
        self._responder = responder

    def readline(self) -> str:
        return self._responder.readline()

    def close(self):
        pass


class _DummyFile:
    def close(self):
        pass


def test_stdio_session_initialize_handshake(monkeypatch) -> None:
    captured_popen: SyncedFakePopen | None = None

    def fake_popen_factory(*args, **kwargs):
        nonlocal captured_popen
        captured_popen = SyncedFakePopen()
        captured_popen.responder.add_response(
            "initialize",
            {"protocolVersion": "2024-11-05", "serverInfo": {"name": "test-server"}},
        )
        return captured_popen

    monkeypatch.setattr(subprocess, 'Popen', fake_popen_factory)

    server = MCPServerConfig(name='test', command=['fake-server'], timeout_seconds=5)
    session = MCPStdioSession(server)
    session.connect()

    assert captured_popen is not None
    assert len(captured_popen.stdin.lines) >= 1
    session.close()


def test_stdio_session_list_tools(monkeypatch) -> None:
    captured_popen: SyncedFakePopen | None = None

    def fake_popen_factory(*args, **kwargs):
        nonlocal captured_popen
        captured_popen = SyncedFakePopen()
        captured_popen.responder.add_response(
            "initialize",
            {"protocolVersion": "2024-11-05"},
        )
        return captured_popen

    monkeypatch.setattr(subprocess, 'Popen', fake_popen_factory)

    server = MCPServerConfig(name='test', command=['fake'], timeout_seconds=5)
    session = MCPStdioSession(server)
    session.connect()

    captured_popen.responder.add_response("tools/list", {
        "tools": [
            {"name": "echo", "description": "echo back", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}},
        ]
    })

    tools = session.list_tools()
    assert len(tools) == 1
    assert tools[0].name == 'echo'
    session.close()


def test_stdio_session_call_tool(monkeypatch) -> None:
    captured_popen: SyncedFakePopen | None = None

    def fake_popen_factory(*args, **kwargs):
        nonlocal captured_popen
        captured_popen = SyncedFakePopen()
        captured_popen.responder.add_response(
            "initialize",
            {"protocolVersion": "2024-11-05"},
        )
        return captured_popen

    monkeypatch.setattr(subprocess, 'Popen', fake_popen_factory)

    server = MCPServerConfig(name='test', command=['fake'], timeout_seconds=5)
    session = MCPStdioSession(server)
    session.connect()

    captured_popen.responder.add_response("tools/call", {
        "content": [{"type": "text", "text": "hello world"}],
    })

    result = session.call_tool('echo', {'text': 'hello'})
    assert result.content == 'hello world'
    assert result.is_error is False
    session.close()


def test_stdio_session_truncates_large_result(monkeypatch) -> None:
    captured_popen: SyncedFakePopen | None = None

    def fake_popen_factory(*args, **kwargs):
        nonlocal captured_popen
        captured_popen = SyncedFakePopen()
        captured_popen.responder.add_response(
            "initialize",
            {"protocolVersion": "2024-11-05"},
        )
        return captured_popen

    monkeypatch.setattr(subprocess, 'Popen', fake_popen_factory)

    server = MCPServerConfig(name='test', command=['fake'], max_return_chars=10, timeout_seconds=5)
    session = MCPStdioSession(server)
    session.connect()

    captured_popen.responder.add_response("tools/call", {
        "content": [{"type": "text", "text": "a" * 100}],
    })

    result = session.call_tool('big', {})
    assert result.content.startswith('aaaaaaaaaa')
    assert result.content.endswith('...[truncated: original 100 chars]')
    assert result.diagnostics['truncated'] is True
    session.close()


def test_stdio_session_handles_tool_error(monkeypatch) -> None:
    captured_popen: SyncedFakePopen | None = None

    def fake_popen_factory(*args, **kwargs):
        nonlocal captured_popen
        captured_popen = SyncedFakePopen()
        captured_popen.responder.add_response(
            "initialize",
            {"protocolVersion": "2024-11-05"},
        )
        return captured_popen

    monkeypatch.setattr(subprocess, 'Popen', fake_popen_factory)

    server = MCPServerConfig(name='test', command=['fake'], timeout_seconds=5)
    session = MCPStdioSession(server)
    session.connect()

    captured_popen.responder.add_response("tools/call", {
        "content": [{"type": "text", "text": "not found"}],
        "isError": True,
    })

    result = session.call_tool('missing', {})
    assert result.is_error is True
    session.close()


# ── Tool handler error handling ────────────────────────────────────

def test_mcp_tool_spec_handler_catches_exception() -> None:
    server = MCPServerConfig(name='srv', command=['cmd'])
    tool_def = MCPToolDefinition(name='test', description='test tool', input_schema={'type': 'object', 'properties': {}})

    session = MCPStdioSession(server)
    service = MCPService([server])

    spec = service._to_tool_spec(server, tool_def, session)
    result = spec.handler()
    assert result.is_error is True
