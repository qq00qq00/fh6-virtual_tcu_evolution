# Virtual TCU — Web UI

Vue 3 dashboard for Virtual TCU. Built output is served by the Python app from `virtual_tcu/web/dist/`.

## Stack

- Vue 3 + Vite + TypeScript + **Tailwind CSS v4** (logic in `.ts`, views in `.vue` without `lang="ts"`)
- [vue-i18n](https://vue-i18n.intlify.dev/) — English + 简体中文
- ESLint — [@antfu/eslint-config](https://github.com/antfu/eslint-config) with **stylistic/format disabled**
- Prettier — code formatting (`npm run format`)

## Development

1. Start the TCU backend (UDP + WebSocket on port 8765):

   ```bash
   python -m virtual_tcu
   ```

2. In another terminal:

   ```bash
   cd web-ui
   npm install
   npm run dev
   ```

3. Open http://127.0.0.1:5173 — Vite proxies `/ws` to the backend.

## Production build

```bash
cd web-ui
npm install
npm run build
```

This writes to `virtual_tcu/web/dist/`. Restart `python -m virtual_tcu` and open http://127.0.0.1:8765.

If `dist/` is missing, the backend falls back to the legacy `index.html`.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Vite dev server |
| `npm run build` | Typecheck + production build |
| `npm run lint` | ESLint |
| `npm run format` | Prettier write |
