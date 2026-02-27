from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# seeding below
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import Balance, ContainerType, TrackingCategory
from infrastructure.sqlite_repo import (
    SqlAlchemyContainerTypeRepository,
    SqlAlchemyTrackingCategoryRepository,
    SqlAlchemyTransactionRepository,
    get_session,
)

# seeding above

router = APIRouter(prefix="/api")


class IssueRequest(BaseModel):
    name: str = Field(..., description="Client name, any case")
    container_type_id: str = Field(..., description="Container type ID, e.g. 'white'")
    quantity: int = Field(..., gt=0, description="How many containers issued")


class ReceiveRequest(BaseModel):
    name: str
    container_type_id: str
    quantity: int = Field(..., gt=0)


@router.post("/issue")
async def issue_containers(
    body: IssueRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Issue containers to a client (OUT).
    """
    # (Optional) could check container type exists via facade.container_type_repo
    tx = await facade.issue(
        name=body.name,
        container_type_id=body.container_type_id,
        quantity=body.quantity,
    )
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "container_type_id": tx.container_type_id,
        "direction": tx.direction,
        "quantity": tx.quantity,
    }


@router.post("/receive")
async def receive_containers(
    body: ReceiveRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Record containers returned by a client (IN).
    """
    tx = await facade.receive(
        name=body.name,
        container_type_id=body.container_type_id,
        quantity=body.quantity,
    )
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "container_type_id": tx.container_type_id,
        "direction": tx.direction,
        "quantity": tx.quantity,
    }


@router.get("/balances", response_model=list[Balance])
async def get_balances(
    facade: LogiFacade = Depends(get_facade),
):
    """
    Get all non-zero balances per client + container type.
    """
    balances = await facade.balances()
    return balances


@router.get("/summary")
async def get_summary(
    facade: LogiFacade = Depends(get_facade),
):
    """
    Returns a client-centric summary of all outstanding container balances.
    Each client shows per-type balances and a total outstanding count.
    """
    result = await facade.summary()
    return {
        "clients": [
            {
                "client_name": c.client_name,
                "total_outstanding": c.total_outstanding,
                "balances": [
                    {
                        "container_label": b.container_label,
                        "container_type_id": b.container_type_id,
                        "balance": b.balance,
                    }
                    for b in c.balances
                ],
            }
            for c in result.clients
        ],
        "grand_total": result.grand_total,
    }


# temp helper below


@router.post("/seed-container-types")
async def seed_container_types(
    session: AsyncSession = Depends(get_session),
):
    """
    Temporary helper: seed some default container types.
    Call once after deploy, or whenever you reset the DB.
    """
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


@router.get("/debug/transactions")
async def debug_transactions(
    session: AsyncSession = Depends(get_session),
):
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


# temp above


@router.post("/setup/primary-category", response_class=HTMLResponse)
async def create_primary_category(
    primary_name: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    primary_name = primary_name.strip()
    if not primary_name:
        return HTMLResponse(
            '<p class="error-msg">Name is required.</p>', status_code=400
        )

    cat_id = primary_name.lower().replace(" ", "-")

    category = TrackingCategory(
        id=cat_id,
        name=primary_name,
        is_balanced=True,
    )

    repo = SqlAlchemyTrackingCategoryRepository(session)
    await repo.save(category)
    await session.commit()

    html = f"""
    <p>Primary category <strong>{category.name}</strong> created.</p>
    <p>
      <a href="/ui">Go to dashboard →</a>
    </p>
    """
    return HTMLResponse(content=html)


@router.post("/setup/secondary-category", response_class=HTMLResponse)
async def create_secondary_category(
    secondary_name: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    secondary_name = secondary_name.strip()
    if not secondary_name:
        return HTMLResponse(
            '<p class="error-msg">Name is required.</p>', status_code=400
        )

    cat_id = secondary_name.lower().replace(" ", "-")

    category = TrackingCategory(
        id=cat_id,
        name=secondary_name,
        is_balanced=False,
    )

    repo = SqlAlchemyTrackingCategoryRepository(session)
    await repo.save(category)
    await session.commit()

    html = f"""
    <p>Secondary category <strong>{category.name}</strong> created.</p>
    """
    return HTMLResponse(content=html)
