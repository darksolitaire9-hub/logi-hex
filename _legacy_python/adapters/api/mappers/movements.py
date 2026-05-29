# adapters/api/mappers/movements.py
"""
Translates domain Movement entities → API MovementOut DTOs.

Rules:
- No business logic here. Pure translation only.
- No DB access. All data is passed in.
- No domain imports except entities and language.
- Language: direction/mode/reason always use .value — never raw strings.
"""

from adapters.api.schemas.movements_common import (
    MovementLineItemOut,
    MovementOut,
    MovementTagOut,
)
from domain.entities import Item, Movement, Tag
from domain.language import WorkspaceMode


def movement_to_out(
    movement: Movement,
    mode: WorkspaceMode,
    items_by_id: dict[str, Item],
    tags_by_id: dict[str, Tag],
) -> MovementOut:
    line_items = [
        MovementLineItemOut(
            item_id=li.item_id,
            item_label=li.label,
            unit=items_by_id[li.item_id].unit if li.item_id in items_by_id else "",
            quantity=li.quantity,
        )
        for li in movement.line_items
    ]

    tags = [
        MovementTagOut(
            id=tag.id,
            label=tag.name,
            color=tag.colour,  # domain uses colour; DTO uses color
        )
        for tag_id in movement.tag_ids
        if (tag := tags_by_id.get(tag_id)) is not None
    ]

    return MovementOut(
        id=movement.id,
        workspace_id=movement.workspace_id,
        direction=movement.direction.value,
        mode=mode.value,
        client_id=movement.client_id,
        client_name=movement.client_name,
        correction_reason=(
            movement.correction_reason.value
            if movement.correction_reason is not None
            else None
        ),
        occurred_at=movement.timestamp,
        created_at=movement.timestamp,
        notes=movement.notes,
        line_items=line_items,
        tags=tags,
    )
