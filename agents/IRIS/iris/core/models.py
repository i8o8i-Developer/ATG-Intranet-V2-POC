from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


# ── Trigger Payload ────────────────────────────────────────────────

class TriggerPayload(BaseModel):
    meeting_id: str
    project_id: str
    r2_path: str
    transcript_status: Literal["completed", "processing"]
    triggered_at: datetime


# ── Rerun Payload ──────────────────────────────────────────────────

class RerunPayload(BaseModel):
    meeting_id: str
    pm_notes: str


# ── IRIS Event ─────────────────────────────────────────────────────

class IRISEvent(BaseModel):
    event: str = "iris.extraction.complete"
    meeting_id: str
    project_id: str
    confidence_score: float
    flagged: bool
    insights_path: str
    timestamp: datetime
    provider: str  # "anthropic" or "openai" — for A/B comparison


# ── Meeting Inputs ─────────────────────────────────────────────────

class MeetingMetadata(BaseModel):
    meeting_id: str
    project_id: str
    date: str
    meeting_type: str
    duration_minutes: int
    security_level: str
    organiser_id: str
    attendee_count_internal: int
    attendee_count_external: int
    language_mix: str
    series_id: Optional[str] = None
    client_id: Optional[str] = None


class Attendee(BaseModel):
    intranet_id: Optional[str] = None
    name: Optional[str] = None
    name_hash: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    type: Literal["internal", "external"]


class MeetingInputs(BaseModel):
    metadata: MeetingMetadata
    attendees: list[Attendee]
    transcript: str


# ── Extraction Result ──────────────────────────────────────────────

class ExtractionResult(BaseModel):
    insights_yaml: str
    confidence_score: float
    flagged: bool
    provider: str
    model: str
