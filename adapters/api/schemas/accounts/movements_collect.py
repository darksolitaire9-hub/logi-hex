# adapters/api/schemas/accounts/movements_collect.py

from decimal import Decimal

from pydantic import BaseModel


class CollectMovementLineItemIn(BaseModel):
    item_id: str
    quantity: Decimal


class CollectMovementIn(BaseModel):
    client_id: str
    items: list[CollectMovementLineItemIn]
    notes: str | None = None
    tag_ids: list[str] | None = None
