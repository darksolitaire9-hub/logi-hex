# domain/entities/accounts.py

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from domain.language import CorrectionReason, MovementDirection


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
