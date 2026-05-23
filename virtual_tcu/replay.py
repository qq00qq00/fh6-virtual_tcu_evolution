"""Format Virtual TCU replay logs (.bin / .bin.gz) to readable text."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import IO, Iterable, Optional, TextIO

from virtual_tcu.telemetry.model import Telemetry
from virtual_tcu.telemetry.parser import parse_fh6_packet
from virtual_tcu.telemetry.replay_reader import iter_replay_records


def _gear_label(gear: int) -> str:
    if gear == 0:
        return "R"
    if gear == 11:
        return "N"
    if gear > 11:
        return f"S{gear - 11}"
    return str(gear)


def format_text_line(rel_ms: int, t: Telemetry, *, prev_gear: Optional[int]) -> str:
    shift = ""
    if prev_gear is not None and t.gear != prev_gear:
        shift = f"  << {_gear_label(prev_gear)}->{_gear_label(t.gear)}"
    return (
        f"{rel_ms:7d} ms  "
        f"gear={_gear_label(t.gear):>2}  "
        f"rpm={t.current_rpm:6.0f}/{t.engine_max_rpm:.0f}  "
        f"speed={t.speed_kmh:6.1f} km/h  "
        f"T={t.throttle:.2f} B={t.brake:.2f}  "
        f"pwr={t.power_w / 1000:5.1f} kW  "
        f"trq={t.torque_nm:5.0f} Nm  "
        f"race={'Y' if t.is_race_on else 'N'}"
        f"{shift}"
    )


def format_csv_row(rel_ms: int, t: Telemetry) -> dict[str, str | int | float]:
    return {
        "time_ms": rel_ms,
        "gear": t.gear,
        "gear_label": _gear_label(t.gear),
        "rpm": round(t.current_rpm, 1),
        "max_rpm": round(t.engine_max_rpm, 1),
        "speed_kmh": round(t.speed_kmh, 2),
        "throttle": round(t.throttle, 3),
        "brake": round(t.brake, 3),
        "power_kw": round(t.power_w / 1000, 2),
        "torque_nm": round(t.torque_nm, 1),
        "boost": round(t.boost_raw, 3),
        "is_race_on": t.is_race_on,
        "car_ordinal": t.car_ordinal,
        "drivetrain": t.drivetrain_name,
        "is_shifting": int(t.is_shifting),
    }


def format_replay(
    path: Path,
    out: TextIO,
    *,
    fmt: str,
    shift_only: bool,
) -> dict:
    prev_gear: Optional[int] = None
    parsed = 0
    skipped = 0
    shifts = 0
    first_ms: Optional[int] = None
    last_ms: Optional[int] = None
    car_ordinal: Optional[int] = None
    csv_rows: list[dict] = []

    if fmt == "text":
        out.write(f"# file: {path.name}\n")

    for rel_ms, raw in iter_replay_records(path):
        if first_ms is None:
            first_ms = rel_ms
        last_ms = rel_ms
        t = parse_fh6_packet(raw)
        if t is None:
            skipped += 1
            continue
        if car_ordinal is None and t.car_ordinal:
            car_ordinal = t.car_ordinal

        gear_changed = prev_gear is not None and t.gear != prev_gear
        if gear_changed:
            shifts += 1
        include = not shift_only or gear_changed or prev_gear is None

        if fmt == "text" and include:
            out.write(format_text_line(rel_ms, t, prev_gear=prev_gear) + "\n")
        elif fmt == "csv" and include:
            csv_rows.append(format_csv_row(rel_ms, t))

        prev_gear = t.gear
        parsed += 1

    if fmt == "csv" and csv_rows:
        writer = csv.DictWriter(out, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    elif fmt == "summary":
        duration_s = ((last_ms or 0) - (first_ms or 0)) / 1000.0
        out.write(f"{path.name}\n")
        out.write(f"  packets: {parsed} parsed, {skipped} skipped\n")
        out.write(f"  duration: {duration_s:.2f} s\n")
        out.write(f"  gear changes: {shifts}\n")
        if car_ordinal is not None:
            out.write(f"  car_ordinal: {car_ordinal}\n")
        out.write("\n")

    duration_ms = (last_ms - first_ms) if first_ms is not None and last_ms is not None else 0
    return {
        "path": path,
        "parsed": parsed,
        "skipped": skipped,
        "shifts": shifts,
        "duration_ms": duration_ms,
        "car_ordinal": car_ordinal,
    }


def format_paths(
    paths: Iterable[Path],
    out: TextIO,
    *,
    fmt: str,
    shift_only: bool,
) -> None:
    path_list = list(paths)
    if not path_list:
        raise SystemExit("no input files matched")

    totals = {"parsed": 0, "skipped": 0, "shifts": 0}
    for i, path in enumerate(path_list):
        stats = format_replay(path, out, fmt=fmt, shift_only=shift_only)
        totals["parsed"] += stats["parsed"]
        totals["skipped"] += stats["skipped"]
        totals["shifts"] += stats["shifts"]

        if fmt == "text" and len(path_list) > 1 and i < len(path_list) - 1:
            out.write("\n")

    if len(path_list) > 1 and fmt == "text":
        out.write(
            f"\n# total: {totals['parsed']} packets, "
            f"{totals['skipped']} skipped, {totals['shifts']} gear changes\n"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Format Virtual TCU replay logs (.bin / .bin.gz) to readable output.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="replay log file(s), e.g. logs/tcu_replay_*.bin.gz",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="write to file instead of stdout",
    )
    parser.add_argument(
        "--format",
        choices=("text", "csv", "summary"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--shift-only",
        action="store_true",
        help="only print rows where gear changed",
    )
    return parser


def resolve_paths(patterns: Iterable[Path]) -> list[Path] | None:
    paths: list[Path] = []
    for pattern in patterns:
        if any(ch in str(pattern) for ch in "*?[]"):
            paths.extend(sorted(Path().glob(str(pattern))))
        elif pattern.exists():
            paths.append(pattern)
        else:
            print(f"[replay] file not found: {pattern}", file=sys.stderr)
            return None
    return paths


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    paths = resolve_paths(args.files)
    if paths is None:
        return 1

    out_io: IO[str]
    close_out = False
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        out_io = args.output.open("w", encoding="utf-8", newline="")
        close_out = True
    else:
        out_io = sys.stdout

    try:
        format_paths(paths, out_io, fmt=args.format, shift_only=args.shift_only)
    except ValueError as e:
        print(f"[replay] {e}", file=sys.stderr)
        return 1
    finally:
        if close_out:
            out_io.close()
            print(f"[replay] wrote {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
