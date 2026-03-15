# Logi-Hex — Ubiquitous Language

## What this is

This file defines the **only** words we use to describe the logi-hex domain.

- Developers use these words in code.
- Designers use these words in the UI.
- Business users see these words in the app.
- Documentation uses these words.

If a term is not in this file, it should not appear in the product.

## Why this exists

Without a shared language:

- Developers say "OUT".
- Designers say "Issue".
- Users say "Send".
- Support hears "that send button is missing".

With a shared language:

- Everyone says **Send**.
- The code uses `MovementDirection.SEND`.
- The UI shows a **Send** button.
- The docs say “Send items to clients”.

---

## Modes

| Term | Code | Meaning |
|---|---|---|
| **Accounts** | `ACCOUNTS` | Track what you’ve sent to people and what they still have of yours |
| **Inventory** | `INVENTORY` | Track what you have in stock right now |

Rules:

- “Accounts” always refers to the **workspace mode**, never to login accounts
  or accounting software.
- Each workspace has exactly one mode, set on creation and never changed.

---

## Actions (user-facing movement types)

These are the only action words shown to users. Each action maps to a single
internal direction.

| Word | Mode | Internal direction | Past tense (history) | Meaning |
|---|---|---|---|---|
| **Send** | Accounts | `OUT` | Sent | You gave items to a client |
| **Collect** | Accounts | `IN` | Collected | A client gave items back to you |
| **Receive** | Inventory | `IN` | Received | Stock arrived or was delivered |
| **Use** | Inventory | `OUT` | Used | Stock was sold or consumed |
| **Correct** | Inventory | `ADJUST` | Corrected | Physical count was wrong and you fixed it |

Rules:

- IN / OUT / ADJUST are **internal ledger terms only**, not shown in the UI.
- UI must always use **Send**, **Collect**, **Receive**, **Use**, **Correct**.

---

## States (what dashboards and labels show)

### Accounts mode

| Word | Meaning | Where used |
|---|---|---|
| **Still Out** | Items a client currently has of yours | Client row on Accounts dashboard |
| **Outstanding** | Total items still out across all clients | Top of Accounts dashboard |
| **Settled** | Client has nothing Still Out | Badge on client in list/detail |

### Inventory mode

| Word | Meaning | Where used |
|---|---|---|
| **In Stock** | Current quantity on hand | Item row on Inventory dashboard |
| **Low** | Stock is near zero and needs attention | Badge on item row (amber) |
| **Empty** | Stock is exactly zero | Badge on item row (red) |
| **Shrinkage** | Unexplained loss revealed by a correction | Badge/label on corrections or reports |

---

## Correction reasons (Inventory mode)

When the user performs **Correct** on an item, they must choose a reason:

| Word | Code | Meaning |
|---|---|---|
| **Shrinkage** | `SHRINKAGE` | Stock is missing due to spoilage, damage, theft, or unknown |
| **Count Correction** | `COUNT_CORRECTION` | A previous count was wrong; adjusting to the real number |

Notes:

- These reasons are user facing.
- They power shrinkage and accuracy analytics.
- The internal concept of an initial starting value (opening stock) is **not**
  shown to the user and has no label in the UI.

---

## Entities

### Workspace

| Word | Meaning |
|---|---|
| **Workspace** | One isolated “notebook” of movements for a business or context |

Rules:

- All items, clients, movements, groups, and tags belong to a workspace.
- No data crosses between workspaces.

---

### Client (Accounts mode)

| Word | Meaning |
|---|---|
| **Client** | Person or place you Send items to in Accounts mode |

Notes:

- Client ids are derived from workspace id + normalised name to avoid collisions.
- Clients exist only in Accounts mode; Inventory mode has no client concept.

---

### Item

| Word | Meaning |
|---|---|
| **Item** | Anything you want to track (Coke, Steel Box, Salmon, etc.) |
| **Unit** | How the item is measured (e.g. `pcs`, `kg`, `L`) |

Rules:

- Every quantity is stored with the item’s unit.
- UI always displays unit next to quantity, never a bare number.

---

### Item Group

| Word | Meaning |
|---|---|
| **Item Group** | A category that groups related items (Drinks, Seafood, Containers, etc.) |

Notes:

