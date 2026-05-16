from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from nerve.router.forwarder import forwarder, ForwarderResult
from nerve.scheduler.job_tracker import track_job
from nerve.errors import quota_monitor
from nerve.errors.handler import handle_failure
from nerve.config import settings

IST = pytz.timezone("Asia/Kolkata")
scheduler = AsyncIOScheduler(timezone=IST)

CRON_JOBS = [
    # DAILY Mon-Fri
    {"id": "night_process_job",     "hour": 2,  "minute": 0,  "dow": "mon-fri", "agent": "cell",   "endpoint": "/cell/jobs/night-process"},
    {"id": "morning_job",           "hour": 8,  "minute": 0,  "dow": "mon-fri", "agent": "cell",   "endpoint": "/cell/jobs/morning"},
    {"id": "cadence_monitor",       "hour": 9,  "minute": 0,  "dow": "mon-fri", "agent": "cortex", "endpoint": "/cortex/jobs/cadence-monitor"},
    {"id": "eod_coverage_check",    "hour": 20, "minute": 0,  "dow": "mon-fri", "agent": "cell",   "endpoint": "/cell/jobs/eod-coverage"},
    {"id": "blocker_aging_check",   "hour": 20, "minute": 5,  "dow": "mon-fri", "agent": "cortex", "endpoint": "/cortex/jobs/blocker-aging"},
    {"id": "milestone_drift_check", "hour": 20, "minute": 10, "dow": "mon-fri", "agent": "cortex", "endpoint": "/cortex/jobs/milestone-drift"},
    {"id": "stroma_capacity_sync",  "hour": 20, "minute": 15, "dow": "mon-fri", "agent": "stroma", "endpoint": "/stroma/jobs/capacity-sync"},
    {"id": "index_freshness_check", "hour": 23, "minute": 0,  "dow": "mon-fri", "agent": "cortex", "endpoint": "/cortex/jobs/index-freshness"},
    {"id": "eod_reminder_job",      "hour": 23, "minute": 30, "dow": "mon-fri", "agent": "cell",   "endpoint": "/cell/jobs/eod-reminder"},
    # MONDAY
    {"id": "weekly_aggregation",      "hour": 6,  "minute": 0,  "dow": "mon", "agent": "cortex", "endpoint": "/cortex/jobs/weekly-aggregation", "timeout": 300},
    {"id": "hot_lock_check",          "hour": 6,  "minute": 45, "dow": "mon", "agent": "cortex", "endpoint": "/cortex/jobs/hot-lock-check"},
    {"id": "weekly_plan_generation",  "hour": 7,  "minute": 15, "dow": "mon", "agent": "cortex", "endpoint": "/cortex/jobs/weekly-plan-generate", "timeout": 300},
    {"id": "weekly_plan_delivery",    "hour": 7,  "minute": 30, "dow": "mon", "agent": "cortex", "endpoint": "/cortex/jobs/weekly-plan-deliver"},
    # SUNDAY
    {"id": "renewal_signal_check",    "hour": 8,  "minute": 0,  "dow": "sun", "agent": "cortex", "endpoint": "/cortex/jobs/renewal-signal"},
]

async def trigger_agent_job(job_def: dict):
    """Generic trigger — used by ALL cron jobs AND manual triggers."""
    # Check if provider is down (skip instead of wasting quota)
    if await quota_monitor.should_skip_job(job_def):
        await track_job(job_def, ForwarderResult(
            success=False, trigger_id="skipped",
            error_type="provider_down", error_message="LLM provider quota exceeded — skipped"))
        return

    result = await forwarder.call_agent(
        agent=job_def["agent"], endpoint=job_def["endpoint"],
        payload={"job": job_def["id"], "triggered_by": "nerve_cron"},
        timeout=job_def.get("timeout", settings.default_job_timeout),
    )
    await track_job(job_def, result)

    if not result.success:
        await handle_failure(job_def, result)

async def start_scheduler():
    for job in CRON_JOBS:
        scheduler.add_job(
            trigger_agent_job,
            CronTrigger(hour=job["hour"], minute=job["minute"],
                        day_of_week=job["dow"], timezone=IST),
            id=job["id"], kwargs={"job_def": job}, replace_existing=True,
        )
    scheduler.start()

async def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
