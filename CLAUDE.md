# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Ka$hy** is a single-user personal finance PWA, in Spanish only, deployed on Vercel at `gestion-dinero-dusky.vercel.app`. It uses **Notion databases as its backend**. The frontend is one self-contained HTML file; a few Vercel serverless functions proxy requests to the Notion API, send push notifications and serve an iOS Shortcut. There is no build step and no linter; `package.json` only pins `web-push` for the server and its tests. A regression suite lives in `tests/`.

**Pushing to `main` publishes to the owner's installed app.** Vercel deploys every push to `main` in about a minute, and the iPhone home-screen app (`start_url` `/index-nuevo.html`) loads that version on its next open. Don't push without the owner's go-ahead, and run the full suite first.

## Running locally

There is no build command. The `/api/*` routes need a Vercel runtime, so serve the project with `vercel dev` (the Vercel CLI) instead of a static file server. A static server loads the UI, but every data call fails.

## Tests

- First time: `tests/setup.sh` (creates `tests/.venv` and `tests/.browsers`, about 355 MB, both git-ignored) and `npm install` (for the push tests).
- Run the whole suite before every commit, from the project root: `tests/.venv/bin/pytest tests`. It takes about 10 minutes (519 tests). Python Playwright drives Chromium at iPhone size (390 × 844) in both themes, with Notion mocked inside the browser (`tests/notion_mock.py`, data in `tests/datos.py`), so it never touches real data. Any request outside the app fails the test.
- `abrir()` emulates «Reduce motion» by default; pass `reducir=False` to test animations.
- Screenshots: `test_capturas.py` compares every screen with `tests/screenshots/baseline/`. On a visual change it fails and leaves `-diff.png` images in `tests/screenshots/current/`; after a deliberate change, review them and run `tests/.venv/bin/pytest tests -k capturas --update-baseline`.
- Notable files: `test_cifras.py` (no amount is ever cut off, with huge amounts at 390 and 320 px), `test_hojas.py` (every sheet fits a 390 × 667 screen, never pans sideways, date fields match their neighbours), `test_contar.py` (count-up on tab entry), `test_seguridad.py` and `test_api_clave.py` (key and token), `test_push_servidor.py` (Node, real Web Push encryption).
- `tests/comparar_estilos.py` is an optional computed-style comparator, run outside pytest.
- Tests marked `xfail` document known bugs and fail once fixed, so remove the mark then.

## Files

- `index-nuevo.html`: **the version in use; make all changes here.** One file of about 5,400 lines with all CSS, markup and JS (no framework, no modules).
- `index.html`: the older version, kept for reference. Don't edit it unless asked.
- `rediseno-demo.html`: the standalone redesign demo with fake data (not linked from the app). `docs/sistema-de-diseno.md` is the design system.
- `kashy-vencimientos.js`: recurring payments, installments, recurring transfers, the monthly contribution and the «due today» logic. The app loads it as a classic script (`window.KashyVencimientos`) and `api/cron-avisos.js` imports it, so the Home alert and the daily notification always agree. Change payments there, not in the HTML; their order there is the order shown in Registrar, the alert and the notification.
- `sw.js`, `manifest.webmanifest`, `icon.png` (512 px), `icon-192.png`: PWA and push. The icon is the «Ka$hy» wordmark, typography and colour only.
- `api/`: `_auth.js`, `_notion.js`, `_ajustes.js`, `_push.js` are helpers; the endpoints are below.
- The owner sometimes updates files through GitHub's web UI, which is why the history shows «Add files via upload» commits.

## API

All endpoints are thin CORS-enabled Vercel functions (`Notion-Version: 2022-06-28`):

- `POST /api/query?dbId=…` → `databases/{dbId}/query`
- `POST /api/page` → create a page; `PATCH /api/page?pageId=…` → update properties; `GET /api/page?pageId=…` → read a page
- `DELETE /api/delete?pageId=…` → archive the page (`archived: true`)
- `GET /api/gasto` → lists for an iOS Shortcut: expense categories read live from Notion, ordered by use in the last 90 days with Apuestas always last, and active accounts with Revolut first. Never cached by the CDN (that would skip the key check); kept 10 min in the function instance. `POST /api/gasto` with `{importe, concepto, categoria?, cuenta?}` creates the expense dated today (Europe/Madrid); without a category (or the legacy «Automática») it guesses it from the concept, and the account defaults to Revolut. It replies with a short text for the Shortcut's notification.
- `GET /api/history?movs=&cuentas=&transfers=&excluir=&hasta=` → daily net-worth history rebuilt from Balance Inicial plus dated movements and transfers, and the raw investment rows. The app adds the portfolio value per day (`valorCarteraDia`) and caches the response in localStorage (`kashy-pat-hist`).
- `/api/gasto` and `/api/history` call this deployment's own proxies and forward the key, so they hold no token.
- `api/push.js` and `api/cron-avisos.js`: see Notifications.

## Security

