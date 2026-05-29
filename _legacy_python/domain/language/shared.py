"""
domain/language/shared.py — Shared language for both Accounts and Inventory modes.

Covers:
- WorkspaceMode and MovementDirection enums (the core domain vocabulary).
- CorrectionReason enum (used in Inventory but defined here as a core type).
- Human-readable labels for modes, directions, past tense, and correction reasons.
- Behavioural rules used by both modes:
    LEDGER_SIGN, VALID_DIRECTIONS, REQUIRES_REASON, USER_FACING_CORRECTION_REASONS.

What does NOT live here:
- Stock states → domain/language/inventory.py
- Dashboard labels per mode → domain/language/accounts.py and inventory.py
- UX suggestions → domain/language/suggestions.py

Human reference: docs/LANGUAGE.md
"""

from enum import StrEnum


class WorkspaceMode(StrEnum):
    """The two modes a workspace can operate in.
    Set once at workspace creation — cannot be changed.
    """

    ACCOUNTS = "ACCOUNTS"
    INVENTORY = "INVENTORY"


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


class CorrectionReason(StrEnum):
    """Why a stock correction was made.
    Required on every CORRECT movement.
    _OPENING_BALANCE is internal only — never shown in the UI.
    """

    SHRINKAGE = "SHRINKAGE"
    COUNT_CORRECTION = "COUNT_CORRECTION"
    _OPENING_BALANCE = "_OPENING_BALANCE"  # system-generated only


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

# ── Internal Ledger Mapping ──────────────────────────────────────────────────
# Maps user-facing directions to internal sign convention for math.
# IN / OUT / ADJUST never surface in the UI — only used inside query calculations.

LEDGER_SIGN: dict[str, int] = {
    MovementDirection.SEND: -1,
    MovementDirection.COLLECT: +1,
    MovementDirection.RECEIVE: +1,
    MovementDirection.USE: -1,
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

REQUIRES_REASON: list[str] = [
    MovementDirection.CORRECT,
]

USER_FACING_CORRECTION_REASONS: list[str] = [
    CorrectionReason.SHRINKAGE,
    CorrectionReason.COUNT_CORRECTION,
]
