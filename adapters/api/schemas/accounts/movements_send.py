# adapters/api/schemas/accounts/movements_send.py

from decimal import Decimal

from pydantic import BaseModel


class SendMovementLineItemIn(BaseModel):
    item_id: str
    quantity: Decimal


class SendMovementIn(BaseModel):
    client_id: str
    items: list[SendMovementLineItemIn]
    notes: str | None = None
    tag_ids: list[str] | None = None
