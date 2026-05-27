# 升降挡算法与模式优化计划

> 日期：2026-05-27
>
> 范围：`virtual_tcu/logic/tcu.py`、`virtual_tcu/detectors/airtime.py`、模式枚举/配置、前端模式展示与输入输出层。

## 结论先行

1. **Dynamic 冗余分析基本成立**：当前 `DYNAMIC` 没有独立换挡算法，只是在 `COMFORT` 与 `RACE` 行为之间按 `DriveStyleTracker.regime` 做参数切换。它适合合并，但不应作为当前用户反馈的第一修复点。
2. **Race 降挡不积极是真问题**：现有 Race 的非制动降挡几乎只在爬坡触发，平路出弯、落地后低转大油门不会主动补挡，且上/下挡冷却会放大迟滞。
3. **腾空锁挡可能失效或落地后恢复慢**：`AirtimeDetector` 依赖“低垂向加速度 + 四轮全部高 slip”，触发条件偏窄；落地后没有专门的 recovery 状态，普通 Race 逻辑又受 `climb_only`、`_no_downshift_until`、post-shift lock 影响。
4. **离合按键不应作为 P0 修复**：离合只能降低游戏内换挡执行延迟，不能解决“该不该降挡”的算法问题。可作为 opt-in 实验功能，对使用 “Manual with Clutch” 且按键映射正确的玩家可能有实际提升；默认开启风险较高。

推荐实施顺序：

1. P0：修复 Race 降挡积极性、腾空/落地状态机与落地补降挡。
2. P1：基于回放/实车日志调参并补测试。
3. P2：合并 Dynamic 到 Comfort/Race，减少模式困惑。
4. P3：增加可选离合辅助，作为性能实验项。

---

## 一、现状核对

### 1. 模式分发链

`TCULogic._process_internal()` 统一处理：

- 暂停/菜单恢复状态清理
- `td.is_shifting` 早退
- 玩家/游戏自身挡位变化导致的上下挡锁
- 历史油门/刹车/速度更新
- 齿比、功率曲线、rev limiter、腾空、yaw transient、drive style 学习
- 倒挡、起步、post-shift lock、挡位不匹配、低速、弯道锁
- 最后按 `Mode` 分发到 `COMFORT / DYNAMIC / RACE / DRIFT / OFFROAD`

这说明模式函数只负责“自动模式核心换挡策略”，不少影响 Race 体验的锁定逻辑发生在模式分发之前或 `_shift_up/_shift_down` 内。

### 2. Race 当前降挡路径

`_mode_race()` 的关键链路：

```text
ANTI-STALL
→ _blocked_by_transient()
→ _track_brake_down(brake_thr = brake_thr * 0.6)
→ wheelspin upshift
→ _track_out_of_band_kickdown(climb_only=True)
→ _track_upshift_in_band(offset=0.03)
→ RACE in band
```

主要问题：

- `_track_out_of_band_kickdown(..., climb_only=True)` 要求 `_on_climb(td)` 成立。用户常见场景“平路出弯 / 落地后大油门低转”不会进入降挡。
- `_should_brake_downshift()` 在 `feat_brake_curve=True` 时，Race 传入的低 `brake_thr` 经常被二次条件抵消：需要刹车 spike 或持续大于约 0.55。结果是 `brake_thr * 0.6` 的意义不足。
- `_shift_down()` 对 `KICKDOWN / PREDICTIVE / TORQUE DOWN / BAND DOWN` 设置 0.70s 串联降挡锁。Race 快速降 2-3 个挡时会显得拖沓。
- `_shift_up()` 所有模式统一设置 `self._no_downshift_until = now + 1.0`。Race 刚升挡后遇到坡顶/落地/出弯低转，1 秒内不能纠正。
- `_track_brake_down()` 只有制动场景会用齿比选择目标挡位；动力需求降挡仍是单挡试探。

### 3. 腾空锁挡当前风险

`AirtimeDetector` 当前条件：

```text
speed_kmh > 20
and abs(accel_y) < 3.0
and all(abs(wheel_slip) > 1.2)
连续 3 帧进入腾空，连续 2 帧退出
```

风险点：

