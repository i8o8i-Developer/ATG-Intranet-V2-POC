from fastapi import APIRouter, HTTPException
from nerve.db.postgres import get_pool, get_provider_status, update_provider_status
from nerve.scheduler.cron_orchestrator import trigger_agent_job, CRON_JOBS

router = APIRouter(prefix="/nerve")

@router.get("/status")
async def status():
    """Summary: total events, job success rate, agent health"""
    # Note: Complex aggregations left for future optimization
    pool = await get_pool()
    query = """
        SELECT agent, status, consecutive_failures, last_success, last_failure 
        FROM nerve_agent_status
    """
    async with pool.acquire() as conn:
        agent_rows = await conn.fetch(query)
        
    return {
        "status": "online",
        "agents": [dict(row) for row in agent_rows]
    }

@router.get("/jobs/history")
async def jobs_history(limit: int = 50):
    """Last N job executions with results"""
    pool = await get_pool()
    query = """
        SELECT trigger_id, job_id, target_agent, success, duration_ms, error_type, completed_at
        FROM nerve_job_log
        ORDER BY completed_at DESC
        LIMIT $1
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, limit)
    return [dict(row) for row in rows]

@router.post("/jobs/trigger/{job_id}")
async def trigger_job(job_id: str):
    """Manually trigger any job (debug)"""
    job_def = next((j for j in CRON_JOBS if j["id"] == job_id), None)
    if not job_def:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Fire asynchronously so we don't block the API
    import asyncio
    asyncio.create_task(trigger_agent_job(job_def))
    return {"status": "triggered", "job_id": job_id}

@router.get("/events/log")
async def events_log(limit: int = 50):
    """Query nerve_event_log"""
    pool = await get_pool()
    query = """
        SELECT id, timestamp, event_type, source, project_id, status 
        FROM nerve_event_log
        ORDER BY timestamp DESC
        LIMIT $1
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, limit)
    return [dict(row) for row in rows]

@router.get("/providers")
async def get_providers():
    """Current LLM provider status"""
    pool = await get_pool()
    query = "SELECT provider, status, last_error, updated_at FROM nerve_provider_status"
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    return [dict(row) for row in rows]

@router.post("/providers/{provider}/reset")
async def reset_provider(provider: str):
    """Manually reset provider to 'ok' after admin resolves"""
    await update_provider_status(provider, "ok", None)
    return {"status": "reset", "provider": provider}
