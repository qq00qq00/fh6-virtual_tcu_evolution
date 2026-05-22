import math

from virtual_tcu.telemetry.model import Telemetry

class DriveStyleTracker:
    """Continuous 0→1 sport-index for Dynamic mode (Audi Tiptronic feel).
    Rises fast (τ=0.3s) on aggressive inputs, falls slow (τ=6s) — one
    calm moment doesn't dump you back to cruise."""

    TAU_UP_S = 0.3
    TAU_DOWN_S = 6.0
    REGIME_CRUISE_MAX = 0.30
    REGIME_SPORT_MIN = 0.55
    HYSTERESIS = 0.03

    def __init__(self):
        self._index = 0.0
        self._last_update = 0.0
        self._regime = "CRUISE"

    def update(self, td: Telemetry, g_lat: float, now: float) -> float:
        score = 0.0
        if td.throttle > 0.65:
            score += 0.5 * min(1.0, (td.throttle - 0.65) / 0.35)
        if td.brake > 0.35:
            score += 0.5 * min(1.0, (td.brake - 0.35) / 0.55)
        abs_g = abs(g_lat)
        if abs_g > 0.4:
            score += 0.6 * min(1.0, (abs_g - 0.4) / 0.8)
        if td.rpm_pct > 0.65:
            score += 0.3 * min(1.0, (td.rpm_pct - 0.65) / 0.35)
        target = min(1.0, score)

        if self._last_update == 0.0:
            self._last_update = now
            self._index = target * 0.5
            self._update_regime()
            return self._index

        dt = now - self._last_update
        self._last_update = now
        if dt <= 0 or dt > 1.0:
            return self._index

        tau = self.TAU_UP_S if target > self._index else self.TAU_DOWN_S
        alpha = 1.0 - math.exp(-dt / tau)
        self._index += alpha * (target - self._index)
        self._update_regime()
        return self._index

    def _update_regime(self):
        h = self.HYSTERESIS
        if self._regime == "CRUISE":
            if self._index >= self.REGIME_CRUISE_MAX + h:
                self._regime = "ADAPTIVE"
        elif self._regime == "ADAPTIVE":
            if self._index < self.REGIME_CRUISE_MAX - h:
                self._regime = "CRUISE"
            elif self._index >= self.REGIME_SPORT_MIN + h:
                self._regime = "SPORT"
        else:
            if self._index < self.REGIME_SPORT_MIN - h:
                self._regime = "ADAPTIVE"

    @property
    def index(self) -> float:
        return self._index

    @property
    def regime(self) -> str:
        return self._regime

