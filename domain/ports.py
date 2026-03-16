"""
domain/ports.py — Abstract ports (interfaces) for logi-hex.

Every port is an ABC. Infrastructure provides the concrete implementations.
All ports are workspace-scoped — workspace_id is always an explicit parameter.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from domain.entities import (
    AccountsSummary,
    Client,
    InventorySummary,
    Item,
    ItemGroup,
    ItemStock,
    Movement,
    StillOutEntry,
    Tag,
    Workspace,
)

# ── Workspace ────────────────────────────────────────────────────────────────


class WorkspaceRepositoryPort(ABC):
    @abstractmethod
    async def save(self, workspace: Workspace) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_owner(self, owner_user_id: str) -> list[Workspace]:
        raise NotImplementedError


# ── Client ───────────────────────────────────────────────────────────────────


class ClientRepositoryPort(ABC):
    @abstractmethod
    async def save(self, client: Client) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, workspace_id: str, client_id: str) -> Client | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, workspace_id: str, name: str) -> Client | None:
        """Return client by normalised name within a workspace."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, workspace_id: str) -> list[Client]:
        raise NotImplementedError


# ── Item Group ───────────────────────────────────────────────────────────────


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


# ── Item ─────────────────────────────────────────────────────────────────────


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


# ── Tag ──────────────────────────────────────────────────────────────────────


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


# ── Movement ─────────────────────────────────────────────────────────────────


class MovementRepositoryPort(ABC):
    @abstractmethod
    async def save(self, movement: Movement) -> None:
        """Persist a movement with all its line items and tag associations."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[Movement]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_client(self, workspace_id: str, client_id: str) -> list[Movement]:
        """Return all movements for a client, newest first."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_item(self, workspace_id: str, item_id: str) -> list[Movement]:
        """Return all movements containing this item, newest first."""
        raise NotImplementedError


# ── Query Ports ──────────────────────────────────────────────────────────────


class AccountsQueryPort(ABC):
    """Read-side queries for Accounts mode dashboards."""

    @abstractmethod
    async def get_still_out_for(
        self,
        workspace_id: str,
        client_id: str,
        item_id: str,
    ) -> Decimal:
        """
        Return SUM(SEND qty) - SUM(COLLECT qty) for one client+item.
        Returns 0 if no movements exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_accounts_summary(self, workspace_id: str) -> AccountsSummary:
        """
        Return all clients with non-zero Still Out,
        their per-item breakdown, and grand total Outstanding.
        """
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


# ── Unit of Work ─────────────────────────────────────────────────────────────


class UnitOfWorkPort(ABC):
    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
