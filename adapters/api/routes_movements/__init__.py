from fastapi import APIRouter

from adapters.api.routes_movements.accounts import router as accounts_router

router = APIRouter(prefix="/workspaces/{workspace_id}/movements", tags=["movements"])

router.include_router(accounts_router)