- Groups are per workspace.
- V1: there is no group-specific behaviour exposed in the UI beyond grouping.

---

### Tag

| Word | Meaning |
|---|---|
| **Tag** | A simple label for filtering and grouping items (frozen, drinks, takeaway, etc.) |

Notes:

- Items can have many tags.
- Tags are per workspace.
- UI uses tags as chips/pills and filter controls.

---

### Movement

| Word | Meaning |
|---|---|
| **Movement** | One logged action (Send, Collect, Receive, Use, or Correct) |

Rules:

- UI shows “Movements” or “Movement history”, not “Transactions”.
- Movements are immutable; corrections are additional movements.

---

### Archived

| Word | Meaning |
|---|---|
| **Archived** | Item no longer used for new movements; history retained |

Rules:

- UI uses “Archived” (not “Deleted”, “Inactive”, or “Disabled”).
- Logging a movement for an archived item is blocked with a clear message.

---

## Units (suggested values)

Units are free text in the domain. The UI may suggest some common units:

| Unit | Meaning | Typical use |
|---|---|---|
| `pcs` | Pieces | Boxes, containers, bottles |
| `kg` | Kilograms | Meat, fish, produce |
| `g` | Grams | Spices, small ingredients |
| `L` | Litres | Drinks, bulk liquids |
| `ml` | Millilitres | Sauces, oils |
| `box` | Box | Packaged items |
| `bag` | Bag | Flour, rice, frozen items |
| `portion` | Portion | Pre-portioned items |

---

## Error messages (language rules)

Error messages must:

- Use the same terms as the rest of the product.
- Name the client and item.
- Show the actual numbers.

Examples:

- **Collect too many items from a client**  
  `"Alice only has 3 pcs of Steel Box. You cannot collect 5 pcs."`

- **Use more than in stock**  
  `"Coke is at 2 pcs. You cannot use 5 pcs."`

- **Use when empty**  
  `"Coke is empty. Receive stock before using it."`

- **Log movement against archived item**  
  `"Steel Box is archived. Reactivate it to log movements."`

- **Correction without reason**  
  `"Please select a reason for this correction."`

- **Zero or negative quantity**  
  `"Please enter a quantity greater than zero."`

---

## How to use this language in code and UI

Backend:

- Import `WorkspaceMode`, `MovementDirection`, `CorrectionReason`, and
  related maps from `domain/language.py`.
- Do **not** hardcode values like `"ACCOUNTS"`, `"INVENTORY"`, `"SEND"`,
  `"RECEIVE"`, or `"SHRINKAGE"` in domain, application, or infrastructure
  code.
- When implementing guards:
  - Use `MovementDirection.COLLECT` and `MovementDirection.USE` to trigger
    balance/stock checks.
- When returning data through the API:
  - Use the labels from `MODE_LABELS`, `DIRECTION_LABELS`, and
    `CORRECTION_REASON_LABELS` where human-readable text is needed.

Frontend:

- Import `WorkspaceMode`, `MovementDirection`, `ModeLabels`,
  `DirectionLabels`, `DashboardLabels`, `ErrorMessages`, and
  `SuggestedUnits` from `frontend/lib/constants/language.ts`.
- Do **not** hardcode button labels like "Send", "Collect", "Receive",
  "Use", or "Correct" in components.
- Use `ModeActions[workspaceMode]` to decide which action buttons to show
  (Accounts vs Inventory).
- Use `DirectionPastTense` when rendering movement history
  (e.g. "Sent 5 boxes", "Used 3 kg").

Process:

- If you need a new term or label, add it here first.
- Only after it is added to this document and to the language constants
  should it appear in code or UI.

---

## Rules summary

1. UI never shows IN / OUT / ADJUST — only Send, Collect, Receive, Use, Correct.
2. UI never shows “Transaction” — only “Movement” or “Movement history”.
3. UI never shows “Balance” alone — use “Still Out” (Accounts) or “In Stock” (Inventory).
4. “Accounts” is the workspace mode — not login accounts or bookkeeping.
5. “Correct” is used only in Inventory mode.
6. Error messages always mention the item and actual quantities.
7. Item quantities always show their unit.
8. Archive does not remove history — it only blocks new movements for that item.
