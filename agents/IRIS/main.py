"""
IRIS service entrypoint.
Run: uvicorn main:app --reload --port 8000
"""

import logging
from fastapi import FastAPI
from iris.api.routes import router
from iris.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

app = FastAPI(
    title="IRIS — Insight & Record Intelligence System",
    description="Extraction intelligence agent for meeting artifacts.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "IRIS",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/iris/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.iris_host,
        port=settings.iris_port,
        reload=True,
    )
