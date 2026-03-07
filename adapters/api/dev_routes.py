# adapters/api/dev_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import ContainerType
from infrastructure.db.config import get_session
from infrastructure.repositories.container_types import (
    SqlAlchemyContainerTypeRepository,
)
from infrastructure.repositories.transactions import (
    SqlAlchemyTransactionRepository,
)

router = APIRouter(prefix="/api/dev", tags=["dev"])


@router.post("/seed-container-types")
async def seed_container_types(session: AsyncSession = Depends(get_session)):
    repo = SqlAlchemyContainerTypeRepository(session)
    defaults = [
        ContainerType(id="white", label="White Box"),
        ContainerType(id="round", label="Round Box"),
        ContainerType(id="glass", label="Big Glass"),
    ]
    for ct in defaults:
        await repo.save(ct)
    await session.commit()
    return {"seeded": [ct.id for ct in defaults]}


@router.get("/transactions")
async def debug_transactions(session: AsyncSession = Depends(get_session)):
    repo = SqlAlchemyTransactionRepository(session)
    txs = await repo.list_all()
    return [
        {
            "id": tx.id,
            "client_id": tx.client_id,
            "client_name": tx.client_name,
            "container_type_id": tx.container_type_id,
            "direction": tx.direction,
            "quantity": tx.quantity,
        }
        for tx in txs
    ]