- 四轮 slip 全部大于阈值过严。部分车辆有 TCS、AWD 或轮速变化不明显时，真实腾空可能无法满足。
- 只用 `accel_y` 与 slip，未利用 `vel_y`。坡顶、跳台、落地过程中的垂向速度对状态转换很有价值。
- 退出腾空后只恢复普通模式，没有 `just_landed` / `landing_recovery_until`。落地时如果挡位过高，Race 仍按普通 `climb_only` 规则判断，可能不降挡。
- `_process_internal()` 中检测到非 TCU 的挡位变化时，在 airborne 下不会增加 `_no_downshift_until/_no_upshift_until`，但如果上一次 TCU 自己升挡或其他锁已经存在，落地后仍可能被锁住。

### 4. Dynamic 冗余程度

当前 `DYNAMIC` 的价值主要是 `DriveStyleTracker`：

- `CRUISE / ADAPTIVE` 分支接近 Comfort，差异是阈值与是否开启 transient block。
- `SPORT` 分支接近 Race，差异是制动阈值、upshift offset 与 fallback。
- 没有独有的目标挡位选择、腾空恢复、功率带策略或特殊场景规则。

因此“删除 Dynamic，保留 DriveStyleTracker 并服务 Comfort/Race”的方向正确。但删除模式涉及后端枚举、配置迁移、前端模式列表、HUD 颜色、历史配置兼容，建议排在 Race/腾空 P0 修复之后。

---

## 二、P0 修复方案：Race 降挡更积极

### 目标

Race 模式应在以下场景更快回到动力带：

- 出弯低转大油门
- 高挡巡航后突然全油门
- 落地后车速仍高但挡位过高
- 重刹后准备重新加速

同时必须保留：

- over-rev 保护
- 弯中不乱升挡
- 腾空时不误触发换挡
- 轮胎严重空转时避免误把打滑当成加速需求

### 方案 A：新增 Race 专用动力需求降挡

在 `_mode_race()` 中，把“动力需求降挡”放在制动降挡之后、wheelspin upshift 之前或之后按实测调整：

```text
ANTI-STALL
→ AIRBORNE / TRANSIENT BLOCK
→ LANDING RECOVERY（见下一节）
→ TRACK BRAKE DOWN
→ RACE POWER DOWN
→ WHEELSPIN UPSHIFT
→ CLIMB BAND DOWN
→ UPSHIFT IN BAND
```

新增 helper 建议：

```python
def _track_power_demand_downshift(
    self,
    td: Telemetry,
    now: float,
    *,
    min_throttle: float = 0.68,
    target_floor: float = 0.60,
    lock_ms: int = 300,
    allow_skip: bool = True,
) -> bool:
    ...
```

触发建议：

- `td.throttle >= 0.68`
- `td.brake < 0.08`
- `td.gear > 2`
- `td.speed_kmh > 25`
- `td.rpm_pct < threshold`
  - 有功率曲线：`threshold = max(0.58, peak_torque_rpm - 0.05)`
  - 无功率曲线：`threshold = 0.60`
- 如果刚重刹结束 2 秒内，可把 `min_throttle` 降到 `0.45`，因为这通常是弯后补油。

目标挡位选择：

- 优先用齿比表算目标挡位，而不是单挡试探。
- 目标转速区间：
  - 自吸/普通：峰值扭矩到峰值功率之间偏扭矩侧，例如 `peak_torque + (peak_power - peak_torque) * 0.45`
  - 无功率曲线：`0.72 * engine_max_rpm`
  - turbo lag 存在时可更接近 `0.75-0.80`，避免升挡后低增压。
- 只选择 projected RPM `< real_redline * 0.98` 的挡位。
- 如果目标挡位小于当前挡位 2 个以上，允许 skip down，但建议先限制为最多双降，避免输入堆叠。

### 方案 B：Race 下调降挡锁

把 `_shift_down()` 的锁定时间从“按 state 写死”改为可选参数：

```python
def _shift_down(
    self,
    td: Telemetry,
    lock_ms: int,
    state: str,
    sub: str = "",
    *,
    cascade_lock_s: float | None = None,
) -> bool:
```

Race 专用建议：

- `BRAKE DOWN`: 0.22-0.30s
- `RACE POWER DOWN`: 0.30-0.40s
- `BAND DOWN`: 0.35-0.45s
- 普通 Comfort/Dynamic 保持当前 0.60-0.90s，避免日常驾驶 hunting。

