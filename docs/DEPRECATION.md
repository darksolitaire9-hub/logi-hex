# Deprecation Log

## Pre-DDD routes (superseded by V1 DDD layer)

These routes existed before the hexagonal architecture refactor.
Old tests in `test_movements.py` and `test_clients.py` covered them.
Both test files were deleted on 2026-03-17 — behaviours to re-test in V1:

| Behaviour | Old route | V1 route (pending) | Test file to create |
|---|---|---|---|
| Create item group | POST /api/tracking-categories | POST /workspaces/{id}/item-groups | test_item_groups.py |
| Create item | POST /api/tracking-items | POST /workspaces/{id}/items | test_items.py |
| Collect movement | POST /api/movements/receive | POST /workspaces/{id}/movements/collect | test_movements_collect.py |
| Collect blocked (no prior send) | same | same | test_movements_collect_guards.py |
| Unknown tag → 404 | POST /api/movements/issue | POST /movements/send or collect | test_movements_send_guards.py |
| Accounts summary | GET /api/summary | GET /workspaces/{id}/accounts | test_accounts_summary.py |
| List clients | GET /api/clients | GET /workspaces/{id}/clients | test_clients.py |

## Routes pending removal

Once V1 routes are fully tested, remove:
- adapters/api/routes_containers.py
- adapters/api/routes_tracking.py
- adapters/api/routes_summary.py
- adapters/api/routes_clients.py
- adapters/api/dev_routes.py (review first)
