# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Ka$hy** is a single-user personal finance PWA (Spanish-first, with English i18n) deployed on Vercel at `gestion-dinero-dusky.vercel.app`. It uses **Notion databases as its backend**. The project has no build step, package.json, or linter; it has a regression test suite in `tests/`. The frontend is a single self-contained HTML file, and a few Vercel serverless functions proxy requests to the Notion API.

## Running locally

There is no build command. The `/api/*` routes need a Vercel runtime, so serve the project with `vercel dev` (the Vercel CLI) instead of a static file server. A static server will load the UI, but every data call will fail.

## Tests

Run the suite before every commit: `tests/.venv/bin/pytest tests` from the project root (first time: `tests/setup.sh`). It uses Python Playwright at iPhone size in both themes, with Notion mocked inside the browser, so it never touches real data. When changing CSS, compare the screenshots: the same command fails on any visual difference and leaves `-diff.png` images in `tests/screenshots/current/`; after a deliberate change, review them and run `tests/.venv/bin/pytest tests -k capturas --update-baseline`. Tests marked `xfail` document known bugs and fail once fixed, so remove the mark then.

## Files

- `index-nuevo.html`: **the version in use; make all changes here by default.** It is one file of about 3.5k lines that holds all CSS, markup, and JS (no framework, no modules). It adds features the old version lacks: a splash screen, a privacy "eye" toggle that hides amounts, swipe gestures, and category chips for filtering movements. It used to have a WebAuthn/passkey (Face ID) app lock; that was removed and the app now opens straight to Inicio.
- `index.html`: the older version, kept for reference. Don't edit it unless asked.
- The owner updates files by uploading them through GitHub's web UI, which is why the history shows repeated "Delete index-nuevo.html" / "Add files via upload" commits.
- `api/query.js`, `api/page.js`, `api/delete.js`: thin CORS-enabled proxies to Notion (`Notion-Version: 2022-06-28`):
  - `POST /api/query?dbId=…` → `databases/{dbId}/query`
  - `POST /api/page` → create a page; `PATCH /api/page?pageId=…` → update page properties; `GET /api/page?pageId=…` → read a page
  - `DELETE /api/delete?pageId=…` → archive the page (`archived: true`)
  - `GET /api/gasto` → lists for an iOS Shortcut (expense categories read live from the Notion Categorías database, ordered by how often they were used in the last 90 days, with Apuestas always last; the GET response is never cached by the CDN, which would skip the key check, and is kept for 10 min in the function instance; active accounts with Revolut first). `POST /api/gasto` with `{importe, concepto, categoria?, cuenta?}` → creates the expense dated today (Europe/Madrid); without a category (or the legacy "Automática") it guesses the category from the concept (category name, then the same keyword map as the app), and the account defaults to Revolut. It replies with a short text for the Shortcut's notification. Like `/api/history`, it calls this deployment's own proxies, so it holds no token.
  - `GET /api/history?movs=&cuentas=&transfers=&excluir=&hasta=` → daily net-worth history of the accounts (excluding MyInvestor) rebuilt from Balance Inicial + dated movements/transfers, plus the raw investment rows. It calls `/api/query` on its own deployment (paginating), so it holds no token. The app adds the portfolio value per day (`valorCarteraDia`, same logic as `fetchValorCartera`) to draw the patrimonio curve, and caches the response in localStorage (`kashy-pat-hist`).

## Architecture of the HTML app

- **Data layer**: `nFetch(path, method, body)` turns Notion-style paths (`/databases/{id}/query`, `/pages`) into calls to the proxies. Updates and deletes call `fetch('/api/page?pageId=…')` and `/api/delete` directly. Notion database IDs are constants near the top of the script: `DB_ID` (movements: expenses and income), `CUENTAS_DB`, `TRANSFER_DB`, and `BUDGET_DB`. `CUENTAS_DB` holds several kinds of records that are told apart by their columns: accounts (`Cuenta o Meta = Cuenta`), savings goals (`Cuenta o Meta = Meta`), the wish list (`Tipo = Wish List`), and MyInvestor investment records (any row with `InvTipo` set, either `Aportación` or `Valor Cartera`, using the `InvImporte` and `InvFecha` columns; `Valor Cartera` rows can also carry `InvFondo`, one of the `FONDOS` keys). The portfolio value comes from `fetchValorCartera()`: for each fund, its latest value plus its share (`pct`) of any later Aportaciones. If some fund has no value recorded yet, it falls back to the latest total value plus later Aportaciones. Investment records used to live in a separate database that the Notion integration can't access, so they were moved here. Every query on `CUENTAS_DB` therefore has to filter by its own record type. Notion property names are in Spanish (`Nombre`, `Tipo`, …). Code that reads results walks `p.properties.X.title[0].plain_text`, `.select.name`, `.number`, and so on, so renaming a Notion property breaks the app without any error.
- **Navigation**: the sections are `<div class="section" id="sec-{name}">` (inicio, movimientos, registrar, stats, cuentas, inversion). `showSec(name, navIdx)` switches between them and calls that section's loader (`loadInicio`, `loadMovs`, `loadStats`, `loadAccounts`/`loadGoals`/`loadWishes`, `loadInversion`). Data is fetched fresh each time a section opens, and skeleton placeholders (`skeletonCards`/`skeletonRows`) show while it loads.
- **i18n**: the `I18N = { es: {...}, en: {...} }` dictionary goes with `t(key, vars)`, which fills `{var}` placeholders and falls back to `es`, then to the key itself. `applyI18n` and `setLang` handle switching languages. Every new user-facing string needs entries in both languages.
- **Theming**: CSS custom properties sit on `:root` (dark) and `[data-theme="light"]`. An inline script in `<head>` applies the saved theme before the first paint.
- **localStorage keys**: these use a `kashy-` prefix (`kashy-theme`, `kashy-lang`) or are named by constants (`PRIV_KEY`). localStorage holds UI preferences and the API key (`kashy-key`); all financial data lives in Notion.
- **Layout**: mobile-first, with `.app` capped at 430px wide and a fixed bottom nav. The app is meant to be installed as an iOS home-screen web app (apple-mobile-web-app meta tags, `icon.png`).
- **Formatting**: amounts are in euros. Use `fmt`/`parseAmt`/`sanitizeAmt` for money and `getDateRange` for month windows.

## Security note

Every `/api/*` endpoint requires the shared secret in the `X-Kashy-Key` header, compared in constant time with the `KASHY_KEY` Vercel env var (`api/_auth.js`). It answers 401 with a wrong or missing key and 500 if the variable is not set. `index-nuevo.html` asks for the key once, stores it in localStorage, and its `fetch` wrapper adds it to every `/api/` call and asks again on a 401. `/api/gasto` and `/api/history` forward the key when they call their own deployment. Never cache an authenticated response in the CDN: it would be served without running the check.

The Notion token lives only in the `NOTION_TOKEN` Vercel env var and `api/_notion.js` reads it; if Notion rejects it the proxies answer 502, never 401, so the app doesn't ask for the key by mistake. Never put a token in the code: the old one remains in the git history, so it must stay revoked.
