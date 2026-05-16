"""
CELL — Contextual Execution & Labour Ledger
FastAPI entrypoint.

Start: uvicorn main:app --host 0.0.0.0 --port 8002
"""
from __future__ import annotations

import logging
import os

import uvicorn
from fastapi import FastAPI

from cell.api.routes import router as cell_router
from cell.api.pm_webhook import router as webhook_router
from cell.db.postgres import get_pool, close_pool
# removed scheduler import
from cell.config import settings

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cell")

from contextlib import asynccontextmanager

# ── Lifecycle ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CELL starting up...")
    await get_pool()   # warm up DB pool
    logger.info(
        "CELL ready | mock_mode=%s | port=%d",
        settings.mock_mode,
        settings.cell_port,
    )
    yield
    logger.info("CELL shutting down...")
    await close_pool()

# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="CELL — Contextual Execution & Labour Ledger",
    description=(
        "Task generation, distribution, and bounty management agent. "
        "Sits between IRIS (meeting intelligence) and the human workforce."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

from cell.api.jobs import router as jobs_router
from cell.api.summary import router as summary_router

app.include_router(cell_router)
app.include_router(webhook_router)
app.include_router(jobs_router)
app.include_router(summary_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.cell_host,
        port=settings.cell_port,
        reload=False,
        log_level="info",
    )
