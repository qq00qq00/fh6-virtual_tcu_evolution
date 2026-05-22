from typing import Optional

from virtual_tcu.telemetry.model import Telemetry


class YawTransientDetector:
    """Brief yaw spikes (≤400 ms) = car correction; sustained = drift.
    During a brief event, blocks all shift decisions; after it ends,
    holds the block 200 ms more so the chassis settles."""

    YAW_THRESHOLD = 0.30
    TRANSIENT_MAX_MS = 400
    POST_EVENT_HOLD_MS = 200

    def __init__(self):
        self._yaw_high_since: Optional[float] = None
        self._block_until: float = 0.0
        self._currently_blocking: bool = False

    def update(self, td: Telemetry, now: float) -> bool:
        yaw_high = abs(td.ang_vel_z) > self.YAW_THRESHOLD

        if yaw_high:
            if self._yaw_high_since is None:
                self._yaw_high_since = now
            duration_ms = (now - self._yaw_high_since) * 1000
            if duration_ms < self.TRANSIENT_MAX_MS:
                self._block_until = now + (self.POST_EVENT_HOLD_MS / 1000.0)
                self._currently_blocking = True
                return True
            self._currently_blocking = False
            return False

        self._yaw_high_since = None
        self._currently_blocking = now < self._block_until
        return self._currently_blocking

    @property
    def is_blocking(self) -> bool:
        return self._currently_blocking

