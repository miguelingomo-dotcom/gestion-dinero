# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Ka$hy** is a single-user personal finance PWA (Spanish-first, with English i18n) deployed on Vercel at `gestion-dinero-dusky.vercel.app`. It uses **Notion databases as its backend**. The project has no build step, package.json, linter, or tests. The frontend is a single self-contained HTML file, and three Vercel serverless functions proxy requests to the Notion API.

## Running locally

There are no build or test commands. The `/api/*` routes need a Vercel runtime, so serve the project with `vercel dev` (the Vercel CLI) instead of a static file server. A static server will load the UI, but every data call will fail.

## Files

- `index-nuevo.html`: **the version in use; make all changes here by default.** It is one file of about 3.5k lines that holds all CSS, markup, and JS (no framework, no modules). It adds features the old version lacks: a splash screen, a privacy "eye" toggle that hides amounts, swipe gestures, category chips for filtering movements, and a WebAuthn/passkey app lock (`registrar`/`verificar`/`unlock`, with `RP_ID` hard-coded to the Vercel domain, so the lock only works over HTTPS on that domain).
- `index.html`: the older version, kept for reference. Don't edit it unless asked.
- The owner updates files by uploading them through GitHub's web UI, which is why the history shows repeated "Delete index-nuevo.html" / "Add files via upload" commits.
- `api/query.js`, `api/page.js`, `api/delete.js`: thin CORS-enabled proxies to Notion (`Notion-Version: 2022-06-28`):
  - `POST /api/query?dbId=…` → `databases/{dbId}/query`
  - `POST /api/page` → create a page; `PATCH /api/page?pageId=…` → update page properties
  - `DELETE /api/delete?pageId=…` → archive the page (`archived: true`)

## Architecture of the HTML app

- **Data layer**: `nFetch(path, method, body)` turns Notion-style paths (`/databases/{id}/query`, `/pages`) into calls to the proxies. Updates and deletes call `fetch('/api/page?pageId=…')` and `/api/delete` directly. Notion database IDs are constants near the top of the script: `DB_ID` (movements: expenses and income), `CUENTAS_DB`, `TRANSFER_DB`, and `BUDGET_DB`. `CUENTAS_DB` holds several kinds of records that are told apart by their columns: accounts (`Cuenta o Meta = Cuenta`), savings goals (`Cuenta o Meta = Meta`), the wish list (`Tipo = Wish List`), and MyInvestor investment records (any row with `InvTipo` set, either `Aportación` or `Valor Cartera`, using the `InvImporte` and `InvFecha` columns; `Valor Cartera` rows can also carry `InvFondo`, one of the `FONDOS` keys). The portfolio value comes from `fetchValorCartera()`: for each fund, its latest value plus its share (`pct`) of any later Aportaciones. If some fund has no value recorded yet, it falls back to the latest total value plus later Aportaciones. Investment records used to live in a separate database that the Notion integration can't access, so they were moved here. Every query on `CUENTAS_DB` therefore has to filter by its own record type. Notion property names are in Spanish (`Nombre`, `Tipo`, …). Code that reads results walks `p.properties.X.title[0].plain_text`, `.select.name`, `.number`, and so on, so renaming a Notion property breaks the app without any error.
- **Navigation**: the sections are `<div class="section" id="sec-{name}">` (inicio, movimientos, registrar, stats, cuentas, inversion). `showSec(name, navIdx)` switches between them and calls that section's loader (`loadInicio`, `loadMovs`, `loadStats`, `loadAccounts`/`loadGoals`/`loadWishes`, `loadInversion`). Data is fetched fresh each time a section opens, and skeleton placeholders (`skeletonCards`/`skeletonRows`) show while it loads.
- **i18n**: the `I18N = { es: {...}, en: {...} }` dictionary goes with `t(key, vars)`, which fills `{var}` placeholders and falls back to `es`, then to the key itself. `applyI18n` and `setLang` handle switching languages. Every new user-facing string needs entries in both languages.
- **Theming**: CSS custom properties sit on `:root` (dark) and `[data-theme="light"]`. An inline script in `<head>` applies the saved theme before the first paint.
- **localStorage keys**: these use a `kashy-` prefix (`kashy-theme`, `kashy-lang`) or are named by constants (`PRIV_KEY`, `LOCK_KEY`, `CRED_KEY`). localStorage only holds UI preferences; all financial data lives in Notion.
- **Layout**: mobile-first, with `.app` capped at 430px wide and a fixed bottom nav. The app is meant to be installed as an iOS home-screen web app (apple-mobile-web-app meta tags, `icon.png`).
- **Formatting**: amounts are in euros. Use `fmt`/`parseAmt`/`sanitizeAmt` for money and `getDateRange` for month windows.

## Security note

The Notion integration token is hard-coded in the three `api/*.js` files and in the HTML (`const TOKEN=…`), and it is committed to git. The HTML sends it as a `Bearer` header, but the proxies ignore that header and use their own copy of the token. The proxies also allow any origin (`Access-Control-Allow-Origin: *`) and do no auth. If this is ever addressed, the fix is to move the token to a Vercel env var (`process.env.NOTION_TOKEN`), remove it from the HTML, and rotate it in Notion. Don't add new copies of the token.
