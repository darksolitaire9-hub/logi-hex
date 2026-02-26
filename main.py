from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from adapters.api.routes import router as api_router
from infrastructure.sqlite_repo import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (nothing to clean up yet)


app = FastAPI(
    title="logi-hex",
    description="Hexagonal container tracking API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
