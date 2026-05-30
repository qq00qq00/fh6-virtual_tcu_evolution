"""Crash / coast recovery tests.

Covers the two fixes for "car won't downshift after an impact":

- 机制 1: a single-frame speed collapse (a crash) breaks the post-shift lock
  so the GEAR MISMATCH recovery can re-gear the car immediately. The driver
  rarely brakes through an impact, so the existing brake-escape never fired.
- 机制 2: with no throttle and no brake (the state after a crash, a spin, or
  lifting into a corner) RACE / OFFROAD now step down toward a usable gear
  instead of bogging in a too-tall gear — previously only COMFORT did.

See the replay analysis in conversation: the real log's t≈70.5 crash left the
car stranded in gear 5 at 4.7 km/h with zero shifts for the whole event.
"""

from tests.conftest import make_telemetry
from virtual_tcu.config.constants import Cfg


def _kinds(out):
    return [k for k, _ in out.shifts]


# --- 机制 1: impact escape from the post-shift lock --------------------------


def test_impact_breaks_post_shift_lock(make_logic, out, clock):
    tcu = make_logic("RACE")
    # Seed speed history at cruise; no shift fires here.
    fast = make_telemetry(speed_ms=120 / 3.6, current_rpm=29 * 120, gear=6)
    clock.now += 0.016
    out.now = clock.now
    tcu.process(fast)

    # Pretend a shift just happened: both the stabilise lock and the cascade
    # downshift lock are armed and would normally swallow the next decision.
    tcu._lock_until = clock.now + 1.0
    tcu._no_downshift_until = clock.now + 1.0
    before = len(out.shifts)

    # Crash: speed collapses 120 -> 18 in one frame, leaving gear 6 far too
    # tall (rpm ~6.5%). The impact escape must drop the lock so MISMATCH fires.
    crash = make_telemetry(speed_ms=18 / 3.6, current_rpm=29 * 18, gear=6)
    clock.now += 0.016
    out.now = clock.now
    tcu.process(crash)

    assert len(out.shifts) > before
    assert tcu._tcu_state == "MISMATCH"


def test_normal_decel_respects_post_shift_lock(make_logic, out, clock):
    # A normal frame-to-frame speed change (below IMPACT_DECEL_KMH) must NOT
    # be mistaken for a crash — the post-shift lock has to hold.
    tcu = make_logic("RACE")
    fast = make_telemetry(speed_ms=120 / 3.6, current_rpm=29 * 120, gear=6)
    clock.now += 0.016
    out.now = clock.now
    tcu.process(fast)

    tcu._lock_until = clock.now + 1.0
    before = len(out.shifts)

    # Lose 10 km/h in a frame — hard braking, but well under the 25 threshold.
    slower = make_telemetry(speed_ms=110 / 3.6, current_rpm=29 * 110, gear=6)
    clock.now += 0.016
    out.now = clock.now
    tcu.process(slower)

    assert len(out.shifts) == before
    assert tcu._tcu_state == "POST-SHIFT"


def test_just_impacted_threshold(make_logic):
    # Direct check of the discriminator against Cfg.IMPACT_DECEL_KMH.
    tcu = make_logic("RACE")
    tcu._speed_history.clear()
    tcu._speed_history.append(100.0)
    tcu._speed_history.append(100.0 - (Cfg.IMPACT_DECEL_KMH - 1.0))  # 24 km/h drop
    assert tcu._just_impacted() is False
    tcu._speed_history.clear()
    tcu._speed_history.append(100.0)
    tcu._speed_history.append(100.0 - (Cfg.IMPACT_DECEL_KMH + 5.0))  # 30 km/h drop
    assert tcu._just_impacted() is True


# --- 机制 2: coast / over-gear recovery downshift ----------------------------


def _coast_state_at_shift(tcu, out, clock, td, frames=5):
    """Run *td* for *frames*, returning the TCU state on the frame a shift
    fires. COAST DOWN arms a post-shift lock, so the final-frame state would
    be POST-SHIFT — we want the state at the moment of the downshift."""
    fired_state = None
    for _ in range(frames):
        clock.now += 0.016
        out.now = clock.now
        before = len(out.shifts)
        tcu.process(td)
        if len(out.shifts) > before:
            fired_state = tcu._tcu_state
    return fired_state


def test_race_coast_downshift_recovers_tall_gear(make_logic, out, clock):
    # gear 6 @ 75 km/h, coasting (no pedals), rpm ~27% < race coast floor 30%,
    # and above the MISMATCH speed floor (~69) so only coast recovery applies.
    tcu = make_logic("RACE")
    td = make_telemetry(speed_ms=75 / 3.6, current_rpm=29 * 75, gear=6)
    fired_state = _coast_state_at_shift(tcu, out, clock, td)
    assert "DOWN" in _kinds(out)
    assert fired_state == "COAST DOWN"


def test_offroad_coast_downshift_recovers_tall_gear(make_logic, out, clock):
    tcu = make_logic("OFFROAD")
    td = make_telemetry(speed_ms=75 / 3.6, current_rpm=29 * 75, gear=6)
    fired_state = _coast_state_at_shift(tcu, out, clock, td)
    assert "DOWN" in _kinds(out)
    assert fired_state == "COAST DOWN"


def test_coast_skips_when_on_throttle(make_logic, out, clock):
    # Light throttle (below the power-demand gate) — not coasting, so no coast
    # downshift, and nothing else should fire either.
    tcu = make_logic("RACE")
    td = make_telemetry(speed_ms=75 / 3.6, current_rpm=29 * 75, accel_raw=int(0.30 * 255), gear=6)
    for _ in range(5):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)
    assert out.shifts == []
    assert tcu._tcu_state != "COAST DOWN"


def test_coast_skips_when_rpm_healthy(make_logic, out, clock):
    # Coasting but rpm still in band (50% > coast floor) — hold the gear.
    tcu = make_logic("RACE")
    td = make_telemetry(speed_ms=140 / 3.6, current_rpm=0.50 * 8000, gear=5)
    for _ in range(5):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)
    assert out.shifts == []
