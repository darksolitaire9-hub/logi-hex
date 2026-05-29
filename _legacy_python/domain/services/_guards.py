"""
domain/services/_guards.py — Shared internal helpers.

Prefixed with _ — not exported from the package.
Used only by other service modules.
"""

from domain.entities import Item
from domain.exceptions import (
    ArchivedItemError,
    ItemNotFoundError,
    WorkspaceModeMismatchError,
)
from domain.language import VALID_DIRECTIONS, MovementDirection, WorkspaceMode
from domain.ports import ItemRepositoryPort


def _guard_direction(direction: MovementDirection, mode: WorkspaceMode) -> None:
    """Raise WorkspaceModeMismatchError if direction is invalid for the mode."""
    if direction not in VALID_DIRECTIONS[mode]:
        raise WorkspaceModeMismatchError(direction, mode)


async def _get_active_item(
    workspace_id: str,
    item_id: str,
    item_repo: ItemRepositoryPort,
) -> Item:
    """
    Fetch an active item by id within a workspace.
    Raises ItemNotFoundError if missing.
    Raises ArchivedItemError if archived.
    """
    item = await item_repo.get_by_id(workspace_id, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    if not item.is_active:
        raise ArchivedItemError(item.label)
    return item
