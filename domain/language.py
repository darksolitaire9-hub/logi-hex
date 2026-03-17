"""
domain/language.py — Shim module re-exporting from domain.language package.

Kept so all existing imports continue to work after modularization:
    from domain.language import WorkspaceMode  ← still valid
    from domain.language import LOW_STOCK_THRESHOLD  ← still valid

Do not add new definitions here. Add them to the appropriate submodule
under domain/language/ and re-export from domain/language/__init__.py.
"""

from domain.language import (  # type: ignore[import-not-found]
    ACCOUNTS_DASHBOARD_LABELS,
    CORRECTION_REASON_LABELS,
    DIRECTION_LABELS,
    DIRECTION_PAST_TENSE,
    INVENTORY_DASHBOARD_LABELS,
    LEDGER_SIGN,
    LOW_STOCK_THRESHOLD,
    MODE_LABELS,
    REQUIRES_REASON,
    STOCK_STATE_LABELS,
    SUGGESTED_UNITS,
    USER_FACING_CORRECTION_REASONS,
    VALID_DIRECTIONS,
    CorrectionReason,
    MovementDirection,
    StockState,
    WorkspaceMode,
)

__all__ = [
    "WorkspaceMode",
    "MovementDirection",
    "CorrectionReason",
    "StockState",
    "MODE_LABELS",
    "DIRECTION_LABELS",
    "DIRECTION_PAST_TENSE",
    "CORRECTION_REASON_LABELS",
    "STOCK_STATE_LABELS",
    "LEDGER_SIGN",
    "VALID_DIRECTIONS",
    "REQUIRES_REASON",
    "USER_FACING_CORRECTION_REASONS",
    "ACCOUNTS_DASHBOARD_LABELS",
    "INVENTORY_DASHBOARD_LABELS",
    "SUGGESTED_UNITS",
    "LOW_STOCK_THRESHOLD",
]
