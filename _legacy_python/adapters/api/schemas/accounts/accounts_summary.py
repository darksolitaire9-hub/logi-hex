from decimal import Decimal

from pydantic import BaseModel


class StillOutEntryOut(BaseModel):
    item_id: str
    item_label: str
    unit: str
    quantity: Decimal


class ClientStillOutOut(BaseModel):
    client_id: str
    client_name: str
    entries: list[StillOutEntryOut]
    total: Decimal
    is_settled: bool


class AccountsSummaryOut(BaseModel):
    clients: list[ClientStillOutOut]
    grand_total: Decimal
