"""Gear ratio learning must ignore engine-braking / overrun samples."""

from tests.conftest import CAR_KEY, make_telemetry
from virtual_tcu.learning.gear_ratio import GearRatioCalibrator


def test_negative_torque_does_not_learn():
    cal = GearRatioCalibrator()
    td = make_telemetry(
        gear=4,
        current_rpm=6000,
        speed_ms=120.0 / 3.6,
        torque_nm=-80.0,
        power_w=-90000,
        accel_raw=255,
    )
    for _ in range(40):
        cal.observe(td)
    assert cal.get_ratios(CAR_KEY) == {}


def test_wot_negative_power_downhill_does_not_learn():
    cal = GearRatioCalibrator()
    cal.load(CAR_KEY, {"ratios": {4: 55.0}, "counts": {4: 20}})
    td = make_telemetry(
        gear=4,
        current_rpm=6000,
        speed_ms=120.0 / 3.6,
        torque_nm=120.0,
        power_w=-95000,
        accel_raw=255,
    )
    for _ in range(30):
        cal.observe(td)
    assert cal.get_ratios(CAR_KEY)[4] == 55.0


def test_positive_drive_updates_ratio():
    cal = GearRatioCalibrator()
    td = make_telemetry(
        gear=4,
        current_rpm=6000,
        speed_ms=120.0 / 3.6,
        torque_nm=250.0,
        power_w=180000,
        accel_raw=255,
    )
    for _ in range(10):
        cal.observe(td)
    assert 45 < cal.get_ratios(CAR_KEY)[4] < 55
