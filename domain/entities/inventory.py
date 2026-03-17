# domain/entities/inventory.py

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

from domain.language import LOW_STOCK_THRESHOLD, StockState


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
