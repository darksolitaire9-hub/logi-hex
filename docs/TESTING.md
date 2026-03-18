# Testing Guide

This document explains how the test suite is organised and which commands to
run for different kinds of changes.

## High-level layout

- **Domain tests**: `tests/domain/`
  - Pure domain logic, no FastAPI, no DB.
  - Use in-memory fakes from `tests/domain/conftest.py`.
- **Integration tests (API)**: `tests/integration/api/`
  - FastAPI + adapters + infrastructure + DB (usually against a test DB).
  - Exercise HTTP contracts end-to-end.

## Domain tests

Domain tests are organised to mirror the domain and HTTP movement structure so
you can jump between code and tests with minimal friction.

### Movements (Send / Collect / Receive / Use / Correct)

- Accounts movements:
  - Send:
    - `tests/domain/movements/accounts/send/test_accounts_send_happy.py`
    - `tests/domain/movements/accounts/send/test_accounts_send_guards.py`
  - Collect:
    - `tests/domain/movements/accounts/collect/test_accounts_collect_happy.py`
    - `tests/domain/movements/accounts/collect/test_accounts_collect_guards.py`

- Inventory movements:
  - Receive:
    - `tests/domain/movements/inventory/receive/test_inventory_receive_happy.py`
    - `tests/domain/movements/inventory/receive/test_inventory_receive_guards.py`
  - Use:
    - `tests/domain/movements/inventory/use/test_inventory_use_happy.py`
    - `tests/domain/movements/inventory/use/test_inventory_use_guards.py`
  - Correct:
    - `tests/domain/movements/inventory/correct/test_inventory_correct_happy.py`
    - `tests/domain/movements/inventory/correct/test_inventory_correct_guards.py`

Each folder splits tests by concern:

- `*_happy.py` — core “it works” scenarios.
- `*_guards.py` — domain invariants and error cases.

### Exceptions and language

- Exceptions:
  - `tests/domain/exceptions/test_accounts_exceptions.py`
  - `tests/domain/exceptions/test_inventory_exceptions.py`
- Inventory stock state:
  - `tests/domain/inventory/test_stock_state.py`

These tests lock in user-facing error messages and stock state rules defined in
`docs/LANGUAGE.md` and `domain/language/inventory.py`.

### Commands

- Run all domain tests:

  ```bash
  pytest tests/domain
  ```

- Run only Accounts domain tests:

  ```bash
  pytest tests/domain/movements/accounts
  ```

- Run only Inventory domain tests:

  ```bash
  pytest tests/domain/movements/inventory
  ```

- Run a single file (example):

  ```bash
  pytest tests/domain/movements/accounts/collect/test_accounts_collect_guards.py
  ```

## Integration tests (API)

Integration tests live under `tests/integration/api/` and mirror the API route
structure.

- Accounts movements:
  - `tests/integration/api/movements/accounts/send/`
  - `tests/integration/api/movements/accounts/collect/`
- Inventory movements:
  - `tests/integration/api/movements/inventory/receive/`
  - `tests/integration/api/movements/inventory/use/`
  - `tests/integration/api/movements/inventory/correct/`

Each folder typically contains:

- `test_*_happy.py` — successful HTTP flows.
- `test_*_auth.py` — auth and workspace existence.
- `test_*_guards.py` — business rule errors at HTTP level.
- `test_*_validation.py` — request body validation.

### Commands

- Run all integration tests:

  ```bash
  pytest tests/integration
  ```

- Run only movements integration tests:

  ```bash
  pytest tests/integration/api/movements
  ```

- Run Accounts Collect integration tests:

  ```bash
  pytest tests/integration/api/movements/accounts/collect
  ```

## Local workflows

- **Changing domain rules** (e.g. guards, exceptions):
  - First run:

    ```bash
    pytest tests/domain
    ```

- **Changing adapters or API schemas**:
  - Run:

    ```bash
    pytest tests/integration
    ```

- **Before pushing** (quick sanity):

  ```bash
  pytest tests/domain tests/integration
  ```

This keeps the domain layer honest and ensures the HTTP surface stays aligned
with the underlying rules.
