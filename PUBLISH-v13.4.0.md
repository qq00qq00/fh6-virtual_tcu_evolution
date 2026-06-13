# 发布 v13.4.0 操作手册 / Publish steps

> 我（Claude）无法直接推送到你的 GitHub 仓库或创建 Release——没有你的凭据。
> 下面是你在**本机仓库**里复制粘贴即可执行的步骤。预计 3–5 分钟。

## 0. 应用改动（二选一）

**A. 用补丁（推荐，若你的仓库就是这份上传的快照）**
把 `v13.4.0-learned-status.patch` 放到仓库根目录，然后：
```bash
git checkout -b release/13.4.0
git apply --check v13.4.0-learned-status.patch   # 先验证能否干净应用
git apply v13.4.0-learned-status.patch
rm v13.4.0-learned-status.patch                  # 不要把补丁本身提交进去
```
如果 `--check` 报冲突（说明你本地已不完全等于上传快照），改用方案 B。

**B. 手动改 17 个文件**
按补丁内容逐文件套用（文件清单见本文件末尾）。

## 1. 同步版本号（可选但建议）
版本号我已直接写进所有文件（13.4.0）。若你想以 `package.json` 为唯一来源再跑一遍：
```bash
node scripts/sync-version.mjs
```
注意：该脚本**不**更新 `virtual_tcu/__init__.py`——我已手动改好，无需再动。

## 2. 本地校验
```bash
# Python 测试（test_restart_argv 那条失败是改动前就有、与本次无关，可忽略）
python -m pytest tests/ -q

# 前端类型检查 / 构建（按你仓库实际脚本）
pnpm install
pnpm -r typecheck   # 或 pnpm -r build
```

## 3. 提交
```bash
git add -A
git commit -m "feat(learning): crossover LEARNED status reflects real gearbox coverage (v13.4.0)

- Gate LEARNED on per-gear ratio convergence (>=5 samples), power-curve
  confidence (>=0.5), and a confirmed top gear (rejected-upshift cap, or a
  30s driving plateau fallback at/above 4th). No telemetry gear-count exists.
- Show 'Learning x/y' progress on dashboard + settings overview (EN/zh-CN).
- Centralise the status on the backend (crossover_learned + learn_* fields);
  HUD/dashboard/electron read one flag instead of 4 copies.
- Tests: tests/test_learn_status.py"
```

## 4. 打标签并推送
```bash
git tag -a v13.4.0 -m "v13.4.0 — Crossover LEARNED status reflects real gearbox coverage"
git push origin release/13.4.0
git push origin v13.4.0
```
（若你直接发到默认分支，把 `release/13.4.0` 换成你的主分支名，并先合并 PR。）

## 5. 创建 GitHub Release
**网页版**：仓库 → Releases → Draft a new release → 选 tag `v13.4.0` →
标题 `v13.4.0` → 正文粘贴 `RELEASE_NOTES_v13.4.0.md` 的内容 → Publish。

**或用 GitHub CLI（gh）**：
```bash
gh release create v13.4.0 \
  --title "v13.4.0 — Crossover LEARNED status reflects real gearbox coverage" \
  --notes-file RELEASE_NOTES_v13.4.0.md
# 如需附构建产物：在末尾追加产物路径，例如 dist/VirtualTCU-Setup-13.4.0.exe
```

---

## 改动文件清单（17）
- `virtual_tcu/logic/tcu.py` — 学习状态门控、追踪、snapshot 字段（核心）
- `virtual_tcu/learning/gear_ratio.py` — `gear_sample_counts/mature_gear_count/max_gear_seen`
- `virtual_tcu/__init__.py`, `pyproject.toml`, `package.json` ×5 — 版本号 13.4.0
- `packages/shared/src/types/telemetry.ts` — 新增 4 个快照字段类型
- `packages/shared/src/locales/en.ts`, `zh-CN.ts` — `crossoverProgress` 文案
- `packages/ui/src/layout/ModeSidebar.vue` — 读 `crossover_learned` + 进度
- `packages/ui/src/settings/SettingsOverview.vue` — 同上
- `apps/electron/src/hud-renderer/hud-view.ts` — 读 `crossover_learned`
- `tests/test_learn_status.py` — 新增 6 个测试
- `CHANGELOG.md` — 13.4.0 条目

## 可调参数（在 `virtual_tcu/logic/tcu.py` 顶部）
- `LEARN_MATURE_SAMPLES = 5` — 每挡视为收敛所需样本数
- `LEARN_CONF_FLOOR = 0.5` — 功率曲线置信度门槛
- `LEARN_PLATEAU_S = 30.0` — 无 cap 时平台期秒数
- `LEARN_MIN_TOP_FALLBACK = 4` — 平台期可信的最低顶挡
