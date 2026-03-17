"""
API router composition.

Builds the root APIRouter by including all modular route files.
Each router owns a specific domain area and registers its own
endpoints under the /api prefix.
"""

from fastapi import APIRouter

from adapters.api.routes_movements import router as movements_router

# from adapters.api.routes_items import router as items_router
# from adapters.api.routes_workspaces import router as workspaces_router


def build_api_router() -> APIRouter:
    """Factory used by main.py to build the API router."""
    router = APIRouter(prefix="/api")

    router.include_router(movements_router)
    # router.include_router(items_router)
    # router.include_router(workspaces_router)

    return router


# Optional convenience: module-level router
router = build_api_router()

__all__ = ["build_api_router", "router"]
