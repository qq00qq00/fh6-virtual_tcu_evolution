import gzip
import struct
import threading
import time
from collections import deque
from pathlib import Path
from typing import BinaryIO

from virtual_tcu import paths
from virtual_tcu.config.constants import Cfg

LOG_MAGIC = b"TCULOG01"

RAW_FORMATS = {"bin.gz", "bin"}
EXPORT_FORMATS = {"txt", "text", "csv", "csv_chart", "json", "jsonl", "summary"}
LOG_FORMATS = RAW_FORMATS | EXPORT_FORMATS


def _normalize_format(output_format: str) -> str:
    output_format = output_format.strip().lower()
    if output_format == "text":
        return "txt"
    return output_format if output_format in LOG_FORMATS else "bin.gz"


def _target_suffix(output_format: str) -> str:
    if output_format in ("txt", "summary"):
        return "txt"
    if output_format == "csv_chart":
        return "chart.html"
    return output_format


def _replay_format(output_format: str) -> str:
    if output_format == "txt":
        return "text"
    if output_format == "csv_chart":
        return "csv"
    return output_format


class TelemetryLogger:
    """Records UDP packets to gzip log. Modes: events (pre-event buffer
    + post-event tail), all (every packet). Auto-stops at LOG_MAX_MB."""

    def __init__(self):
        self._lock = threading.Lock()
        self._mode = "off"
        self._file: BinaryIO | None = None
        self._path: Path | None = None
        self._target_path: Path | None = None
        self._format = "bin.gz"
        self._start_time = 0.0
        self._packets_logged = 0
        self._bytes_written = 0
        self._buffer: deque[tuple] = deque(maxlen=60)
        self._post_event_remaining = 0

    @property
    def is_recording(self) -> bool:
        return self._file is not None

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def status(self) -> dict:
        return {
            "mode": self._mode,
            "recording": self.is_recording,
            "packets": self._packets_logged,
            "size_kb": self._bytes_written // 1024,
            "file": self._target_path.name if self._target_path else None,
            "format": self._format,
        }

    def start(self, mode: str, output_format: str = "bin.gz") -> bool:
        if self.is_recording:
            self.stop()
        if mode not in ("events", "all"):
            return False
        output_format = _normalize_format(output_format)
        ts = time.strftime("%Y%m%d_%H%M%S")
        target_path = (
            paths.log_dir() / f"{Cfg.LOG_FILE_PREFIX}_{ts}.{_target_suffix(output_format)}"
        )
        capture_path = (
            target_path
            if output_format in RAW_FORMATS
            else paths.log_dir() / f".{Cfg.LOG_FILE_PREFIX}_{ts}.capture.bin.gz"
        )
        with self._lock:
            try:
                f: BinaryIO
                if capture_path.suffix == ".gz":
                    f = gzip.open(capture_path, "wb", compresslevel=6)
                else:
                    f = capture_path.open("wb")
                f.write(LOG_MAGIC)
                self._file = f
                self._path = capture_path
                self._target_path = target_path
                self._format = output_format
                self._mode = mode
                self._start_time = time.time()
                self._packets_logged = 0
                self._bytes_written = len(LOG_MAGIC)
                self._buffer.clear()
                self._post_event_remaining = 0
                return True
            except Exception as e:
                print(f"[Logger] start failed: {e}")
                self._file = None
                return False

    def stop(self, *, discard: bool = False) -> str | None:
        with self._lock:
            if self._file is None:
                return None
            try:
                self._file.close()
            except Exception:
                pass
            capture_path = self._path
            target_path = self._target_path or self._path
            output_format = self._format
            self._file = None
            self._mode = "off"

        if capture_path is None:
            return None
        if discard:
            try:
                capture_path.unlink(missing_ok=True)
            except Exception:
                pass
            return None
        if output_format in RAW_FORMATS:
            return str(capture_path)
        if target_path is None:
            return None
        try:
            from virtual_tcu.replay import format_paths

            if output_format == "csv_chart":
                import tempfile

                from virtual_tcu.telemetry.snapshot_chart import render_chart_html

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".csv",
                    delete=False,
                    encoding="utf-8",
                    newline="",
                ) as tmp:
                    format_paths([capture_path], tmp, fmt="csv", shift_only=False)
                    tmp_path = Path(tmp.name)
                chart_path = render_chart_html(tmp_path, out_path=target_path, delete_source=True)
                try:
                    capture_path.unlink(missing_ok=True)
                except Exception:
                    pass
                return str(chart_path) if chart_path else None

            with target_path.open("w", encoding="utf-8", newline="") as out:
                format_paths(
                    [capture_path],
                    out,
                    fmt=_replay_format(output_format),
                    shift_only=False,
                )
            try:
                capture_path.unlink(missing_ok=True)
            except Exception:
                pass
            return str(target_path)
        except Exception as e:
            print(f"[Logger] export failed: {e}")
            return str(capture_path)

    def mark_event(self):
        with self._lock:
            if self._file is None or self._mode != "events":
                return
            for buf_ms, buf_raw in self._buffer:
                self._write_record_locked(buf_ms, buf_raw)
            self._buffer.clear()
            self._post_event_remaining = 30

    def write_packet(self, raw: bytes):
        with self._lock:
            if self._file is None or not raw:
                return
            if self._bytes_written >= Cfg.LOG_MAX_MB * 1024 * 1024:
                pass
            else:
                rel_ms = int((time.time() - self._start_time) * 1000)
                if self._mode == "all":
                    self._write_record_locked(rel_ms, raw)
                    return
                self._buffer.append((rel_ms, raw))
                if self._post_event_remaining > 0:
                    self._write_record_locked(rel_ms, raw)
                    self._post_event_remaining -= 1
                return
        self.stop()

    def _write_record_locked(self, rel_ms: int, raw: bytes):
        try:
            header = struct.pack("<IH", rel_ms, len(raw))
            if self._file is None:
                return
            self._file.write(header)
            self._file.write(raw)
            self._bytes_written += 6 + len(raw)
            self._packets_logged += 1
        except Exception as e:
            print(f"[Logger] write error: {e}")
            try:
                if self._file is not None:
                    self._file.close()
            except Exception:
                pass
            self._file = None
            self._mode = "off"
