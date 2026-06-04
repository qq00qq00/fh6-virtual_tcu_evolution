# AGENTS.md

## Cursor Cloud specific instructions

### Platform constraint

Virtual TCU **production runtime is Windows-only** (`python -m virtual_tcu` exits on non-`win32`). On Linux cloud VMs, validate the repo with **CI-parity checks** (lint, typecheck, builds) plus **`pnpm test:py`** (TCU logic with fake telemetry). Do not expect keyboard injection, FH6 UDP, or Electron packaged installers to work on Linux.

### Node.js version

The monorepo requires **Node ≥ 24** (`package.json` `engines`, `.node-version`). The VM default Node may be 22 (`/exec-daemon/node`). Before `pnpm install` or any pnpm script:

```bash
export PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH"
corepack enable && corepack prepare pnpm@10.33.0 --activate
```

(Install Node 24 once with `nvm install 24` if that directory is missing.)

### Python tools on PATH

`pip install --user` puts `pytest` and `ruff` under `~/.local/bin`. Include it when running Python tooling:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Standard commands (repo root)

See `CLAUDE.md` and root `package.json`. Typical Linux validation loop:

| Step | Command |
|------|---------|
| Install JS | `pnpm install --frozen-lockfile` |
| Install Python | `pip install -r requirements.txt -r requirements-dev.txt` |
| Typecheck | `pnpm typecheck` |
| Lint | `pnpm lint` (or CI split: `pnpm exec eslint .` + `ruff check virtual_tcu virtual_tcu.py`) |
| Unit tests | `pnpm test:py` |
| Build UI | `pnpm build:dashboard` → `virtual_tcu/web/dist/` |
| Build Electron | `pnpm build:electron` (compile only; no Windows installer on Linux) |

GitHub Actions (`.github/workflows/ci.yml`) runs typecheck, ESLint, Ruff, `build:dashboard`, and `build:electron` on Ubuntu — **not** pytest.

### Optional: Web UI smoke on Linux

After `pnpm build:dashboard`, you can serve the dashboard with aiohttp by running `WebServer` from a small inline/async script with `TCULogic` + `FakeOutput` (see `tests/conftest.py`). The real app entrypoint `main()` will not start on Linux. Vite dev (`pnpm dev:dashboard`, port 5173) proxies `/ws` to `127.0.0.1:8765` and needs a backend on that port.

### Git hooks

`.husky/pre-commit` runs `pnpm exec lint-staged` (ESLint/Prettier/Ruff on staged files). `.husky/commit-msg` uses commitlint.

### Services (Windows full stack)

For end-to-end desktop + game testing on Windows: Electron (`pnpm dev:electron`) spawns `python -m virtual_tcu --backend-only`; dashboard at `http://127.0.0.1:8765`; FH6 UDP on port 5555. See `CLAUDE.md` for ports, hotkeys, and Administrator notes.
