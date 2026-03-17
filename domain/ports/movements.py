"""
domain/ports/movements.py — Ports for movements (shared by both modes).

Covers:
- MovementRepositoryPort: persistence and basic queries for movements.

All ports are workspace-scoped:
workspace_id is always an explicit parameter.

Human reference: docs/V1-SCOPE.md — Movements.
"""

from abc import ABC, abstractmethod

from domain.entities import Movement


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
