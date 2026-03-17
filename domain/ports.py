"""
domain/ports.py — Shim module re-exporting from domain.ports package.

Kept so all existing imports continue to work after modularization:

    from domain.ports import ClientRepositoryPort
    from domain.ports import StockQueryPort

Do not add new ports here. Add them to the appropriate submodule under
domain/ports/ and re-export from domain/ports/__init__.py.
"""

from domain.ports import (  # type: ignore[import-not-found]
    AccountsQueryPort,
    ClientRepositoryPort,
    ItemGroupRepositoryPort,
    ItemRepositoryPort,
    MovementRepositoryPort,
    StockQueryPort,
    TagRepositoryPort,
    UnitOfWorkPort,
    WorkspaceRepositoryPort,
)

__all__ = [
    "WorkspaceRepositoryPort",
    "UnitOfWorkPort",
    "ClientRepositoryPort",
    "MovementRepositoryPort",
    "ItemGroupRepositoryPort",
    "ItemRepositoryPort",
    "TagRepositoryPort",
    "AccountsQueryPort",
    "StockQueryPort",
]
