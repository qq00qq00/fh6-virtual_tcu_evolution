"""Post-processing converter for replay logs.

After TelemetryLogger saves a .bin.gz file, this module converts it
to the user-selected output format.  When the target format is CSV,
the converter automatically splits output by race segments (is_race_on
transitions) and bundles roaming data separately.

The original .bin.gz file is always kept alongside any converted output.
"""

from __future__ import annotations

import csv
import json
import threading
from collections.abc import Callable
from io import StringIO
from pathlib import Path

from virtual_tcu.replay import format_text_line, telemetry_record
from virtual_tcu.telemetry.parser import parse_fh6_packet
from virtual_tcu.telemetry.replay_reader import iter_replay_records

# ---------------------------------------------------------------------------
# CSV auto-split helper
# ---------------------------------------------------------------------------


def _write_csv_file(path: Path, rows: list[dict]) -> None:
    """Write a list of dicts to a CSV file."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def convert_replay_csv_split(
    bin_gz_path: Path,
    *,
    base_name: str | None = None,
) -> list[Path]:
    """Convert a .bin.gz replay to auto-split CSV files.

    Returns a list of generated CSV file paths.

    Splitting rules:
    - Frames with is_race_on == 0 → roaming file
    - Each contiguous run of is_race_on == 1 → raceN file
    - Car ordinal is included in filenames
    """
    out_dir = bin_gz_path.parent
    if base_name is None:
        # tcu_replay_20260604_220500.bin.gz → replay_20260604_220500
        stem = bin_gz_path.stem  # tcu_replay_20260604_220500.bin
        if stem.endswith(".bin"):
            stem = stem[:-4]
        # Remove the tcu_ prefix for cleaner names
        if stem.startswith("tcu_"):
            stem = stem[4:]
        base_name = stem

    roaming_rows: list[dict] = []
    race_segments: list[list[dict]] = []
    current_race_rows: list[dict] = []
    prev_race_on = False
    car_ordinal: int = 0

    for rel_ms, raw in iter_replay_records(bin_gz_path):
        t = parse_fh6_packet(raw)
        if t is None:
            continue

        if t.car_ordinal and not car_ordinal:
            car_ordinal = t.car_ordinal

        row = telemetry_record(rel_ms, t)
        is_racing = bool(t.is_race_on)

        if is_racing:
            if not prev_race_on:
                # Transition 0→1: start a new race segment
                current_race_rows = []
            current_race_rows.append(row)
        else:
            if prev_race_on and current_race_rows:
                # Transition 1→0: end of a race segment
                race_segments.append(current_race_rows)
                current_race_rows = []
            roaming_rows.append(row)

        prev_race_on = is_racing

    # Flush any trailing race segment
    if current_race_rows:
        race_segments.append(current_race_rows)

    # Write output files
    generated: list[Path] = []

    if roaming_rows:
        roaming_path = out_dir / f"{base_name}_roaming.csv"
        _write_csv_file(roaming_path, roaming_rows)
        generated.append(roaming_path)

    for i, segment in enumerate(race_segments, start=1):
        seg_car = segment[0].get("car_ordinal", car_ordinal) or car_ordinal
        seg_path = out_dir / f"{base_name}_race{i}_car{seg_car}.csv"
        _write_csv_file(seg_path, segment)
        generated.append(seg_path)

    return generated


# ---------------------------------------------------------------------------
# Generic format converter
# ---------------------------------------------------------------------------


def convert_replay(
    bin_gz_path: Path,
    fmt: str,
) -> list[Path]:
    """Convert a .bin.gz replay log to the specified format.

    Returns a list of generated file paths. The original .bin.gz is kept.

    Supported formats:
    - 'bin.gz': no conversion needed (returns empty list)
    - 'csv': auto-split by race segment
    - 'csv_chart': HTML chart per segment (no CSV kept)
    - 'json': single JSON array file
    - 'jsonl': one JSON object per line
    - 'summary': text summary
    - 'text': human-readable text
    """
    if fmt == "bin.gz":
        return []  # Nothing to convert

    out_dir = bin_gz_path.parent
    stem = bin_gz_path.stem
    if stem.endswith(".bin"):
        stem = stem[:-4]
    if stem.startswith("tcu_"):
        stem = stem[4:]

    if fmt == "csv_chart":
        from virtual_tcu.telemetry.snapshot_chart import render_chart_html

        html_files: list[Path] = []
        for csv_path in convert_replay_csv_split(bin_gz_path, base_name=stem):
            html_path = csv_path.with_name(f"{csv_path.stem}.chart.html")
            chart = render_chart_html(csv_path, out_path=html_path, delete_source=True)
            if chart is not None:
                html_files.append(chart)
        return html_files

    if fmt == "csv":
        return convert_replay_csv_split(bin_gz_path, base_name=stem)

    # For non-CSV formats, produce a single output file
    if fmt in ("json", "jsonl"):
        out_path = out_dir / f"{stem}.{fmt}"
    else:
        out_path = out_dir / f"{stem}_{fmt}.txt"

    rows: list[dict] = []
    lines: list[str] = []
    prev_gear: int | None = None

    for rel_ms, raw in iter_replay_records(bin_gz_path):
        t = parse_fh6_packet(raw)
        if t is None:
            continue
        if fmt == "json":
            rows.append(telemetry_record(rel_ms, t))
        elif fmt == "jsonl":
            lines.append(json.dumps(telemetry_record(rel_ms, t), ensure_ascii=False))
        elif fmt == "text":
            lines.append(format_text_line(rel_ms, t, prev_gear=prev_gear))
        prev_gear = t.gear if t else prev_gear

    if fmt == "summary":
        # Use existing format_replay for summary
        from virtual_tcu.replay import format_replay

        buf = StringIO()
        format_replay(bin_gz_path, buf, fmt="summary", shift_only=False)
        out_path.write_text(buf.getvalue(), encoding="utf-8")
        return [out_path]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        if fmt == "json":
            json.dump(rows, f, ensure_ascii=False, indent=2)
            f.write("\n")
        elif fmt == "jsonl":
            f.write("\n".join(lines) + "\n")
        elif fmt == "text":
            f.write("\n".join(lines) + "\n")

    return [out_path]


# ---------------------------------------------------------------------------
# Async wrapper for use in the web server
# ---------------------------------------------------------------------------


def convert_replay_async(
    bin_gz_path: Path,
    fmt: str,
    *,
    on_done: Callable[[list[Path]], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    """Run convert_replay in a background thread."""

    def _worker():
        try:
            result = convert_replay(bin_gz_path, fmt)
            if on_done:
                on_done(result)
        except Exception as e:
            print(f"[LogConverter] conversion failed: {e}")
            if on_error:
                on_error(e)

    threading.Thread(target=_worker, daemon=True, name="log-converter").start()
