from pydantic import BaseModel


class ItemGroupIn(BaseModel):
    name: str


class ItemGroupOut(BaseModel):
    id: str
    workspace_id: str
    name: str
