import logging

from nerve.router.forwarder import forwarder
from nerve.db.postgres import update_event_status
from nerve.alerts.slack import slack_alert

logger = logging.getLogger(__name__)

async def route_event(payload, event_id: int):
    """Routes incoming events to the appropriate agents."""
    logger.info(f"Routing event {payload.event} with ID {event_id}")
    
    try:
        if payload.event == "iris.extraction.complete":
            # Fan out to CELL and CORTEX
            import asyncio
            cell_call = forwarder.call_agent("cell", "/cell/ingest-nerve", payload.model_dump())
            cortex_call = forwarder.call_agent("cortex", "/cortex/ingest-nerve", payload.model_dump())
            
            results = await asyncio.gather(cell_call, cortex_call, return_exceptions=True)
            
            failed = []
            for res, target in zip(results, ["CELL", "CORTEX"]):
                if isinstance(res, Exception):
                    failed.append(f"{target} exception: {str(res)}")
                elif not res.success:
                    failed.append(f"{target} failed: {res.error_message}")
                    
            if failed:
                err = " | ".join(failed)
                await slack_alert(f"Fan-out failed for event {event_id}: {err}")
                await update_event_status(event_id, "failed", err)
            else:
                await update_event_status(event_id, "completed")
                
        else:
            logger.warning(f"Unknown event type: {payload.event}")
            await update_event_status(event_id, "ignored", "Unknown event type")
            
    except Exception as e:
        logger.exception(f"Error routing event {event_id}")
        await slack_alert(f"Internal error routing event {event_id}: {e}")
        await update_event_status(event_id, "error", str(e))
