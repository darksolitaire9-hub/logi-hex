from pydantic import BaseModel


class ClientOut(BaseModel):
    id: str
    workspace_id: str
    name: str
