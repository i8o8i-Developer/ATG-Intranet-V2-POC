from fastapi import APIRouter, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from nerve.config import settings
from nerve.db.postgres import log_event
from nerve.router.event_router import route_event

router = APIRouter(prefix="/nerve")

class EventPayload(BaseModel):
    event: str                          # meeting.saved | iris.extraction.complete | etc
    meeting_id: Optional[str] = None
    project_id: Optional[str] = None
    
    class Config:
        extra = "allow"                 # pass through all extra fields

@router.post("/event", status_code=202)
async def receive_event(payload: EventPayload, background_tasks: BackgroundTasks,
                        x_api_key: str = Header(None)):
    if x_api_key != settings.nerve_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    event_id = await log_event(
        event_type=payload.event, 
        source="external",
        project_id=payload.project_id, 
        meeting_id=payload.meeting_id,
        details=payload.model_dump(),
    )
    
    background_tasks.add_task(route_event, payload, event_id)
    return {"status": "accepted", "event_id": event_id}
