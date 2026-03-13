import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from adapters.api import build_api_router
from adapters.api.routes_auth import router as auth_router
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError
from infrastructure.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database schema is managed by Alembic migrations.
    # Run `alembic upgrade head` before starting the app.
    yield


app = FastAPI(
    title=settings.app_title,
    description="Hexagonal container tracking API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None if not settings.debug else "/docs",
    redoc_url=None if not settings.debug else "/redoc",
    openapi_url=None if not settings.debug else "/openapi.json",
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Global preflight handler ----------
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str) -> Response:
    # Let CORSMiddleware attach CORS headers; keep OPTIONS logic minimal.
    return Response(status_code=204)


# ---------- Exception handlers ----------
@app.exception_handler(UnknownContainerTypeError)
async def unknown_container_type_handler(
    request: Request,
    exc: UnknownContainerTypeError,
):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(InsufficientBalanceError)
async def insufficient_balance_handler(
    request: Request,
    exc: InsufficientBalanceError,
):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ---------- Routers ----------
app.include_router(auth_router)  # /api/auth/* (no auth required)
app.include_router(
    build_api_router()
)  # /api/* (authed via get_facade / get_current_user)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
