# tests/domain/fakes.py

import asyncio
from typing import Dict, List, Tuple

from domain.entities import (
    Balance,
    Client,
    ContainerTransaction,
    ContainerType,
    TrackingCategory,
    TrackingItem,
    Transaction,
)
from domain.ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    GenericTransactionRepositoryPort,
    TrackingCategoryRepositoryPort,
    TrackingItemRepositoryPort,
    TransactionRepositoryPort,
)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class FakeClientRepo(ClientRepositoryPort):
    def __init__(self):
        self._by_name: dict[str, Client] = {}

    async def get_or_create_by_name(self, name: str) -> Client:
        normalized = name.lower().strip()
        if normalized in self._by_name:
            return self._by_name[normalized]
        client = Client.from_name(name)
        self._by_name[normalized] = client
        return client

    async def list_all(self) -> List[Client]:
        return list(self._by_name.values())


class FakeContainerTypeRepo(ContainerTypeRepositoryPort):
    def __init__(self, types: dict[str, ContainerType] | None = None):
        self._types = types or {}

    async def list_all(self) -> List[ContainerType]:
        return list(self._types.values())

    async def get_by_id(self, type_id: str) -> ContainerType | None:
        return self._types.get(type_id)

    async def save(self, container_type: ContainerType) -> None:
        self._types[container_type.id] = container_type

    async def delete(self, type_id: str) -> None:
        self._types.pop(type_id, None)


class FakeTrackingCategoryRepo(TrackingCategoryRepositoryPort):
    def __init__(self, categories: dict[str, TrackingCategory] | None = None):
        self._categories = categories or {}

    async def list_all(self) -> List[TrackingCategory]:
        return list(self._categories.values())

    async def get_by_id(self, category_id: str) -> TrackingCategory | None:
        return self._categories.get(category_id)

    async def save(self, category: TrackingCategory) -> None:
        self._categories[category.id] = category

    async def delete(self, category_id: str) -> None:
        self._categories.pop(category_id, None)


class FakeTrackingItemRepo(TrackingItemRepositoryPort):
    def __init__(self, items: dict[str, TrackingItem] | None = None):
        self._items = items or {}

    async def list_all_by_category(self, category_id: str) -> List[TrackingItem]:
        return [
            item for item in self._items.values() if item.category_id == category_id
        ]

    async def get_by_id(self, item_id: str) -> TrackingItem | None:
        return self._items.get(item_id)

    async def save(self, item: TrackingItem) -> None:
        self._items[item.id] = item

    async def delete(self, item_id: str) -> None:
        self._items.pop(item_id, None)


class FakeTxRepo(TransactionRepositoryPort):
    def __init__(self):
        self.saved: list[ContainerTransaction] = []

    async def save(self, tx: ContainerTransaction) -> None:
        self.saved.append(tx)

    async def list_all(self) -> List[ContainerTransaction]:
        return list(self.saved)


class FakeGenericTxRepo(GenericTransactionRepositoryPort):
    def __init__(self):
        self.saved: list[Transaction] = []

    async def save(self, tx: Transaction) -> None:
        self.saved.append(tx)

    async def list_all(self) -> List[Transaction]:
        return list(self.saved)


class FakeBalanceQuery(BalanceQueryPort):
    def __init__(self, balances: Dict[Tuple[str, str], int] | None = None):
        # key: (client_id, tracking_item_id or container_type_id)
        self._balances = balances or {}

    async def get_balance_for(self, client_id: str, tracking_item_id: str) -> int:
        return self._balances.get((client_id, tracking_item_id), 0)

    async def get_balances(self) -> List[Balance]:
        return []
