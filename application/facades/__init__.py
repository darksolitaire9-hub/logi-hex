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
    AccountsMixin,
    InventoryMixin,
    MovementsMixin,
    ItemsMixin,
    TagsMixin,
    ClientsMixin,
    FacadeBase,
):
    """Entry point for all application operations.

    Composed from focused mixins — one per domain area.
    Owns no logic. Delegates everything to domain services via ports.
    All methods are workspace-scoped.
    """

    pass


__all__ = ["LogiFacade"]
