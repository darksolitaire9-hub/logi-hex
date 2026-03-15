# logi-hex

logi-hex is a small, opinionated system for tracking how things move in and out
of your business.

It answers two questions:

1. **Accounts mode** — What have I sent to people, and what do they still have?
2. **Inventory mode** — What do I have in stock right now?

Everything is built around one simple rule:

> Every time something moves, write it down once, in one place.

---

## Why logi-hex exists

Most small businesses track this information in their heads, on WhatsApp, or
spread across spreadsheets and paper slips. That works until:

- You forget who still has your containers.
- You miscount stock and run out mid-service.
- You lose track of shrinkage (waste, theft, spoilage).

logi-hex gives you:

- A single **ledger of movements**.
- Two workspace modes that match how you actually work.
- A clear, consistent language for everyone on the team.

---

## Core concepts

### Workspaces

A **workspace** is a single, isolated “notebook” of movements.

- One business or job = one workspace.
- Each workspace has a **mode**:
  - `ACCOUNTS` — track items sent to clients and what they still have.
  - `INVENTORY` — track items in stock.
- All items, clients, movements, and tags belong to a workspace.
- Data never crosses between workspaces.

You choose the mode once when you create a workspace. It cannot be changed
later for that workspace.

---

### Modes

#### Accounts mode

Use **Accounts** when you send physical things to people and expect them back.

Examples:

- You send steel boxes with food to clients and they return the boxes later.
- You lend crates, trays, or equipment to regular customers.

In this mode you:

- **Send** items to clients.
- **Collect** items back from clients.
- See what is **Still Out** per client.
- See the **Outstanding** total across all clients.

The system guarantees:

- You cannot **Collect** more of an item from a client than they currently
  have “Still Out”.

#### Inventory mode

Use **Inventory** when you care about how much you have in stock right now.

Examples:

- Bottles of drinks.
- Kilos of meat or prawns.
- Boxes of sauce or dry goods.

In this mode you:

- **Receive** stock when deliveries arrive.
- **Use** stock when it is sold or consumed.
- **Correct** stock if the physical count does not match the system.
- See the current **In Stock** quantity for every item.

The system guarantees:

- You cannot **Use** more of an item than you have in stock.

---

### Items

An **item** is anything you want to track.

Each item has:

- `label` — e.g. `"Coke"`, `"Steel Box"`, `"Salmon"`.
- `unit` — e.g. `"pcs"`, `"kg"`, `"L"`.
- `group` — an **Item Group** such as `"Drinks"`, `"Seafood"`, `"Containers"`.
- `tags` — free-form labels like `"frozen"`, `"urgent"`, `"takeaway"`.
- `workspace_id` — which workspace it belongs to.
- `is_active` — `True` for normal items, `False` when archived.

Items are shared between modes, but how you interact with them depends on the
workspace mode.

---

### Clients (Accounts mode)

A **client** is a person or place you send items to in **Accounts** mode.

- Clients are created by name.
- Under the hood, each client id is derived from the workspace id and a
  normalised name, to avoid collisions like `"Alice"` vs `"Alice Smith"`.
- Clients are workspace-specific.

In **Accounts** mode, all **Send** and **Collect** movements are tied to a
client.

---

### Movements

A **movement** is a single logged action. There are five user-facing movement
types:

- **Send** (Accounts) — you gave items to a client.
- **Collect** (Accounts) — a client gave items back to you.
- **Receive** (Inventory) — stock arrived / was delivered.
- **Use** (Inventory) — stock was sold or consumed.
- **Correct** (Inventory) — you fixed the stock count to match reality.

Every movement records:

- Workspace.
- Direction (one of the above).
- Which client (Accounts) or which item (Inventory).
- One or more line items with quantities in the item’s unit.
- Optional tags and notes.
- Timestamp (UTC).

Movements are **immutable**:

- Existing movements are not edited or deleted.
- Corrections are represented as new movements.

---

### Corrections and reasons

