# v13.4.0 — Crossover "Learned" status reflects real gearbox coverage

## English

### Why
The green **LEARNED** badge used to flip after a single 1→2 launch. It only
required two gears with one ratio sample each, and a power curve that returned
a peak at *any* confidence — both of which a single hard launch satisfies. The
badge said "done" while most of the gearbox was still unmapped.

### What changed
Forza's telemetry has **no gear-count field** (only the current gear, one byte),
so "have we learned the whole box?" can't be read directly — it has to be
inferred. The status is now gated on three things at once:

1. **Per-gear convergence** — every gear up to the top has a *settled* ratio
   (≥5 samples), not a one-frame reading.
2. **Power-curve confidence** — `confidence ≥ 0.5`, instead of merely "a peak
   exists".
3. **Confirmed top gear** — either a rejected upshift proved the top (the
   existing per-car cap), or, for Manual/cruising where that never fires, a
   **driving plateau**: no higher gear reached for 30 s of genuine driving,
   and only at/above 4th.

A quick 1→2 launch therefore stays **LEARNING**. The badge only goes **LEARNED**
once you've actually driven up through the box and each gear has converged.

### Also
- The calibration badge now shows **progress** while learning — e.g.
  `Learning 4/6` (matured gears / detected top gear) — on the Web dashboard and
  settings overview, so convergence is visible instead of a status that jumps
  straight to done. Full EN / zh-CN.
- All three surfaces (HUD chrome, Web dashboard, Electron overview) now read one
  backend-computed `crossover_learned` flag instead of each recomputing the
  status, removing four copies of the same logic.

### Tests
`tests/test_learn_status.py` covers the gating: a 1→2 launch is never learned;
a full converged box with a proven cap is; low confidence blocks it; the plateau
fallback works without a cap but is refused below 4th; and the high-water-mark
tracker advances and resets correctly.

No behavioural change to shifting logic — this release only changes when the
*status* reports "learned" and adds the progress readout.

---

## 简体中文

### 背景
旧版绿色「已学会」徽章，往往一次「一档升二档」起步就点亮了。它只要求 2 个挡位、
每个挡位 1 个样本，加上一条「能算出峰值」的功率曲线（不看置信度）——而一次大脚
起步就能同时满足这两条。结果是变速箱大部分还没标定，徽章却显示「完成」。

### 本次改动
FH 遥测里**没有总挡数字段**（只有当前挡，一个字节），所以「整个变速箱学完了
没有」无法直接读取，只能推断。现在「已学会」需要**同时**满足三点：

1. **逐挡收敛** —— 到顶挡为止，每个挡位的齿比都已*稳定*（≥5 个样本），
   而不是一帧的瞬时读数。
2. **功率曲线置信度** —— `confidence ≥ 0.5`，不再是「能算出峰值就行」。
3. **顶挡已确认** —— 要么升挡被游戏拒绝从而证明了顶挡（沿用原有的 per-car cap），
   要么（手动/巡航下 cap 不触发时）通过**驾驶平台期**：在真实驾驶下持续 30 秒
   没有再升到更高挡，且挡位在 4 挡及以上。

因此一次「一升二」起步会保持**学习中**。只有当你真正把挡位逐级升上去、每个挡
都收敛后，徽章才会变成**已学会**。

### 还有
- 学习过程中徽章会显示**进度** —— 例如 `学习中 4/6`（已成熟挡数 / 检测到的顶挡）——
  在网页面板和设置概览中可见，不再是突然跳到完成。中英双语。
- HUD、网页面板、Electron 概览三处现在统一读取后端算好的 `crossover_learned`，
  不再各自重复判定，消除了 4 份重复逻辑。

### 测试
`tests/test_learn_status.py` 覆盖了门控：一升二永不判已学会；完整收敛 + 已证明
顶挡才判已学会；低置信度会阻止；无 cap 时平台期兜底生效但 4 挡以下拒绝；高水位
追踪器在到达新挡时推进、并正确重置平台期计时。

换挡逻辑本身无任何行为变化——本次只改变了**状态**何时报告「已学会」，并新增进度显示。
