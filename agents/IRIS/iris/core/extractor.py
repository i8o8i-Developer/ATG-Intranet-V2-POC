"""
Core extraction pipeline.
Reads R2 artifacts → calls LLM → validates YAML → returns ExtractionResult.
"""

import yaml
import logging
from typing import Optional

from iris.core.models import MeetingInputs, MeetingMetadata, Attendee, ExtractionResult
from iris.llm.client import llm_client
from iris.prompts.system import SYSTEM_PROMPT
from iris.prompts.templates import build_user_message
from iris.storage.r2_client import r2

logger = logging.getLogger(__name__)


VALID_MEETING_TYPES = {
    "standup", "sprint-planning", "client-call", "milestone-review",
    "cross-dept", "design-review", "sales-bd", "hr", "company-allhands", "vendor",
}


def load_meeting_inputs(r2_path: str, r2_client=None) -> MeetingInputs:
    """Read all meeting artifacts from R2 (or mock) storage."""
    logger.info(f"Loading meeting inputs from: {r2_path}")
    _r2 = r2_client or r2

    raw_metadata = _r2.read_json(r2_path, "metadata.json")
    raw_attendees = _r2.read_json(r2_path, "attendees.json")
    transcript = _r2.read_text(r2_path, "transcript.txt")

    metadata = MeetingMetadata(**raw_metadata)
    attendees = [Attendee(**a) for a in raw_attendees]

    return MeetingInputs(
        metadata=metadata,
        attendees=attendees,
        transcript=transcript,
    )


def _strip_fences(raw: str) -> str:
    """Strip markdown code fences if present."""
    clean = raw.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing fence
        clean = "\n".join(lines)
    return clean


def _repair_yaml(text: str) -> str:
    """
    Attempt to fix common LLM YAML issues:
    - Unquoted string values containing colons (e.g. velocity_note: foo: bar)
    """
    import re
    repaired_lines = []
    # Matches: key: value where value contains an unquoted colon not followed by \n
    pattern = re.compile(r'^(\s*[\w_]+:\s)(.+:.+)$')
    for line in text.split("\n"):
        m = pattern.match(line)
        if m:
            key_part = m.group(1)
            val_part = m.group(2).strip()
            # Skip if already quoted or is a YAML special (true/false/null/number)
            if not (val_part.startswith('"') or val_part.startswith("'")
                    or val_part in ("true", "false", "null")
                    or val_part.lstrip("-").isdigit()):
                val_part = '"' + val_part.replace('"', '\\"') + '"'
                line = key_part + val_part
        repaired_lines.append(line)
    return "\n".join(repaired_lines)


def _parse_and_validate_yaml(raw: str, meeting_id: str) -> tuple[dict, str]:
    """
    Parse LLM output as YAML.
    Strips markdown fences, attempts repair on common issues.
    Returns (parsed_dict, clean_yaml_string).
    """
    clean = _strip_fences(raw)

    try:
        parsed = yaml.safe_load(clean)
    except yaml.YAMLError:
        # Attempt repair on colon-in-value issues
        logger.warning(f"[{meeting_id}] YAML parse failed, attempting repair...")
        clean = _repair_yaml(clean)
        try:
            parsed = yaml.safe_load(clean)
        except yaml.YAMLError as e:
            logger.error(f"[{meeting_id}] YAML repair failed: {e}")
            raise ValueError(f"LLM returned invalid YAML: {e}")

    if not isinstance(parsed, dict):
        raise ValueError(f"Expected YAML dict, got {type(parsed)}")

    return parsed, clean


def _extract_confidence(parsed: dict) -> float:
    """Pull extraction_confidence from parsed YAML, clamp to [0.0, 1.0]."""
    raw = parsed.get("extraction_confidence", 0.5)
    try:
        score = float(raw)
    except (TypeError, ValueError):
        score = 0.5
    return max(0.0, min(1.0, score))


def run_extraction(
    r2_path: str,
    meeting_id: str,
    pm_notes: str = "",
    provider_override: Optional[str] = None,
    r2_client=None,
) -> ExtractionResult:
    """
    Full extraction pipeline for one meeting.

    Args:
        r2_path: R2 folder path for this meeting.
        meeting_id: Meeting identifier (used for logging).
        pm_notes: Optional PM correction notes (for rerun).
        provider_override: Force a specific LLM provider for this call.

    Returns:
        ExtractionResult with insights_yaml, confidence_score, flagged, provider, model.
    """
    # Use override or default client
    from iris.llm.client import LLMClient
    client = LLMClient(provider=provider_override) if provider_override else llm_client

    logger.info(f"[{meeting_id}] Starting extraction with {client.provider}/{client.model_name}")

    # 1. Load inputs
    inputs = load_meeting_inputs(r2_path, r2_client=r2_client)

    meeting_type = inputs.metadata.meeting_type
    if meeting_type not in VALID_MEETING_TYPES:
        logger.warning(f"[{meeting_id}] Unknown meeting_type '{meeting_type}' — using BASE only")

    # 2. Build prompt
    user_message = build_user_message(inputs, pm_notes=pm_notes)

    # 3. Call LLM
    logger.info(f"[{meeting_id}] Calling LLM...")
    raw_output = client.complete(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=4096,
        temperature=0.1,
    )

    # 4. Parse & validate YAML
    parsed, clean_yaml = _parse_and_validate_yaml(raw_output, meeting_id)

    # 5. Extract confidence
    confidence = _extract_confidence(parsed)
    flagged = confidence < 0.6

    logger.info(
        f"[{meeting_id}] Extraction complete — confidence={confidence:.2f}, flagged={flagged}"
    )

    return ExtractionResult(
        insights_yaml=clean_yaml,
        confidence_score=confidence,
        flagged=flagged,
        provider=client.provider,
        model=client.model_name,
    )
