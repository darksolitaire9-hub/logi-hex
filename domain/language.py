"""
domain/language.py — Logi-Hex Ubiquitous Language (Python)

WHAT THIS FILE IS:
    Single source of truth for all domain language in the backend.
    Every enum, label, and constant used across domain, application,
    infrastructure, and API layers is imported from here.

THE RULE:
    Never hardcode mode names, directions, reasons, or label strings
    anywhere in the codebase. Always import from this file.

HUMAN REFERENCE:
    See docs/LANGUAGE.md for the full plain-English explanation.
"""

from enum import StrEnum

# ── Workspace ────────────────────────────────────────────────────────────────


class WorkspaceMode(StrEnum):
    """The two modes a workspace can operate in.
    Set once at workspace creation — cannot be changed.
    """

    ACCOUNTS = "ACCOUNTS"
    INVENTORY = "INVENTORY"


# ── Movement Directions ──────────────────────────────────────────────────────


class MovementDirection(StrEnum):
    """The five user-facing actions. Only valid directions in the system.

    SEND    → Accounts OUT  (you gave items to a client)
    COLLECT → Accounts IN   (client returned items to you)
    RECEIVE → Inventory IN  (stock arrived / was delivered)
    USE     → Inventory OUT (stock was sold or consumed)
    CORRECT → Inventory ADJUST (physical count differs from system)
    """

    SEND = "SEND"
    COLLECT = "COLLECT"
    RECEIVE = "RECEIVE"
    USE = "USE"
    CORRECT = "CORRECT"


# ── Correction Reasons ───────────────────────────────────────────────────────


class CorrectionReason(StrEnum):
    """Why a stock correction was made.
    Required on every CORRECT movement.
    _OPENING_BALANCE is internal only — never shown in the UI.
    """

    SHRINKAGE = "SHRINKAGE"
    COUNT_CORRECTION = "COUNT_CORRECTION"
    _OPENING_BALANCE = "_OPENING_BALANCE"  # system-generated only


# ── Stock States ─────────────────────────────────────────────────────────────


class StockState(StrEnum):
    """Visual state of an item's stock level. Used for dashboard badges."""

    IN_STOCK = "IN_STOCK"
    LOW = "LOW"
    EMPTY = "EMPTY"


# ── Human-Readable Labels ────────────────────────────────────────────────────

MODE_LABELS: dict[str, str] = {
    WorkspaceMode.ACCOUNTS: "Accounts",
    WorkspaceMode.INVENTORY: "Inventory",
}

DIRECTION_LABELS: dict[str, str] = {
    MovementDirection.SEND: "Send",
    MovementDirection.COLLECT: "Collect",
    MovementDirection.RECEIVE: "Receive",
    MovementDirection.USE: "Use",
    MovementDirection.CORRECT: "Correct",
}

DIRECTION_PAST_TENSE: dict[str, str] = {
    MovementDirection.SEND: "Sent",
    MovementDirection.COLLECT: "Collected",
    MovementDirection.RECEIVE: "Received",
    MovementDirection.USE: "Used",
    MovementDirection.CORRECT: "Corrected",
}

CORRECTION_REASON_LABELS: dict[str, str] = {
    CorrectionReason.SHRINKAGE: "Shrinkage",
    CorrectionReason.COUNT_CORRECTION: "Count Correction",
    # _OPENING_BALANCE intentionally omitted — internal only
}

STOCK_STATE_LABELS: dict[str, str] = {
    StockState.IN_STOCK: "In Stock",
    StockState.LOW: "Low",
    StockState.EMPTY: "Empty",
}

# ── Internal Ledger Mapping ──────────────────────────────────────────────────
# Maps user-facing directions to internal sign convention for math.
# IN/OUT/ADJUST never surfaces in UI — only used inside query calculations.

LEDGER_SIGN: dict[str, int] = {
    MovementDirection.SEND: -1,  # OUT: decreases nothing (balance tracked separately)
    MovementDirection.COLLECT: +1,  # IN
    MovementDirection.RECEIVE: +1,  # IN
    MovementDirection.USE: -1,  # OUT
    MovementDirection.CORRECT: 0,  # ADJUST: delta stored directly in line item quantity
}

# ── Mode Constraints ─────────────────────────────────────────────────────────

VALID_DIRECTIONS: dict[str, list[str]] = {
    WorkspaceMode.ACCOUNTS: [
        MovementDirection.SEND,
        MovementDirection.COLLECT,
    ],
    WorkspaceMode.INVENTORY: [
        MovementDirection.RECEIVE,
        MovementDirection.USE,
        MovementDirection.CORRECT,
    ],
}

# Directions that require a correction reason field
REQUIRES_REASON: list[str] = [
    MovementDirection.CORRECT,
]

# Correction reasons that can be selected by a user in the UI
USER_FACING_CORRECTION_REASONS: list[str] = [
    CorrectionReason.SHRINKAGE,
    CorrectionReason.COUNT_CORRECTION,
]

# ── Suggested Units ──────────────────────────────────────────────────────────

SUGGESTED_UNITS: list[dict[str, str]] = [
    {"value": "pcs", "label": "Pieces (pcs)"},
    {"value": "kg", "label": "Kilograms (kg)"},
    {"value": "g", "label": "Grams (g)"},
    {"value": "L", "label": "Litres (L)"},
    {"value": "ml", "label": "Millilitres (ml)"},
    {"value": "box", "label": "Box"},
    {"value": "bag", "label": "Bag"},
    {"value": "portion", "label": "Portion"},
]

# ── Low Stock Threshold ──────────────────────────────────────────────────────

LOW_STOCK_THRESHOLD = 3  # items with in_stock < this are marked LOW
