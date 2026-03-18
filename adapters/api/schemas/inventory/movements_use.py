# adapters/api/schemas/inventory/movements_use.py

from decimal import Decimal

from pydantic import BaseModel


class UseMovementIn(BaseModel):
    item_id: str
    quantity: Decimal
    notes: str | None = None
    tag_ids: list[str] | None = None
