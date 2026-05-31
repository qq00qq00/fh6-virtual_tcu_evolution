"""Drive-style regime tests and the Comfort/Race inline adaptation.

The DYNAMIC mode was merged away: DriveStyleTracker.regime now adapts
Comfort (CRUISE = classic, ADAPTIVE/SPORT = sportier) and Race (CRUISE =
slightly earlier upshift to cut cruise drone). These guard that wiring.
"""

from tests.conftest import make_telemetry
from virtual_tcu.learning.drive_style import DriveStyleTracker


def _kinds(out):
    return [k for k, _ in out.shifts]


def test_regime_rises_to_sport_then_decays_to_cruise():
    ds = DriveStyleTracker()
    assert ds.regime == "CRUISE"

    # Aggressive driving: full throttle, high lateral g, high revs.
    now = 0.0
    aggressive = make_telemetry(accel_raw=255, current_rpm=8000.0)
    for _ in range(6):
        now += 0.1
        ds.update(aggressive, g_lat=1.2, now=now)
    assert ds.regime == "SPORT"

    # Back off completely: index decays slowly (tau=6s) back to CRUISE.
    calm = make_telemetry(accel_raw=0, current_rpm=0.0)
    for _ in range(40):
        now += 0.5
        ds.update(calm, g_lat=0.0, now=now)
    assert ds.regime == "CRUISE"


def test_comfort_cruise_eff_upshift_when_calm(make_logic, out, clock):
    # Default regime is CRUISE -> classic Comfort, which upshifts to save
    # fuel on a steady light-throttle cruise.
    tcu = make_logic("COMFORT")
    td = make_telemetry(
        speed_ms=72.7 / 3.6, current_rpm=0.40 * 8000, accel_raw=int(0.30 * 255), gear=4
    )
    for _ in range(20):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)
    assert "UP" in _kinds(out)


def test_comfort_sporty_suppresses_cruise_eff(make_logic, out, clock):
    # Same calm cruise, but a sporty regime: the fuel-saving CRUISE EFF
    # upshift is suppressed (rpm is below the sport upshift curve too).
    tcu = make_logic("COMFORT")
    tcu._drive_style._index = 0.6
    tcu._drive_style._regime = "SPORT"
    tcu._drive_style._last_update = clock.now
    td = make_telemetry(
        speed_ms=72.7 / 3.6, current_rpm=0.40 * 8000, accel_raw=int(0.30 * 255), gear=4
    )
    for _ in range(20):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)
    assert "UP" not in _kinds(out)
    assert tcu._drive_style.regime in ("SPORT", "ADAPTIVE")


def test_race_cruise_quiet_label_when_calm(make_logic, out, clock):
    # Race + CRUISE regime: in-band end state is tagged "cruise".
    tcu = make_logic("RACE")
    td = make_telemetry(
        speed_ms=72.7 / 3.6, current_rpm=0.50 * 8000, accel_raw=int(0.30 * 255), gear=4
    )
    for _ in range(5):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)
    assert tcu._tcu_state == "RACE"
    assert tcu._tcu_state_sub == "cruise"


def test_race_in_band_label_when_sporty(make_logic, out, clock):
    # Race + SPORT regime: classic in-band label, later upshift offset.
    tcu = make_logic("RACE")
    tcu._drive_style._index = 0.6
    tcu._drive_style._regime = "SPORT"
    tcu._drive_style._last_update = clock.now
    td = make_telemetry(
        speed_ms=72.7 / 3.6, current_rpm=0.50 * 8000, accel_raw=int(0.30 * 255), gear=4
    )
    for _ in range(5):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)
    assert tcu._tcu_state == "RACE"
    assert tcu._tcu_state_sub == "in band"
