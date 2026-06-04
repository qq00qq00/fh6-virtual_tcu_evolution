import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_snapshot(csv_path: str):
    """
    Reads a fusion snapshot CSV and plots the key telemetry curves
    (RPM, Throttle, Brake, Speed) leading up to an event.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"Error: Could not find file {csv_path}")
        return

    print(f"Loading {path.name}...")
    df = pd.read_csv(path)

    # We want time on the X axis, zeroed out at the event trigger (usually near the end).
    # Since it's a 4-second buffer (3s before, 1s after), we'll just plot by raw time.
    # The 'timestamp' column is UNIX epoch, so we normalize it to start from 0.
    if "timestamp_ms" in df.columns:
        df["time_sec"] = (df["timestamp_ms"] - df["timestamp_ms"].iloc[0]) / 1000.0
        x_col = "time_sec"
    else:
        # Fallback if no timestamp
        df["frame_idx"] = df.index
        x_col = "frame_idx"

    # Setup the plot with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"Fusion Snapshot: {path.name}", fontsize=14, fontweight="bold")

    # Subplot 1: RPM vs Speed
    ax1.set_title("Engine RPM % vs Speed")
    if "rpm_pct" in df.columns:
        ax1.plot(df[x_col], df["rpm_pct"], color="blue", label="Engine RPM %", linewidth=2)
    ax1.set_ylabel("RPM %")
    ax1.grid(True, linestyle="--", alpha=0.6)

    # Add speed on secondary Y axis
    if "speed_kmh" in df.columns:
        ax1_speed = ax1.twinx()
        ax1_speed.plot(
            df[x_col], df["speed_kmh"], color="purple", label="Speed (km/h)", linestyle="--"
        )
        ax1_speed.set_ylabel("Speed (km/h)")

    # Legend for top subplot
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    if "speed_kmh" in df.columns:
        lines_1_s, labels_1_s = ax1_speed.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_1_s, labels_1 + labels_1_s, loc="upper left")
    else:
        ax1.legend(loc="upper left")

    # Subplot 2: Pedals (Throttle / Brake)
    ax2.set_title("Driver Inputs (Throttle / Brake)")
    if "throttle" in df.columns:
        ax2.plot(df[x_col], df["throttle"], color="green", label="Throttle %", linewidth=2)
    if "brake" in df.columns:
        ax2.plot(df[x_col], df["brake"], color="red", label="Brake %", linewidth=2)
    ax2.set_ylabel("Pedal %")
    ax2.set_ylim(-5, 105)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper left")

    # Subplot 3: TCU State / Gear / Slip
    ax3.set_title("TCU Internal State & Slip")
    if "gear" in df.columns:
        ax3.step(df[x_col], df["gear"], color="orange", label="Current Gear", linewidth=2)
        ax3.set_ylabel("Gear", color="orange")

    # Plot slip ratio on secondary axis if available
    ax3_slip = ax3.twinx()
    if "max_slip_ratio" in df.columns:
        ax3_slip.plot(
            df[x_col], df["max_slip_ratio"], color="cyan", label="Max Slip Ratio", linewidth=1.5
        )
        ax3_slip.set_ylabel("Slip Ratio", color="cyan")

    # Highlight the exact moment of the snapshot trigger
    # Since we keep 1 sec post-event (approx 60 frames), the event is near len(df) - 60
    trigger_idx = max(0, len(df) - 60)
    trigger_time = df[x_col].iloc[trigger_idx]
    for ax in [ax1, ax2, ax3]:
        ax.axvline(x=trigger_time, color="red", linestyle=":", label="Snapshot Trigger")

    lines_3, labels_3 = ax3.get_legend_handles_labels()
    lines_3_s, labels_3_s = ax3_slip.get_legend_handles_labels()
    ax3.legend(lines_3 + lines_3_s, labels_3 + labels_3_s, loc="upper left")

    ax3.set_xlabel("Time (seconds)")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Fusion Snapshot CSV data")
    parser.add_argument("csv_file", help="Path to the snapshot CSV file in the logs/ folder")
    args = parser.parse_args()
    plot_snapshot(args.csv_file)
