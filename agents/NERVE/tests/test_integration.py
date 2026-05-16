import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

# Mock settings
import sys
from pydantic import BaseModel

class MockSettings(BaseModel):
    database_url: str = "postgresql://mock"
    nerve_api_key: str = "dev-nerve-key"
    default_job_timeout: int = 60
    slack_bot_token: str = ""
    slack_admin_channel: str = ""
    agent_urls: dict = {
        "iris": "http://mock-iris",
        "cell": "http://mock-cell",
        "cortex": "http://mock-cortex",
        "stroma": "http://mock-stroma",
    }

mock_settings = MockSettings()
sys.modules['nerve.config'] = MagicMock()
sys.modules['nerve.config'].settings = mock_settings

from nerve.router.forwarder import ForwarderResult
from nerve.router.event_router import route_event
from nerve.scheduler.cron_orchestrator import trigger_agent_job
from nerve.errors.handler import handle_failure

class TestNERVEIntegration(unittest.IsolatedAsyncioTestCase):

    @patch('nerve.router.event_router.update_event_status', new_callable=AsyncMock)
    @patch('nerve.router.event_router.forwarder.call_agent', new_callable=AsyncMock)
    @patch('nerve.router.event_router.slack_alert', new_callable=AsyncMock)
    async def test_event_routing_meeting_saved(self, mock_slack, mock_call, mock_update):
        # 1. Test meeting.saved triggers IRIS
        mock_call.return_value = ForwarderResult(success=True, trigger_id="123")
        
        class MockPayload:
            event = "meeting.saved"
            def model_dump(self): return {"event": "meeting.saved"}
            
        await route_event(MockPayload(), 1)
        mock_call.assert_called_once_with(agent="iris", endpoint="/iris/trigger", payload={"event": "meeting.saved"})
        mock_update.assert_called_once_with(1, "completed")

    @patch('nerve.router.event_router.update_event_status', new_callable=AsyncMock)
    @patch('nerve.router.event_router.forwarder.call_agent', new_callable=AsyncMock)
    @patch('nerve.router.event_router.slack_alert', new_callable=AsyncMock)
    async def test_event_routing_extraction_complete(self, mock_slack, mock_call, mock_update):
        # 2. Test extraction.complete fans out to CELL and CORTEX
        mock_call.return_value = ForwarderResult(success=True, trigger_id="456")
        
        class MockPayload:
            event = "iris.extraction.complete"
            def model_dump(self): return {"event": "iris.extraction.complete"}
            
        await route_event(MockPayload(), 2)
        
        self.assertEqual(mock_call.call_count, 2)
        mock_update.assert_called_once_with(2, "completed")

    @patch('nerve.scheduler.cron_orchestrator.track_job', new_callable=AsyncMock)
    @patch('nerve.scheduler.cron_orchestrator.handle_failure', new_callable=AsyncMock)
    @patch('nerve.scheduler.cron_orchestrator.forwarder.call_agent', new_callable=AsyncMock)
    @patch('nerve.scheduler.cron_orchestrator.quota_monitor.should_skip_job', new_callable=AsyncMock)
    async def test_cron_trigger_success(self, mock_skip, mock_call, mock_fail, mock_track):
        # 3. Test successful cron job trigger
        mock_skip.return_value = False
        mock_call.return_value = ForwarderResult(success=True, trigger_id="789")
        
        job_def = {"id": "morning_job", "agent": "cell", "endpoint": "/cell/jobs/morning"}
        await trigger_agent_job(job_def)
        
        mock_call.assert_called_once()
        mock_track.assert_called_once()
        mock_fail.assert_not_called()

    @patch('nerve.errors.handler.forwarder.call_agent', new_callable=AsyncMock)
    @patch('nerve.errors.handler.track_job', new_callable=AsyncMock)
    @patch('nerve.errors.handler.slack_alert', new_callable=AsyncMock)
    async def test_error_handler_agent_down(self, mock_slack, mock_track, mock_call):
        # 4. Test agent_down retries 3 times
        # Mock asyncio.sleep so the test runs instantly
        with patch('asyncio.sleep', new_callable=AsyncMock):
            mock_call.return_value = ForwarderResult(success=False, trigger_id="fail", error_type="agent_down")
            
            job_def = {"id": "morning_job", "agent": "cell", "endpoint": "/cell/jobs/morning"}
            res = ForwarderResult(success=False, trigger_id="fail", error_type="agent_down", error_message="conn refused")
            
            await handle_failure(job_def, res)
            
            # Should have retried 3 times
            self.assertEqual(mock_call.call_count, 3)
            # Should have alerted after giving up
            mock_slack.assert_called_once()

    @patch('nerve.errors.handler.quota_monitor.mark_provider_down', new_callable=AsyncMock)
    @patch('nerve.errors.handler.slack_alert', new_callable=AsyncMock)
    @patch('nerve.errors.handler.forwarder.call_agent', new_callable=AsyncMock)
    async def test_error_handler_quota_exceeded(self, mock_call, mock_slack, mock_mark):
        # 5. Test quota_exceeded halts and does not retry
        job_def = {"id": "morning_job", "agent": "cell", "endpoint": "/cell/jobs/morning"}
        res = ForwarderResult(success=False, trigger_id="quota", error_type="quota_exceeded", error_message="out of tokens")
        
        await handle_failure(job_def, res)
        
        mock_call.assert_not_called()  # No retries
        mock_mark.assert_called_once_with("cell", "quota_exceeded")
        mock_slack.assert_called_once()

if __name__ == '__main__':
    unittest.main()
