"""
Shared in-memory fakes and fixtures for domain tests.
No DB, no FastAPI, no async SQLAlchemy — pure domain logic only.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from domain.entities import Client, Item, ItemGroup, Movement, Workspace
from domain.language import MovementDirection, WorkspaceMode
from domain.ports import (
    AccountsQueryPort,
    ClientRepositoryPort,
    ItemRepositoryPort,
    MovementRepositoryPort,
    StockQueryPort,
    UnitOfWorkPort,
)

# ── Constants ─────────────────────────────────────────────────────────────────

WS_ID = "workspace-001"
WS_MODE_ACCOUNTS = WorkspaceMode.ACCOUNTS
WS_MODE_INVENTORY = WorkspaceMode.INVENTORY

CLIENT_ID = "client-001"
CLIENT_NAME = "alice"

ITEM_ID = "item-001"
ITEM_LABEL = "Steel Box"
ITEM_UNIT = "pcs"


# ── Fakes ─────────────────────────────────────────────────────────────────────


class FakeUoW(UnitOfWorkPort):
    def __init__(self):
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


class FakeClientRepository(ClientRepositoryPort):
    def __init__(self, client: Client):
        self._client = client

    async def save(self, client: Client) -> None:
        self._client = client

    async def get_by_id(self, workspace_id: str, client_id: str) -> Client | None:
        if self._client.id == client_id:
            return self._client
        return None

    async def get_by_name(self, workspace_id: str, name: str) -> Client | None:
        if self._client.name == name.lower().strip():
            return self._client
        return None

    async def list_all(self, workspace_id: str) -> list[Client]:
        return [self._client]


class FakeItemRepository(ItemRepositoryPort):
    def __init__(self, items: list[Item]):
        self._items = {item.id: item for item in items}

    async def save(self, item: Item) -> None:
        self._items[item.id] = item

    async def get_by_id(self, workspace_id: str, item_id: str) -> Item | None:
        return self._items.get(item_id)

    async def list_all(self, workspace_id: str) -> list[Item]:
        return list(self._items.values())

    async def list_active(self, workspace_id: str) -> list[Item]:
        return [i for i in self._items.values() if i.is_active]


class FakeMovementRepository(MovementRepositoryPort):
    def __init__(self):
        self.saved: list[Movement] = []

    async def save(self, movement: Movement) -> None:
        self.saved.append(movement)

    async def list_by_workspace(self, workspace_id: str) -> list[Movement]:
        return self.saved

    async def list_by_client(self, workspace_id: str, client_id: str) -> list[Movement]:
        return [m for m in self.saved if m.client_id == client_id]

    async def list_by_item(self, workspace_id: str, item_id: str) -> list[Movement]:
        return [
            m for m in self.saved if any(li.item_id == item_id for li in m.line_items)
        ]


class FakeAccountsQuery(AccountsQueryPort):
    """Configurable still-out value per (client_id, item_id)."""

    def __init__(self, still_out: dict[tuple[str, str], Decimal] | None = None):
        self._still_out = still_out or {}

    async def get_still_out_for(
        self, workspace_id: str, client_id: str, item_id: str
    ) -> Decimal:
        return self._still_out.get((client_id, item_id), Decimal("0"))

    async def get_accounts_summary(self, workspace_id: str):
        raise NotImplementedError


class FakeStockQuery(StockQueryPort):
    """Configurable in-stock value per item_id."""

    def __init__(self, stock: dict[str, Decimal] | None = None):
        self._stock = stock or {}

    async def get_stock_for(self, workspace_id: str, item_id: str) -> Decimal:
        return self._stock.get(item_id, Decimal("0"))

    async def get_inventory_summary(self, workspace_id: str):
        raise NotImplementedError


# ── Fixture helpers ───────────────────────────────────────────────────────────


def make_client() -> Client:
    return Client(id=CLIENT_ID, workspace_id=WS_ID, name=CLIENT_NAME)


def make_item(is_active: bool = True) -> Item:
    return Item(
        id=ITEM_ID,
        workspace_id=WS_ID,
        group_id="group-001",
        label=ITEM_LABEL,
        unit=ITEM_UNIT,
        is_active=is_active,
    )
