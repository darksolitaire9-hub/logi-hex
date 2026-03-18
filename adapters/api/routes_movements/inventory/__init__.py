from fastapi import APIRouter

from adapters.api.routes_movements.inventory.receive import router as receive_router

router = APIRouter()

router.include_router(receive_router)
