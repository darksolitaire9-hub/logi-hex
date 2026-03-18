# Deprecation Log

## Pre-DDD routes (superseded by V1 DDD layer)

These routes existed before the hexagonal architecture refactor.
Old tests in `test_movements.py` and `test_clients.py` covered them.
Both test files were deleted on 2026-03-17 — behaviours to re-test in V1:

| Behaviour | Old route | V1 route | V1 tests |
|---|---|---|---|
| Create item group | POST /api/tracking-categories | POST /workspaces/{id}/item-groups | (pending) |
| Create item | POST /api/tracking-items | POST /workspaces/{id}/items | (pending) |
| Collect movement | POST /api/movements/receive | POST /workspaces/{id}/movements/collect | tests/integration/api/movements/accounts/collect/ |
| Collect blocked (no prior send) | same | same | tests/integration/api/movements/accounts/collect/test_movements_collect_guards.py |
| Unknown tag → 404 | POST /api/movements/issue | POST /workspaces/{id}/movements/send or /collect | tests/integration/api/movements/accounts/send/test_movements_send_guards.py |
| Accounts summary | GET /api/summary | GET /workspaces/{id}/accounts | (pending) |
| List clients | GET /api/clients | GET /workspaces/{id}/clients | (pending) |

## Routes pending removal

Once V1 routes are fully tested, remove:
- adapters/api/routes_containers.py
- adapters/api/routes_tracking.py
- adapters/api/routes_summary.py
- adapters/api/routes_clients.py
- adapters/api/dev_routes.py (review first)

## Adapter refactors

These are internal adapter-level refactors that do not change the public HTTP
contract but improve modularity.

- 2026-03-17: `adapters/api/routes_movements.py` replaced by the
  `adapters/api/routes_movements/` package
  - API entrypoint unchanged: movements still mounted via `adapters/api/__init__.py`
  - Initial structure (Accounts mode):
    - `adapters/api/routes_movements/__init__.py`
    - `adapters/api/routes_movements/accounts/send/`
    - `adapters/api/routes_movements/accounts/collect/`
  - Send and collect tests under:
    - `tests/integration/api/movements/accounts/send/`
    - `tests/integration/api/movements/accounts/collect/`
  - Deleted `tests/integration/test_generic_transaction_repo.py`
    (legacy `Transaction` model). Behaviour is now covered by movement-based
    repositories and integration tests.

- 2026-03-18: Inventory RECEIVE endpoint added to
  `adapters/api/routes_movements/` package
  - New schema: `adapters/api/schemas/movements_receive.py`
    - `ReceiveMovementIn`: item_id, quantity, notes (optional), tag_ids (optional)
    - Flat schema — Inventory movements are per-item, no line items list
  - New routes:
    - `adapters/api/routes_movements/inventory/__init__.py`
    - `adapters/api/routes_movements/inventory/receive/__init__.py`
    - POST /workspaces/{id}/movements/receive
  - `adapters/api/routes_movements/__init__.py` updated to wire inventory router
  - Tests under `tests/integration/api/movements/inventory/receive/`:
    - `test_movements_receive.py`: happy path, notes optional, tag_ids optional
    - `test_movements_receive_auth.py`: 401 no auth, 404 unknown workspace
    - `test_movements_receive_guards.py`: 409 accounts workspace, 400 archived item, 404 unknown item
    - `test_movements_receive_validation.py`: 400 zero quantity, 422 missing item_id, 422 missing quantity

## Domain refactors

These are internal domain-level refactors that preserve public behaviour and
HTTP contracts but improve modularity and discoverability.

- 2026-03-17: `domain/entities.py` replaced by the `domain/entities/` package
  - New structure:
    - `domain/entities/workspaces.py`
    - `domain/entities/accounts.py`
    - `domain/entities/inventory.py`
    - `domain/entities/tags.py`
    - `domain/entities/__init__.py` re-exporting the public entities
  - 2026-03-18: `domain/entities.py` shim deleted — Python always prefers the
    package; shim was never loaded at runtime.
  - No changes to entity behaviour or imports.

- 2026-03-17: `domain/language.py` replaced by the `domain/language/` package
  - New structure:
    - `domain/language/shared.py` — shared enums, labels, and rules
      (WorkspaceMode, MovementDirection, CorrectionReason, LEDGER_SIGN,
      VALID_DIRECTIONS, etc.)
    - `domain/language/accounts.py` — Accounts dashboard labels
      (Still Out, Outstanding, Settled)
    - `domain/language/inventory.py` — StockState enum, stock state labels,
      LOW_STOCK_THRESHOLD, inventory dashboard labels
      (In Stock, Low, Empty, Shrinkage)
    - `domain/language/suggestions.py` — SUGGESTED_UNITS
    - `domain/language/__init__.py` re-exporting the public language API
  - 2026-03-18: `domain/language.py` shim deleted — same reason as entities.
  - No changes to enum values, labels, or rules.

- 2026-03-17: `domain/exceptions.py` replaced by the `domain/exceptions/` package
  - New structure:
    - `domain/exceptions/shared.py` — shared exceptions:
      WorkspaceNotFoundError, WorkspaceModeMismatchError, ArchivedItemError,
      EmptyMovementError, ItemNotFoundError, ItemGroupNotFoundError,
      TagNotFoundError
    - `domain/exceptions/accounts.py` — Accounts-specific exceptions:
      InsufficientStillOutError, ClientNotFoundError
    - `domain/exceptions/inventory.py` — Inventory-specific exceptions:
      InsufficientStockError, CorrectionReasonRequiredError
    - `domain/exceptions/__init__.py` re-exporting the public exceptions API
  - 2026-03-18: `domain/exceptions.py` shim deleted — same reason as entities.
  - Exception messages remain aligned with `docs/LANGUAGE.md`.

- 2026-03-17: `domain/ports.py` replaced by the `domain/ports/` package
  - New structure:
    - `domain/ports/workspaces.py` — WorkspaceRepositoryPort, UnitOfWorkPort
    - `domain/ports/accounts.py` — ClientRepositoryPort, AccountsQueryPort
    - `domain/ports/inventory.py` — ItemGroupRepositoryPort,
      ItemRepositoryPort, TagRepositoryPort, StockQueryPort
    - `domain/ports/movements.py` — MovementRepositoryPort
    - `domain/ports/__init__.py` re-exporting the public ports API
  - 2026-03-18: `domain/ports.py` shim deleted — same reason as entities.
  - No changes to port method signatures or behaviour.
