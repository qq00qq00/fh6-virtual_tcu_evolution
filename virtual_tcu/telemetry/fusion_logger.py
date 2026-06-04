import csv
import threading
import time
from collections import deque

from virtual_tcu import paths
from virtual_tcu.telemetry.model import Telemetry


class FusionSnapshotLogger:
    """
    Flight Recorder style logger. Keeps the last 3 seconds of high-frequency
    telemetry and TCU state in a ring buffer. Dumps to CSV on triggers.
    """

    def __init__(self, buffer_size=180, post_event_size=60):
        # buffer_size: 180 frames = 3 seconds at 60Hz
        # post_event_size: 60 frames = 1 second at 60Hz
        self._buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()

        self._post_event_remaining = 0
        self._current_snapshot_reason = None
        self._snapshot_buffer = []

        self.on_snapshot_created = None  # Callback(reason, filename, chart_filename | None)
        self._chart_on_save = False

    def _get_fused_row(self, td: Telemetry, tcu_state: dict) -> dict:
        """Combine raw telemetry and TCU state into a single flat dict."""
        row = {
            "timestamp_ms": int(time.time() * 1000),
            "game_time_ms": td.session_timestamp,
            "rpm_pct": round(td.rpm_pct, 4),
            "speed_kmh": round(td.speed_kmh, 2),
            "throttle": round(td.throttle, 4),
            "brake": round(td.brake, 4),
            "max_slip_ratio": round(max(td.front_slip, td.rear_slip), 4),
            "gear": td.gear,
            "is_race_on": td.is_race_on,
            "car_ordinal": td.car_ordinal,
        }
        # Add TCU internal states
        row.update(tcu_state)
        return row

    def push(self, td: Telemetry, tcu_state: dict):
        """Called every frame at 60Hz."""
        row = self._get_fused_row(td, tcu_state)

        with self._lock:
            # Always keep history in the main buffer
            self._buffer.append(row)

            # If we are currently capturing post-event frames
            if self._post_event_remaining > 0:
                self._snapshot_buffer.append(row)
                self._post_event_remaining -= 1

                if self._post_event_remaining == 0:
                    self._flush_snapshot_async()

    def trigger_snapshot(self, reason: str, post_event_frames: int = 60):
        """Trigger a snapshot. Will capture history + post event frames."""
        with self._lock:
            if self._post_event_remaining > 0:
                # Already capturing a snapshot, ignore new trigger
                return

            self._current_snapshot_reason = reason
            self._post_event_remaining = post_event_frames
            # Clone current history buffer
            self._snapshot_buffer = list(self._buffer)

    def _flush_snapshot_async(self):
        """Write the snapshot to disk in a separate thread."""
        reason = self._current_snapshot_reason
        data = self._snapshot_buffer

        self._current_snapshot_reason = None
        self._snapshot_buffer = []

        if not data:
            return

        def _writer():
            self._write_snapshot(reason, data)

        threading.Thread(target=_writer, daemon=True).start()

    def set_chart_on_save(self, enabled: bool) -> None:
        self._chart_on_save = enabled

    def dump_snapshot(self, reason: str) -> str | None:
        """Write the current ring buffer immediately and return the filename."""
        with self._lock:
            data = list(self._buffer)
        if not data:
            return None
        return self._write_snapshot(reason, data)

    def _write_snapshot(self, reason: str, data: list[dict]) -> str | None:
        car_ordinal = data[0].get("car_ordinal", 0)
        ts = time.strftime("%Y%m%d_%H%M%S")
        stem = f"snapshot_car{car_ordinal}_{ts}_{reason}"

        try:
            if self._chart_on_save:
                from virtual_tcu.telemetry.snapshot_chart import write_chart_html

                filename = f"{stem}.chart.html"
                path = paths.log_dir() / filename
                rows = [{k: "" if v is None else str(v) for k, v in row.items()} for row in data]
                if write_chart_html(rows, path, title=filename) is None:
                    return None
            else:
                filename = f"{stem}.csv"
                path = paths.log_dir() / filename
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                    writer.writeheader()
                    writer.writerows(data)

            print(f"[FusionLogger] Saved snapshot: {filename}")
            if self.on_snapshot_created:
                self.on_snapshot_created(reason, filename, None)
            return filename
        except Exception as e:
            print(f"[FusionLogger] Failed to save snapshot: {e}")
            return None
