# main.py
"""
FastAPI application for the logi-hex backend.

This service exposes a pure JSON API on port 8000.
The Nuxt frontend will talk to it via a dev/prod reverse proxy
(e.g. Nuxt Nitro in dev, NGINX/Vercel in prod), so the browser only
ever calls `/api/...` on the frontend origin.
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adapters.api.routes import router as api_router
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError
from infrastructure.sqlite_repo import init_db

# Configure basic logging for the whole app
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan hook.

    Runs once on startup, before the first request, and once on shutdown.
    Here we ensure the SQLite database and tables exist by calling `init_db()`.
    """
    await init_db()
    yield
    # If you ever need graceful shutdown logic, add it after `yield`.


# Create the FastAPI app instance.
# NOTE: No static files, no HTML templates — this is a pure JSON API.
app = FastAPI(
    title="logi-hex",
    description="Hexagonal container tracking API",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------- Exception handlers ----------


@app.exception_handler(UnknownContainerTypeError)
async def unknown_container_type_handler(
    request: Request, exc: UnknownContainerTypeError
):
    """
    Translate UnknownContainerTypeError into a 422 JSON response.

    The frontend can surface `detail` to the user as a validation-style error.
    """
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(InsufficientBalanceError)
async def insufficient_balance_handler(request: Request, exc: InsufficientBalanceError):
    """
    Translate InsufficientBalanceError into a 422 JSON response.

    This is raised when a client tries to return more containers than they owe.
    """
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected server errors.

    Logs the error and returns a generic 500 JSON response so the client
    gets a consistent shape even on failures.
    """
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ---------- Routers ----------

# Attach the API router under its configured prefix (e.g. `/api`).
# This router should only define JSON endpoints — no HTML responses.
app.include_router(api_router)


# ---------- Local development entrypoint ----------

if __name__ == "__main__":
    """
    Run the app with Uvicorn for local development.

    The Nuxt dev server will proxy `/api/*` requests to this process on port 8000.
    In production, you would typically run Uvicorn/Gunicorn under a reverse
    proxy (NGINX, etc.) that also forwards `/api/*` to this app.
    """
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
