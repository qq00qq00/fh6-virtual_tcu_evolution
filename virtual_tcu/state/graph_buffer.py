import threading
import time
from collections import deque
from typing import Deque

from virtual_tcu.telemetry.model import Telemetry


class GraphBuffer:
    def __init__(self, max_points: int = 300):
        self._buf: Deque[tuple] = deque(maxlen=max_points)
        self._lock = threading.Lock()

    def push(self, td: Telemetry):
        with self._lock:
            self._buf.append(
                (
                    time.time(),
                    td.rpm_pct,
                    td.throttle,
                    td.brake,
                    td.speed_kmh,
                    td.gear,
                )
            )

    def snapshot(self) -> list:
        with self._lock:
            return list(self._buf)

