"""
domain/ports/__init__.py — Domain ports public API for logi-hex.

This is the ONLY import path consumers should use:

    from domain.ports import ClientRepositoryPort
    from domain.ports import StockQueryPort

Submodules (workspaces, accounts, inventory, movements) are implementation detail.
Do not import from them directly outside of domain/ports/.

Human reference: docs/V1-SCOPE.md.
"""

from .accounts import AccountsQueryPort, ClientRepositoryPort
from .inventory import (
    ItemGroupRepositoryPort,
    ItemRepositoryPort,
    StockQueryPort,
    TagRepositoryPort,
)
from .movements import MovementRepositoryPort
from .workspaces import UnitOfWorkPort, WorkspaceRepositoryPort

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
