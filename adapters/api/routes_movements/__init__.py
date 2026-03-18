from fastapi import APIRouter

from adapters.api.routes_movements.accounts import router as accounts_router
from adapters.api.routes_movements.inventory import router as inventory_router

router = APIRouter(prefix="/workspaces/{workspace_id}/movements", tags=["movements"])

router.include_router(accounts_router)
router.include_router(inventory_router)
