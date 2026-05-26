import threading
import time


class Watchdog:
    def __init__(self):
        self._last_heartbeat = time.time()
        self._has_ever_beat = False
        self._lock = threading.Lock()

    def heartbeat(self):
        with self._lock:
            self._last_heartbeat = time.time()
            self._has_ever_beat = True

    def check(self) -> bool:
        with self._lock:
            if not self._has_ever_beat:
                return False
            return (time.time() - self._last_heartbeat) > 5.0
