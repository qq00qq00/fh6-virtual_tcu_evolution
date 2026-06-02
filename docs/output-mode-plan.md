# 输出模式决策与换挡 Bug 计划

> 日期：2026-06-02
>
> 决策：**移除虚拟手柄（vgamepad / ViGEmBus）输出模式**。保留 keyboard（默认）与 vjoy 两种输出。

---

## 一、为什么删除手柄模式

虚拟手柄模式（`GamepadOutput`，基于 vgamepad/ViGEmBus）作为「并列的第二个 XInput 设备」存在固有缺陷：

- `VX360Gamepad.update()` 每帧上报整包 XInput 状态，未镜像的**方向摇杆 / 油门轴被打回中立**，与玩家真手柄冲突 → 转弯发卡、不跟手。
- 之前只镜像了刹车（LT），无法镜像方向/油门（程序拿不到玩家摇杆原始输入）。

唯一能彻底消除冲突的路线是 **HidHide + 全量合并**（隐藏物理手柄、读真手柄全量回写虚拟手柄）。但评估结论是该方案：

1. **引入新的延迟链路**：需 60–120Hz 实时读真手柄并回写，任何抖动都变成转向/油门延迟——和我们要解决的卡顿同类问题，可能继续引发一系列连锁问题；
2. **无法服务方向盘 / 力反馈用户**：Xbox360 手柄模型没有 FFB 回传通道；
3. **运维风险高**：依赖内核驱动，退出/崩溃必须恢复隐藏，否则物理手柄在其它程序里"消失"。

综合「收益有限 + 新延迟风险 + 仅服务手柄不服务方向盘 + 运维复杂」，决定**直接删除手柄模式**，而不是投入 HidHide。

## 二、保留的输出方案

| 方案 | 冲突 | 适用 | 说明 |
|---|---|---|---|
| **keyboard（默认）** | 无（离散按键，不碰轴） | 手柄 / 方向盘 / 键盘 | E/Q 注入。FH 偶发输入方案/HUD 图标切换 |
| **vjoy** | 基本无 | 安装 vJoy 的用户 | 直选挡或顺序挡，力反馈方向盘不被打断 |

> 历史配置 `output_mode: "gamepad"` 会在 `app.py` 自动回退到 keyboard（`else` 分支），无需用户干预。

## 三、本次删除涉及的改动

- 后端：删除 `virtual_tcu/input/gamepad_output.py`；`__init__.py` / `app.py` / `web/server.py` 去除手柄分支与 `check_gamepad`；`interface.py` 删除 `set_brake`（仅手柄需要的刹车镜像）；`tcu.py` 去除 `set_brake` 调用；`constants.py` 删除 `gamepad_*` 默认项。
- 前端：`OUTPUT_MODE_OPTIONS` 去掉 gamepad；删除 `GAMEPAD_BUTTON_*`、`check_gamepad`/`gamepad_check`、`installViGEmBus`、`VIGEMBUS_DRIVER_URL`、相关文案与设置 UI。
- Electron：删除 `vigem-installer.ts`、`app:install-vigembus` IPC、preload `installViGEmBus`。
- 打包/CI：`requirements.txt` / `pyproject.toml` / `uv.lock` 去除 `vgamepad`；`virtual_tcu.spec` 去除 vgamepad/ViGEmClient.dll 收集；`electron-builder.yml` 去除 `driver/` 资源；`release.yml` 去除 vgamepad 安装；删除 `driver/ViGEmBusSetup_x64.msi`。
- 测试：删除 `test_gamepad_output_*` 与 `mock_vgamepad`。

验证：`ruff` / `eslint` / `vue-tsc`（dashboard + electron）全部通过；后端模块导入正常。

---

## 四、删除手柄后，先前三个问题的现状复核

> 关键结论：**Bug 3 已随手柄模式一并消失；Bug 1 与 Bug 2 的换挡逻辑根因与输出无关，仍然存在，需单独修复。**

### Bug 1 — 满油门时反复升/降档、红线附近横跳
- **仍然存在**。根因在 `logic/tcu.py` 的换挡逻辑（学习红线 < 真实断油点导致 `rpm_pct>1.0`，与升/降档判定互相打架），与输出后端无关。

### Bug 2 — 撞停 / 停车时刹车一直输入
- **「刹车一直输入」这个具体表现已消失**：它来自手柄 LT 刹车镜像（`set_brake` + `_apply_brake`/`_release_brake`），随手柄模式删除而消失。
- **但底层逻辑 Bug 仍在**：停车 + 踩刹车 + 挡位卡住时，`GEAR MISMATCH` / `STANDSTILL` 每帧都触发降档。合成场景实测：200 帧 → **200 次降档命令**。删手柄后这会在 keyboard 模式下表现为**疯狂刷 E/Q 按键**（vjoy 模式刷按钮）。仍需修。

机制（与之前结论一致）：
- `GEAR MISMATCH` 分支每帧 `self._no_downshift_until = 0.0`，清掉降档冷却；
- 刹车逃逸分支 `if td.brake > 0.45 and (self._lock_until - now) > 0.20: self._lock_until = now + 0.20` 会**穿透** post-shift 锁，而 `_shift_down` 每次又把 `_lock_until` 重新拉到 `now+0.35`，导致每帧都能穿透 → 每帧降档。

### Bug 3 — 手柄模式转弯卡、不跟手
- **已彻底消失**：该问题是虚拟手柄轴冲突独有的，手柄模式删除后不复存在。

---

## 五、下一步（换挡逻辑修复，与输出无关）

1. **Bug 2**：停车/低速 `MISMATCH`/`STANDSTILL` 恢复降档加最小间隔，避免每帧重置 `_no_downshift_until`；让刹车逃逸不被 `_shift_down` 的新锁无限穿透（区分"逃逸一次"与"已在停车恢复中"）。
2. **Bug 1**：对「学习红线 < 真实断油」做夹紧/迟滞；降档目标挡位需保证降挡后转速明显低于升档点（避免一降就想升）；`rpm_pct>1.0`（顶限速器）时禁止任何降档，只允许升档/保持。
3. 补回归测试：停车+刹车降档次数上限、满油门加速无 1.5s 内升降反复。
