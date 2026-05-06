from __future__ import annotations

import time
from dataclasses import dataclass, field
from minicliagent.core.mcp.models import MCPServerConfig, MCPServerDiagnostic, MCPToolDefinition
from minicliagent.core.mcp.transport import MCPStdioSession
from minicliagent.core.tools.models import ToolResult, ToolSpec


@dataclass
class MCPToolRuntime:
    server: MCPServerConfig
    session: MCPStdioSession | None = None
    tools: list[ToolSpec] = field(default_factory=list)
    healthy: bool = False
    error: str | None = None
    connect_retries: int = 0
    last_health_at: float = 0.0

    def close(self) -> None:
        if self.session is not None:
            self.session.close()
            self.session = None


@dataclass
class MCPService:
    server_configs: list[MCPServerConfig]
    _runtimes: list[MCPToolRuntime] = field(init=False, default_factory=list)
    logger: object | None = None
    max_connect_retries: int = 2
    connect_retry_delay: float = 0.5

    def __post_init__(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        for runtime in self._runtimes:
            runtime.close()
        self._runtimes = self._connect_all()

    def register_tools(self, registry) -> dict[str, list[str]]:
        """Register MCP tools into the registry. Returns name->registered_names map.

        Skips tools whose names conflict with already-registered built-in tools.
        """
        builtin_names = {spec.name for spec in registry.list_specs()}
        registered: dict[str, list[str]] = {}
        for runtime in self._runtimes:
            names: list[str] = []
            for tool in runtime.tools:
                if tool.name in builtin_names:
                    if self.logger is not None:
                        self.logger.log(
                            "warning",
                            "mcp_tool_conflict",
                            server=runtime.server.name,
                            tool=tool.name,
                            reason="name_collision_with_builtin",
                        )
                    continue
                registry.register(tool)
                names.append(tool.name)
                builtin_names.add(tool.name)
            registered[runtime.server.name] = names
        return registered

    def diagnostics(self) -> list[MCPServerDiagnostic]:
        return [
            MCPServerDiagnostic(
                name=runtime.server.name,
                enabled=runtime.server.enabled,
                healthy=runtime.healthy,
                tool_count=len(runtime.tools),
                command=runtime.server.command,
                tool_prefix=runtime.server.tool_prefix,
                error=runtime.error,
            )
            for runtime in self._runtimes
        ]

    def tool_list(self) -> list[MCPToolDefinition]:
        tools: list[MCPToolDefinition] = []
        seen: set[str] = set()
        for runtime in self._runtimes:
            if not runtime.healthy:
                continue
            for tool in runtime.tools:
                if tool.name not in seen:
                    seen.add(tool.name)
                    tools.append(MCPToolDefinition(
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.input_schema,
                    ))
        return tools

    def health_check(self) -> dict[str, bool]:
        result: dict[str, bool] = {}
        for runtime in self._runtimes:
            if not runtime.server.enabled:
                result[runtime.server.name] = False
                continue
            healthy = runtime.session is not None and runtime.session.health_check()
            if healthy != runtime.healthy:
                runtime.healthy = healthy
                if not healthy:
                    runtime.error = "health check failed"
            result[runtime.server.name] = healthy
        return result

    def is_tool_healthy(self, tool_name: str) -> bool:
        for runtime in self._runtimes:
            for tool in runtime.tools:
                if tool.name == tool_name:
                    return runtime.healthy
        return False

    def _connect_all(self) -> list[MCPToolRuntime]:
        runtimes: list[MCPToolRuntime] = []
        for server in self.server_configs:
            runtime = MCPToolRuntime(server=server)
            if not server.enabled:
                runtimes.append(runtime)
                if self.logger is not None:
                    self.logger.log("info", "mcp_server_disabled", server=server.name)
                continue
            self._connect_runtime(runtime)
            runtimes.append(runtime)
        return runtimes

    def _connect_runtime(self, runtime: MCPToolRuntime) -> None:
        server = runtime.server
        last_error: str | None = None
        for attempt in range(self.max_connect_retries + 1):
            if attempt > 0:
                time.sleep(self.connect_retry_delay)
            try:
                session = MCPStdioSession(server)
                session.connect()
                mcp_tools = session.list_tools()
                tool_specs = [self._to_tool_spec(server, t, session) for t in mcp_tools]
                runtime.session = session
                runtime.tools = tool_specs
                runtime.healthy = True
                runtime.connect_retries = attempt
                runtime.error = None
                if self.logger is not None:
                    self.logger.log(
                        "info",
                        "mcp_server_connected",
                        server=server.name,
                        tool_count=len(tool_specs),
                        retries=attempt,
                    )
                return
            except Exception as exc:
                last_error = str(exc)
                if self.logger is not None:
                    self.logger.log(
                        "warning",
                        "mcp_connect_attempt_failed",
                        server=server.name,
                        attempt=attempt,
                        error=last_error,
                    )
        runtime.healthy = False
        runtime.error = last_error
        runtime.connect_retries = self.max_connect_retries
        if self.logger is not None:
            self.logger.log(
                "error",
                "mcp_server_connect_failed",
                server=server.name,
                error=last_error,
            )

    def _to_tool_spec(self, server: MCPServerConfig, tool: MCPToolDefinition, session: MCPStdioSession) -> ToolSpec:
        prefix = server.tool_prefix or server.name
        tool_name = f"{prefix}.{tool.name}"

        def handler(**kwargs):
            try:
                result = session.call_tool(tool.name, kwargs)
                return ToolResult(content=result.content, is_error=result.is_error)
            except Exception as exc:
                return ToolResult(content=str(exc), is_error=True)

        return ToolSpec(
            name=tool_name,
            description=tool.description,
            input_schema=tool.input_schema,
            handler=handler,
            tags={"mcp", server.name},
        )
