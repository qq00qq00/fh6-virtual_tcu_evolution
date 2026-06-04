"""Build self-contained HTML telemetry charts (no CSV export in app save path)."""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path


def _parse_float(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _time_axis(rows: list[dict[str, str]]) -> list[float]:
    if not rows:
        return []
    if "timestamp_ms" in rows[0]:
        t0 = _parse_float(rows[0]["timestamp_ms"])
        return [(_parse_float(r["timestamp_ms"]) - t0) / 1000.0 for r in rows]
    if "time_ms" in rows[0]:
        t0 = _parse_float(rows[0]["time_ms"])
        return [(_parse_float(r["time_ms"]) - t0) / 1000.0 for r in rows]
    return [float(i) for i in range(len(rows))]


def _x_axis_label(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "Time (s)"
    if "timestamp_ms" in rows[0] or "time_ms" in rows[0]:
        return "Time (s)"
    return "Frame"


def _series(rows: list[dict[str, str]], key: str) -> list[float | None]:
    if not rows or key not in rows[0]:
        return []
    return [_parse_float(r.get(key)) for r in rows]


def _slip_series(rows: list[dict[str, str]]) -> list[float | None]:
    if not rows:
        return []
    if "max_slip_ratio" in rows[0]:
        return [_parse_float(r.get("max_slip_ratio")) for r in rows]
    front = _series(rows, "front_slip")
    rear = _series(rows, "rear_slip")
    if front and rear:
        return [max(f, r) for f, r in zip(front, rear, strict=False)]
    return front or rear


def _scale(
    values: list[float | None], lo_pad: float = 0.05, hi_pad: float = 0.05
) -> tuple[float, float]:
    nums = [v for v in values if v is not None]
    if not nums:
        return 0.0, 1.0
    lo, hi = min(nums), max(nums)
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    return lo - span * lo_pad, hi + span * hi_pad


def _combined_scale(
    series: list[tuple[str, list[float | None], str, bool]],
) -> tuple[float, float]:
    vals: list[float | None] = []
    for _, ys, _, _ in series:
        vals.extend(ys)
    return _scale(vals)


def _format_tick(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2g}"


def _linear_ticks(y_min: float, y_max: float, count: int = 5) -> list[float]:
    if count < 2:
        return [y_min, y_max]
    step = (y_max - y_min) / (count - 1)
    return [y_min + i * step for i in range(count)]


class _ChartGeom:
    """Plot area geometry with room for axis labels and ticks."""

    def __init__(self, width: int, height: int, *, dual_y: bool) -> None:
        self.width = width
        self.height = height
        self.left = 58
        self.right = width - (52 if dual_y else 16)
        self.top = 26
        self.bottom = height - 42
        self.plot_w = self.right - self.left
        self.plot_h = self.bottom - self.top

    def px(self, x: float, xs: list[float]) -> float:
        x0, x1 = xs[0], xs[-1]
        span = (x1 - x0) or 1.0
        return self.left + (x - x0) / span * self.plot_w

    def py(self, y: float, y_min: float, y_max: float) -> float:
        span = (y_max - y_min) or 1.0
        return self.top + (1.0 - (y - y_min) / span) * self.plot_h


def _polyline(
    geom: _ChartGeom,
    xs: list[float],
    ys: list[float | None],
    *,
    y_min: float,
    y_max: float,
    color: str,
    stroke_width: float = 2,
    step: bool = False,
) -> str:
    if not xs or y_max <= y_min:
        return ""

    points: list[tuple[float, float]] = []
    for x, y in zip(xs, ys, strict=False):
        if y is None:
            continue
        points.append((geom.px(x, xs), geom.py(y, y_min, y_max)))

    if len(points) < 2:
        if not points:
            return ""
        x, y = points[0]
        return (
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="{color}" '
            f'stroke="{color}" stroke-width="{stroke_width}"/>'
        )

    if step:
        d_parts = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
        for (_, y_prev), (x_cur, y_cur) in zip(points, points[1:], strict=False):
            d_parts.append(f"L {x_cur:.2f} {y_prev:.2f} L {x_cur:.2f} {y_cur:.2f}")
        d = " ".join(d_parts)
    else:
        d = " ".join(
            (f"{'M' if i == 0 else 'L'} {x:.2f} {y:.2f}" for i, (x, y) in enumerate(points))
        )
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke_width}"/>'


def _vline(geom: _ChartGeom, xs: list[float], trigger_idx: int) -> str:
    if not xs or trigger_idx < 0 or trigger_idx >= len(xs):
        return ""
    x = geom.px(xs[trigger_idx], xs)
    return (
        f'<line x1="{x:.2f}" y1="{geom.top}" x2="{x:.2f}" y2="{geom.bottom:.2f}" '
        f'stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 3"/>'
    )


def _axis_layer(
    geom: _ChartGeom,
    xs: list[float],
    *,
    x_label: str,
    y_left: tuple[str, float, float] | None,
    y_right: tuple[str, float, float] | None,
) -> str:
    parts: list[str] = [
        f'<rect x="{geom.left}" y="{geom.top}" width="{geom.plot_w}" '
        f'height="{geom.plot_h}" fill="#0f172a" rx="4"/>',
        f'<line x1="{geom.left}" y1="{geom.bottom}" x2="{geom.right}" y2="{geom.bottom}" '
        f'class="axis-line"/>',
    ]

    if y_left:
        label, y_min, y_max = y_left
        parts.append(
            f'<line x1="{geom.left}" y1="{geom.top}" x2="{geom.left}" y2="{geom.bottom}" '
            f'class="axis-line"/>'
        )
        cy = geom.top + geom.plot_h / 2
        parts.append(
            f'<text x="14" y="{cy:.2f}" transform="rotate(-90 14 {cy:.2f})" '
            f'text-anchor="middle" class="axis-title">{escape(label)}</text>'
        )
        for tick in _linear_ticks(y_min, y_max):
            y = geom.py(tick, y_min, y_max)
            parts.append(
                f'<line x1="{geom.left}" y1="{y:.2f}" x2="{geom.right}" y2="{y:.2f}" '
                f'class="grid-line"/>'
            )
            parts.append(
                f'<line x1="{geom.left - 4}" y1="{y:.2f}" x2="{geom.left}" y2="{y:.2f}" '
                f'class="tick-line"/>'
            )
            parts.append(
                f'<text x="{geom.left - 8}" y="{y + 3.5:.2f}" text-anchor="end" '
                f'class="tick-label">{_format_tick(tick)}</text>'
            )

    if y_right:
        label, y_min, y_max = y_right
        parts.append(
            f'<line x1="{geom.right}" y1="{geom.top}" x2="{geom.right}" y2="{geom.bottom}" '
            f'class="axis-line"/>'
        )
        cy = geom.top + geom.plot_h / 2
        parts.append(
            f'<text x="{geom.width - 10}" y="{cy:.2f}" '
            f'transform="rotate(90 {geom.width - 10:.2f} {cy:.2f})" '
            f'text-anchor="middle" class="axis-title">{escape(label)}</text>'
        )
        for tick in _linear_ticks(y_min, y_max):
            y = geom.py(tick, y_min, y_max)
            parts.append(
                f'<line x1="{geom.right}" y1="{y:.2f}" x2="{geom.right + 4}" y2="{y:.2f}" '
                f'class="tick-line"/>'
            )
            parts.append(
                f'<text x="{geom.right + 8}" y="{y + 3.5:.2f}" text-anchor="start" '
                f'class="tick-label">{_format_tick(tick)}</text>'
            )

    if xs:
        x0, x1 = xs[0], xs[-1]
        for tick in _linear_ticks(x0, x1):
            x = geom.px(tick, xs)
            parts.append(
                f'<line x1="{x:.2f}" y1="{geom.top}" x2="{x:.2f}" y2="{geom.bottom}" '
                f'class="grid-line"/>'
            )
            parts.append(
                f'<line x1="{x:.2f}" y1="{geom.bottom}" x2="{x:.2f}" '
                f'y2="{geom.bottom + 4}" class="tick-line"/>'
            )
            parts.append(
                f'<text x="{x:.2f}" y="{geom.bottom + 16}" text-anchor="middle" '
                f'class="tick-label">{_format_tick(tick)}</text>'
            )

    cx = geom.left + geom.plot_w / 2
    parts.append(
        f'<text x="{cx:.2f}" y="{geom.height - 6}" text-anchor="middle" '
        f'class="axis-title">{escape(x_label)}</text>'
    )
    return "\n    ".join(parts)


def _panel_svg(
    title: str,
    xs: list[float],
    series: list[tuple[str, list[float | None], str, bool]],
    *,
    width: int = 720,
    height: int = 220,
    trigger_idx: int | None = None,
    y2_series: list[tuple[str, list[float | None], str]] | None = None,
    x_label: str = "Time (s)",
    y_left_label: str | None = None,
    y_right_label: str | None = None,
    shared_left_scale: bool = False,
) -> str:
    dual_y = bool(y2_series)
    geom = _ChartGeom(width, height, dual_y=dual_y)

    if series:
        y_left_min, y_left_max = (
            _combined_scale(series) if shared_left_scale else _scale(series[0][1])
        )
    else:
        y_left_min, y_left_max = 0.0, 1.0

    y_right_min, y_right_max = (0.0, 1.0)
    if y2_series:
        y_right_min, y_right_max = _scale(y2_series[0][1])

    paths = ""
    for _, ys, color, step in series:
        y_min, y_max = (y_left_min, y_left_max) if shared_left_scale else _scale(ys)
        paths += _polyline(geom, xs, ys, y_min=y_min, y_max=y_max, color=color, step=step)

    y2_paths = ""
    if y2_series:
        for _, ys, color in y2_series:
            y2_paths += _polyline(
                geom,
                xs,
                ys,
                y_min=y_right_min,
                y_max=y_right_max,
                color=color,
            )

    axes = _axis_layer(
        geom,
        xs,
        x_label=x_label,
        y_left=(y_left_label, y_left_min, y_left_max) if y_left_label and series else None,
        y_right=(y_right_label, y_right_min, y_right_max) if y_right_label and y2_series else None,
    )
    vline = _vline(geom, xs, trigger_idx) if trigger_idx is not None else ""
    legend = " ".join(
        f'<span class="lg"><i style="background:{color}"></i>{escape(label)}</span>'
        for label, _, color, _ in series
    )
    if y2_series:
        legend += " " + " ".join(
            f'<span class="lg"><i style="background:{color}"></i>{escape(label)}</span>'
            for label, _, color in y2_series
        )

    return f"""
<section class="panel">
  <h3>{escape(title)}</h3>
  <div class="legend">{legend}</div>
  <svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img">
    {axes}
    {paths}{y2_paths}{vline}
  </svg>
</section>"""


def _chart_rows_to_html(rows: list[dict[str, str]], title: str) -> str | None:
    if not rows:
        return None

    xs = _time_axis(rows)
    x_label = _x_axis_label(rows)
    trigger_idx = max(0, len(xs) - 60) if len(xs) > 1 else 0

    rpm = _series(rows, "rpm_pct")
    speed = _series(rows, "speed_kmh")
    throttle = _series(rows, "throttle")
    brake = _series(rows, "brake")
    gear = _series(rows, "gear")
    slip = _slip_series(rows)

    panels = [
        _panel_svg(
            "Engine RPM % vs Speed",
            xs,
            [("RPM %", rpm, "#3b82f6", False)] if rpm else [],
            y2_series=[("Speed (km/h)", speed, "#a855f7")] if speed else None,
            trigger_idx=trigger_idx,
            x_label=x_label,
            y_left_label="RPM %" if rpm else None,
            y_right_label="Speed (km/h)" if speed else None,
        ),
        _panel_svg(
            "Driver Inputs (Throttle / Brake)",
            xs,
            [
                *([("Throttle %", throttle, "#22c55e", False)] if throttle else []),
                *([("Brake %", brake, "#ef4444", False)] if brake else []),
            ],
            trigger_idx=trigger_idx,
            x_label=x_label,
            y_left_label="Pedal %" if throttle or brake else None,
            shared_left_scale=True,
        ),
        _panel_svg(
            "TCU State & Slip",
            xs,
            [("Gear", gear, "#f97316", True)] if gear else [],
            y2_series=[("Max slip", slip, "#22d3ee")] if slip else None,
            trigger_idx=trigger_idx,
            x_label=x_label,
            y_left_label="Gear" if gear else None,
            y_right_label="Slip ratio" if slip else None,
        ),
    ]

    body = "\n".join(panels)
    safe_title = escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{safe_title}</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #020617; color: #e2e8f0; }}
    header {{ padding: 16px 20px; border-bottom: 1px solid #1e293b; }}
    header h1 {{ margin: 0; font-size: 1.1rem; }}
    header p {{ margin: 6px 0 0; color: #94a3b8; font-size: 0.85rem; }}
    main {{ padding: 12px 16px 24px; max-width: 960px; margin: 0 auto; }}
    .panel {{ margin-bottom: 18px; }}
    .panel h3 {{ margin: 0 0 8px; font-size: 0.95rem; }}
    .legend {{ margin-bottom: 6px; font-size: 0.8rem; color: #cbd5e1; }}
    .lg {{ margin-right: 12px; }}
    .lg i {{
      display: inline-block; width: 10px; height: 10px; border-radius: 2px;
      margin-right: 4px; vertical-align: middle;
    }}
    svg {{ background: #0b1220; border-radius: 8px; border: 1px solid #1e293b; }}
    .axis-title {{ fill: #94a3b8; font-size: 11px; font-family: system-ui, sans-serif; }}
    .tick-label {{ fill: #64748b; font-size: 10px; font-family: system-ui, sans-serif; }}
    .axis-line {{ stroke: #475569; stroke-width: 1.2; }}
    .tick-line {{ stroke: #475569; stroke-width: 1; }}
    .grid-line {{ stroke: #1e293b; stroke-width: 1; }}
  </style>
</head>
<body>
  <header>
    <h1>{safe_title}</h1>
    <p>red dashed line ≈ snapshot trigger</p>
  </header>
  <main>
{body}
  </main>
</body>
</html>
"""


def write_chart_html(
    rows: list[dict[str, str]], out_path: Path, *, title: str | None = None
) -> Path | None:
    """Write chart HTML to *out_path* from in-memory rows."""
    html = _chart_rows_to_html(rows, title or out_path.name)
    if html is None:
        return None
    out_path = Path(out_path)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"[SnapshotChart] Wrote {out_path.name}")
        return out_path
    except OSError as e:
        print(f"[SnapshotChart] Failed to write chart: {e}")
        return None


def render_chart_html(
    csv_path: Path,
    *,
    out_path: Path | None = None,
    delete_source: bool = False,
) -> Path | None:
    """Build chart HTML from a CSV file (CLI / temp export)."""
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        return None
    rows = _load_rows(csv_path)
    dest = out_path or (csv_path.parent / f"{csv_path.stem}.chart.html")
    result = write_chart_html(rows, dest, title=csv_path.name)
    if result and delete_source:
        try:
            csv_path.unlink(missing_ok=True)
        except OSError:
            pass
    return result
