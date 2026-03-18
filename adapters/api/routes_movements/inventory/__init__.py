# adapters/api/routes_movements/inventory/__init__.py

from fastapi import APIRouter

from adapters.api.routes_movements.inventory.receive import router as receive_router
from adapters.api.routes_movements.inventory.use import router as use_router

router = APIRouter()

router.include_router(receive_router)
router.include_router(use_router)
