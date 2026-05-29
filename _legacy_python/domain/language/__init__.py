"""
domain/language/__init__.py — Ubiquitous language public API for logi-hex.

This is the ONLY import path consumers should use:
    from domain.language import WorkspaceMode
    from domain.language import ACCOUNTS_DASHBOARD_LABELS

Submodules (shared, accounts, inventory, suggestions) are implementation
detail. Do not import from them directly outside of domain/language/.

Human reference: docs/LANGUAGE.md
"""

from .accounts import (
    ACCOUNTS_DASHBOARD_LABELS,
)
from .inventory import (
    INVENTORY_DASHBOARD_LABELS,
    LOW_STOCK_THRESHOLD,
    STOCK_STATE_LABELS,
    StockState,
)
from .shared import (
    CORRECTION_REASON_LABELS,
    DIRECTION_LABELS,
    DIRECTION_PAST_TENSE,
    LEDGER_SIGN,
    MODE_LABELS,
    REQUIRES_REASON,
    USER_FACING_CORRECTION_REASONS,
    VALID_DIRECTIONS,
    CorrectionReason,
    MovementDirection,
    WorkspaceMode,
)
from .suggestions import (
    SUGGESTED_UNITS,
)

__all__ = [
    # Shared enums
    "WorkspaceMode",
    "MovementDirection",
    "CorrectionReason",
    # Inventory enum
    "StockState",
    # Shared labels
    "MODE_LABELS",
    "DIRECTION_LABELS",
    "DIRECTION_PAST_TENSE",
    "CORRECTION_REASON_LABELS",
    # Inventory labels
    "STOCK_STATE_LABELS",
    "LOW_STOCK_THRESHOLD",
    # Dashboard labels
    "ACCOUNTS_DASHBOARD_LABELS",
    "INVENTORY_DASHBOARD_LABELS",
    # Rules
    "LEDGER_SIGN",
    "VALID_DIRECTIONS",
    "REQUIRES_REASON",
    "USER_FACING_CORRECTION_REASONS",
    # UX
    "SUGGESTED_UNITS",
]
