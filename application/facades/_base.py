"""
application/facades/_base.py — FacadeBase: port storage and wiring.

All mixins inherit from this. No business logic here — just __init__.
"""

from domain.ports import (
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


class FacadeBase:
    def __init__(
        self,
        workspace_repo: WorkspaceRepositoryPort,
        client_repo: ClientRepositoryPort,
        group_repo: ItemGroupRepositoryPort,
        item_repo: ItemRepositoryPort,
        tag_repo: TagRepositoryPort,
        movement_repo: MovementRepositoryPort,
        accounts_query: AccountsQueryPort,
        stock_query: StockQueryPort,
        uow: UnitOfWorkPort,
    ) -> None:
        self._workspace_repo = workspace_repo
        self._client_repo = client_repo
        self._group_repo = group_repo
        self._item_repo = item_repo
        self._tag_repo = tag_repo
        self._movement_repo = movement_repo
        self._accounts_query = accounts_query
        self._stock_query = stock_query
        self._uow = uow
