"""
domain/services/inventory.py — Inventory mode movements: Receive, Use, Correct.
"""

from decimal import Decimal

from domain.entities import Movement, MovementLineItem
from domain.exceptions import (
    CorrectionReasonRequiredError,
    EmptyMovementError,
    InsufficientStockError,
)
from domain.language import CorrectionReason, MovementDirection, WorkspaceMode
from domain.ports import (
    ItemRepositoryPort,
    MovementRepositoryPort,
    StockQueryPort,
    UnitOfWorkPort,
)
from domain.services._guards import _get_active_item, _guard_direction


async def receive_stock(
    workspace_id: str,
    mode: WorkspaceMode,
    item_id: str,
    quantity: Decimal,
    notes: str | None,
    tag_ids: list[str] | None,
    item_repo: ItemRepositoryPort,
    movement_repo: MovementRepositoryPort,
    uow: UnitOfWorkPort,
) -> Movement:
    """
    Log a Receive movement — stock arriving on your shelf.
    Guard: none. You can always Receive.
    """
    _guard_direction(MovementDirection.RECEIVE, mode)

    if quantity <= Decimal("0"):
        raise EmptyMovementError()

    item = await _get_active_item(workspace_id, item_id, item_repo)

    movement = Movement.create(
        workspace_id=workspace_id,
        direction=MovementDirection.RECEIVE,
        line_items=[
            MovementLineItem(item_id=item.id, label=item.label, quantity=quantity)
        ],
        tag_ids=tag_ids or [],
        notes=notes,
    )
    await movement_repo.save(movement)
    await uow.commit()
    return movement


async def use_stock(
    workspace_id: str,
    mode: WorkspaceMode,
    item_id: str,
    quantity: Decimal,
    notes: str | None,
    tag_ids: list[str] | None,
    item_repo: ItemRepositoryPort,
    movement_repo: MovementRepositoryPort,
    stock_query: StockQueryPort,
    uow: UnitOfWorkPort,
) -> Movement:
    """
    Log a Use movement — stock sold or consumed.
    Guard: quantity must not exceed current In Stock.
    """
    _guard_direction(MovementDirection.USE, mode)

    if quantity <= Decimal("0"):
        raise EmptyMovementError()

    item = await _get_active_item(workspace_id, item_id, item_repo)

    in_stock = await stock_query.get_stock_for(workspace_id, item_id)
    if quantity > in_stock:
        raise InsufficientStockError(
            item_label=item.label,
            unit=item.unit,
            in_stock=in_stock,
            requested=quantity,
        )

    movement = Movement.create(
        workspace_id=workspace_id,
        direction=MovementDirection.USE,
        line_items=[
            MovementLineItem(item_id=item.id, label=item.label, quantity=quantity)
        ],
        tag_ids=tag_ids or [],
        notes=notes,
    )
    await movement_repo.save(movement)
    await uow.commit()
    return movement


async def correct_stock(
    workspace_id: str,
    mode: WorkspaceMode,
    item_id: str,
    actual_quantity: Decimal,
    reason: CorrectionReason,
    notes: str | None,
    item_repo: ItemRepositoryPort,
    movement_repo: MovementRepositoryPort,
    stock_query: StockQueryPort,
    uow: UnitOfWorkPort,
) -> Movement:
    """
    Log a Correct movement — physical count differs from system.
    Guard: reason is required and must be a user-facing reason.
    Line item quantity stores the delta (actual - current in stock).
    Actual can be zero — all stock gone is a valid correction.
    """
    _guard_direction(MovementDirection.CORRECT, mode)

    if reason is None or reason == CorrectionReason._OPENING_BALANCE:
        raise CorrectionReasonRequiredError()

    if actual_quantity < Decimal("0"):
        raise EmptyMovementError()

    item = await _get_active_item(workspace_id, item_id, item_repo)

    current = await stock_query.get_stock_for(workspace_id, item_id)
    delta = actual_quantity - current  # negative = shrinkage, positive = found more

    movement = Movement.create(
        workspace_id=workspace_id,
        direction=MovementDirection.CORRECT,
        line_items=[
            MovementLineItem(item_id=item.id, label=item.label, quantity=delta)
        ],
        correction_reason=reason,
        notes=notes,
    )
    await movement_repo.save(movement)
    await uow.commit()
    return movement
