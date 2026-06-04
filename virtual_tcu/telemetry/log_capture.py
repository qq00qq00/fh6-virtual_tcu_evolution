import sys
import threading
from collections import deque


class TeeStdout:
    """Intercepts sys.stdout to capture prints while still writing to console."""

    def __init__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._lock = threading.Lock()
        self._buffer = deque(maxlen=200)
        self._listeners = []

    def install(self):
        sys.stdout = self
        sys.stderr = self

    def restore(self):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

    def add_listener(self, callback):
        with self._lock:
            self._listeners.append(callback)

    def snapshot(self) -> list[dict]:
        with self._lock:
            return list(self._buffer)

    def remove_listener(self, callback):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def write(self, text: str):
        self._original_stdout.write(text)

        # Don't broadcast empty newlines or carriage returns alone
        cleaned = text.strip()
        if cleaned:
            # Simple heuristic for log level based on prefix
            level = "INFO"
            if "[ERROR]" in cleaned or "[!!]" in cleaned or "failed:" in cleaned:
                level = "ERROR"
            elif "[WARN]" in cleaned or "[!]" in cleaned:
                level = "WARN"
            elif "[DEBUG]" in cleaned:
                level = "DEBUG"

            msg = {"type": "system_log", "level": level, "msg": cleaned}

            with self._lock:
                self._buffer.append(msg)
                listeners = list(self._listeners)

            for cb in listeners:
                try:
                    cb(msg)
                except Exception:
                    pass

    def flush(self):
        self._original_stdout.flush()


# Global singleton for log capture
log_capture = TeeStdout()
