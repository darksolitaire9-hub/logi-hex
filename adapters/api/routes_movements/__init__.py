from adapters.api.routes_movements.collect import router as collect_router
from adapters.api.routes_movements.send import router as send_router
from fastapi import APIRouter

router = APIRouter(prefix="/workspaces/{workspace_id}/movements", tags=["movements"])

router.include_router(send_router)
router.include_router(collect_router)
