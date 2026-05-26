# Changelog

## [13.1.0] — 2026-05-27

### Added

- **Gamepad output mode** — choose between keyboard (E/Q) and virtual Xbox 360 controller (XInput) for shift injection. Gamepad mode uses `vgamepad` + ViGEmBus driver and supports 10 configurable button options (A/B/X/Y/LB/RB/DPAD…). Default mapping: **B** = upshift, **X** = downshift.
- **Per-car profile persistence** — learned gear ratios, power-curve data, and rev-limiter detection are now saved to `tcu_profiles.json` keyed by `(car_ordinal, car_class, PI)`. Data survives restarts and is restored automatically when you switch back to a previously-driven car+tune combination.
- **"Save & Restart Backend" button** in network and output-mode settings, so configuration changes that require a restart (IP/port/UDP port, output mode) can be applied in one click.
- **Gamepad button selector** — a dropdown (not free-text input) in both the Electron Settings and the Web UI for choosing gamepad shift buttons, showing descriptive labels like "A (bottom)", "LB (左肩键)".
- **Line-buffered stdout parsing** — prevents a rare 30 s startup timeout when the `[backend-ready]` marker is split across two OS pipe chunks.
- **Renderer sandbox enabled** on both the Settings and HUD `BrowserWindow` instances, blocking direct Node.js access from renderer processes (Electron security hardening).

### Changed

- **Output interface abstraction** — `VirtualKeyboard` is now `KeyboardOutput`, implementing the shared `OutputInterface` ABC. `TCULogic` and `ReverseHoldDetector` interact with the interface, making keyboard/gamepad backends fully interchangeable.
- **Vehicle identity** — the internal identifier for a car is now the composite `car_key = (car_ordinal, car_class, PI)` instead of bare `car_ordinal`. This fixes a long-standing bug where swapping to a differently-tuned copy of the same car model did not trigger a fresh learning cycle.
- **`vgamepad`** is now a regular (non-optional) Python dependency. If the ViGEmBus driver is not installed, switching to gamepad mode prints a clear error and automatically falls back to keyboard output.

### Fixed

- Same car model with different tune setups no longer silently reuses stale gear-ratio and power-curve data from the previous tune.
- `ProfileStore` was instantiated but never called at runtime — `tcu_profiles.json` was never created. Now works as documented.

---

# 更新日志

## [13.1.0] — 2026-05-27

### 新增

- **手柄输出模式** — 可选择键盘（E/Q）或虚拟 Xbox 360 手柄（XInput）来注入换挡指令。手柄模式使用 `vgamepad` + ViGEmBus 驱动，支持 10 种可配置按钮（A/B/X/Y/LB/RB/十字键…）。默认映射：**B** = 升挡，**X** = 降挡。
- **每车档案持久化** — 学习到的齿轮比、动力曲线和断油转速数据现在会按 `(car_ordinal, car_class, PI)` 三维度保存至 `tcu_profiles.json`。数据在重启后保留，切换回之前驾驶过的车辆+调校组合时自动恢复。
- **「保存并重启后端」按钮** — 在网络设置和输出模式卡片中，一键保存并重启后端，适用于需要重启才能生效的配置变更（IP/端口/UDP 端口、输出模式切换）。
- **手柄按钮选择器** — Electron 设置窗口和 Web UI 中均使用下拉框（而非文本输入）选择手柄换挡按键，带描述性标签如「A (底部)」「LB (左肩键)」。
- **行缓冲 stdout 解析** — 防止 `[backend-ready]` 标记在 OS 管道中被切分为两个 chunk 时导致的 30 秒超时启动失败。
- **启用渲染器沙箱** — Settings 和 HUD 两个 `BrowserWindow` 均启用 `sandbox: true`，阻止渲染进程直接访问 Node.js API（Electron 安全加固）。

### 变更

- **输出接口抽象** — `VirtualKeyboard` 现为 `KeyboardOutput`，实现统一的 `OutputInterface` 抽象基类。`TCULogic` 和 `ReverseHoldDetector` 通过接口交互，键盘/手柄后端可完全互换。
- **车辆标识** — 内部车辆标识符现为复合的 `car_key = (car_ordinal, car_class, PI)`，而非单独的 `car_ordinal`。修复了一个长期存在的 bug：切换到同一车型的不同调校时，学习系统不会触发新的学习周期。
- **`vgamepad`** 现为常规（非可选）Python 依赖。若 ViGEmBus 驱动未安装，切换到手柄模式时会打印清晰的错误提示并自动回退到键盘模式。

### 修复

- 同一车型的不同调校不再静默复用上一个调校的过期齿轮比和动力曲线数据。
- `ProfileStore` 之前被实例化但从未在运行时调用——`tcu_profiles.json` 从未被创建。现在按文档说明正常工作。
