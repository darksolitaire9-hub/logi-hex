# Logi-Hex Issue Tracking Registry (Source of Truth)

This document is the **single source of truth** for all known runtime issues, bugs, and tasks in the Logi-Hex project. 
It replaces ad-hoc checklists and fragmented assumptions. Before implementing any fix or investigating any new bug, reference this document to ensure proper context and avoid regressions.

## Project Stack Baseline
- **Frontend Framework**: Nuxt 4 (`nuxt ^4.3.1`, `vue ^3.5.28`)
- **Desktop Framework**: Tauri v2 (`@tauri-apps/api ^2.0.1`, rust `tauri = "2.0.0-rc.17"`)
- **Database**: SQLite (managed via `@tauri-apps/plugin-sql` and Rust `sqlx = "0.8.6"`)
- **Styling**: Tailwind CSS (`tailwindcss ^4.2.1`), Nuxt UI
- **I18n**: `@nuxtjs/i18n ^9.5.6` (Lazy loading enabled)

---

## Issue Registry

### Issue ID: I-1 [RESOLVED]
**Title:** Nuxt i18n raw keys in Tauri packaged app
**Status:** **[RESOLVED]**
**Description:** Packaged app was rendering raw keys (e.g. `login.title`) instead of localized strings.
**Root Cause:** Nuxt was not bundling the locale files from `app/locales/` because `nuxt.config.ts` was pointing to `locales/` and explicitly defining static files.
**Resolution:** Consolidated translation JSON files into `frontend/locales/{lang}/login.json` and updated `nuxt.config.ts` accordingly.

---

### Issue ID: I-2 [RESOLVED]
**Title:** "Create Workspace" form submit does nothing
**Status:** **[RESOLVED]**
**Description:** Submitting the "Create Workspace" onboarding form showed no errors, performed no navigation, and failed to create a DB record because the underlying IPC call silently failed.
**Root Cause:** The `workspaces` table did not exist because migrations were aborting. The `1_init.sql` migration contained `PRAGMA journal_mode=WAL;`. Because the Rust backend (`sqlx` via `init_db`) opened the DB pool first and set WAL mode, executing that `PRAGMA` from the `tauri_plugin_sql` JS initialization later triggered a SQLite locking error. This swallowed error caused `Database.load()` to fail, leaving the UI stuck.
**Resolution:** Removed `PRAGMA journal_mode=WAL;` from `1_init.sql`. (WAL is already enabled at the connection layer by `sqlx` in `init_db`).

---

### Issue ID: I-3 [RESOLVED]
**Title:** Other languages not loading correctly
**Status:** **[RESOLVED]**
**Description:** Although the English raw keys issue (I-1) was fixed, switching to other languages (ES, JA) may not be fully functioning yet.
**Root Cause Hypothesis:** Missing locale JSON files for non-English languages or lazy-loading path resolution issues in Tauri build.
**Resolution:** The root cause was indeed missing files. We generated the corresponding `core.json`, `inventory.json`, and `errors.json` for the `es` and `ja` locales and correctly registered them in the `locales` array within `nuxt.config.ts`. The UI now updates correctly when switching languages.
---

### Issue ID: I-4 [RESOLVED]
**Title:** CSP and Tauri capabilities blocking frontend SQL and assets
**Status:** **[RESOLVED]**
**Description:** The frontend encountered errors indicating `sql.load` was not allowed, CSP blocking connections to local `tauri.localhost` endpoints and the external `api.iconify.design` icon server, and inline script execution blocks.
**Root Cause:** Tauri v2 blocks all plugin IPC commands by default and imposes a strict default CSP that blocks inline scripts and unexpected connection origins.
**Resolution:** Added `"sql:allow-load"`, `"sql:allow-select"`, `"sql:allow-execute"`, and `"sql:allow-close"` permissions in `default.json` (strictly scoped to the `main` window). Adjusted the `security.csp` in `tauri.conf.json` to allow `'unsafe-inline'` for script execution and added `http://tauri.localhost`, `https://tauri.localhost`, and `https://api.iconify.design` to `connect-src`. Tested with successfully passing static generation and Tauri compiler builds.

---

## Tracking Schema (For Future Issues)
When adding a new issue, use the following format:
```markdown
### Issue ID: I-X
**Title:** [Short description]
**Status:** [Open | Investigating | In Progress | Resolved]
**Description:** [What is happening vs what is expected]
**Root Cause Hypothesis:** [Current best guess based on evidence]
**Next Steps (Evidence Plan):** [Specific actions to prove/disprove hypothesis]
```
