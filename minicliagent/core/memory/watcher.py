from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class MemoryFileWatcher:
    """Watches memory files with 1.5s debounce polling.

    Monitors summary_path and fragments_dir for changes and calls
    the on_change callback after debounce period elapses without changes.
    """

    summary_path: Path
    fragments_dir: Path
    on_change: Callable[[], None]
    debounce_seconds: float = 1.5
    poll_interval: float = 0.5

    def __post_init__(self) -> None:
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_mtime: float = 0.0
        self._pending_change = False
        self._debounce_timer: float | None = None

    def _get_current_mtime(self) -> float:
        """Get the most recent modification time across all watched files."""
        mtimes: list[float] = []

        if self.summary_path.exists():
            mtimes.append(self.summary_path.stat().st_mtime)

        if self.fragments_dir.exists():
            for path in self.fragments_dir.glob("*.md"):
                try:
                    mtimes.append(path.stat().st_mtime)
                except OSError:
                    pass

        return max(mtimes) if mtimes else 0.0

    def _check_for_changes(self) -> bool:
        """Check if any watched files have changed since last check."""
        current_mtime = self._get_current_mtime()
        if current_mtime > self._last_mtime:
            self._last_mtime = current_mtime
            return True
        return False

    def _poll_loop(self) -> None:
        """Main polling loop with debounce logic."""
        while self._running:
            if self._check_for_changes():
                if not self._pending_change:
                    self._pending_change = True
                    self._debounce_timer = time.monotonic()
            else:
                if self._pending_change and self._debounce_timer is not None:
                    elapsed = time.monotonic() - self._debounce_timer
                    if elapsed >= self.debounce_seconds:
                        self._pending_change = False
                        self._debounce_timer = None
                        try:
                            self.on_change()
                        except (OSError, RuntimeError) as exc:
                            pass  # non-fatal

            time.sleep(self.poll_interval)

    def start(self) -> None:
        """Start the file watcher in a background thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._last_mtime = self._get_current_mtime()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop the file watcher."""
        with self._lock:
            self._running = False
            self._pending_change = False
            self._debounce_timer = None

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        with self._lock:
            return self._running

    def trigger(self) -> None:
        """Manually trigger the on_change callback."""
        try:
            self.on_change()
        except (OSError, RuntimeError):
            pass  # non-fatal
