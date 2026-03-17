# adapters/api/utils/movements.py
"""
Reusable helpers for movement routes.

Rules:
- No business logic. No domain rules enforced here.
- No HTTP concerns (no status codes, no HTTPException).
- Pure functions and thin async helpers only.
"""

from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol, TypeVar

from application.facades import LogiFacade
from domain.entities import Item, Tag


class HasItemAndQuantity(Protocol):
    item_id: str
    quantity: Decimal


TItem = TypeVar("TItem", bound=HasItemAndQuantity)


def aggregate_quantities(
    items: Sequence[TItem],
) -> dict[str, Decimal]:
    """Aggregate quantities per item_id from a list of line items."""
    result: dict[str, Decimal] = {}
    for li in items:
        result[li.item_id] = result.get(li.item_id, Decimal("0")) + li.quantity
    return result


async def load_mapper_context(
    facade: LogiFacade,
    workspace_id: str,
) -> tuple[dict[str, Item], dict[str, Tag]]:
    """Fetch items and tags needed by the movement mapper."""
    all_items = await facade.list_items(workspace_id, active_only=False)
    all_tags = await facade.list_tags(workspace_id)
    return (
        {item.id: item for item in all_items},
        {tag.id: tag for tag in all_tags},
    )
