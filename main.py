# main.py
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from adapters.api import build_api_router  # ← registry (Change 3)
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError
from infrastructure.config import settings  # ← Change 1
from infrastructure.sqlite_repo import init_db

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_title,  # ← was hardcoded "logi-hex"
    description="Hexagonal container tracking API",
    version=settings.app_version,
    lifespan=lifespan,
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Exception handlers ----------
@app.exception_handler(UnknownContainerTypeError)
async def unknown_container_type_handler(
    request: Request, exc: UnknownContainerTypeError
):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(InsufficientBalanceError)
async def insufficient_balance_handler(request: Request, exc: InsufficientBalanceError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ---------- Routers ----------
app.include_router(build_api_router())  # ← was: include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
