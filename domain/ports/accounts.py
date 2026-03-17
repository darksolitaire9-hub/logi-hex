"""
domain/ports/accounts.py — Ports specific to Accounts mode.

Covers:
- ClientRepositoryPort: persistence for clients.
- AccountsQueryPort: read-side queries for Accounts dashboards.

All ports are workspace-scoped:
workspace_id is always an explicit parameter.

Human reference: docs/V1-SCOPE.md — Clients, Movements — Accounts mode, Dashboards.
"""

from abc import ABC, abstractmethod
from decimal import Decimal

from domain.entities import AccountsSummary, Client


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
