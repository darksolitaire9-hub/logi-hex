"""
domain/language/accounts.py — Language specific to Accounts mode.

Covers:
- Dashboard state labels shown to users in Accounts mode:
    Still Out, Outstanding, Settled.

What does NOT live here:
- WorkspaceMode, MovementDirection → domain/language/shared.py
- Inventory states → domain/language/inventory.py

Human reference: docs/LANGUAGE.md — States (Accounts mode)
"""

from .shared import WorkspaceMode  # noqa: F401 — re-exported for convenience

# ── Accounts Dashboard Labels ─────────────────────────────────────────────────
# These are the exact words shown in the Accounts dashboard UI.
# Do NOT hardcode these strings in components or API responses.

ACCOUNTS_DASHBOARD_LABELS: dict[str, str] = {
    "still_out": "Still Out",  # Items a client currently has of yours
    "outstanding": "Outstanding",  # Total items still out across all clients
    "settled": "Settled",  # Client has nothing Still Out
}
