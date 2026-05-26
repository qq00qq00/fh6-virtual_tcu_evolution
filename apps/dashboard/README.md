# Virtual TCU — Dashboard

Vue 3 dashboard for Virtual TCU. Built output is served by the Python app from `virtual_tcu/web/dist/`.

## Stack

- Vue 3 + Vite + TypeScript + **Tailwind CSS v4** + Naive UI
- [vue-i18n](https://vue-i18n.intlify.dev/) — English + 简体中文
- ESLint — [@antfu/eslint-config](https://github.com/antfu/eslint-config)
- Prettier — code formatting

## Development

1. Start the TCU backend (UDP + WebSocket on port 8765):

   ```bash
   python -m virtual_tcu
   ```

2. In another terminal:

   ```bash
   cd apps/dashboard
   pnpm install
   pnpm dev
   ```

3. Open http://127.0.0.1:5173 — Vite proxies `/ws` to the backend.

## Production build

```bash
cd apps/dashboard
pnpm install
pnpm build
```

This writes to `virtual_tcu/web/dist/`. Restart `python -m virtual_tcu` and open http://127.0.0.1:8765.

If `dist/` is missing, the backend falls back to the legacy `index.html`.

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Vite dev server |
| `pnpm build` | Typecheck + production build |
| `pnpm lint` | ESLint |
| `pnpm format` | Prettier write |
