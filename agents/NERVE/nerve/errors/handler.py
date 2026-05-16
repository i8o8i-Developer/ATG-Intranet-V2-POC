import asyncio
from nerve.router.forwarder import forwarder, ForwarderResult
from nerve.scheduler.job_tracker import track_job
from nerve.errors import quota_monitor
from nerve.alerts.slack import slack_alert
from nerve.config import settings

RETRY_POLICY = {
    "agent_down":        {"max_retries": 3, "backoff": [30, 120, 600]},
    "timeout":           {"max_retries": 1, "backoff": [120]},
    "job_failed":        {"max_retries": 1, "backoff": [300]},
    "db_timeout":        {"max_retries": 1, "backoff": [120]},
    "quota_exceeded":    {"max_retries": 0},   # NEVER retry
    "credits_exhausted": {"max_retries": 0},   # NEVER retry
}

async def handle_failure(job_def: dict, result: ForwarderResult):
    error_type = result.error_type or "job_failed"
    policy = RETRY_POLICY.get(error_type, RETRY_POLICY["job_failed"])

    # Quota/credit -> update provider status, alert, don't retry
    if error_type in ("quota_exceeded", "credits_exhausted"):
        await quota_monitor.mark_provider_down(job_def["agent"], error_type)
        await slack_alert(f"🚨 {error_type} on {job_def['agent']} — {result.error_message}")
        return

    # Retry with backoff
    for attempt, delay in enumerate(policy["backoff"][:policy["max_retries"]]):
        await asyncio.sleep(delay)
        retry_result = await forwarder.call_agent(
            job_def["agent"], job_def["endpoint"],
            payload={"job": job_def["id"], "triggered_by": "nerve_retry"},
            timeout=job_def.get("timeout", settings.default_job_timeout),
        )
        await track_job(job_def, retry_result)
        if retry_result.success:
            return

    # All retries exhausted
    await slack_alert(
        f"⚠ {job_def['id']} failed on {job_def['agent']} after "
        f"{policy['max_retries']} retries — {result.error_message}")