同时考虑给 `_shift_up()` 增加 `downshift_lock_s` 参数：

```python
def _shift_up(..., *, downshift_lock_s: float = 1.0) -> bool:
```

Race upshift 可降到 `0.45-0.60s`；如果处于 landing recovery，可进一步允许“低转大油门 override”。

### 方案 C：Race 制动降挡绕开过严 brake curve

当前 `brake_thr` 在 Race 中乘以 0.6，但 `_should_brake_downshift()` 又要求刹车 spike 或持续重刹。建议给 track brake down 单独入口：

```python
def _should_track_brake_downshift(self, td: Telemetry, base_thr: float) -> bool:
    if td.brake < base_thr:
        return False
    if self._brake_is_spike():
        return True
    if td.brake > 0.30 and self._speed_decreasing(delta=0.8):
        return True
    if td.brake > 0.45:
        return True
    return False
```

这样 Race/Offroad 的制动降挡不再被 Comfort 的平顺策略束缚。

---

## 三、P0 修复方案：腾空锁挡与落地补降挡

### 目标

- 腾空期间可靠锁住自动换挡，避免空中乱升/乱降。
- 落地后短时间内优先恢复动力带，尤其 Race/Offroad。
- 对坡顶、路肩、短暂颠簸避免误判。

### 方案 A：扩展 AirtimeDetector 状态机

建议把 `AirtimeDetector` 从单一 `is_airborne` 扩展为：

```python
class AirtimeDetector:
    @property
    def is_airborne(self) -> bool: ...

    @property
    def just_landed(self) -> bool: ...

    @property
    def landing_until(self) -> float: ...
```

`update(td, now)` 返回状态变化：

```python
AirState(
    airborne: bool,
    just_landed: bool,
    airborne_started: bool,
    landing_started: bool,
)
```

检测条件建议从“必须全部满足”改为加权投票：

- 强条件：
  - `speed_kmh > 20`
  - `abs(accel_y) < 3.0` 或 `abs(vel_y) > 1.0`
- 轮胎条件：
  - 四轮 slip 全部高：强证据
  - 至少 2-3 个轮高 slip：中证据
  - slip 不高但 `vel_y` 明显且垂向加速度低：短暂候选，最多允许 2-3 帧
- 进入：
  - 强证据连续 2 帧即可进入
  - 中证据连续 3 帧进入
- 退出：
  - `abs(vel_y) < 0.6` 且不再低 G/高 slip，连续 2-3 帧
  - 退出瞬间设置 `landing_until = now + 0.75`

这样比当前“四轮全部 slip > 1.2 连续 3 帧”更能覆盖真实跳跃。

### 方案 B：落地 recovery 钩子

在 `_process_internal()` 更新 airtime 后记录边沿：

```python
air_state = self._airtime.update(td, now)
if air_state.landing_started:
    self._landing_recovery_until = now + 0.90
    self._no_downshift_until = 0.0
    self._no_predictive_until = 0.0
    self._no_upshift_until = max(self._no_upshift_until, now + 0.80)
```

设计意图：

- 清掉降挡锁，让落地后可以立刻补挡。
- 短暂禁止升挡，防止落地轮速/RPM 尖峰触发误升挡。
- 保留 over-rev 检查，不允许危险降挡。

### 方案 C：Race/Offroad 落地补挡规则

在 Race/Offroad 的 transient block 之后、普通规则之前加入：

```python
if self._landing_recovery_until > now:
    if self._landing_recovery_downshift(td, now):
        return
```

触发建议：

- `td.gear > 1`
- `td.speed_kmh > 20`
- `td.throttle > 0.35` 或最近 0.8s 内油门 ramp 明显
- `td.rpm_pct < target_floor`
  - Race：`target_floor = peak_torque - 0.03`，fallback `0.62`
  - Offroad：fallback `0.58`，更重视扭矩
- 如果刹车仍大于 `0.25`，优先走 `_track_brake_down()` 的目标挡位。

状态文案：

- 腾空中：`AIRBORNE / holding decisions`
- 刚落地：`LANDING / recovering power`
- 补降挡：`LANDING DOWN / →target`

前端 snapshot 可继续使用现有 `airborne`，建议增加：

