"""
domain/ports/inventory.py — Ports specific to Inventory mode.

Covers:
- ItemGroupRepositoryPort: persistence for item groups.
- ItemRepositoryPort: persistence for items.
- TagRepositoryPort: persistence and associations for tags.
- StockQueryPort: read-side queries for Inventory dashboards.

All ports are workspace-scoped:
workspace_id is always an explicit parameter.

Human reference: docs/V1-SCOPE.md — Items, Item Groups, Tags, Movements — Inventory mode, Dashboards.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from domain.entities import InventorySummary, Item, ItemGroup, Tag


class ItemGroupRepositoryPort(ABC):
    @abstractmethod
    async def save(self, group: ItemGroup) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, workspace_id: str, group_id: str) -> ItemGroup | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, workspace_id: str) -> list[ItemGroup]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, workspace_id: str, group_id: str) -> None:
        raise NotImplementedError


class ItemRepositoryPort(ABC):
    @abstractmethod
    async def save(self, item: Item) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, workspace_id: str, item_id: str) -> Item | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, workspace_id: str) -> list[Item]:
        """Return all items including archived."""
        raise NotImplementedError

    @abstractmethod
    async def list_active(self, workspace_id: str) -> list[Item]:
        """Return only active (non-archived) items."""
        raise NotImplementedError


class TagRepositoryPort(ABC):
    @abstractmethod
    async def save(self, tag: Tag) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, workspace_id: str, tag_id: str) -> Tag | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, workspace_id: str) -> list[Tag]:
        raise NotImplementedError

    @abstractmethod
    async def assign_to_item(self, item_id: str, tag_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_from_item(self, item_id: str, tag_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_ids_for_item(self, item_id: str) -> list[str]:
        raise NotImplementedError


class StockQueryPort(ABC):
    """Read-side queries for Inventory mode dashboards."""

    @abstractmethod
    async def get_stock_for(self, workspace_id: str, item_id: str) -> Decimal:
        """
        Return current In Stock for one item.
        Formula: SUM(RECEIVE) - SUM(USE) + SUM(CORRECT deltas)
        Returns 0 if no movements exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_inventory_summary(self, workspace_id: str) -> InventorySummary:
        """
        Return all items with current In Stock, stock state badge,
        group, tags, and correction flag.
        """
        raise NotImplementedError
