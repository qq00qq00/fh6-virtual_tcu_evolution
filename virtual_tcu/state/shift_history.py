import threading
import time
from collections import deque
from typing import Deque, Optional

from virtual_tcu.telemetry.model import Telemetry


class ShiftHistory:
    def __init__(self, max_size: int = 20):
        self._history: Deque[dict] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def record(
        self,
        action: str,
        td: Telemetry,
        reason: str = "",
        rule: str = "",
        blocked_by: Optional[str] = None,
    ):
        with self._lock:
            self._history.append(
                {
                    "ts": time.time(),
                    "action": action,
                    "gear": td.gear,
                    "rpm_pct": round(td.rpm_pct * 100, 1),
                    "throttle": round(td.throttle * 100, 1),
                    "brake": round(td.brake * 100, 1),
                    "speed": round(td.speed_kmh, 1),
                    "reason": reason,
                    "rule": rule,
                    "blocked_by": blocked_by,
                }
            )

    def snapshot(self) -> list:
        with self._lock:
            return list(self._history)

