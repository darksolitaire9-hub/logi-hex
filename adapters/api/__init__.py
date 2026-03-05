# adapters/api/__init__.py
from fastapi import APIRouter

from adapters.api.routes import router as logi_router
from infrastructure.config import settings


def build_api_router() -> APIRouter:
    root = APIRouter()
    root.include_router(logi_router)  # prefix="/api" lives in routes.py

    # Uncomment this only after dev_routes.py exists and works
    # if settings.debug:
    #     from adapters.api.dev_routes import router as dev_router
    #     root.include_router(dev_router)

    return root



