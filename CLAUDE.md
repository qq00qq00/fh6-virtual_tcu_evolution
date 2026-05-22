# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Virtual TCU is a Windows-only external adaptive transmission controller for Forza Horizon 6. It reads real-time UDP telemetry from the game, makes shift decisions based on driving conditions, and injects keyboard inputs (E=upshift, Q=downshift) to control the in-game transmission.

## Running

```bash
python -m virtual_tcu
# or (backward compatible)
python virtual_tcu.py
```

Requires Windows (uses `winsound`, `keyboard` library needs admin for global key injection). Opens a web UI at http://127.0.0.1:8765 with live dashboard and settings.

## Dependencies

```bash
pip install -r requirements.txt
```

- `keyboard` — required, global hotkey registration and virtual key injection
- `aiohttp` — optional, enables the web UI (runs headless without it)
- `pypresence` — optional, Discord Rich Presence integration

## Architecture

Python package under `virtual_tcu/`. Entry point: `virtual_tcu/app.py`. No test suite.

```
virtual_tcu/
  app.py              # main(), hotkeys, async loop
  deps.py             # optional imports (keyboard, aiohttp, winsound)
  config/             # Cfg, DEFAULTS, ConfigStore
  telemetry/          # Telemetry model, FH6 parser, UDP receiver, replay logger
  input/              # VirtualKeyboard (E/Q injection)
  storage/            # ProfileStore (per-car JSON)
  core/               # Mode enum
  detectors/          # Reverse hold, airtime, yaw transient
  learning/           # Gear ratios, power curve, rev limiter, drive style
  state/              # Shift history, session stats, graph buffer, watchdog
  logic/tcu.py        # TCULogic — shift rules and drive modes
  web/                # WebServer + index.html dashboard
  integrations/       # Discord RPC
```

### Core Data Flow

1. **TelemetryReceiver** — UDP socket on port 5555, parses FH6's 324-byte packet into a `Telemetry` dataclass
2. **TCULogic.process()** — runs at 60Hz in the async loop, evaluates shift rules against current telemetry
3. **VirtualKeyboard** — fires E/Q keypresses in daemon threads with configurable hold duration
4. **WebServer** — aiohttp app serves `web/index.html` and broadcasts state over WebSocket at 30Hz

### Learning Systems (per-car, runtime only — not persisted)

- **GearRatioCalibrator** — learns rpm/kmh ratio per gear from telemetry samples; enables projected-RPM calculations for over-rev protection and target gear selection
- **PowerCurveDetector** — fits a parabola to (rpm_fraction, torque) samples; derives peak torque/power RPM analytically for optimal upshift points
- **RevLimiterDetector** — detects the real fuel-cut RPM (often below Forza's reported max) by identifying the sawtooth oscillation pattern at WOT
- **DriveStyleTracker** — continuous 0→1 sport index with asymmetric time constants (fast rise, slow decay); drives Dynamic mode's CRUISE/ADAPTIVE/SPORT regime selection

### Drive Modes

Each mode is a method on `TCULogic` (`_mode_comfort`, `_mode_dynamic`, `_mode_race`, `_mode_drift`, `_mode_offroad`). They share common building blocks: `_track_brake_down`, `_track_upshift_in_band`, `_track_out_of_band_kickdown`, and safety guards (anti-stall, over-rev, cornering lock, airtime lock, transient lock).

### Configuration

- `tcu_config.json` — all tunable parameters (shift points, feature toggles, hotkeys). Auto-created with defaults on first run. Editable live via web UI.
- `tcu_profiles.json` — per-car profile storage (keyed by car_ordinal)
- `logs/` — gzipped telemetry replay logs (binary format with `TCULOG01` magic header)

### Web UI

Vue 3 + TypeScript app in `web-ui/` using Tailwind CSS 4, vue-i18n (en + zh-CN). Path alias `@` → `web-ui/src/`.

```bash
cd web-ui
npm install
npm run dev          # port 5173, proxies /ws → localhost:8765
npm run build        # vue-tsc --noEmit + vite build → virtual_tcu/web/dist/
npm run lint         # eslint (flat config, @antfu/eslint-config)
npm run format       # prettier + prettier-plugin-tailwindcss
npm run typecheck    # vue-tsc --noEmit
```

Legacy `virtual_tcu/web/index.html` is served if `dist/` is absent.

WebSocket messages: `telemetry`, `state`, `config_reset`, `log_status`. Settings use `set_config` and persist immediately.

## Key Constants

- UDP port: 5555 (class `Cfg` in `config/constants.py`)
- Web UI port: 8765
- Shift keys: E (up), Q (down) — `input/keyboard.py`
- Packet size: 324 bytes (FH6 "Car Dash" format)
- Hotkeys: F9 (cycle mode), F8 (toggle log) — configurable

## Platform Constraint

Windows-only. `main()` exits immediately on non-win32 platforms. The `keyboard` library requires elevated privileges for global key injection on some systems.
