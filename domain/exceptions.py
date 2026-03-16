"""
domain/exceptions.py — Domain-level exceptions for logi-hex.

All exception messages use the agreed Ubiquitous Language from docs/LANGUAGE.md.
No internal terms (balance, direction, constraint) in user-facing messages.
"""

from decimal import Decimal


class InsufficientStillOutError(Exception):
    def __init__(
        self,
        client_name: str,
        item_label: str,
        unit: str,
        still_out: Decimal,
        requested: Decimal,
    ):
        self.client_name = client_name
        self.item_label = item_label
        self.unit = unit
        self.still_out = still_out
        self.requested = requested
        super().__init__(
            f"{client_name} only has {still_out} {unit} of {item_label}. "
            f"You cannot collect {requested} {unit}."
        )


class InsufficientStockError(Exception):
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


class ArchivedItemError(Exception):
    """
    Raised when a movement is attempted against an archived item.
    """

    def __init__(self, item_label: str):
        self.item_label = item_label
        super().__init__(f"{item_label} is archived. Reactivate it to log movements.")


class WorkspaceModeMismatchError(Exception):
    """
    Raised when a movement direction is invalid for the workspace mode.
    Internal guard — should not reach the user if routes are correct.
    """

    def __init__(self, direction: str, mode: str):
        super().__init__(f"Direction '{direction}' is not valid in {mode} mode.")


class ItemNotFoundError(Exception):
    """Raised when a referenced item does not exist in this workspace."""

    def __init__(self, item_id: str):
        super().__init__(f"Item '{item_id}' does not exist in this workspace.")


class ClientNotFoundError(Exception):
    """Raised when a referenced client does not exist in this workspace."""

    def __init__(self, client_id: str):
        super().__init__(f"Client '{client_id}' does not exist in this workspace.")


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace does not exist or does not belong to this user."""

    def __init__(self, workspace_id: str):
        super().__init__(f"Workspace '{workspace_id}' not found.")


class CorrectionReasonRequiredError(Exception):
    """Raised when a Correct movement is submitted without a reason."""

    def __init__(self):
        super().__init__("Please select a reason for this correction.")


class EmptyMovementError(Exception):
    """Raised when a movement is submitted with no valid line items."""

    def __init__(self):
        super().__init__("Please enter a quantity greater than zero.")
