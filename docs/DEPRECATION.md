# Deprecation Log

## Pre-DDD routes (superseded by V1 DDD layer)

These routes existed before the hexagonal architecture refactor.
Old tests in `test_movements.py` and `test_clients.py` covered them.
Both test files were deleted on 2026-03-17 — behaviours to re-test in V1:

| Behaviour | Old route | V1 route | V1 tests |
|---|---|---|---|
| Create item group | POST /api/tracking-categories | POST /workspaces/{id}/item-groups | (pending) |
| Create item | POST /api/tracking-items | POST /workspaces/{id}/items | (pending) |
| Collect movement | POST /api/movements/receive | POST /workspaces/{id}/movements/collect | tests/integration/api/movements/collect/test_happy.py |
| Collect blocked (no prior send) | same | same | tests/integration/api/movements/collect/test_guards.py |
| Unknown tag → 404 | POST /api/movements/issue | POST /workspaces/{id}/movements/send or /collect | tests/integration/api/movements/send/test_guards.py |
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

These are internal adapter-level refactors that do not change the public HTTP contract but improve modularity.

- 2026-03-17: `adapters/api/routes_movements.py` replaced by the `adapters/api/routes_movements/` package
  - API entrypoint unchanged: movements still mounted via `adapters/api/__init__.py`
  - New structure: `routes_movements/__init__.py`, `routes_movements/send/`, `routes_movements/collect/`
  - Send and collect tests moved under `tests/integration/api/movements/send/` and `tests/integration/api/movements/collect/`
