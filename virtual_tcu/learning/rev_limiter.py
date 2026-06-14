from collections import deque

from virtual_tcu.telemetry.model import Telemetry


class RevLimiterDetector:
    """Learns the real rev limiter per car. Forza's reported engine_max_rpm
    is a nominal ceiling, often well above the actual fuel-cut RPM.

    Detection: the limiter has an unmistakable signature at full throttle
    — RPM stops progressing and oscillates in a sawtooth against a fixed
    ceiling. We watch a sliding RPM window; when its maximum stays flat
    (engine not progressing) AND the window oscillates (the sawtooth),
    that ceiling is the cutoff. A steady climb fails the 'flat max' test;
    a WOT hill-crawl fails the 'oscillation' test; noise dips fail both.
    Converges in ~0.7s of sustained limiter bounce."""

    MIN_THROTTLE = 0.92
    POST_SHIFT_IGNORE_S = 0.6
    WINDOW = 24
    STABLE_FRAMES = 18
    MIN_PEAK_PCT = 0.62
    PEAK_EPS = 40.0
    MIN_OSCILLATION = 150.0
    # A real fuel cut COLLAPSES torque (no combustion) — over the sawtooth
    # window the engine drops to near zero/negative torque at least once. A
    # bogus "ceiling" produced by the shifter repeatedly upshifting at the same
    # rpm shows full, steady torque there instead (the engine is still making
    # peak power, it just keeps getting shifted). So a candidate is only a
    # limiter if the MIN torque in the window has fallen below this fraction of
    # the car's observed peak torque. Without this guard the detector learns a
    # ceiling wherever the car happens to be upshifted, then that value is
    # substituted as engine_max_rpm and locks in chronic early shifting.
    LIMITER_TORQUE_COLLAPSE_RATIO = 0.45

    def __init__(self):
        self._redline: dict[tuple, float] = {}
        self._rpm_window: dict[tuple, deque[float]] = {}
        self._torque_window: dict[tuple, deque[float]] = {}
        self._peak_torque: dict[tuple, float] = {}
        self._peak_hold: dict[tuple, tuple] = {}

    def _reset(self, car: tuple):
        self._rpm_window.pop(car, None)
        self._torque_window.pop(car, None)
        self._peak_hold.pop(car, None)

    def observe(self, td: Telemetry, last_downshift_time: float, now: float):
        car = td.car_key
        if (
            car[0] <= 0
            or td.is_shifting
            or td.engine_max_rpm <= 0
            or td.throttle < self.MIN_THROTTLE
            or now - last_downshift_time < self.POST_SHIFT_IGNORE_S
            or td.rear_slip > 0.8
            or td.front_slip > 0.8
        ):
            # Wheelspin makes RPM oscillate at WOT without being the
            # limiter — exclude it, same as the gear-ratio calibrator.
            self._reset(car)
            return

        # Track the engine's peak (WOT) torque so the collapse test below has a
        # reference for "the engine is still making power here".
        if td.torque_nm > self._peak_torque.get(car, 0.0):
            self._peak_torque[car] = td.torque_nm

        win = self._rpm_window.setdefault(car, deque(maxlen=self.WINDOW))
        twin = self._torque_window.setdefault(car, deque(maxlen=self.WINDOW))
        win.append(td.current_rpm)
        twin.append(td.torque_nm)
        if len(win) < self.WINDOW:
            return

        wmax, wmin = max(win), min(win)
        # Must be high enough to be a plausible limiter, and oscillating
        # (the sawtooth) — a flat WOT hill-crawl is rejected here.
        if wmax < td.engine_max_rpm * self.MIN_PEAK_PCT or (wmax - wmin) < self.MIN_OSCILLATION:
            self._peak_hold.pop(car, None)
            return

        held_peak, held_frames = self._peak_hold.get(car, (wmax, 0))
        if abs(wmax - held_peak) <= self.PEAK_EPS:
            held_peak = max(held_peak, wmax)
            held_frames += 1
        else:
            held_peak, held_frames = wmax, 0  # peak moved → still climbing
        self._peak_hold[car] = (held_peak, held_frames)

        if held_frames >= self.STABLE_FRAMES:
            # Power-collapse guard: a genuine fuel cut drives torque to
            # near-zero/negative somewhere in the window. If the engine is still
            # pulling hard (min torque stays well above a fraction of peak), this
            # "ceiling" is just where the shifter keeps upshifting, NOT the
            # limiter — refuse it, or we'd poison engine_max_rpm and lock in
            # early shifts (the exact failure this detector caused on high-power
            # cars). Mirrors the upstream "refuted by strong power" rule.
            peak_tq = self._peak_torque.get(car, 0.0)
            twin = self._torque_window.get(car)
            if peak_tq <= 0.0 or twin is None or len(twin) < self.WINDOW:
                return
            if min(twin) > peak_tq * self.LIMITER_TORQUE_COLLAPSE_RATIO:
                return  # engine still making power at this rpm → not a cut
            # Cutoff only ever rises: every confirmed bounce is a real
            # limiter sample, and the engine cannot exceed the limiter at
            # WOT. The highest confirmed bounce is the true cutoff, so a
            # stray low reading can never drag the estimate down.
            if held_peak > self._redline.get(car, 0.0):
                self._redline[car] = held_peak

    def effective_redline(self, td: Telemetry) -> float | None:
        return self._redline.get(td.car_key)

    def dump(self, car: tuple) -> float | None:
        """Return the learned redline for *car*, or None."""
        return self._redline.get(car)

    def load(self, car: tuple, redline: float):
        """Restore a previously-learned redline for *car*."""
        if isinstance(redline, (int, float)) and redline > 0:
            self._redline[car] = float(redline)
