from typing import Dict, Optional

from virtual_tcu.telemetry.model import Telemetry

class GearRatioCalibrator:
    """Learns rpm/kmh ratio per car/gear. The ratio is a fixed property of
    the transmission — valid whenever the wheels grip and no shift is in
    progress, regardless of throttle or whether speed is steady. Uses a
    running mean with outlier rejection: an estimate exists from the first
    valid sample and converges within a second of driving in each gear."""

    MIN_SPEED_KMH = 25.0
    OUTLIER_TOLERANCE = 0.18
    LEARN_RATE = 0.08
    OUTLIER_GRACE = 5  # samples before outlier rejection kicks in

    def __init__(self):
        self._ratios: Dict[int, Dict[int, float]] = {}
        self._counts: Dict[int, Dict[int, int]] = {}

    def observe(self, td: Telemetry):
        if td.car_ordinal <= 0 or td.gear < 1 or td.gear > 10:
            return
        if td.is_shifting:
            return
        if td.speed_kmh < self.MIN_SPEED_KMH or td.current_rpm <= 0:
            return
        # Wheelspin breaks the wheel-ground relationship → invalid ratio
        if td.rear_slip > 0.8 or td.front_slip > 0.8:
            return
        ratio = td.current_rpm / td.speed_kmh
        if ratio < 15 or ratio > 500:
            return

        car_ratios = self._ratios.setdefault(td.car_ordinal, {})
        car_counts = self._counts.setdefault(td.car_ordinal, {})
        gear = td.gear

        if gear not in car_ratios:
            car_ratios[gear] = ratio
            car_counts[gear] = 1
            return

        current = car_ratios[gear]
        n = car_counts[gear]
        # Reject outliers once a base is established (a mid-shift glitch or
        # slip spike that slipped past the filters)
        if n >= self.OUTLIER_GRACE:
            if abs(ratio - current) / current > self.OUTLIER_TOLERANCE:
                return
        # Running mean: true average early, stable low-pass once mature
        rate = max(self.LEARN_RATE, 1.0 / (n + 1))
        car_ratios[gear] = current + rate * (ratio - current)
        car_counts[gear] = n + 1

    def project_rpm_after_shift(
        self, td: Telemetry, target_gear: int
    ) -> Optional[float]:
        car_ratios = self._ratios.get(td.car_ordinal)
        if not car_ratios:
            return None
        target_ratio = car_ratios.get(target_gear)
        if not target_ratio:
            return None
        return target_ratio * td.speed_kmh

    def get_ratios(self, car_ordinal: int) -> Dict[int, float]:
        """Public accessor — learned rpm/kmh ratios for a car, or empty."""
        return self._ratios.get(car_ordinal, {})

    def has_data(self, car_ordinal: int) -> bool:
        return car_ordinal in self._ratios and len(self._ratios[car_ordinal]) >= 2