In **Inventory** mode, sometimes the system’s number and the shelf’s number
don’t match. When that happens you use **Correct**.

- You pick the item.
- You enter how many you actually have right now.
- You choose a reason:
  - `Shrinkage` — missing due to spoilage, damage, theft, or unknown.
  - `Count Correction` — a previous count was wrong.

The system:

- Sets stock to the new number.
- Keeps the reason, so shrinkage and counting errors can be analysed later.

The concept of “Opening Balance” (starting stock) is kept internal:

- When you add an item, the UI can ask: “How many do you have right now?”
- If you answer, the system stores that as an internal starting movement.
- Users never see “Opening Balance” as a label.

---

### Tags

Tags are simple labels you can attach to items, such as:

- `frozen`
- `drinks`
- `seafood`
- `takeaway`

You can:

- Filter dashboards by tag (e.g. only see frozen items).
- Use tags to group items for reporting.

Tags are per-workspace.

---

## V1 feature scope (short version)

In v1, logi-hex supports:

- Multiple users.
- Multiple workspaces per user.
- Two workspace modes: Accounts and Inventory.
- Items with units, groups, tags, and archived state.
- Clients in Accounts mode.
- Movements:
  - Accounts: Send and Collect with guard on Collect.
  - Inventory: Receive, Use, Correct with guard on Use.
- Dashboards:
  - Accounts: per-client “Still Out” and total “Outstanding”.
  - Inventory: per-item “In Stock”, with Low/Empty badges.
- Immutable movement history for each client and item.
- Basic stock correction with reasons (Shrinkage, Count Correction).

Out of scope for v1:

- Locations or warehouses.
- Costs and COGS.
- Composite/recipe items.
- Reservations (holding stock without using it).
- Role-based access control.

For the detailed v1 scope and constraints, see [`docs/V1-SCOPE.md`](docs/V1-SCOPE.md).

For the full language reference used across the app, see
[`docs/LANGUAGE.md`](docs/LANGUAGE.md).

---

## Implementation roadmap (for contributors)

This project follows a Domain-Driven Design approach. The next steps for the
current `feat/workspaces` work are:

1. **Language and docs first**
   - Add and review:
     - `docs/LANGUAGE.md`
     - `docs/V1-SCOPE.md`
     - `domain/language.py`
     - `frontend/lib/constants/language.ts`
   - Rule: no new terms in code or UI outside these files.

2. **Domain alignment**
   - Introduce `WorkspaceMode` and `MovementDirection` enums in the domain
     (imported from `domain/language.py`).
   - Add `workspace_id` to all domain entities that represent data stored in
     the database (Items, Clients, Movements, Groups, Tags).
   - Ensure movement entities:
     - Are immutable.
     - Use `Decimal` for quantities.
     - Do not leak raw `"IN" / "OUT"` into application or adapter layers.

3. **Guards and invariants**
   - Implement domain-level guards:
     - Accounts mode: cannot **Collect** more than a client has “Still Out”.
     - Inventory mode: cannot **Use** more than is “In Stock”.
     - Inventory mode: **Correct** requires a reason.
   - Write unit tests for these invariants before changing API or UI.

4. **Workspace isolation**
   - Ensure all repositories and queries accept and filter by `workspace_id`.
   - Add tests to prove data from one workspace never appears in another.

5. **Adapters and frontend**
   - Update API routes to:
     - Accept `workspace_id` explicitly (path or header).
     - Use `MovementDirection` values (`SEND`, `COLLECT`, etc.) instead of
       raw internal directions.
   - Update frontend to:
     - Draw all labels and actions from `frontend/lib/constants/language.ts`.
     - Use the mode-specific action sets:
       - Accounts: Send, Collect.
       - Inventory: Receive, Use, Correct.

6. **Persistence / DB**
   - Keep SQLAlchemy models portable (no SQLite-specific features).
   - Wrap all movement writes in a Unit of Work / transaction to guarantee
     atomic multi-line movements.
