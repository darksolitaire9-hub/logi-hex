"""
domain/entities.py — Core domain entities for logi-hex.

All entities use the Ubiquitous Language defined in domain/language.py.
No legacy ContainerType, ContentType, or ContainerTransaction here.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from domain.language import (
    LOW_STOCK_THRESHOLD,
    CorrectionReason,
    MovementDirection,
    StockState,
    WorkspaceMode,
)

# ── Workspace ────────────────────────────────────────────────────────────────


@dataclass
class Workspace:
    """
    One isolated notebook of movements.
    Mode is set on creation and cannot be changed.
    """

    id: str
    name: str
    mode: WorkspaceMode
    owner_user_id: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        mode: WorkspaceMode,
        owner_user_id: str,
    ) -> "Workspace":
        return cls(
            id=uuid4().hex,
            name=name.strip(),
            mode=mode,
            owner_user_id=owner_user_id,
            created_at=datetime.now(timezone.utc),
        )


# ── Client ───────────────────────────────────────────────────────────────────


@dataclass
class Client:
    """
    Person or place you Send items to. Accounts mode only.
    ID is derived from workspace_id + normalised name — collision-safe.
    """

    id: str
    workspace_id: str
    name: str  # normalised: lowercase, stripped

    @classmethod
    def create(cls, workspace_id: str, name: str) -> "Client":
        normalised = name.lower().strip()
        client_id = hashlib.md5(f"{workspace_id}:{normalised}".encode()).hexdigest()[
            :16
        ]
        return cls(id=client_id, workspace_id=workspace_id, name=normalised)


# ── Item Group ───────────────────────────────────────────────────────────────


@dataclass
class ItemGroup:
    """
    A category that groups related Items.
    V1: purely organisational — no rules enforced per group.
    """

    id: str
    workspace_id: str
    name: str

    @classmethod
    def create(cls, workspace_id: str, name: str) -> "ItemGroup":
        return cls(
            id=uuid4().hex,
            workspace_id=workspace_id,
            name=name.strip(),
        )


# ── Item ─────────────────────────────────────────────────────────────────────


@dataclass
class Item:
    """
    Anything being tracked — Coke, Steel Box, Salmon, etc.
    Belongs to one workspace and one ItemGroup.
    """

    id: str
    workspace_id: str
    group_id: str
    label: str
    unit: str  # free text: pcs, kg, L, box, etc.
    is_active: bool = True

    @classmethod
    def create(
        cls,
        workspace_id: str,
        group_id: str,
        label: str,
        unit: str,
    ) -> "Item":
        return cls(
            id=uuid4().hex,
            workspace_id=workspace_id,
            group_id=group_id,
            label=label.strip(),
            unit=unit.strip(),
        )

    def archive(self) -> None:
        """Mark item as archived — blocks new movements."""
        self.is_active = False

    def reactivate(self) -> None:
        self.is_active = True


# ── Tag ──────────────────────────────────────────────────────────────────────


@dataclass
class Tag:
    """
    A filter label for items (and optionally movements).
    e.g. frozen, urgent, drinks, takeaway.
    """

    id: str
    workspace_id: str
    name: str  # normalised lowercase
    colour: str | None = None

    @classmethod
    def create(
        cls,
        workspace_id: str,
        name: str,
        colour: str | None = None,
    ) -> "Tag":
        return cls(
            id=uuid4().hex,
            workspace_id=workspace_id,
            name=name.strip().lower(),
            colour=colour,
        )


# ── Movement ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class MovementLineItem:
    """
    One item in a movement with its quantity.

    Quantity semantics:
    - SEND / RECEIVE / USE: always positive (service handles sign in math)
    - CORRECT: delta = target - stock_before_correction (can be negative)
    """

    item_id: str
    label: str
    quantity: Decimal


@dataclass(frozen=True)
class Movement:
    """
    A single logged action. Immutable — never updated or deleted.

    Accounts mode uses: SEND, COLLECT
    Inventory mode uses: RECEIVE, USE, CORRECT
    """

    id: str
    workspace_id: str
    direction: MovementDirection
    timestamp: datetime
    line_items: list[MovementLineItem]
    client_id: str | None = None  # Accounts mode
    client_name: str | None = None  # Accounts mode (denormalised for history)
    correction_reason: CorrectionReason | None = None  # CORRECT only
    tag_ids: list[str] = field(default_factory=list)
    notes: str | None = None

    @classmethod
    def create(
        cls,
        workspace_id: str,
        direction: MovementDirection,
        line_items: list[MovementLineItem],
        client_id: str | None = None,
        client_name: str | None = None,
        correction_reason: CorrectionReason | None = None,
        tag_ids: list[str] | None = None,
        notes: str | None = None,
    ) -> "Movement":
        return cls(
            id=uuid4().hex,
            workspace_id=workspace_id,
            direction=direction,
            timestamp=datetime.now(timezone.utc),
            line_items=line_items,
            client_id=client_id,
            client_name=client_name,
            correction_reason=correction_reason,
            tag_ids=tag_ids or [],
            notes=notes,
        )


# ── Query Result Objects ──────────────────────────────────────────────────────
# These are returned from query ports — not stored directly in DB.


@dataclass
class StillOutEntry:
    """How many of one item a client Still Out (Accounts mode)."""

    item_id: str
    item_label: str
    unit: str
    quantity: Decimal


@dataclass
class ClientStillOut:
    """Per-client Still Out summary (Accounts dashboard row)."""

    client_id: str
    client_name: str
    entries: list[StillOutEntry] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((e.quantity for e in self.entries), Decimal("0"))

    @property
    def is_settled(self) -> bool:
        return self.total == Decimal("0")


@dataclass
class AccountsSummary:
    """Full Accounts dashboard result."""

    clients: list[ClientStillOut] = field(default_factory=list)

    @property
    def grand_total(self) -> Decimal:
        return sum((c.total for c in self.clients), Decimal("0"))


@dataclass
class ItemStock:
    """Current stock for one item (Inventory dashboard row)."""

    item_id: str
    item_label: str
    unit: str
    group_id: str
    group_name: str
    in_stock: Decimal
    tag_ids: list[str] = field(default_factory=list)
    has_corrections: bool = False

    @property
    def stock_state(self) -> StockState:
        if self.in_stock <= Decimal("0"):
            return StockState.EMPTY
        if self.in_stock < Decimal(str(LOW_STOCK_THRESHOLD)):
            return StockState.LOW
        return StockState.IN_STOCK


@dataclass
class InventorySummary:
    """Full Inventory dashboard result."""

    items: list[ItemStock] = field(default_factory=list)
