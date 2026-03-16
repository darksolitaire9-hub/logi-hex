from decimal import Decimal

from domain.entities import Item, Movement, MovementLineItem
from domain.exceptions import ItemNotFoundError
from domain.language import CorrectionReason, MovementDirection
from domain.ports import (
    ItemRepositoryPort,
    MovementRepositoryPort,
    UnitOfWorkPort,
)


async def create_item(
    workspace_id: str,
    group_id: str,
    label: str,
    unit: str,
    item_repo: ItemRepositoryPort,
    uow: UnitOfWorkPort,
) -> Item:
    item = Item.create(
        workspace_id=workspace_id,
        group_id=group_id,
        label=label,
        unit=unit,
    )
    await item_repo.save(item)
    await uow.commit()
    return item


async def create_item_with_opening_stock(
    workspace_id: str,
    group_id: str,
    label: str,
    unit: str,
    opening_quantity: Decimal,
    item_repo: ItemRepositoryPort,
    movement_repo: MovementRepositoryPort,
    uow: UnitOfWorkPort,
) -> tuple[Item, Movement]:
    """
    Create an item and set its opening stock in one atomic write.
    The opening stock movement uses _OPENING_BALANCE internally —
    never shown to the user as a Receive.
    Triggered when the user answers "How many do you have right now?" > 0.
    """
    item = Item.create(
        workspace_id=workspace_id,
        group_id=group_id,
        label=label,
        unit=unit,
    )
    await item_repo.save(item)

    movement = Movement.create(
        workspace_id=workspace_id,
        direction=MovementDirection.RECEIVE,
        line_items=[
            MovementLineItem(
                item_id=item.id,
                label=item.label,
                quantity=opening_quantity,
            )
        ],
        correction_reason=CorrectionReason._OPENING_BALANCE,
    )
    await movement_repo.save(movement)
    await uow.commit()
    return item, movement


async def archive_item(
    workspace_id: str,
    item_id: str,
    item_repo: ItemRepositoryPort,
    uow: UnitOfWorkPort,
) -> Item:
    item = await item_repo.get_by_id(workspace_id, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    item.archive()
    await item_repo.save(item)
    await uow.commit()
    return item


async def reactivate_item(
    workspace_id: str,
    item_id: str,
    item_repo: ItemRepositoryPort,
    uow: UnitOfWorkPort,
) -> Item:
    item = await item_repo.get_by_id(workspace_id, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    item.reactivate()
    await item_repo.save(item)
    await uow.commit()
    return item


async def list_items(
    workspace_id: str,
    item_repo: ItemRepositoryPort,
    active_only: bool = True,
) -> list[Item]:
    if active_only:
        return await item_repo.list_active(workspace_id)
    return await item_repo.list_all(workspace_id)
