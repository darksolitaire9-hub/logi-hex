from fastapi import APIRouter

from adapters.api.routes_movements.inventory.correct import router as correct_router
from adapters.api.routes_movements.inventory.receive import router as receive_router
from adapters.api.routes_movements.inventory.use import router as use_router

router = APIRouter()

router.include_router(receive_router)
router.include_router(use_router)
router.include_router(correct_router)