- `landing_recovery: bool`
- `airtime_state: "GROUND" | "AIRBORNE" | "LANDING"`

---

## 四、P1 验证与调参

### 单元测试

建议新增 Python 测试覆盖：

1. `AirtimeDetector`
   - 真实腾空：低 G + 高 `vel_y` + 部分 wheel slip，能进入 airborne。
   - 短路肩/坡顶：1 帧异常不进入 airborne。
   - 落地边沿：从 airborne 到 grounded 时产生一次 `just_landed`，并维持 landing window。
2. Race power down
   - 高挡、低 RPM、70%+ throttle、非爬坡：应触发降挡。
   - projected RPM 超红线：必须阻止。
   - 刚升挡后低转大油门：Race override 能在合理锁定后纠正。
3. Race brake down
   - 中高强度持续刹车但非 spike：Race 应降挡。
   - Comfort 保持原平顺行为。

### 回放验证

使用 telemetry replay 增加对比指标：

- 从落地帧到第一次有效降挡的延迟
- 从全油门低转到第一次降挡的延迟
- Race 模式每分钟误降挡次数
- 过转保护触发次数
- wheelspin upshift 与 landing down 的冲突次数

建议验收标准：

- Race 平路低转大油门在 0.3-0.5s 内开始降挡。
- 落地后若 RPM 低于目标动力带，在 0.2-0.4s 内开始补降挡。
- 腾空期间不再触发普通 upshift/downshift。
- Comfort 日常巡航行为不发生明显变化。

---

## 五、P2 模式优化：合并 Dynamic

### 是否合并

建议合并，但放在 Race/腾空修复之后。

理由：

- 当前用户反馈集中在 Race 与 airtime，删除 Dynamic 不会直接解决。
- 删除模式会影响后端枚举、配置、前端模式列表、HUD、i18n、历史 `current_mode` 迁移。
- 先把 `DriveStyleTracker` 用在 Comfort/Race 中，再删除 UI 模式，用户感知更平滑。

### 合并策略

1. `Mode.DYNAMIC` 从 `MODE_ORDER` 与前端 `DRIVE_MODES` 删除。
2. 配置迁移：
   - 如果旧配置 `current_mode == "DYNAMIC"`，启动时迁移到 `COMFORT`。
   - 保留 `dynamic_up_*` 配置一个版本，读取时映射为 Comfort sport 曲线参数；后续再清理。
3. Comfort 内联 drive style：
   - `CRUISE`：保留 cruise efficiency upshift。
   - `ADAPTIVE`：降低 kickdown/predictive 阈值，启用 transient block。
   - `SPORT`：提高 upshift 曲线、降低动力降挡阈值，但不要完全变成 Race。
4. Race 使用 drive style 做“保守上限”：
   - index 低且油门低时，允许稍早升挡以降低巡航噪音。
   - 一旦 throttle/rpm/brake/lat-g 表现为运动驾驶，立即恢复完整 Race 策略。
5. 前端保留 `drive_style_regime` 展示，让用户看到 Comfort/Race 内部自适应状态。

### 不建议合并 Offroad

Offroad 虽然与 Race 相似，但仍有真实独有价值：

- `TORQUE DOWN` 对低速爬坡有用。
- 轮速差误判过滤 `_is_spinning_not_traction()` 更适合越野。
- anti-stall 更早介入。

如果未来要减少模式数量，先观察 Race 修复后 Offroad 使用率与日志表现，再决定是否合并。

---

## 六、P3 离合按键评估

### 是否需要

不需要作为当前 Race/腾空问题的修复前提。

原因：

- Race 降挡不积极是“决策没有触发 / 锁定太长”，离合不能让算法主动降挡。
- 腾空锁挡失效是“状态检测与落地恢复”问题，离合不能改善状态判断。
- 当前 `OutputInterface` 只抽象了 `shift_up / shift_down / shift_down_double`，没有离合通道；直接加入会影响 keyboard 与 gamepad 两套输出。

### 什么时候有提升

如果玩家在 Forza 中使用 **Manual with Clutch**，并且离合按键/按钮映射正确，TCU 在换挡时自动按住离合可能带来：

- 更短的游戏内换挡延迟
- 更少的换挡期间动力中断
- 连续降挡时更顺畅

