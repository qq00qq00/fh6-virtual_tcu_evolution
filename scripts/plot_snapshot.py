import argparse
from pathlib import Path

from virtual_tcu.telemetry.snapshot_chart import render_chart_html


def plot_snapshot(csv_path: str, *, html: bool = False, show: bool = True):
    """Plot or export HTML chart for a fusion / telemetry CSV."""
    path = Path(csv_path)
    if not path.exists():
        print(f"Error: Could not find file {csv_path}")
        return

    if html:
        out = render_chart_html(path)
        if out:
            print(f"Wrote {out}")
        return

    try:
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError:
        print("matplotlib/pandas not installed; use --html for chart export")
        out = render_chart_html(path)
        if out:
            print(f"Wrote {out}")
        return

    print(f"Loading {path.name}...")
    df = pd.read_csv(path)

    if "timestamp_ms" in df.columns:
        df["time_sec"] = (df["timestamp_ms"] - df["timestamp_ms"].iloc[0]) / 1000.0
        x_col = "time_sec"
    else:
        df["frame_idx"] = df.index
        x_col = "frame_idx"

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"Fusion Snapshot: {path.name}", fontsize=14, fontweight="bold")

    ax1.set_title("Engine RPM % vs Speed")
    if "rpm_pct" in df.columns:
        ax1.plot(df[x_col], df["rpm_pct"], color="blue", label="Engine RPM %", linewidth=2)
    ax1.set_ylabel("RPM %")
    ax1.grid(True, linestyle="--", alpha=0.6)

    if "speed_kmh" in df.columns:
        ax1_speed = ax1.twinx()
        ax1_speed.plot(
            df[x_col], df["speed_kmh"], color="purple", label="Speed (km/h)", linestyle="--"
        )
        ax1_speed.set_ylabel("Speed (km/h)")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    if "speed_kmh" in df.columns:
        lines_1_s, labels_1_s = ax1_speed.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_1_s, labels_1 + labels_1_s, loc="upper left")
    else:
        ax1.legend(loc="upper left")

    ax2.set_title("Driver Inputs (Throttle / Brake)")
    if "throttle" in df.columns:
        ax2.plot(df[x_col], df["throttle"], color="green", label="Throttle %", linewidth=2)
    if "brake" in df.columns:
        ax2.plot(df[x_col], df["brake"], color="red", label="Brake %", linewidth=2)
    ax2.set_ylabel("Pedal %")
    ax2.set_ylim(-5, 105)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper left")

    ax3.set_title("TCU Internal State & Slip")
    if "gear" in df.columns:
        ax3.step(df[x_col], df["gear"], color="orange", label="Current Gear", linewidth=2)
        ax3.set_ylabel("Gear", color="orange")

    ax3_slip = ax3.twinx()
    if "max_slip_ratio" in df.columns:
        ax3_slip.plot(
            df[x_col], df["max_slip_ratio"], color="cyan", label="Max Slip Ratio", linewidth=1.5
        )
        ax3_slip.set_ylabel("Slip Ratio", color="cyan")

    trigger_idx = max(0, len(df) - 60)
    trigger_time = df[x_col].iloc[trigger_idx]
    for ax in [ax1, ax2, ax3]:
        ax.axvline(x=trigger_time, color="red", linestyle=":", label="Snapshot Trigger")

    lines_3, labels_3 = ax3.get_legend_handles_labels()
    lines_3_s, labels_3_s = ax3_slip.get_legend_handles_labels()
    ax3.legend(lines_3 + lines_3_s, labels_3 + labels_3_s, loc="upper left")

    ax3.set_xlabel("Time (seconds)")
    plt.tight_layout()
    if show:
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Fusion Snapshot CSV data")
    parser.add_argument("csv_file", help="Path to the snapshot CSV file in the logs/ folder")
    parser.add_argument(
        "--html",
        action="store_true",
        help="Write self-contained .chart.html (no matplotlib)",
    )
    args = parser.parse_args()
    plot_snapshot(args.csv_file, html=args.html, show=not args.html)
