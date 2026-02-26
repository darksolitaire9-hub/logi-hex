from abc import ABC, abstractmethod
from typing import List

from .entities import Balance, Client, ContainerTransaction, ContainerType


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
    async def get_balance_for(self, client_id: str, container_type_id: str) -> int:
        """
        Return SUM(OUT) - SUM(IN) for a single (client_id, container_type_id).
        If there are no transactions, return 0.
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
