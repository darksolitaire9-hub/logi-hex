"""
domain/language/inventory.py — Language specific to Inventory mode.

Covers:
- StockState enum: the visual state of an item's stock level.
- Human-readable labels for stock states.
- LOW_STOCK_THRESHOLD: the boundary below which an item is considered Low.
- Dashboard state labels shown to users in Inventory mode:
    In Stock, Low, Empty, Shrinkage.

What does NOT live here:
- WorkspaceMode, MovementDirection, CorrectionReason → domain/language/shared.py
- Accounts states → domain/language/accounts.py

Human reference: docs/LANGUAGE.md — States (Inventory mode)
"""

from enum import StrEnum


class StockState(StrEnum):
    """Visual state of an item's stock level. Used for dashboard badges."""

    IN_STOCK = "IN_STOCK"
    LOW = "LOW"
    EMPTY = "EMPTY"


# ── Stock State Labels ────────────────────────────────────────────────────────

STOCK_STATE_LABELS: dict[str, str] = {
    StockState.IN_STOCK: "In Stock",
    StockState.LOW: "Low",
    StockState.EMPTY: "Empty",
}

# ── Low Stock Threshold ───────────────────────────────────────────────────────
# Items with in_stock < LOW_STOCK_THRESHOLD are shown with a Low badge.

LOW_STOCK_THRESHOLD = 3

# ── Inventory Dashboard Labels ────────────────────────────────────────────────
# These are the exact words shown in the Inventory dashboard UI.
# Do NOT hardcode these strings in components or API responses.

INVENTORY_DASHBOARD_LABELS: dict[str, str] = {
    "in_stock": "In Stock",  # Current quantity on hand
    "low": "Low",  # Stock is near zero and needs attention (amber badge)
    "empty": "Empty",  # Stock is exactly zero (red badge)
    "shrinkage": "Shrinkage",  # Unexplained loss revealed by a correction
}
