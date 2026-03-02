from abc import ABC, abstractmethod
from typing import List

from .entities import (
    Balance,
    Client,
    ContainerTransaction,
    ContainerType,
    SummaryResult,
    TrackingCategory,
    TrackingItem,
    Transaction,
)


class ClientRepositoryPort(ABC):
    """Port for loading/creating clients."""

    @abstractmethod
    async def get_or_create_by_name(self, name: str) -> Client:
        """Normalize name, find existing client or create a new one."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> List[Client]:
        """Return all registered clients."""
        raise NotImplementedError


class ContainerTypeRepositoryPort(ABC):
    """Port for managing container types (box kinds, crates, etc.)."""

    @abstractmethod
    async def list_all(self) -> List[ContainerType]:
        """Return all available container types."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, type_id: str) -> ContainerType | None:
        """Return a container type by its id, or None if missing."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, container_type: ContainerType) -> None:
        """Create or update a container type."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, type_id: str) -> None:
        """Delete a container type by id."""
        raise NotImplementedError


class TrackingCategoryRepositoryPort(ABC):
    """Port for managing tracking categories."""

    @abstractmethod
    async def list_all(self) -> List[TrackingCategory]:
        """Return all tracking categories."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, category_id: str) -> TrackingCategory | None:
        """Return a category by its id, or None if missing."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, category: TrackingCategory) -> None:
        """Create or update a tracking category."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, category_id: str) -> None:
        """Delete a tracking category by id."""
        raise NotImplementedError


class TrackingItemRepositoryPort(ABC):
    """Port for managing tracking items within a category."""

    @abstractmethod
    async def list_all_by_category(self, category_id: str) -> List[TrackingItem]:
        """Return all items for a given category."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, item_id: str) -> TrackingItem | None:
        """Return a tracking item by its id, or None if missing."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, item: TrackingItem) -> None:
        """Create or update a tracking item."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, item_id: str) -> None:
        """Delete a tracking item by id."""
        raise NotImplementedError


class TransactionRepositoryPort(ABC):
    """Port for appending and listing container transactions."""

    @abstractmethod
    async def save(self, tx: ContainerTransaction) -> None:
        """Append a new transaction to the ledger."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> List[ContainerTransaction]:
        """Return all transactions (for debugging or exports)."""
        raise NotImplementedError


class GenericTransactionRepositoryPort(ABC):
    """Port for appending and listing generic multi-item transactions."""

    @abstractmethod
    async def save(self, tx: Transaction) -> None:
        """Append a new generic transaction to the ledger."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> List[Transaction]:
        """Return all generic transactions."""
        raise NotImplementedError


class BalanceQueryPort(ABC):
    """Port for querying current balances per client + container type."""

    @abstractmethod
    async def get_balances(self) -> List[Balance]:
        """
        Return balances where balance != 0.
        Each balance is SUM(OUT) - SUM(IN) per client_id + container_type_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_balance_for(self, client_id: str, tracking_item_id: str) -> int:
        """
        Return SUM(OUT) - SUM(IN) for a single (client_id, tracking_item_id).
        If there are no transactions, return 0.
        """
        raise NotImplementedError


class SummaryQueryPort(ABC):
    """Port for retrieving the client-centric summary of outstanding balances."""

    @abstractmethod
    async def get_summary(self) -> SummaryResult:
        """
        Returns all clients with non-zero balances, their per-type breakdown,
        and a grand total of all outstanding containers.
        """
        raise NotImplementedError


# temp  down
class UnitOfWorkPort(ABC):
    """Port for committing/rolling back a group of operations."""

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


# temp above
