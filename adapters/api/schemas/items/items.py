from decimal import Decimal

from pydantic import BaseModel


class ItemIn(BaseModel):
    group_id: str
    label: str
    unit: str
    opening_quantity: Decimal | None = None


class ItemOut(BaseModel):
    id: str
    workspace_id: str
    group_id: str
    label: str
    unit: str
    is_active: bool
