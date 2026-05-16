from nerve.router.forwarder import ForwarderResult
from nerve.db.postgres import insert_job_log

async def track_job(job_def: dict, result: ForwarderResult):
    """Insert into nerve_job_log."""
    await insert_job_log(
        trigger_id=result.trigger_id,
        job_id=job_def["id"],
        target_agent=job_def["agent"],
        target_endpoint=job_def["endpoint"],
        success=result.success,
        duration_ms=result.duration_ms,
        error_type=result.error_type,
        error_message=result.error_message,
        response_payload=result.response,
    )
