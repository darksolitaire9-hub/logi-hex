# main.py

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, staticfiles
from fastapi.responses import JSONResponse

from adapters.api.routes import router as api_router
from adapters.ui.routes import router as ui_router  # new
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError
from infrastructure.sqlite_repo import init_db

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="logi-hex",
    description="Hexagonal container tracking API",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
]

app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")


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


app.include_router(api_router)
app.include_router(ui_router)  # new


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
