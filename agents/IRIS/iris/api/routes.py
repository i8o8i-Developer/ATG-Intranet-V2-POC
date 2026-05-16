"""
IRIS FastAPI routes.
POST /iris/trigger  — main extraction trigger
POST /iris/rerun    — PM-corrected re-extraction
GET  /iris/health   — health check
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from iris.core.models import TriggerPayload, RerunPayload, IRISEvent
from iris.core.extractor import run_extraction
from iris.core.emitter import emit_extraction_complete
from iris.storage.r2_client import r2
from iris.llm.client import llm_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/iris")


@router.post("/trigger", response_model=IRISEvent)
def trigger_extraction(
    payload: TriggerPayload,
    provider: Optional[str] = Query(
        default=None,
        description="Override LLM provider for this request: 'anthropic' or 'openai'",
    ),
):
    """
    Main IRIS trigger. Fired when a meeting record is fully saved.
    Rejects requests where transcript_status != completed.
    """
    if payload.transcript_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"IRIS only triggers on completed transcripts. "
                   f"Current status: {payload.transcript_status}",
        )

    logger.info(
        f"Trigger received — meeting={payload.meeting_id}, "
        f"project={payload.project_id}, provider_override={provider}"
    )

    try:
        result = run_extraction(
            r2_path=payload.r2_path,
            meeting_id=payload.meeting_id,
            provider_override=provider,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Extraction failed for {payload.meeting_id}")
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")

    # Write insights.yaml to R2
    insights_path = r2.write_text(
        payload.r2_path, "insights.yaml", result.insights_yaml
    )

    # Emit event to NERVE
    event = emit_extraction_complete(
        meeting_id=payload.meeting_id,
        project_id=payload.project_id,
        confidence_score=result.confidence_score,
        flagged=result.flagged,
        insights_path=insights_path,
        provider=result.provider,
    )

    return event


@router.post("/rerun", response_model=IRISEvent)
def rerun_extraction(
    payload: RerunPayload,
    provider: Optional[str] = Query(
        default=None,
        description="Override LLM provider for this rerun: 'anthropic' or 'openai'",
    ),
):
    """
    PM-corrected re-extraction entrypoint.
    Reads PM notes, re-extracts from same artifacts, overwrites insights.yaml.
    """
    logger.info(f"Rerun triggered — meeting={payload.meeting_id}")

    # Locate the R2 path by scanning mock storage for this meeting_id
    r2_path, project_id = _find_meeting_r2_path(payload.meeting_id)
    if not r2_path:
        raise HTTPException(
            status_code=404,
            detail=f"No R2 artifacts found for meeting_id={payload.meeting_id}",
        )

    try:
        result = run_extraction(
            r2_path=r2_path,
            meeting_id=payload.meeting_id,
            pm_notes=payload.pm_notes,
            provider_override=provider,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Rerun failed for {payload.meeting_id}")
        raise HTTPException(status_code=500, detail=f"Rerun error: {str(e)}")

    # Overwrite insights.yaml
    insights_path = r2.write_text(r2_path, "insights.yaml", result.insights_yaml)

    # Emit updated event
    event = emit_extraction_complete(
        meeting_id=payload.meeting_id,
        project_id=project_id,
        confidence_score=result.confidence_score,
        flagged=result.flagged,
        insights_path=insights_path,
        provider=result.provider,
    )

    return event


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "iris",
        "llm": llm_client.info(),
    }


def _find_meeting_r2_path(meeting_id: str) -> tuple[Optional[str], Optional[str]]:
    """
    Scan mock R2 storage to locate the r2_path for a given meeting_id.
    Reads metadata.json in each meeting folder.
    Returns (r2_path, project_id) or (None, None) if not found.
    """
    import json
    from pathlib import Path
    from iris.config import settings

    base = Path(settings.r2_mock_base_path)
    if not base.exists():
        return None, None

    for metadata_file in base.rglob("metadata.json"):
        try:
            data = json.loads(metadata_file.read_text())
            if data.get("meeting_id") == meeting_id:
                # r2_path is relative to base
                folder = metadata_file.parent
                r2_relative = "/" + str(folder.relative_to(base))
                return r2_relative, data.get("project_id")
        except Exception:
            continue

    return None, None
