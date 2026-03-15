# Logi-Hex — V1 Scope and Constraints

This document defines exactly what V1 of logi-hex will do and what it will not
do. It exists to prevent scope creep and accidental introduction of new
behaviour.

---

## Goals for V1

V1 should:

- Track movements of items in two clear modes:
  - Accounts — items sent to clients and collected back.
  - Inventory — items received, used, and corrected.
- Enforce basic safety rules:
  - Cannot Collect more than a client currently has.
  - Cannot Use more than is in stock.
- Provide clear dashboards:
  - Accounts: “Still Out” per client, “Outstanding” total.
  - Inventory: “In Stock” per item, with Low/Empty indicators.
- Keep a simple, immutable history of movements for audit and learning.

V1 should **not** try to be full accounting, full ERP, or recipe management.

---

## In-scope features

### 1. Authentication

- User registration and login.
- Session management (stay logged in between page loads).
- Basic password-based login is sufficient for V1.

### 2. Workspaces

- A user can have multiple workspaces.
- Each workspace has:
  - `id`
  - `name`
  - `mode` ∈ { `ACCOUNTS`, `INVENTORY` }
  - `owner_user_id`
- Workspace mode is chosen on creation and cannot be changed later.
- All domain data (items, clients, movements, groups, tags) is scoped to a workspace.
- The UI has:
  - A workspace picker after login.
  - A “Switch workspace” control in the main navigation.

### 3. Items

- Create, read, update, archive items per workspace.
- Each item has:
  - `id`
  - `label`
  - `unit` (free text)
  - `group_id` (Item Group)
  - `workspace_id`
  - `is_active` (false = archived)
- Items can be tagged with multiple tags.
- V1 does not support locations or multiple warehouses.

### 4. Item Groups

- Create and list Item Groups per workspace.
- Each group has:
  - `id`
  - `name`
  - `workspace_id`
- V1: Item Groups are used for organisation and filtering; no special rules per group in the UI.

### 5. Tags

- Create and list tags per workspace.
- Assign tags to items (many-to-many).
- Filter dashboards by tag.

### 6. Clients (Accounts mode only)

- Create and list clients per workspace (Accounts mode).
- Client ids are derived from a normalised name and workspace id to avoid
  collisions.
- Clients are used only for Accounts movements (Send/Collect).

### 7. Movements — Accounts mode

- Log **Send** movements:
  - Choose a client.
  - Add one or more items with positive quantities.
  - Optional note and tags.
- Log **Collect** movements:
  - Choose a client.
  - Add one or more items with positive quantities.
  - System enforces:
    - For each item, `Collect quantity ≤ current Still Out`.
- Movements:
  - Are stored with immutable records (no updates, no deletes).
  - Belong to one workspace and one client.
  - Store UTC timestamp.

### 8. Movements — Inventory mode

- Log **Receive** movements:
  - Choose an item.
  - Positive quantity.
  - Optional note and tags.
- Log **Use** movements:
  - Choose an item.
  - Positive quantity.
  - System enforces:
    - `Use quantity ≤ current In Stock`.
- Log **Correct** movements:
  - Choose an item.
  - Enter the actual quantity on hand (target).
  - Choose a reason (`Shrinkage` or `Count Correction`).
  - System sets stock to the target value.
- Movements:
  - Are immutable.
  - Belong to one workspace and one item.
  - Store UTC timestamp.

### 9. Dashboards

#### Accounts dashboard

- For each client with non-zero “Still Out”:
  - Client name.
  - Per-item quantities “Still Out” with unit.
  - Last activity timestamp.
- Aggregated:
  - “Outstanding” total across all clients.
- A client detail view shows:
  - Full movement history (Send/Collect).
  - Current per-item “Still Out”.
  - Clear label if client is “Settled” (no items Still Out).

#### Inventory dashboard

- For each item:
  - Item label.
  - Item Group.
  - Tags.
  - “In Stock” quantity with unit.
  - Stock state badge: In Stock / Low / Empty.
- Filter controls:
  - Filter by tag.
- An item detail view shows:
  - Full movement history (Receive/Use/Correct).
  - Current “In Stock”.
  - Indication if there have been corrections.

---

## Out-of-scope for V1

These features must **not** be implemented in V1, even partially:

- Locations / warehouses / shelves (no `from_location` / `to_location`).
- Reservations (no “hold” state separate from stock).
- Composite / recipe items (no automatic component movements).
- Cost tracking, COGS, unit cost, or valuation.
- Batch imports/exports (beyond simple CSV export if desired later).
- Role-based access control (only owner-level for now).
- Reporting dashboards beyond the core views described above.
- Time-based analytics (trends, charts) beyond what movement history provides.

---

## Technical constraints

### Backend

- Use SQLAlchemy models with generic types. No SQLite-specific SQL in the domain
  logic or migrations.
- All DB writes for movements must be wrapped in a Unit of Work / transaction,
  to guarantee atomicity for multi-line movements.
- All timestamps stored as timezone-aware UTC.
- All entities have `workspace_id` and are consistently filtered by it.
- Migration path from SQLite to PostgreSQL must remain straightforward:
  - Single `DATABASE_URL` env variable for engine configuration.
  - No reliance on SQLite-specific features.

### Frontend

- All labels, button texts, and error messages must come from central language
  constants (see `frontend/lib/constants/language.ts`).
- No hardcoded mode names (“Accounts”, “Inventory”), actions (“Send”, “Use”),
  or reasons in components.
- The action bar in each mode must show the correct buttons:
  - Accounts: Send, Collect.
  - Inventory: Receive, Use, Correct.
- The log flow must be simple:
  - No raw “IN / OUT” toggles.
  - User always starts by choosing one of the named actions.

---

## Testing requirements

As a minimum, V1 must include tests that verify:

- Domain:
  - Cannot Collect more than Still Out for a given client/item/workspace.
  - Cannot Use more than In Stock for a given item/workspace.
  - Correct sets stock to the exact target, and reason is required.
  - Archived items cannot be used in new movements.
  - Workspace isolation: movements and summaries do not cross workspaces.
- API / Integration:
  - Creating a workspace, adding items/clients, logging movements, and
    reading dashboards all work end-to-end in both modes.
  - Error responses use the agreed language and structure (no leaking of
    raw DB errors or internal terms).

---

## Guardrails for future changes

To avoid accidental scope creep or regressions:

- Any new feature proposal must be checked against this document.
  - If it is not clearly in-scope for V1, it should be deferred to a later
    version and documented separately.
- Any new term or label introduced in the UI or API must be:
  1. Added to `docs/LANGUAGE.md`.
  2. Reflected in `domain/language.py`.
  3. Reflected in `frontend/lib/constants/language.ts`.
- Changes to movement behaviour (what Send/Collect/Receive/Use/Correct do)
  must:
  - Be captured as explicit domain rules.
  - Have tests written before or alongside the change.
- Features explicitly listed as “Out-of-scope for V1” (locations, costs,
  recipes, reservations, etc.) must not appear in:
  - APIs
  - UI
  - Database schema
  - Domain model
  until a future scope document explicitly brings them in.
