import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

# Setup mock config before anything imports it
import sys
from pydantic import BaseModel

class MockSettings(BaseModel):
    database_url: str = "postgresql://mock"
    agent_urls: dict = {"cell": "http://mock-cell", "iris": "http://mock-iris"}

mock_settings = MockSettings()
sys.modules['nerve.config'] = MagicMock()
sys.modules['nerve.config'].settings = mock_settings

from nerve.db.postgres import (
    init_pool, close_pool, get_pool, log_event, update_event_status,
    insert_job_log, update_agent_status, update_provider_status,
    get_provider_status, get_all_agent_statuses
)
import nerve.db.postgres as pg

class TestDatabaseFunctions(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Reset the global pool before each test
        pg._pool = None
        
        # Create a mock connection and pool
        self.mock_conn = AsyncMock()
        self.mock_pool = MagicMock()
        self.mock_pool.close = AsyncMock()
        
        # When pool.acquire() is used as an async context manager, 
        # it needs to return the mock connection
        acquire_ctx = AsyncMock()
        acquire_ctx.__aenter__.return_value = self.mock_conn
        self.mock_pool.acquire.return_value = acquire_ctx
        
    async def asyncTearDown(self):
        pg._pool = None

    @patch('nerve.db.postgres.asyncpg.create_pool', new_callable=AsyncMock)
    async def test_init_and_close_pool(self, mock_create_pool):
        mock_create_pool.return_value = self.mock_pool
        
        # Test get_pool raises when not initialized
        with self.assertRaisesRegex(Exception, "Database pool not initialized"):
            await get_pool()
            
        # Initialize
        await init_pool()
        mock_create_pool.assert_called_once_with(
            "postgresql://mock", min_size=2, max_size=10
        )
        
        # Now get_pool should work
        pool = await get_pool()
        self.assertEqual(pool, self.mock_pool)
        
        # Close
        await close_pool()
        self.mock_pool.close.assert_called_once()

    async def test_log_event(self):
        pg._pool = self.mock_pool
        self.mock_conn.fetchval.return_value = 123
        
        event_id = await log_event(
            event_type="test_event",
            source="test_source",
            project_id="proj1",
            meeting_id="meet1",
            details={"key": "value"}
        )
        
        self.assertEqual(event_id, 123)
        self.mock_conn.fetchval.assert_called_once()
        args, _ = self.mock_conn.fetchval.call_args
        self.assertIn("INSERT INTO nerve_event_log", args[0])
        self.assertEqual(args[1], "test_event")
        self.assertEqual(args[5], '{"key": "value"}')

    async def test_update_event_status(self):
        pg._pool = self.mock_pool
        
        await update_event_status(event_id=123, status="failed", error_message="oops")
        
        self.mock_conn.execute.assert_called_once()
        args, _ = self.mock_conn.execute.call_args
        self.assertIn("UPDATE nerve_event_log", args[0])
        self.assertEqual(args[1], "failed")
        self.assertEqual(args[2], "oops")
        self.assertEqual(args[3], 123)

    async def test_insert_job_log(self):
        pg._pool = self.mock_pool
        self.mock_conn.fetchval.return_value = 456
        
        log_id = await insert_job_log(
            trigger_id="trig1", job_id="job1", target_agent="cell",
            target_endpoint="/ep", success=True, duration_ms=150,
            error_type=None, error_message=None, response_payload={"res": "ok"}
        )
        
        self.assertEqual(log_id, 456)
        self.mock_conn.fetchval.assert_called_once()
        args, _ = self.mock_conn.fetchval.call_args
        self.assertIn("INSERT INTO nerve_job_log", args[0])
        self.assertEqual(args[1], "trig1")
        self.assertEqual(args[9], '{"res": "ok"}')

    async def test_update_agent_status_success(self):
        pg._pool = self.mock_pool
        
        await update_agent_status("cell", success=True)
        
        # 1 call for upsert (INSERT ... ON CONFLICT), 1 call for UPDATE success
        self.assertEqual(self.mock_conn.execute.call_count, 2)
        
        upsert_args = self.mock_conn.execute.call_args_list[0][0]
        self.assertIn("INSERT INTO nerve_agent_status", upsert_args[0])
        self.assertEqual(upsert_args[1], "cell")
        self.assertEqual(upsert_args[2], "http://mock-cell")
        
        update_args = self.mock_conn.execute.call_args_list[1][0]
        self.assertIn("status = 'healthy'", update_args[0])

    async def test_update_agent_status_failure(self):
        pg._pool = self.mock_pool
        
        await update_agent_status("cell", success=False, error="agent_down")
        
        self.assertEqual(self.mock_conn.execute.call_count, 2)
        
        update_args = self.mock_conn.execute.call_args_list[1][0]
        self.assertIn("status = 'degraded'", update_args[0])
        self.assertIn("consecutive_failures = consecutive_failures + 1", update_args[0])

    async def test_update_provider_status(self):
        pg._pool = self.mock_pool
        
        await update_provider_status("openai", "quota_exceeded", "out of credits")
        
        self.mock_conn.execute.assert_called_once()
        args, _ = self.mock_conn.execute.call_args
        self.assertIn("INSERT INTO nerve_provider_status", args[0])
        self.assertEqual(args[1], "openai")
        self.assertEqual(args[2], "quota_exceeded")
        self.assertEqual(args[3], "out of credits")

    async def test_get_provider_status(self):
        pg._pool = self.mock_pool
        self.mock_conn.fetchval.return_value = "quota_exceeded"
        
        status = await get_provider_status("openai")
        
        self.assertEqual(status, "quota_exceeded")
        self.mock_conn.fetchval.assert_called_once()
        
        # Test fallback when status is None
        self.mock_conn.fetchval.return_value = None
        status = await get_provider_status("anthropic")
        self.assertEqual(status, "ok")

    async def test_get_all_agent_statuses(self):
        pg._pool = self.mock_pool
        self.mock_conn.fetch.return_value = [
            {"agent": "cell", "status": "healthy"},
            {"agent": "iris", "status": "degraded"}
        ]
        
        statuses = await get_all_agent_statuses()
        
        self.assertEqual(statuses, {"cell": "healthy", "iris": "degraded"})
        self.mock_conn.fetch.assert_called_once()

if __name__ == '__main__':
    unittest.main()
