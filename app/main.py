from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database import create_all
from app.routers import auth, dashboard, records, users

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Finance Dashboard API",
    description="Role-based finance data management backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def startup_event() -> None:
    if settings.run_db_init_on_startup:
        create_all()


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": exc.__class__.__name__},
    )
