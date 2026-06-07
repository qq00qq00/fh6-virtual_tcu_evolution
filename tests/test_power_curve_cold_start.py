"""Cold-start power curve: mid-range-only samples must not cause early upshifts."""

from tests.conftest import CAR_KEY, make_telemetry
from virtual_tcu.learning.power_curve import PowerCurveDetector

_MAX_RPM = 8000.0
_FALLBACK = 0.94


def _feed_mid_range_only(det: PowerCurveDetector, *, gear: int = 4) -> None:
    for _ in range(40):
        for r in (0.35, 0.45, 0.55, 0.65):
            trq = 280 * (1 - ((r - 0.55) / 0.45) ** 2)
            td = make_telemetry(
                gear=gear,
                current_rpm=r * _MAX_RPM,
                engine_max_rpm=_MAX_RPM,
                torque_nm=trq,
                accel_raw=255,
            )
            det.observe(td)


def test_mid_range_only_uses_fallback_upshift_point():
    det = PowerCurveDetector()
    _feed_mid_range_only(det)
    td = make_telemetry(gear=4, current_rpm=0.60 * _MAX_RPM, engine_max_rpm=_MAX_RPM)
    assert det.optimal_upshift_rpm(td, fallback=_FALLBACK, offset=0.03) == _FALLBACK


def test_stationary_first_gear_rev_counts_toward_high_rpm_coverage():
    det = PowerCurveDetector()
    for _ in range(20):
        for r in (0.55, 0.70, 0.85, 0.93, 0.97):
            trq = 300 * (1 - ((r - 0.55) / 0.5) ** 2)
            td = make_telemetry(
                gear=1,
                speed_ms=0.0,
                current_rpm=r * _MAX_RPM,
                engine_max_rpm=_MAX_RPM,
                torque_nm=trq,
                accel_raw=255,
                brake_raw=200,
            )
            det.observe(td)
    assert det._max_r[CAR_KEY] >= 0.93
    assert det.has_data(CAR_KEY)


def test_high_rpm_na_engine_shifts_near_redline():
    """Torque holds flat to the limiter — peak power is effectively redline."""
    det = PowerCurveDetector()
    for _ in range(30):
        for r in (0.45, 0.60, 0.75, 0.88, 0.95):
            trq = 290 if r < 0.80 else 285
            td = make_telemetry(
                gear=4,
                current_rpm=r * _MAX_RPM,
                engine_max_rpm=_MAX_RPM,
                torque_nm=trq,
                accel_raw=255,
            )
            det.observe(td)
    td = make_telemetry(gear=4, current_rpm=0.80 * _MAX_RPM, engine_max_rpm=_MAX_RPM)
    up = det.optimal_upshift_rpm(td, fallback=_FALLBACK, offset=0.03)
    assert up >= 0.90
