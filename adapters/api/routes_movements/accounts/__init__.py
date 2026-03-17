from fastapi import APIRouter

from adapters.api.routes_movements.accounts.collect import router as collect_router
from adapters.api.routes_movements.accounts.send import router as send_router

router = APIRouter()

router.include_router(send_router)
router.include_router(collect_router)
