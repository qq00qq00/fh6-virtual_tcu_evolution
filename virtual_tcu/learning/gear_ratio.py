from virtual_tcu.telemetry.model import Telemetry


class GearRatioCalibrator:
    """Learns rpm/kmh ratio per car/gear. The ratio is a fixed property of
    the transmission — valid whenever the wheels grip and no shift is in
    progress, under positive drive torque. Uses a running mean with outlier
    rejection: an estimate exists from the first valid sample and converges
    within a second of driving in each gear."""

    MIN_SPEED_KMH = 25.0
    OUTLIER_TOLERANCE = 0.18
    LEARN_RATE = 0.08
    OUTLIER_GRACE = 5  # samples before outlier rejection kicks in
    # Reject samples that would collapse spacing between adjacent gears.
    ORDER_TOLERANCE = 0.03

    def __init__(self):
        self._ratios: dict[tuple, dict[int, float]] = {}
        self._counts: dict[tuple, dict[int, int]] = {}

    @staticmethod
    def _is_driven_sample(td: Telemetry) -> bool:
        """Ratio is only meaningful when the engine drives the wheels."""
        if td.torque_nm <= 0:
            return False
        # Overrun / snow-downhill drag: full throttle but wheels turning the crank.
        if td.throttle > 0.45 and td.power_w < 0:
            return False
        return True

    def _order_ok(self, car_ratios: dict[int, float], gear: int, ratio: float, n: int) -> bool:
        """Higher gears must have a lower rpm/kmh ratio than lower gears."""
        if n < self.OUTLIER_GRACE:
            return True
        tol = self.ORDER_TOLERANCE
        lower = car_ratios.get(gear - 1)
        if lower is not None and ratio >= lower * (1.0 - tol):
            return False
        higher = car_ratios.get(gear + 1)
        if higher is not None and ratio <= higher * (1.0 + tol):
            return False
        return True

    def observe(self, td: Telemetry):
        ck = td.car_key
        if ck[0] <= 0 or td.gear < 1 or td.gear > 10:
            return
        if td.is_shifting:
            return
        if td.speed_kmh < self.MIN_SPEED_KMH or td.current_rpm <= 0:
            return
        if not self._is_driven_sample(td):
            return
        # Wheelspin breaks the wheel-ground relationship → invalid ratio
        if td.rear_slip > 0.8 or td.front_slip > 0.8:
            return
        ratio = td.current_rpm / td.speed_kmh
        if ratio < 15 or ratio > 500:
            return

        car_ratios = self._ratios.setdefault(ck, {})
        car_counts = self._counts.setdefault(ck, {})
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
        if not self._order_ok(car_ratios, gear, ratio, n):
            return
        # Running mean: true average early, stable low-pass once mature
        rate = max(self.LEARN_RATE, 1.0 / (n + 1))
        car_ratios[gear] = current + rate * (ratio - current)
        car_counts[gear] = n + 1

    def project_rpm_after_shift(self, td: Telemetry, target_gear: int) -> float | None:
        car_ratios = self._ratios.get(td.car_key)
        if not car_ratios:
            return None
        target_ratio = car_ratios.get(target_gear)
        if not target_ratio:
            return None
        return target_ratio * td.speed_kmh

    def get_ratios(self, car_key: tuple) -> dict[int, float]:
        """Public accessor — learned rpm/kmh ratios for a car, or empty."""
        return self._ratios.get(car_key, {})

    def has_data(self, car_key: tuple) -> bool:
        return car_key in self._ratios and len(self._ratios[car_key]) >= 2

    def dump(self, car_key: tuple) -> dict | None:
        """Serialise learned ratios for *car_key*, or None if no data."""
        if not self.has_data(car_key):
            return None
        return {
            "ratios": dict(self._ratios.get(car_key, {})),
            "counts": dict(self._counts.get(car_key, {})),
        }

    def load(self, car_key: tuple, data: dict):
        """Restore ratios from a previously-saved dump."""
        if not isinstance(data, dict):
            return
        ratios = data.get("ratios")
        counts = data.get("counts")
        if isinstance(ratios, dict):
            self._ratios[car_key] = {int(k): float(v) for k, v in ratios.items()}
        if isinstance(counts, dict):
            self._counts[car_key] = {int(k): int(v) for k, v in counts.items()}
