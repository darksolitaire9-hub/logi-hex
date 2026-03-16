"""
application/facades — LogiFacade assembled from focused mixins.

Usage:
    from application.facades import LogiFacade

Call site is identical to the old flat file:
    facade.send_items(...)
    facade.receive_stock(...)
"""

from application.facades._base import FacadeBase
from application.facades.accounts import AccountsMixin
from application.facades.clients import ClientsMixin
from application.facades.inventory import InventoryMixin
from application.facades.items import ItemsMixin
from application.facades.movements import MovementsMixin
from application.facades.tags import TagsMixin
from application.facades.workspaces import WorkspacesMixin


class LogiFacade(
    WorkspacesMixin,
    ClientsMixin,
    ItemsMixin,
    TagsMixin,
    AccountsMixin,
    InventoryMixin,
    MovementsMixin,
    FacadeBase,
):
    """
    Single entry point for all application operations.

    Composed from focused mixins — one per domain area.
    Owns no logic. Delegates everything to domain services via ports.
    All methods are workspace-scoped.
    """

    pass


__all__ = ["LogiFacade"]
