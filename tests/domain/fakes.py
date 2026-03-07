# tests/domain/fakes.py

import asyncio
from typing import Dict, Tuple

from domain.entities import (
    Balance,
    Client,
    ContainerTransaction,
    ContainerType,
    TrackingCategory,
    TrackingItem,
    Transaction,
)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class FakeClientRepo:
    def __init__(self):
        self._by_name: dict[str, Client] = {}

    async def get_or_create_by_name(self, name: str) -> Client:
        normalized = name.lower().strip()
        if normalized in self._by_name:
            return self._by_name[normalized]
        client = Client.from_name(name)
        self._by_name[normalized] = client
        return client

    async def list_all(self):
        return list(self._by_name.values())


class FakeContainerTypeRepo:
    def __init__(self, types: dict[str, ContainerType] | None = None):
        self._types = types or {}

    async def get_by_id(self, type_id: str):
        return self._types.get(type_id)

    async def save(self, container_type: ContainerType):
        self._types[container_type.id] = container_type


class FakeTrackingCategoryRepo:
    def __init__(self, categories: dict[str, TrackingCategory] | None = None):
        self._categories = categories or {}

    async def get_by_id(self, category_id: str):
        return self._categories.get(category_id)

    async def save(self, category: TrackingCategory):
        self._categories[category.id] = category


class FakeTrackingItemRepo:
    def __init__(self, items: dict[str, TrackingItem] | None = None):
        self._items = items or {}

    async def get_by_id(self, item_id: str):
        return self._items.get(item_id)

    async def save(self, item: TrackingItem):
        self._items[item.id] = item


class FakeTxRepo:
    def __init__(self):
        self.saved: list[ContainerTransaction] = []

    async def save(self, tx: ContainerTransaction) -> None:
        self.saved.append(tx)

    async def list_all(self):
        return list(self.saved)


class FakeGenericTxRepo:
    def __init__(self):
        self.saved: list[Transaction] = []

    async def save(self, tx: Transaction) -> None:
        self.saved.append(tx)

    async def list_all(self):
        return list(self.saved)


class FakeBalanceQuery:
    def __init__(self, balances: Dict[Tuple[str, str], int] | None = None):
        # key: (client_id, tracking_item_id or container_type_id)
        self._balances = balances or {}

    async def get_balance_for(self, client_id: str, tracking_item_id: str) -> int:
        return self._balances.get((client_id, tracking_item_id), 0)

    async def get_balances(self) -> list[Balance]:
        return []
