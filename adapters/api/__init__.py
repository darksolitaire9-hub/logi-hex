"""
API router composition.

Builds the root APIRouter by including all modular route files.
Each router owns a specific domain area and registers its own
endpoints under the /api prefix.
"""

from fastapi import APIRouter

from adapters.api.routes_containers import router as containers_router
from adapters.api.routes_movements import router as movements_router
from adapters.api.routes_summary import router as summary_router
from adapters.api.routes_tracking import router as tracking_router


def build_api_router() -> APIRouter:
    """
    Composes all domain-specific routers into a single root router.

    To add a new domain area, create a new routes_*.py file and
    include_router it here.
    """
    root = APIRouter()
    root.include_router(containers_router)
    root.include_router(movements_router)
    root.include_router(tracking_router)
    root.include_router(summary_router)
    return root
