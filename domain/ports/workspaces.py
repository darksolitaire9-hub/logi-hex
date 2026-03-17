"""
domain/ports/workspaces.py — Workspace and unit-of-work ports.

Covers:
- WorkspaceRepositoryPort: CRUD operations for workspaces.
- UnitOfWorkPort: transactional boundary for write operations.

All ports are workspace-scoped where applicable:
workspace_id is always an explicit parameter.

Human reference: docs/V1-SCOPE.md — Workspaces, Technical constraints.
"""

from abc import ABC, abstractmethod

from domain.entities import Workspace


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


class UnitOfWorkPort(ABC):
    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
