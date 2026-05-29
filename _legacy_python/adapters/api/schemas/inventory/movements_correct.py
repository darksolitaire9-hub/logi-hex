# adapters/api/schemas/inventory/movements_correct.py

from decimal import Decimal

from pydantic import BaseModel

from domain.language import CorrectionReason


class CorrectMovementIn(BaseModel):
    item_id: str
    actual_quantity: Decimal
    reason: CorrectionReason
    notes: str | None = None
