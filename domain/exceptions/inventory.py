"""
domain/exceptions/inventory.py — Exceptions specific to Inventory mode.

Covers:
- InsufficientStockError: cannot Use more than is currently In Stock.
- CorrectionReasonRequiredError: Correct movement submitted without a reason.

Message language: docs/LANGUAGE.md — Error messages.
"""

from decimal import Decimal


class InsufficientStockError(Exception):
    """
    Raised when a Use movement requests more than the item's current In Stock quantity.

    Two message shapes depending on current stock:

    - Empty:
        "Coke is empty. Receive stock before using it."
    - Non-zero:
        "Coke is at 2 pcs. You cannot use 5 pcs."
    """

    def __init__(
        self,
        item_label: str,
        unit: str,
        in_stock: Decimal,
        requested: Decimal,
    ):
        self.item_label = item_label
        self.unit = unit
        self.in_stock = in_stock
        self.requested = requested

        if in_stock <= Decimal("0"):
            super().__init__(f"{item_label} is empty. Receive stock before using it.")
        else:
            super().__init__(
                f"{item_label} is at {in_stock} {unit}. "
                f"You cannot use {requested} {unit}."
            )


class CorrectionReasonRequiredError(Exception):
    """Raised when a Correct movement is submitted without a reason."""

    def __init__(self):
        super().__init__("Please select a reason for this correction.")
