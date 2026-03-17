# adapters/api/schemas/movements_common.py

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class MovementLineItemOut(BaseModel):
    item_id: str
    item_label: str
    unit: str
    quantity: Decimal


class MovementTagOut(BaseModel):
    id: str
    label: str
    color: str | None = None


class MovementOut(BaseModel):
    id: str
    workspace_id: str

    direction: Literal["SEND", "COLLECT", "RECEIVE", "USE", "CORRECT"]
    mode: Literal["ACCOUNTS", "INVENTORY"]

    # Accounts-only
    client_id: str | None = None
    client_name: str | None = None

    # Inventory-only
    correction_reason: str | None = None  # e.g. "SHRINKAGE", "COUNT_CORRECTION"

    occurred_at: datetime
    created_at: datetime

    notes: str | None = None

    line_items: list[MovementLineItemOut]
    tags: list[MovementTagOut]
