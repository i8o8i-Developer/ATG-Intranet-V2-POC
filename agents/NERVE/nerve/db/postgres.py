import asyncpg
import json
from typing import Optional, Dict, Any
from nerve.config import settings

_pool: Optional[Any] = None

class MockConnection:
    async def fetchval(self, query, *args): return 1
    async def execute(self, query, *args): pass
    async def fetch(self, query, *args): return []

class MockPool:
    def acquire(self):
        class ContextManager:
            async def __aenter__(self): return MockConnection()
            async def __aexit__(self, exc_type, exc, tb): pass
        return ContextManager()
    async def close(self): pass

async def init_pool():
    global _pool
    if settings.mock_mode:
        print("WARNING: Running in MOCK_MODE. Database is bypassed.")
        _pool = MockPool()
        return

    _pool = await asyncpg.create_pool(
        settings.database_url, 
        min_size=2, 
        max_size=10
    )

async def close_pool():
    if _pool:
        await _pool.close()

async def get_pool() -> Any:
    if not _pool:
        raise Exception("Database pool not initialized")
    return _pool

async def log_event(event_type: str, source: str, project_id: Optional[str], meeting_id: Optional[str], details: Dict[str, Any]) -> int:
    """Append to nerve_event_log. Returns event ID."""
    pool = await get_pool()
    query = """
        INSERT INTO nerve_event_log (event_type, source, project_id, meeting_id, details, status)
        VALUES ($1, $2, $3, $4, $5, 'received')
        RETURNING id
    """
    async with pool.acquire() as conn:
        return await conn.fetchval(query, event_type, source, project_id, meeting_id, json.dumps(details))

async def update_event_status(event_id: int, status: str, error_message: Optional[str] = None):
    pool = await get_pool()
    query = """
        UPDATE nerve_event_log 
        SET status = $1, error_message = $2
        WHERE id = $3
    """
    async with pool.acquire() as conn:
        await conn.execute(query, status, error_message, event_id)

async def insert_job_log(trigger_id: str, job_id: str, target_agent: str, target_endpoint: str,
                         success: bool, duration_ms: int, error_type: Optional[str], error_message: Optional[str],
                         response_payload: Optional[Dict[str, Any]]) -> int:
    """Insert into nerve_job_log. Returns log ID."""
    pool = await get_pool()
    query = """
        INSERT INTO nerve_job_log (trigger_id, job_id, target_agent, target_endpoint, success, duration_ms, error_type, error_message, response_payload, completed_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
        RETURNING id
    """
    async with pool.acquire() as conn:
        return await conn.fetchval(
            query, 
            trigger_id, job_id, target_agent, target_endpoint, 
            success, duration_ms, error_type, error_message, 
            json.dumps(response_payload) if response_payload else None
        )

async def update_agent_status(agent: str, success: bool, error: Optional[str] = None):
    """Update nerve_agent_status: increment consecutive_failures or reset."""
    pool = await get_pool()
    
    # First, ensure the agent exists in the DB.
    # Note: Using INSERT ... ON CONFLICT requires a unique constraint, which primary key provides.
    
    upsert_query = """
        INSERT INTO nerve_agent_status (agent, base_url, status)
        VALUES ($1, $2, 'unknown')
        ON CONFLICT (agent) DO NOTHING
    """
    base_url = settings.agent_urls.get(agent, "")
    
    async with pool.acquire() as conn:
        await conn.execute(upsert_query, agent, base_url)
        
        if success:
            query = """
                UPDATE nerve_agent_status 
                SET status = 'healthy', 
                    last_success = NOW(), 
                    consecutive_failures = 0, 
                    updated_at = NOW()
                WHERE agent = $1
            """
            await conn.execute(query, agent)
        else:
            query = """
                UPDATE nerve_agent_status 
                SET status = 'degraded', 
                    last_failure = NOW(), 
                    consecutive_failures = consecutive_failures + 1, 
                    updated_at = NOW()
                WHERE agent = $1
            """
            await conn.execute(query, agent)

async def update_provider_status(provider: str, status: str, error: Optional[str] = None):
    """Update nerve_provider_status."""
    pool = await get_pool()
    
    upsert_query = """
        INSERT INTO nerve_provider_status (provider, status, last_error)
        VALUES ($1, $2, $3)
        ON CONFLICT (provider) DO UPDATE 
        SET status = EXCLUDED.status,
            last_error = EXCLUDED.last_error,
            updated_at = NOW()
    """
    async with pool.acquire() as conn:
        await conn.execute(upsert_query, provider, status, error)

async def get_provider_status(provider: str) -> str:
    """Return current status: 'ok' | 'quota_exceeded' | 'credits_exhausted'."""
    pool = await get_pool()
    query = "SELECT status FROM nerve_provider_status WHERE provider = $1"
    async with pool.acquire() as conn:
        status = await conn.fetchval(query, provider)
        return status or 'ok'

async def get_all_agent_statuses() -> dict:
    """Return {agent: status} for health endpoint."""
    pool = await get_pool()
    query = "SELECT agent, status FROM nerve_agent_status"
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        return {row['agent']: row['status'] for row in rows}
