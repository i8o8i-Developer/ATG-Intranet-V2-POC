from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

from cell.scheduler.jobs import (
    morning_job,
    night_process_job,
    eod_reminder_job,
)

async def eod_coverage_check_job():
    # Placeholder for a missing job function in cell.scheduler.jobs
    logger.info("eod_coverage_check_job executed (placeholder)")
    pass

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cell/jobs")

class JobPayload(BaseModel):
    job: str
    triggered_by: str

def verify_trigger(x_trigger_id: str, x_api_key: str):
    # In a real implementation we would verify the API key against settings
    # and maybe deduplicate based on x_trigger_id
    if not x_trigger_id:
        raise HTTPException(status_code=400, detail="Missing X-Trigger-ID")
    # For now we assume NERVE calls are trusted in this demo
    pass

import time

@router.post("/morning")
async def trigger_morning(payload: JobPayload, x_trigger_id: str = Header(None), x_api_key: str = Header(None)):
    verify_trigger(x_trigger_id, x_api_key)
    logger.info(f"Received NERVE trigger for morning_job (Trigger ID: {x_trigger_id})")
    start = time.monotonic()
    try:
        await morning_job()
        duration = int((time.monotonic() - start) * 1000)
        return {"success": True, "job": "morning_job", "duration_ms": duration, "error": None}
    except Exception as e:
        logger.exception("morning_job failed")
        duration = int((time.monotonic() - start) * 1000)
        return {"success": False, "job": "morning_job", "duration_ms": duration, "error": "job_failed", "error_message": str(e)}

@router.post("/night-process")
async def trigger_night_process(payload: JobPayload, x_trigger_id: str = Header(None), x_api_key: str = Header(None)):
    verify_trigger(x_trigger_id, x_api_key)
    logger.info(f"Received NERVE trigger for night_processing_job (Trigger ID: {x_trigger_id})")
    start = time.monotonic()
    try:
        await night_process_job()
        duration = int((time.monotonic() - start) * 1000)
        return {"success": True, "job": "night_process_job", "duration_ms": duration, "error": None}
    except Exception as e:
        logger.exception("night_processing_job failed")
        duration = int((time.monotonic() - start) * 1000)
        return {"success": False, "job": "night_process_job", "duration_ms": duration, "error": "job_failed", "error_message": str(e)}

@router.post("/eod-reminder")
async def trigger_eod_reminder(payload: JobPayload, x_trigger_id: str = Header(None), x_api_key: str = Header(None)):
    verify_trigger(x_trigger_id, x_api_key)
    logger.info(f"Received NERVE trigger for eod_reminder_job (Trigger ID: {x_trigger_id})")
    start = time.monotonic()
    try:
        await eod_reminder_job()
        duration = int((time.monotonic() - start) * 1000)
        return {"success": True, "job": "eod_reminder_job", "duration_ms": duration, "error": None}
    except Exception as e:
        logger.exception("eod_reminder_job failed")
        duration = int((time.monotonic() - start) * 1000)
        return {"success": False, "job": "eod_reminder_job", "duration_ms": duration, "error": "job_failed", "error_message": str(e)}

@router.post("/eod-coverage")
async def trigger_eod_coverage(payload: JobPayload, x_trigger_id: str = Header(None), x_api_key: str = Header(None)):
    verify_trigger(x_trigger_id, x_api_key)
    logger.info(f"Received NERVE trigger for eod_coverage_check_job (Trigger ID: {x_trigger_id})")
    start = time.monotonic()
    try:
        await eod_coverage_check_job()
        duration = int((time.monotonic() - start) * 1000)
        return {"success": True, "job": "eod_coverage_check_job", "duration_ms": duration, "error": None}
    except Exception as e:
        logger.exception("eod_coverage_check_job failed")
        duration = int((time.monotonic() - start) * 1000)
        return {"success": False, "job": "eod_coverage_check_job", "duration_ms": duration, "error": "job_failed", "error_message": str(e)}
