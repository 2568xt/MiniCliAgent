from __future__ import annotations

import subprocess
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from minicliagent.core.runtime.event_bus import EventBus


@dataclass
class BackgroundTask:
    task_id: str
    command: str
    status: str
    result: str = ""


class BackgroundManager:
    def __init__(
        self,
        workspace_root: Path,
        timeout_seconds: int = 300,
        event_bus: EventBus | None = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.timeout_seconds = timeout_seconds
        self.event_bus = event_bus
        self._tasks: dict[str, BackgroundTask] = {}
        self._notifications: list[dict] = []
        self._lock = threading.Lock()

    def start(self, command: str) -> str:
        task_id = str(uuid.uuid4())[:8]
        self._tasks[task_id] = BackgroundTask(
            task_id=task_id,
            command=command,
            status="running",
        )
        thread = threading.Thread(target=self._run, args=(task_id, command), daemon=True)
        thread.start()
        if self.event_bus is not None:
            self.event_bus.emit("background_started", {"task_id": task_id, "command": command})
        return task_id

    def _run(self, task_id: str, command: str) -> None:
        status = "completed"
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            output = (result.stdout + result.stderr).strip() or "(no output)"
            if result.returncode != 0:
                status = "error"
        except subprocess.TimeoutExpired:
            output = f"Error: Timeout ({self.timeout_seconds}s)"
            status = "timeout"
        except Exception as exc:
            output = str(exc)
            status = "error"

        task = self._tasks[task_id]
        if task.status == "cancelled":
            return
        task.status = status
        task.result = output[:50000]
        if self.event_bus is not None:
            self.event_bus.emit("background_finished", {"task_id": task_id, "status": task.status})
        with self._lock:
            self._notifications.append(
                {
                    "task_id": task_id,
                    "status": task.status,
                    "command": task.command,
                    "result": task.result,
                }
            )

    def get(self, task_id: str) -> BackgroundTask:
        return self._tasks[task_id]

    def list_tasks(self) -> list[BackgroundTask]:
        return list(self._tasks.values())

    def cancel(self, task_id: str) -> BackgroundTask:
        task = self._tasks[task_id]
        task.status = "cancelled"
        task.result = "Cancelled by user"
        if self.event_bus is not None:
            self.event_bus.emit("background_cancelled", {"task_id": task_id})
        with self._lock:
            self._notifications.append(
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "command": task.command,
                    "result": task.result,
                }
            )
        return task

    def drain_notifications(self) -> list[dict]:
        with self._lock:
            notifications = list(self._notifications)
            self._notifications.clear()
        return notifications
