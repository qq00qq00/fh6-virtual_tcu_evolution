# Changelog

## [Unreleased]

### Removed

- **Virtual XInput gamepad output mode** — removed entirely (`GamepadOutput`, `vgamepad`/ViGEmBus dependency, the bundled `driver/ViGEmBusSetup_x64.msi`, the `installViGEmBus`/`check_gamepad` IPC + WebSocket paths, and all gamepad button settings/locales). As a second XInput device it sent a full controller-state packet on every shift, zeroing the player's steering/throttle and making cornering feel laggy/unresponsive; mirroring only the brake (LT) could not fix steering, and the conflict-free alternative (HidHide full passthrough) would add a new real-time latency path and cannot serve force-feedback wheels. Output is now **keyboard** (default) or **vJoy**. Saved configs with `output_mode: "gamepad"` automatically fall back to keyboard.
- **`OutputInterface.set_brake`** — only the virtual gamepad needed the brake mirror; removed from the interface and the TCU loop.

## [13.1.2] — 2026-05-29

### Added

- **HTTP health polling for Electron backend ready** — the main process treats aiohttp as ready when localhost responds, in addition to the `[backend-ready]` stdout marker.
- **ViGEmBus MSI integrity check** — Electron verifies the SHA-256 of the bundled installer before launching it.

### Changed

- **Electron backend lifecycle module** — spawn/stop/restart moved to `BackendLifecycle` with serialized restart, async process-tree kill, and `readline` stdout parsing.
- **IPC action results** — `openExternal` and `installViGEmBus` return `{ ok, error }` for clearer error handling in the settings UI.

### Fixed

- **Backend crash on Japanese Windows (cp932)** — force UTF-8 on stdout/stderr and use ASCII-safe console log text so PyInstaller builds no longer exit before the web server starts.
- **Concurrent backend restart race** — tray and IPC restart no longer spawn overlapping Python processes when triggered in quick succession.

### Security

- **`open-external` URL policy** — block localhost, private IPs, and link-local hosts from renderer-initiated `shell.openExternal` (manual LAN dashboard access in an external browser is unchanged).

---

## [13.1.1] — 2026-05-27

### Added

- **ViGEmBus driver installer bundled** — `driver/ViGEmBusSetup_x64.msi` is included in the Electron installer (`resources/driver/`) and published in the repo for direct download. Settings UI shows an **Install Driver** button that launches the bundled MSI.
- **Gamepad driver pre-check** — switching to gamepad mode in settings runs a WebSocket `check_gamepad` probe before saving config, with localized error prompts and an install shortcut when the driver is missing.
- **`effective_output_mode` in WebSocket init** — the dashboard now knows whether the backend is actually running keyboard or gamepad output (config alone may differ until restart).

### Changed

- **Lightweight gamepad availability check** — the probe now opens a transient ViGEmBus connection instead of spawning a temporary virtual XInput device, avoiding ghost controllers and false "driver not installed" errors while a gamepad is already active.
- **PyInstaller vgamepad bundling** — `virtual_tcu.spec` collects `ViGEmClient.dll` and vgamepad hidden imports without importing the package at build time (CI/build hosts do not need ViGEmBus installed).
- **Lazy vgamepad import** — removed the startup `import vgamepad` from `deps.py` so keyboard mode still launches if the gamepad client DLL is unavailable.
- **`installViGEmBus` refactored** into the settings store for cleaner encapsulation across Electron and Web UI contexts.

### Fixed

- **Packaged backend crash on startup** — PyInstaller now bundles `ViGEmClient.dll` under `vgamepad/win/vigem/client/{x64,x86}/`, fixing `FileNotFoundError` in release builds.
- **False gamepad driver detection** — skip the probe when the backend is already in gamepad mode; increased check timeout to 8 s for cold PyInstaller imports.
- **Electron backend lifecycle** — kill hung/orphaned backend processes on restart; validate HTTP/HTTPS URLs before `openExternal`; ensure backend shuts down cleanly on app quit.

---

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

## [13.1.2] — 2026-05-29

### 新增

- **Electron 后端 HTTP 健康探测** — 除 stdout `[backend-ready]` 外，主进程通过本机 HTTP 响应判断 aiohttp 是否已就绪。
- **ViGEmBus MSI 完整性校验** — 启动安装包前校验内置 MSI 的 SHA-256，防止被篡改后静默执行。

### 变更

- **Electron 后端生命周期模块** — 抽离 `BackendLifecycle`，重启互斥、异步进程树杀灭、`readline` 按行解析 stdout。
- **IPC 结构化返回** — `openExternal` 与 `installViGEmBus` 返回 `{ ok, error }`，设置页可展示明确错误。

### 修复

- **日文 Windows (cp932) 启动崩溃** — 强制 stdout/stderr 使用 UTF-8，控制台日志改为 ASCII 安全字符，避免打包版在 banner 处 `UnicodeEncodeError` 导致一直 disconnected。
- **并发重启竞态** — 托盘/IPC 快速连点「重启后端」不再重叠拉起多个 Python 进程。

### 安全

- **`open-external` URL 策略** — 拦截渲染进程发起的 localhost、内网与 link-local 链接（用户在其它设备浏览器手动访问局域网仪表板不受影响）。

---

## [13.1.1] — 2026-05-27

### 新增

- **内置 ViGEmBus 驱动安装包** — `driver/ViGEmBusSetup_x64.msi` 随 Electron 安装包分发（`resources/driver/`），并上传至仓库供直接下载。设置页提供 **安装驱动** 按钮，一键启动内置 MSI。
- **手柄驱动预检** — 在设置中切换到手柄模式时，保存配置前通过 WebSocket `check_gamepad` 检测驱动是否可用；失败时显示本地化提示，并可直接跳转安装。
- **WebSocket init 新增 `effective_output_mode`** — 前端可获知后端当前实际运行的输出模式（键盘/手柄），而不只看 config 里的配置值（切换后需重启后端才生效）。

### 变更

- **轻量级手柄可用性检测** — 预检改为临时连接 ViGEmBus 总线，不再创建临时虚拟 XInput 手柄，避免产生 ghost 手柄，以及在后端已运行手柄模式时误报「驱动未安装」。
- **PyInstaller vgamepad 打包** — `virtual_tcu.spec` 在不 import vgamepad 的前提下收集 `ViGEmClient.dll` 及 hidden imports，CI/构建机无需安装 ViGEmBus 驱动。
- **vgamepad 延迟加载** — 移除 `deps.py` 启动时的 `import vgamepad`，手柄客户端 DLL 不可用时键盘模式仍可正常启动。
- **`installViGEmBus` 重构** — 移入 settings store，Electron 设置窗口与 Web UI 共用更清晰的封装。

### 修复

- **打包版后端启动崩溃** — PyInstaller 现会将 `ViGEmClient.dll` 打入 `vgamepad/win/vigem/client/{x64,x86}/`，修复发版后 `FileNotFoundError`。
- **手柄驱动误报** — 后端已在手柄模式运行时跳过预检；检测超时延长至 8 秒，适配 PyInstaller 冷启动较慢的 import。
- **Electron 后端生命周期** — 重启时清理挂死/孤儿后端进程；`openExternal` 前校验 HTTP/HTTPS URL；退出应用前确保后端正常关闭。

---

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
