# Logi-Hex Project Roadmap

This roadmap defines the strategic phases to achieve a stable, secure, and fully-tested Tauri + Nuxt desktop application, strictly adhering to the "Rust is the brain, Frontend is a thin client" commander's intent.

## Git Commit Policy (Strict)

All commits must follow the **Atomic Commit Policy**.
- **One logical change per commit.** Do not bundle unrelated features or fixes.
- Use standard conventional commits prefixes:
  - `feat:` (New features)
  - `fix:` (Bug fixes)
  - `refactor:` (Code restructuring without behavior changes)
  - `test:` (Adding or updating tests)
  - `docs:` (Documentation updates)

---

## Phase 1: Architectural Pivot (The Rust Brain)
**Status:** Completed ✅

The frontend previously used `tauri-plugin-sql` to execute raw database queries. This violated the thin-client architecture. We have successfully migrated all data logic into strongly-typed Rust Tauri commands.

- [x] **Vertical Slice 1: Workspaces**
  - Created Rust `commands::workspace`.
  - Refactored `useWorkspace.ts` to use `invoke()`.
- [x] **Vertical Slice 2: Core Entities (Items, Clients)**
  - Created Rust `commands::item` and `commands::client`.
  - Refactored `useItems.ts` and `useClients.ts`.
- [x] **Vertical Slice 3: Ledger & Alerts**
  - Refactored remaining composables (`useAlerts.ts`, etc.).
  - Completely uninstalled and removed `tauri-plugin-sql` from the frontend bundle.

## Phase 2: Test Environment & IPC Safety
**Status:** In Progress ⏳

Before adding UI tests, we must establish database isolation so tests do not pollute user data, and generate TypeScript types from Rust structs to prevent IPC contract drift.

- [ ] **TypeScript Binding Generation**
  - Add `ts-rs` dependency to Cargo.toml.
  - Derive `TS` on all payload/response structs in `types/mod.rs` to auto-generate `frontend/app/types/bindings.ts`.
- [ ] **Database Isolation for Testing**
  - Modify SQLite initialization in `db/mod.rs` to detect the `LOGIHEX_TEST_ENV` environment variable.
  - Inject an in-memory SQLite database (`sqlite::memory:`) or temp database path when testing to prevent pollution of `logihex.db`.

## Phase 3: Vitest UI Component Testing
**Status:** Pending ⏳

Because the frontend is a pure thin client interacting only via `invoke()`, components can be tested deterministically with mocked IPC states.

- [ ] Configure Vitest (`vitest.config.ts`) to work with Nuxt 4 and `happy-dom`.
- [ ] Create a global Tauri IPC mock in `frontend/app/utils/tauri-mock.ts` to intercept `invoke` calls.
- [ ] Add `"test": "vitest"` script to `package.json`.
- [ ] Write component integration tests (e.g. Workspace flow and onboarding).

## Phase 4: End-to-End (E2E) Testing Harness
**Status:** Pending ⏳

Configure E2E testing to run the Tauri application webview and simulate user interactions against the isolated testing database.

- [ ] Choose and configure E2E testing framework (WebdriverIO or Playwright).
- [ ] Write first E2E flow verifying workspace onboarding and navigation without database pollution.