- Every `/api/*` endpoint requires the shared secret in the `X-Kashy-Key` header, compared in constant time with the `KASHY_KEY` Vercel env var (`api/_auth.js`). It answers 401 with a wrong or missing key and 500 if the variable is not set.
- The app asks for the key once, stores it in localStorage (`kashy-key`), adds it to every `/api/` call through its `fetch` wrapper and asks again on a 401. It can be changed in Ajustes › Cambiar clave (the new key is checked at once by refreshing).
- The Notion token lives only in the `NOTION_TOKEN` Vercel env var, read by `api/_notion.js`. If Notion rejects it the proxies answer 502, never 401, so the app doesn't ask for the key by mistake. Never put a token in the code: an old one remains in the git history and must stay revoked.
- Never cache an authenticated response in the CDN: it would be served without running the check.
- The app makes no external requests at runtime: no web fonts, no logo API, no analytics. Icons and logos are bundled. The tests enforce it.

## Notifications

- `sw.js` only handles `push` and `notificationclick`: no `fetch` handler, no `tag`, it never closes notifications. `manifest.webmanifest` (`start_url` `/index-nuevo.html`) is what lets iOS install the app with push.
- The toggle, the test button and the status messages are in the Ajustes sheet. `api/push.js` (behind `X-Kashy-Key`) returns the VAPID public key, saves or deletes the subscription and sends a test notification.
- `api/cron-avisos.js` (behind `CRON_SECRET`) runs from two Vercel crons (07:00 and 08:00 UTC, `vercel.json`) and only sends between 9:00 and 9:59 Madrid time, once a day, with TTL 24 h and no Topic.
- State (the subscription, the last send date, the last portfolio value reminded) lives in the Notion database «Ajustes Kashy» (`api/_ajustes.js`).
- Env vars: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`, `CRON_SECRET`. Reinstalling the home-screen app drops the subscription: turn notifications on again in Ajustes.

## Architecture of the HTML app

- **Data layer**: `nFetch(path, method, body)` turns Notion-style paths into calls to the proxies; updates and deletes call `/api/page` and `/api/delete` directly. Database IDs are constants near the top of the script: `DB_ID` (movements), `CUENTAS_DB` and `TRANSFER_DB`. Notion property names are in Spanish, and the code walks `p.properties.X.title[0].plain_text`, `.select.name`, `.number` and so on, so renaming a Notion property breaks the app without any error.
- **`CUENTAS_DB`** holds several kinds of rows, told apart by their columns: accounts (`Cuenta o Meta = Cuenta`) and MyInvestor records (any row with `InvTipo`: `Aportación` or `Valor Cartera`, with `InvImporte`, `InvFecha` and, for values, `InvFondo`, one of the `FONDOS` keys). Notion still holds old savings-goal rows (`Cuenta o Meta = Meta`) and wish-list rows (`Tipo = Wish List`); the app no longer shows them and must never edit or delete them. Every query on `CUENTAS_DB` filters by its own record type so they never show up as accounts (`test_metas_y_deseos_de_notion_nunca_salen_como_cuentas`).
- **Portfolio**: `fetchValorCartera()` gives each fund's latest value plus its share (`pct`) of later contributions; if some fund has no value yet, the latest total plus later contributions. The Inversión history lists every contribution but only the current value of each fund; older values stay in Notion and still feed the chart and the return.
- **Navigation**: sections are `<div class="section" id="sec-{name}">` (inicio, movimientos, registrar, stats, cuentas, inversion). `showSec(name, navIdx)` switches and calls the section's loader (`loadInicio`, `loadMovs`, `loadStats`, `loadAccounts`, `loadInversion`); tapping the current tab only scrolls to the top. There are no Recargar buttons and no pull-to-refresh (removed: it fired by accident while scrolling): data refreshes when switching tabs and after every write.
- **Cache (stale-while-revalidate)**: opening a section shows its last data at once and refreshes it from Notion behind. Lists go through `pintar(el, key, html)`, which repaints only if the HTML changed, and `mostrarGuardado`, which shows what is in memory or in localStorage (`kashy-cache-v1`). A skeleton appears only when nothing is cached. Every write through the `fetch` wrapper schedules `refrescarTrasEscritura`, which refreshes everything already shown. Never assign `innerHTML` directly on a cached list: use `pintar`, or call `marcarTocadas()` after editing the DOM by hand. A failed Notion query must throw, not count as empty, or the cache would store it. At most 4 `/api/` requests run at once.
- **Inicio**: patrimonio (accounts plus portfolio) with its breakdown (opens from the title, the amount or «Desglose», not from the summary), the chart with periods and finger scrub, the Gastado/Ingresado/Balance card, the «Hoy vence» and MyInvestor alerts, the account carousel (opens that account) and expenses by category. The gear opens Ajustes.
- **Movimientos**: type, account and category chips, and a search (`buscarMovs` waits 300 ms; `loadMovs` adds a Notion `title contains` on Nombre and, when the text matches a category or an account, that relation; transfers match by their accounts or name). Rows are grouped by day with their balance; swipe for Editar/Eliminar.
- **Registrar**: expense/income, the amount sized to its text (`ajustarImporteReg`), a merchant suggestion that picks its category unless chosen by hand (`CAT_DE_COMERCIO`), account chips, categories, Hoy/Ayer/Otra, the success moment, «Deshacer», recurring payments with installment bars (each in its category colour; finished ones hidden) and quick incomes.
- **Cuentas**: grouped account rows with bank logos. An expanded account shows Mover and Desactivar (Añadir and Retirar stay hidden on purpose) and, via `cargarMovsCuenta`, its movements and its transfers in and out («A …» / «De …», purple) mixed by date; transfer rows (`.acc-tr-row`, `data-tr`) open `openEditTransfer`, also on long press. Recurring transfers and inactive accounts (reactivate) follow.
- **Inversión**: portfolio value, Aportado/Rendimiento/Rentabilidad, funds (tap the ISIN to copy it), monthly contribution, «Nueva aportación», «Actualizar valor» per fund, and the history.
- **Stats** (opened from Inicio): periods; for «Este mes», cumulative spending day by day with the previous month up to the same day in grey (`renderTrendMes`); category donut, income sources, top expenses, comparison with the previous month, activity, insight and the monthly history with CSV export.
- **Ajustes sheet** (`openAjustes`): theme, Ocultar importes (same as the eye), notifications and Cambiar clave.
- **Removed features**: Presupuestos (and its sheet), Metas de ahorro, Lista de deseos, the annual investment goal, the Recargar buttons, pull-to-refresh and the old WebAuthn/Face ID lock. Don't bring them back unless asked.
- **i18n**: `I18N = { es: {...}, en: {...} }` with `t(key, vars)`, which fills `{var}` placeholders and falls back to `es`, then to the key. The app is Spanish only: add new strings to `es` only; the `en` dictionary is kept but not maintained.
- **localStorage**: `kashy-` keys (`kashy-theme`, `kashy-lang`, `kashy-key`, `kashy-cache-v1`, `kashy-pat-hist`) or constants (`PRIV_KEY`). Only UI preferences, the API key and the screen cache; all financial data lives in Notion.
- **Layout**: mobile-first, `.app` capped at 430 px, fixed bottom bar, installed as an iOS home-screen web app.
- **Formatting**: amounts in euros with `fmt`/`parseAmt`/`sanitizeAmt`, Spanish format («84,50 €», a space before € and %); editable amounts use `importeCampo`. Dates are local (`hoyLocal`, `fechaLocalDe`), never UTC.

## Design system (see `docs/sistema-de-diseno.md`)

- **Theming**: CSS custom properties on `:root` (dark) and `[data-theme="light"]`, applied before the first paint by an inline script. Expenses `--red`/`--negative`, income `--green`/`--positive`, transfers and selection `--accent` (`#5B4CEB` light, `#A197FF` dark). The system font (`--font`, SF Pro on the iPhone; `--font-round` for big figures).
- **Design kit**: `svgIco(name)` draws a bundled Lucide icon (`KIT_ICONOS`). `fichaCat(id)` is a category tile with its icon and colour from `CAT_META`, keyed by the Notion category id (Coche shows the Hyundai logo). `fichaCuenta(name)` is an account tile with its bank logo (`KIT_LOGOS`, from the banks' own sites, plus Revolut from Simple Icons). `fichaMov(name, catId)` shows a merchant's logo when `comercioDe(name)` finds it in the name (`COMERCIOS` lists how each merchant is written, compared without case, accents, emoji or punctuation, one typo allowed on single words; `MARCA` says how to draw it), otherwise the category tile. `sinEmoji` strips a leading emoji from a Notion name only when displaying it; names in Notion keep their emoji because installments match by exact name.
- The redesigned screens' CSS lives in scoped blocks at the end of `<style>` (`/* ══ REDISEÑO · … ══ */`).
- **Amounts are never cut off**: `autoFitAmount(el)` shrinks an amount's font until it fits its own box (down to half size) and then lets it wrap; `ajustarCifras(root)` runs it on every `CIFRAS_AJUSTABLES` element and on resize. An amount needs a box with a width (block, and `min-width:0` inside flex or grid). `ponerCifra` draws a `data-partes` element in two sizes («5925» and «,00 €»).
- **Sheets always fit and never pan sideways**: every `.modal-overlay` sheet fits a 390 × 667 screen without scrolling, with `.modal-btns` sticky at the bottom; the sheet only moves vertically (`overflow-x:hidden`, `touch-action:pan-y`) and only chip rows scroll sideways (`.chips-wrap`, `.fila-desliza`, `overscroll-behavior-x:contain`). Date inputs match the field beside them, with `line-height` equal to their height so iOS centres the value.
- **Count-up**: `contarAlEntrar(name)`, called by `showSec`, counts a tab's headline figures (`CIFRAS_AL_ENTRAR`) from 0 in 600 ms; not on the same tab, after a sheet or on background refreshes. `animateCounter` and it share a per-element turn (`_turno`/`_hacia`) so new data takes over. With «Reduce motion» no figure counts, the patrimonio on app open included.