但如果玩家使用普通 Manual 或 Automatic：

- 离合输入可能无效。
- 错误映射可能导致错过换挡、空挡感、车辆突然失去动力。
- 多按键时序不当可能比当前单键更慢。

### 建议实现为 opt-in 实验功能

新增配置：

```python
"feat_clutch_assist": False,
"clutch_key": "shift",
"gamepad_clutch": "LB",
"clutch_pre_ms": 20,
"clutch_overlap_ms": 55,
"clutch_release_ms": 25,
"clutch_modes": ["RACE", "OFFROAD"],
```

输出层设计：

```python
class OutputInterface:
    def shift_up(self, use_clutch: bool = False): ...
    def shift_down(self, use_clutch: bool = False): ...
    def shift_down_double(self, use_clutch: bool = False): ...
```

键盘时序：

```text
press clutch
wait clutch_pre_ms
press shift key
wait clutch_overlap_ms
release shift key
wait clutch_release_ms
release clutch
```

Gamepad 注意：

- 当前 `GamepadOutput` 只支持按钮，不支持 trigger 轴。
- 如果用户把离合映射到 LB/RB/A 等按钮，可以直接支持。
- 如果要支持 LT/RT 作为离合，需要扩展 vgamepad trigger 输出，单独处理 analog axis。

验收指标：

- 同一车辆同一挡位，记录按键触发到 `td.gear` 改变的帧数。
- 比较单键 shift 与 clutch-assisted shift 的中位延迟。
- 若没有明显降低延迟或误换挡增加，则默认继续关闭。

---

## 七、建议实施任务清单

### P0-1 Race 动力降挡

- [ ] 新增 `_target_gear_for_power()`：基于齿比和功率曲线选择目标挡。
- [ ] 新增 `_track_power_demand_downshift()`：非爬坡低转大油门主动降挡。
- [ ] `_mode_race()` 接入 power down，保留 over-rev 保护。
- [ ] `_shift_down()` 支持 `cascade_lock_s`，Race 使用更短串联锁。
- [ ] `_shift_up()` 支持 `downshift_lock_s`，Race upshift 不再统一锁 1s。

### P0-2 腾空与落地恢复

- [ ] `AirtimeDetector.update(td, now)` 返回状态边沿。
- [ ] 引入 `vel_y` 与部分 wheel slip 投票，降低漏判。
- [ ] 增加 `landing_recovery_until`。
- [ ] 落地时清理 downshift/predictive lock，短暂禁止 upshift。
- [ ] Race/Offroad 接入 `_landing_recovery_downshift()`。
- [ ] snapshot 增加 `landing_recovery` / `airtime_state`。

### P1 测试与日志

- [ ] 增加 AirtimeDetector 单元测试。
- [ ] 增加 Race power down / brake down 测试。
- [ ] 增加 replay 对比指标输出。
- [ ] 用真实用户日志验证阈值。

### P2 Dynamic 合并

- [ ] Comfort 内联 drive style 自适应参数。
- [ ] Race 内联 drive style 低负载保守策略。
- [ ] `MODE_ORDER` 移除 `DYNAMIC`。
- [ ] 旧配置 `DYNAMIC` 迁移到 `COMFORT`。
- [ ] 更新 `packages/shared/src/config/modes.ts`、`types/ws.ts`、HUD mode 类型与颜色、i18n。
- [ ] 删除 `_mode_dynamic/_dynamic_cruise/_dynamic_sport`。

### P3 离合辅助

- [ ] 扩展配置与 UI。
- [ ] 扩展 `OutputInterface`。
- [ ] KeyboardOutput 支持 clutch sequence。
- [ ] GamepadOutput 支持按钮式 clutch；trigger 轴另行评估。
- [ ] 增加换挡延迟 A/B 日志指标。

---

## 八、最终建议

当前最值得优先做的是 **Race 降挡策略 + 落地 recovery**，这两项直接对应用户反馈，并且能在不改变模式数量的情况下验证算法收益。

Dynamic 删除建议作为第二阶段进行：它确实重复，但属于产品/交互简化，不是 Race 体验问题的根因。

离合辅助建议作为实验开关加入，不默认启用。它可能提升实际游戏中的换挡速度，但前提是玩家使用 Manual with Clutch，且按键时序经测试可靠。
