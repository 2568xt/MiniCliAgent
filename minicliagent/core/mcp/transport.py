from __future__ import annotations

import json
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from queue import Empty, Queue

from minicliagent.core.mcp.models import MCPServerConfig, MCPToolCallResult, MCPToolDefinition


@dataclass
class MCPStdioSession:
    """Persistent MCP stdio session managing subprocess lifecycle and JSON-RPC."""

    config: MCPServerConfig
    _proc: subprocess.Popen | None = field(init=False, default=None)
    _next_id: int = field(init=False, default=0)
    _pending: dict[int, Queue] = field(init=False, default_factory=dict)
    _reader_thread: threading.Thread | None = field(init=False, default=None)
    _closed: bool = field(init=False, default=False)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock)

    def connect(self) -> None:
        if self._proc is not None:
            return
        try:
            self._proc = subprocess.Popen(
                list(self.config.command),
                cwd=str(self.config.cwd) if self.config.cwd else None,
                env=self._merged_env(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "MiniCLIAgent", "version": "0.1.0"},
            }, timeout=self.config.timeout_seconds)
            self._send_notification("initialized", {})
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
        if self._proc is not None:
            try:
                self._proc.stdin.close()
                self._proc.stdout.close()
                self._proc.stderr.close()
            except OSError:
                pass
            try:
                self._proc.wait(timeout=3)
            except (subprocess.TimeoutExpired, OSError):
                self._proc.kill()
                try:
                    self._proc.wait(timeout=2)
                except (subprocess.TimeoutExpired, OSError):
                    pass
            self._proc = None

    def list_tools(self) -> list[MCPToolDefinition]:
        response = self._send_request("tools/list", {}, timeout=self.config.timeout_seconds)
        tools = response.get("tools", [])
        return [
            MCPToolDefinition(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", {"type": "object", "properties": {}}),
            )
            for tool in tools
        ]

    def call_tool(self, name: str, arguments: dict) -> MCPToolCallResult:
        response = self._send_request(
            "tools/call",
            {"name": name, "arguments": arguments},
            timeout=self.config.timeout_seconds,
        )
        content = response.get("content", "")
        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = "".join(text_parts)
        text = str(content)
        truncated = len(text) > self.config.max_return_chars
        if truncated:
            text = text[:self.config.max_return_chars]
        return MCPToolCallResult(
            content=text,
            is_error=bool(response.get("isError", False)),
            diagnostics={"server": self.config.name, "truncated": truncated},
        )

    def health_check(self) -> bool:
        if self._proc is None or self._proc.poll() is not None:
            return False
        try:
            self._send_request("ping", {}, timeout=3.0)
            return True
        except Exception:
            return False

    def _send_request(self, method: str, params: dict, timeout: float) -> dict:
        req_id = self._next_id
        self._next_id += 1
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        queue: Queue = Queue()
        with self._lock:
            self._pending[req_id] = queue
        self._write_line(json.dumps(payload))
        try:
            result = queue.get(timeout=timeout)
        except Empty:
            with self._lock:
                self._pending.pop(req_id, None)
            raise TimeoutError(f"MCP request '{method}' timed out after {timeout}s")
        if "error" in result:
            raise RuntimeError(result["error"].get("message", str(result["error"])))
        return result.get("result", {})

    def _send_notification(self, method: str, params: dict) -> None:
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        self._write_line(json.dumps(payload))

    def _write_line(self, line: str) -> None:
        if self._proc is None:
            raise RuntimeError("MCP transport not connected")
        self._proc.stdin.write(line + "\n")
        self._proc.stdin.flush()

    def _read_loop(self) -> None:
        while not self._closed and self._proc is not None and self._proc.stdout is not None:
            try:
                line = self._proc.stdout.readline()
            except (ValueError, OSError):
                break
            if not line:
                break
            try:
                message = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            req_id = message.get("id")
            if req_id is not None:
                with self._lock:
                    queue = self._pending.pop(req_id, None)
                if queue is not None:
                    queue.put(message)

    def _merged_env(self) -> dict[str, str]:
        import os
        env = dict(os.environ)
        env.update(self.config.env)
        return env


@dataclass
class MCPTransportClient:
    """Factory-compatible wrapper. Creates a session per call for simplicity.
    For persistent sessions, use MCPStdioSession directly via the service.
    """

    config: MCPServerConfig

    def list_tools(self) -> list[MCPToolDefinition]:
        session = MCPStdioSession(self.config)
        try:
            session.connect()
            return session.list_tools()
        finally:
            session.close()

    def call_tool(self, name: str, arguments: dict) -> MCPToolCallResult:
        session = MCPStdioSession(self.config)
        try:
            session.connect()
            return session.call_tool(name, arguments)
        finally:
            session.close()
