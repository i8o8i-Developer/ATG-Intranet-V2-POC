from fastapi import APIRouter
from nerve.db.postgres import get_pool, get_all_agent_statuses
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nerve")

from nerve.scheduler.cron_orchestrator import scheduler

def scheduler_is_running() -> bool:
    return scheduler.running

async def check_db() -> bool:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        return False

@router.get("/health")
async def health():
    return {
        "status": "ok", 
        "service": "nerve",
        "scheduler_running": scheduler_is_running(),
        "db_connected": await check_db(),
        "agents": await get_all_agent_statuses(),
    }
