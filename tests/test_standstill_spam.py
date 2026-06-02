"""Regression: the TCU must not spam downshift commands every frame while the
car is stopped/crawling on the brake in a gear that can't drop further.

Real-world symptom (gamepad era): after crashing to a stop with the brake held,
GEAR MISMATCH fired a downshift on *every* telemetry frame (~125/s). The
per-frame ``_no_downshift_until = 0.0`` in the MISMATCH branch defeated the
post-downshift cascade cooldown, so the command rate was unbounded. On keyboard
that is a flood of Q presses; on the (removed) gamepad it re-mirrored the brake
each frame. The recovery downshift is still wanted — just rate-limited.
"""

from tests.conftest import make_telemetry


def _downshifts(out):
    return [k for k, _ in out.shifts if k.startswith("DOWN")]


def test_standstill_braking_does_not_spam_downshifts(make_logic, out, clock):
    # Stopped on the brake, stuck in gear 3 (the game won't drop it): MISMATCH
    # applies (speed below the sensible floor, rpm low). Over 200 frames at 60Hz
    # the recovery downshift must be gated by the cascade cooldown, not fired
    # every frame.
    tcu = make_logic("RACE")
    td = make_telemetry(
        gear=3,
        current_rpm=900,
        engine_max_rpm=8000,
        speed_ms=0.5,  # ~1.8 km/h
        brake_raw=255,
        accel_raw=0,
    )
    for _ in range(200):
        clock.now += 0.016
        out.now = clock.now
        tcu.process(td)

    n = len(_downshifts(out))
    # Cascade cooldown is ~0.3 s, so 200 frames (~3.2 s) allows ~11 commands.
    assert n <= 15, f"downshift spam not gated: {n} commands in 200 frames"
    # Still recovers (does fire at least once).
    assert n >= 1
