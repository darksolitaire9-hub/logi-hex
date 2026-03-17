"""
domain/exceptions/__init__.py — Domain exceptions public API for logi-hex.

This is the ONLY import path consumers should use:

    from domain.exceptions import InsufficientStillOutError
    from domain.exceptions import InsufficientStockError

Submodules (shared, accounts, inventory) are implementation detail.
Do not import from them directly outside of domain/exceptions/.

Message language: docs/LANGUAGE.md — Error messages.
"""

from .accounts import (
    ClientNotFoundError,
    InsufficientStillOutError,
)
from .inventory import (
    CorrectionReasonRequiredError,
    InsufficientStockError,
)
from .shared import (
    ArchivedItemError,
    EmptyMovementError,
    ItemGroupNotFoundError,
    ItemNotFoundError,
    TagNotFoundError,
    WorkspaceModeMismatchError,
    WorkspaceNotFoundError,
)

__all__ = [
    # Shared
    "WorkspaceNotFoundError",
    "WorkspaceModeMismatchError",
    "ArchivedItemError",
    "EmptyMovementError",
    "ItemNotFoundError",
    "ItemGroupNotFoundError",
    "TagNotFoundError",
    # Accounts
    "InsufficientStillOutError",
    "ClientNotFoundError",
    # Inventory
    "InsufficientStockError",
    "CorrectionReasonRequiredError",
]
