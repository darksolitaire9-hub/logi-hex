"""
domain/services/accounts.py — Accounts mode movements: Send and Collect.
"""

from decimal import Decimal

from domain.entities import Movement, MovementLineItem
from domain.exceptions import (
    ClientNotFoundError,
    EmptyMovementError,
    InsufficientStillOutError,
)
from domain.language import MovementDirection, WorkspaceMode
from domain.ports import (
    AccountsQueryPort,
    ClientRepositoryPort,
    ItemRepositoryPort,
    MovementRepositoryPort,
    UnitOfWorkPort,
)
from domain.services._guards import _get_active_item, _guard_direction


async def send_items(
    workspace_id: str,
    mode: WorkspaceMode,
    client_id: str,
    item_quantities: dict[str, Decimal],
    notes: str | None,
    tag_ids: list[str] | None,
    client_repo: ClientRepositoryPort,
    item_repo: ItemRepositoryPort,
    movement_repo: MovementRepositoryPort,
    uow: UnitOfWorkPort,
) -> Movement:
    """
    Log a Send movement — items leaving your hands to a client.
    Guard: none. You can always Send.
    Atomic: all items validated before any write.
    """
    _guard_direction(MovementDirection.SEND, mode)

    client = await client_repo.get_by_id(workspace_id, client_id)
    if client is None:
        raise ClientNotFoundError(client_id)

    line_items: list[MovementLineItem] = []
    for item_id, qty in item_quantities.items():
        if qty <= Decimal("0"):
            continue
        item = await _get_active_item(workspace_id, item_id, item_repo)
        line_items.append(
            MovementLineItem(item_id=item.id, label=item.label, quantity=qty)
        )

    if not line_items:
        raise EmptyMovementError()

    movement = Movement.create(
        workspace_id=workspace_id,
        direction=MovementDirection.SEND,
        line_items=line_items,
        client_id=client.id,
        client_name=client.name,
        tag_ids=tag_ids or [],
        notes=notes,
    )
    await movement_repo.save(movement)
    await uow.commit()
    return movement


async def collect_items(
    workspace_id: str,
    mode: WorkspaceMode,
    client_id: str,
    item_quantities: dict[str, Decimal],
    notes: str | None,
    tag_ids: list[str] | None,
    client_repo: ClientRepositoryPort,
    item_repo: ItemRepositoryPort,
    movement_repo: MovementRepositoryPort,
    accounts_query: AccountsQueryPort,
    uow: UnitOfWorkPort,
) -> Movement:
    """
    Log a Collect movement — items returning from a client.
    Guard: Collect qty must not exceed Still Out per item.
    Atomic: ALL items checked before ANY write.
    One failure rejects the entire movement.
    """
    _guard_direction(MovementDirection.COLLECT, mode)

    client = await client_repo.get_by_id(workspace_id, client_id)
    if client is None:
        raise ClientNotFoundError(client_id)

    # Phase 1 — validate everything, write nothing
    line_items: list[MovementLineItem] = []
    for item_id, qty in item_quantities.items():
        if qty <= Decimal("0"):
            continue
        item = await _get_active_item(workspace_id, item_id, item_repo)
        still_out = await accounts_query.get_still_out_for(
            workspace_id, client_id, item_id
        )
        if qty > still_out:
            raise InsufficientStillOutError(
                client_name=client.name,
                item_label=item.label,
                unit=item.unit,
                still_out=still_out,
                requested=qty,
            )
        line_items.append(
            MovementLineItem(item_id=item.id, label=item.label, quantity=qty)
        )

    if not line_items:
        raise EmptyMovementError()

    # Phase 2 — all guards passed, write atomically
    movement = Movement.create(
        workspace_id=workspace_id,
        direction=MovementDirection.COLLECT,
        line_items=line_items,
        client_id=client.id,
        client_name=client.name,
        tag_ids=tag_ids or [],
        notes=notes,
    )
    await movement_repo.save(movement)
    await uow.commit()
    return movement
