from contextlib import asynccontextmanager
from fastapi import FastAPI
from nerve.config import settings
from nerve.db.postgres import init_pool, close_pool
from nerve.api import webhooks, health, admin
from nerve.scheduler.cron_orchestrator import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await start_scheduler()
    yield
    await stop_scheduler()
    await close_pool()

app = FastAPI(title="NERVE", version="1.0.0", lifespan=lifespan)
app.include_router(webhooks.router)
app.include_router(health.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.nerve_host, port=settings.nerve_port, reload=True)
