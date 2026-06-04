"""Driving Log — CSV event logger for shift analysis.

Records a row of comprehensive telemetry + TCU decision data every time
a shift event occurs (auto or manual).  Writing is offloaded to a
background thread so the 60 Hz processing loop is never blocked by I/O.
"""

from __future__ import annotations

import csv
import io
import threading
import time
from pathlib import Path
from queue import Empty, SimpleQueue

from virtual_tcu import paths
from virtual_tcu.telemetry.model import Telemetry

# Column order mirrors the design table in the implementation plan.
_COLUMNS: list[str] = [
    "timestamp",
    "session_time_s",
    "game_timestamp_ms",
    "action",
    "gear_before",
    "gear_after",
    "reason",
    "rule",
    "tcu_state",
    "tcu_state_sub",
    "current_rpm",
    "engine_max_rpm",
    "rpm_pct",
    "power_kw",
    "torque_nm",
    "speed_kmh",
    "vel_z",
    "throttle",
    "brake",
    "clutch_raw",
    "drivetrain",
    "slip_fl",
    "slip_fr",
    "slip_rl",
    "slip_rr",
    "accel_x",
    "accel_z",
    "g_lat",
    "g_lon",
    "ang_vel_z",
    "boost_raw",
    "is_race_on",
    "car_ordinal",
    "car_class",
    "pi",
]


class DrivingLogger:
    """Append-only CSV logger for shift events.

    Lifecycle
    ---------
    * ``start()``  — opens a new timestamped CSV file under ``logs/``.
    * ``log_event(...)``  — enqueues one row (non-blocking).
    * ``stop()``   — flushes remaining rows and closes the file.

    The ``enabled`` flag is checked by the caller (TCULogic) so that the
    logger itself stays simple and stateless regarding the config store.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._path: Path | None = None
        self._file: io.TextIOWrapper | None = None
        self._writer: csv.writer | None = None
        self._start_time: float = 0.0
        self._event_count: int = 0

        # Background writer
        self._queue: SimpleQueue[list | None] = SimpleQueue()
        self._thread: threading.Thread | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self._file is not None

    @property
    def status(self) -> dict:
        return {
            "active": self.is_active,
            "events": self._event_count,
            "file": self._path.name if self._path else None,
        }

    def start(self, car_ordinal: int = 0) -> bool:
        """Open a new CSV log file.  Returns *True* on success."""
        if self.is_active:
            self.stop()
        ts = time.strftime("%Y%m%d_%H%M%S")
        if car_ordinal > 0:
            filename = f"driving_log_car{car_ordinal}_{ts}.csv"
        else:
            filename = f"driving_log_{ts}.csv"
        path = paths.log_dir() / filename
        try:
            f = open(path, "w", newline="", encoding="utf-8-sig")  # noqa: SIM115
            writer = csv.writer(f)
            writer.writerow(_COLUMNS)
            f.flush()
        except Exception as e:
            print(f"[DrivingLog] start failed: {e}")
            return False

        with self._lock:
            self._path = path
            self._file = f
            self._writer = writer
            self._start_time = time.time()
            self._event_count = 0

        self._running = True
        self._thread = threading.Thread(
            target=self._writer_loop, name="DrivingLog_Writer", daemon=True
        )
        self._thread.start()
        return True

    def stop(self) -> str | None:
        """Flush and close the current log.  Returns the file path."""
        self._running = False
        # Sentinel to unblock the writer thread
        self._queue.put(None)
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        with self._lock:
            if self._file is None:
                return None
            try:
                self._file.flush()
                self._file.close()
            except Exception:
                pass
            p = str(self._path) if self._path else None
            self._file = None
            self._writer = None
            return p

    def log_event(
        self,
        action: str,
        td: Telemetry,
        *,
        gear_before: int | None = None,
        gear_after: int | None = None,
        reason: str = "",
        rule: str = "",
        tcu_state: str = "",
        tcu_state_sub: str = "",
        g_lat: float = 0.0,
        g_lon: float = 0.0,
    ) -> None:
        """Enqueue one CSV row.  Non-blocking — never stalls the caller."""
        if not self.is_active:
            return

        now = time.time()
        session_t = round(now - self._start_time, 3) if self._start_time else 0.0

        if gear_before is None:
            gear_before = td.gear
        if gear_after is None:
            if "UP" in action:
                gear_after = td.gear + 1
            elif "DOWN" in action:
                gear_after = td.gear - 1
            else:
                gear_after = td.gear

        row = [
            round(now, 3),
            session_t,
            td.session_timestamp,
            action,
            gear_before,
            gear_after,
            reason,
            rule,
            tcu_state,
            tcu_state_sub,
            round(td.current_rpm, 1),
            round(td.engine_max_rpm, 1),
            round(td.rpm_pct * 100, 2),
            round(td.power_w / 1000.0, 2),
            round(td.torque_nm, 1),
            round(td.speed_kmh, 2),
            round(td.vel_z, 3),
            round(td.throttle * 100, 1),
            round(td.brake * 100, 1),
            td.clutch_raw,
            td.drivetrain_name,
            round(td.slip_fl, 4),
            round(td.slip_fr, 4),
            round(td.slip_rl, 4),
            round(td.slip_rr, 4),
            round(td.accel_x, 4),
            round(td.accel_z, 4),
            round(g_lat, 4),
            round(g_lon, 4),
            round(td.ang_vel_z, 4),
            round(td.boost_raw, 4),
            int(td.is_race_on),
            td.car_ordinal,
            td.car_class,
            td.pi,
        ]
        self._queue.put(row)

    # ------------------------------------------------------------------
    # Background writer
    # ------------------------------------------------------------------

    def _writer_loop(self) -> None:
        """Drain the queue and write rows to the CSV file."""
        while self._running:
            try:
                row = self._queue.get(timeout=0.5)
            except Empty:
                continue
            if row is None:  # sentinel
                break
            with self._lock:
                if self._writer is None or self._file is None:
                    break
                try:
                    self._writer.writerow(row)
                    self._event_count += 1
                    # Flush every row for crash-safety — event rate is low
                    # (only on shift events, not every 60 Hz tick).
                    self._file.flush()
                except Exception as e:
                    print(f"[DrivingLog] write error: {e}")
                    break

        # Drain remaining items on shutdown
        while not self._queue.empty():
            try:
                row = self._queue.get_nowait()
            except Empty:
                break
            if row is None:
                continue
            with self._lock:
                if self._writer is None or self._file is None:
                    break
                try:
                    self._writer.writerow(row)
                    self._event_count += 1
                except Exception:
                    break
        with self._lock:
            if self._file is not None:
                try:
                    self._file.flush()
                except Exception:
                    pass
