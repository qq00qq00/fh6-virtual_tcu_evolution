"""Crossover 'learned' status must reflect real gearbox coverage, not a quick
1->2 launch. Telemetry carries no top-gear field, so the badge is gated on
per-gear ratio convergence + power-curve confidence + a confirmed top gear
(a rejected-upshift cap, or a driving-plateau fallback).
"""

from tests.conftest import CAR_KEY, make_telemetry
from virtual_tcu.logic.tcu import (
    LEARN_CONF_FLOOR,
    LEARN_MATURE_SAMPLES,
    LEARN_MIN_TOP_FALLBACK,
    LEARN_PLATEAU_S,
)


def _seed(tcu, gears, samples):
    ratios = {g: 240.0 / g for g in gears}
    counts = {g: samples for g in gears}
    tcu._calibrator.load(CAR_KEY, {"ratios": ratios, "counts": counts})


def test_two_gear_launch_not_learned(make_logic):
    # 1st and 2nd only, one sample each — a single 1->2 launch.
    tcu = make_logic("RACE", seed_ratios=False)
    _seed(tcu, [1, 2], 1)
    tcu._max_gear_seen[CAR_KEY] = 2
    tcu._power_curve.confidence = lambda ck: 0.9  # pretend the curve is confident
    mature, target, progress, learned = tcu._learn_status(make_telemetry(gear=2))
    assert mature == 0  # one sample per gear is below the maturity bar
    assert not learned


def test_full_box_with_cap_is_learned(make_logic):
    tcu = make_logic("RACE", seed_ratios=False)
    gears = [1, 2, 3, 4, 5, 6]
    _seed(tcu, gears, LEARN_MATURE_SAMPLES)
    tcu._max_gear_seen[CAR_KEY] = 6
    tcu._upshift_cap_by_key[CAR_KEY] = 6  # a rejected upshift proved 6 is top
    tcu._power_curve.confidence = lambda ck: 0.9
    mature, target, progress, learned = tcu._learn_status(make_telemetry(gear=6))
    assert target == 6 and mature == 6
    assert progress == 1.0
    assert learned


def test_low_confidence_blocks_learned(make_logic):
    tcu = make_logic("RACE", seed_ratios=False)
    _seed(tcu, [1, 2, 3, 4, 5, 6], LEARN_MATURE_SAMPLES)
    tcu._max_gear_seen[CAR_KEY] = 6
    tcu._upshift_cap_by_key[CAR_KEY] = 6
    tcu._power_curve.confidence = lambda ck: LEARN_CONF_FLOOR - 0.1
    *_, learned = tcu._learn_status(make_telemetry(gear=6))
    assert not learned


def test_plateau_fallback_without_cap(make_logic):
    tcu = make_logic("RACE", seed_ratios=False)
    _seed(tcu, [1, 2, 3, 4, 5], LEARN_MATURE_SAMPLES)
    tcu._max_gear_seen[CAR_KEY] = 5
    tcu._power_curve.confidence = lambda ck: 0.9
    td = make_telemetry(gear=5)
    # No cap and no plateau time yet -> still learning.
    *_, learned = tcu._learn_status(td)
    assert not learned
    # Once a driving plateau is reached, the highest gear seen is accepted.
    tcu._gear_plateau_s[CAR_KEY] = LEARN_PLATEAU_S
    *_, learned = tcu._learn_status(td)
    assert learned


def test_plateau_below_min_top_not_learned(make_logic):
    assert LEARN_MIN_TOP_FALLBACK > 3  # precondition for this guard
    tcu = make_logic("RACE", seed_ratios=False)
    _seed(tcu, [1, 2, 3], LEARN_MATURE_SAMPLES)
    tcu._max_gear_seen[CAR_KEY] = 3  # too low to trust a plateau as 'top'
    tcu._gear_plateau_s[CAR_KEY] = LEARN_PLATEAU_S * 2
    tcu._power_curve.confidence = lambda ck: 0.9
    *_, learned = tcu._learn_status(make_telemetry(gear=3))
    assert not learned


def test_tracking_advances_max_gear_and_resets_plateau(make_logic, out, clock):
    tcu = make_logic("RACE", seed_ratios=False)
    td3 = make_telemetry(gear=3, speed_ms=120 / 3.6, accel_raw=int(0.5 * 255), is_race_on=1)
    for _ in range(5):
        clock.now += 0.1
        out.now = clock.now
        tcu.process(td3)
    assert tcu._max_gear_seen[CAR_KEY] == 3
    assert tcu._gear_plateau_s[CAR_KEY] > 0.0
    # Reaching 4th advances the high-water mark and resets the plateau clock.
    td4 = make_telemetry(gear=4, speed_ms=140 / 3.6, accel_raw=int(0.5 * 255), is_race_on=1)
    clock.now += 0.1
    out.now = clock.now
    tcu.process(td4)
    assert tcu._max_gear_seen[CAR_KEY] == 4
    assert tcu._gear_plateau_s[CAR_KEY] == 0.0
