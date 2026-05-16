import httpx
import uuid
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from nerve.config import settings
from nerve.db.postgres import update_agent_status

@dataclass
class ForwarderResult:
    success: bool
    trigger_id: str
    status_code: int = 0
    response: Optional[dict] = None
    error_type: Optional[str] = None        # agent_down | timeout | quota_exceeded | ...
    error_message: Optional[str] = None
    duration_ms: int = 0

class AgentForwarder:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.default_job_timeout)

    async def call_agent(self, agent: str, endpoint: str,
                         payload: dict, timeout: Optional[int] = None) -> ForwarderResult:
        base_url = settings.agent_urls.get(agent)
        trigger_id = str(uuid.uuid4())
        
        if not base_url:
            return ForwarderResult(
                success=False, trigger_id=trigger_id,
                error_type="config_error",
                error_message=f"Agent '{agent}' URL not configured."
            )

        url = f"{base_url}{endpoint}"
        headers = {
            "X-API-Key": settings.nerve_api_key,
            "X-Trigger-ID": trigger_id,
        }

        try:
            start = time.monotonic()
            resp = await self.client.post(
                url, 
                json=payload, 
                headers=headers,
                timeout=timeout or settings.default_job_timeout
            )
            elapsed = int((time.monotonic() - start) * 1000)
            
            # The agent responds with a JSON object containing {success, error, error_message}
            try:
                data = resp.json()
            except ValueError:
                # Agent returned non-JSON
                data = {"error": "invalid_json_response", "error_message": resp.text}
                
            success = data.get("success", resp.status_code < 400)
            error_type = data.get("error") if not success else None

            await update_agent_status(agent, success=success, error=error_type)
            return ForwarderResult(
                success=success, trigger_id=trigger_id,
                status_code=resp.status_code, response=data,
                error_type=error_type, duration_ms=elapsed,
                error_message=data.get("error_message")
            )

        except httpx.ConnectError:
            await update_agent_status(agent, success=False, error="agent_down")
            return ForwarderResult(
                success=False, trigger_id=trigger_id,
                error_type="agent_down",
                error_message=f"{agent} unreachable at {url}"
            )

        except httpx.TimeoutException:
            await update_agent_status(agent, success=False, error="timeout")
            return ForwarderResult(
                success=False, trigger_id=trigger_id,
                error_type="timeout",
                error_message=f"{agent} timed out"
            )

forwarder = AgentForwarder()
