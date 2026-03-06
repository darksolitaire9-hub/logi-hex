from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4


@dataclass
class ContainerType:
    id: str  # e.g. "white", "round", "glass"
    label: str  # e.g. "White Box", "Round Box", "Big Glass"


@dataclass
class ContentType:
    id: str  # e.g. "frozen", "fresh"
    label: str  # e.g. "Frozen", "Fresh"


@dataclass
class Client:
    id: str  # auto-generated from name e.g. "cshin"
    name: str  # normalized lowercase e.g. "shivam"

    @classmethod
    def from_name(cls, name: str) -> "Client":
        norm = name.lower().strip().replace(" ", "").replace("-", "")
        client_id = f"c{norm[:4].zfill(3)}"
        return cls(id=client_id, name=name.lower().strip())


@dataclass
class TrackingCategory:
    """
    User-defined category of things to track.

    Examples:
    - id="boxes", name="Boxes", is_balanced=True
    - id="food", name="Food", is_balanced=False (informational only)
    """

    id: str
    name: str
    is_balanced: bool


@dataclass
class TrackingItem:
    """
    Item within a tracking category.

    Examples:
    - id="red-box", category_id="boxes", label="Red Box"
    - id="salad", category_id="food", label="Salad"
    """

    id: str
    category_id: str
    label: str


@dataclass(frozen=True)
class TransactionLineItem:
    """
    One primary tracked item within a transaction, with quantity.

    This is where balances are enforced for balanced categories.
    """

    tracking_item_id: str
    label: str
    quantity: int


@dataclass(frozen=True)
class ContainerTransaction:
    id: str
    timestamp: datetime
    client_id: str
    client_name: str
    container_type_id: str
    direction: Literal["OUT", "IN"]  # OUT = issued, IN = returned
    quantity: int
    content_type_ids: list[str]  # list of ContentType IDs attached to this movement
    note: str | None = None  # optional free-text note

    @classmethod
    def issue(
        cls,
        client: Client,
        container_type_id: str,
        quantity: int,
        content_type_ids: list[str] | None = None,
        note: str | None = None,
    ) -> "ContainerTransaction":
        return cls(
            id=uuid4().hex,
            timestamp=datetime.now(),
            client_id=client.id,
            client_name=client.name,
            container_type_id=container_type_id,
            direction="OUT",
            quantity=quantity,
            content_type_ids=content_type_ids or [],
            note=note,
        )

    @classmethod
    def receive(
        cls,
        client: Client,
        container_type_id: str,
        quantity: int,
        content_type_ids: list[str] | None = None,
        note: str | None = None,
    ) -> "ContainerTransaction":
        return cls(
            id=uuid4().hex,
            timestamp=datetime.now(),
            client_id=client.id,
            client_name=client.name,
            container_type_id=container_type_id,
            direction="IN",
            quantity=quantity,
            content_type_ids=content_type_ids or [],
            note=note,
        )


@dataclass(frozen=True)
class Transaction:
    """
    Generic transaction that can contain multiple primary line items
    and optional secondary (informational) items.

    Direction semantics remain:
    - OUT = issued / going out
    - IN  = returned / coming in
    """

    id: str
    timestamp: datetime
    client_id: str
    client_name: str
    direction: Literal["OUT", "IN"]
    line_items: list[TransactionLineItem]
    secondary_items: list[str]  # tracking_item_ids of secondary category
    notes: str | None = None

    @classmethod
    def create(
        cls,
        client: "Client",
        direction: Literal["OUT", "IN"],
        line_items: list[TransactionLineItem],
        secondary_items: list[str] | None = None,
        notes: str | None = None,
    ) -> "Transaction":
        return cls(
            id=uuid4().hex,
            timestamp=datetime.now(),
            client_id=client.id,
            client_name=client.name,
            direction=direction,
            line_items=line_items,
            secondary_items=secondary_items or [],
            notes=notes,
        )


@dataclass
class Balance:
    client_id: str
    client_name: str
    container_type_id: str
    container_label: str
    balance: int  # SUM(OUT) - SUM(IN) — positive means client owes you


@dataclass
class ClientBalanceSummary:
    """Per-client summary: all non-zero box balances and their total."""

    client_id: str
    client_name: str
    total_outstanding: int
    balances: list[Balance] = field(default_factory=list)


@dataclass
class SummaryResult:
    """Top-level summary: all clients with outstanding boxes + grand total."""

    clients: list[ClientBalanceSummary] = field(default_factory=list)
    grand_total: int = 0
