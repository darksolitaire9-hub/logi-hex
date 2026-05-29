"""
domain/exceptions/accounts.py — Exceptions specific to Accounts mode.

Covers:
- InsufficientStillOutError: cannot Collect more than a client currently has Still Out.
- ClientNotFoundError: referenced client does not exist in this workspace.

Message language: docs/LANGUAGE.md — Error messages.
"""

from decimal import Decimal


class InsufficientStillOutError(Exception):
    """
    Raised when a Collect movement requests more than the client currently has Still Out.

    Example:
        "Alice only has 3 pcs of Steel Box. You cannot collect 5 pcs."
    """

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


class ClientNotFoundError(Exception):
    """Raised when a referenced client does not exist in this workspace."""

    def __init__(self, client_id: str):
        super().__init__(f"Client '{client_id}' does not exist in this workspace.")
