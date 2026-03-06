from fastapi import APIRouter, Depends

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import Balance

router = APIRouter(prefix="/api")


@router.get("/balances", response_model=list[Balance])
async def get_balances(facade: LogiFacade = Depends(get_facade)):
    return await facade.balances()


@router.get("/summary")
async def get_summary(facade: LogiFacade = Depends(get_facade)):
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
