from fastapi import APIRouter, Depends
from pydantic import BaseModel

from application.facades import LogiFacade

from .dependencies import get_facade

router = APIRouter(prefix="/api")


class ClientResponse(BaseModel):
    id: str
    name: str


@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(
    facade: LogiFacade = Depends(get_facade),
):
    clients = await facade.list_clients()
    return [ClientResponse(id=c.id, name=c.name) for c in clients]
