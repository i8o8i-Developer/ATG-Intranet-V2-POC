"""
Tests for the core extraction pipeline.
These make real LLM calls — run with actual API keys.
Use pytest -m "not live" to skip LLM tests in CI without keys.
"""

import pytest
import yaml
import os

from iris.storage.r2_client import R2Client
from iris.core.extractor import run_extraction

# Import all meeting fixtures
from tests.fixtures.meetings import (
    standup,
    client_call,
    sprint_planning,
    milestone_review,
    cross_dept,
    design_review,
    sales_bd,
    hr_meeting,
    allhands,
    vendor_meeting,
)

# ── Helpers ───────────────────────────────────────────────────────

def seed_and_extract(tmp_path, fixture_module, provider="anthropic"):
    r2 = R2Client(base_path=str(tmp_path))
    meta = fixture_module.METADATA
    r2_path = f"/projects/{meta['project_id']}/{meta['date']}_{meta['meeting_id']}"
    r2.seed_meeting(r2_path, meta, fixture_module.ATTENDEES, fixture_module.TRANSCRIPT)
    result = run_extraction(
        r2_path=r2_path,
        meeting_id=meta["meeting_id"],
        provider_override=provider,
        r2_client=r2,
    )
    parsed = yaml.safe_load(result.insights_yaml)
    return result, parsed


def assert_base_fields(parsed, expected_meeting_type, expected_security_level):
    """Assert all required BASE fields are present and correct."""
    assert parsed.get("meeting_id") is not None
    assert parsed.get("project_id") is not None
    assert parsed.get("date") is not None
    assert parsed.get("meeting_type") == expected_meeting_type
    assert parsed.get("security_level") == expected_security_level
    assert parsed.get("extraction_confidence") is not None
    assert 0.0 <= float(parsed["extraction_confidence"]) <= 1.0
    assert "extraction_review" in parsed
    assert "follow_up_type" in parsed
    assert parsed.get("consumer_level") is not None
    assert "tags" in parsed
    assert parsed.get("previous_meeting_ref") is None  # Never set by IRIS


# ── Meeting type tests ────────────────────────────────────────────

@pytest.mark.live
def test_standup_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, standup)
    assert_base_fields(parsed, "standup", "INTERNAL")
    assert "standup" in parsed
    sd = parsed["standup"]
    assert "all_green" in sd
    assert isinstance(sd.get("blocked_today"), list)
    assert isinstance(sd.get("silent_members"), list)
    # Rohit should be blocked
    blocked_ids = [b.get("person_id") for b in sd.get("blocked_today", [])]
    assert "p-rohit-002" in blocked_ids
    # Dev should be silent
    silent_ids = [s.get("person_id") for s in sd.get("silent_members", [])]
    assert "p-dev-003" in silent_ids
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_client_call_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, client_call)
    assert_base_fields(parsed, "client-call", "INTERNAL")
    assert "client" in parsed
    cl = parsed["client"]
    assert cl.get("sentiment") in ("positive", "neutral", "negative", "mixed")
    assert isinstance(cl.get("commitments"), list)
    assert cl.get("deadline_pressure") is True
    assert cl.get("client_id") == "CLIENT-ACME-001"
    assert parsed.get("consumer_level") == "pm"
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_sprint_planning_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, sprint_planning)
    assert_base_fields(parsed, "sprint-planning", "INTERNAL")
    assert "internal" in parsed
    sp = parsed["internal"]
    assert isinstance(sp.get("decisions"), list)
    assert isinstance(sp.get("deferred_items"), list)
    # Reporting dashboard should be deferred/out of scope
    decisions_text = " ".join([d.get("text", "") for d in sp.get("decisions", [])])
    scope_text = " ".join([s.get("item", "") for s in sp.get("scope_adjustments", [])])
    assert "dashboard" in (decisions_text + scope_text).lower()
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_milestone_review_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, milestone_review)
    assert_base_fields(parsed, "milestone-review", "INTERNAL")
    assert "milestone_review" in parsed
    mr = parsed["milestone_review"]
    assert mr.get("acceptance_status") in ("accepted", "partial", "rejected")
    assert isinstance(mr.get("sign_offs"), list)
    assert mr.get("payment_trigger") is False
    assert mr.get("next_milestone_at_risk") is True
    assert parsed.get("consumer_level") == "dept-head"
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_cross_dept_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, cross_dept)
    assert_base_fields(parsed, "cross-dept", "INTERNAL")
    assert "cross_dept" in parsed
    cd = parsed["cross_dept"]
    assert isinstance(cd.get("departments_present"), list)
    assert cd.get("dependency_status") is not None
    assert isinstance(cd.get("unresolved_items"), list)
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_design_review_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, design_review)
    assert_base_fields(parsed, "design-review", "INTERNAL")
    assert "design_review" in parsed
    dr = parsed["design_review"]
    assert dr.get("approval_status") in ("approved", "conditional", "rejected")
    assert isinstance(dr.get("feedback_items"), list)
    assert dr.get("blocking_development") is True
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_sales_bd_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, sales_bd)
    assert_base_fields(parsed, "sales-bd", "CONFIDENTIAL")
    assert "sales_bd" in parsed
    sb = parsed["sales_bd"]
    assert sb.get("meeting_subtype") is not None
    assert "qualification_signals" in sb
    # Decision maker was NOT present in this meeting
    assert sb["qualification_signals"].get("decision_maker_present") is False
    # Budget was confirmed
    assert sb["qualification_signals"].get("budget_confirmed") is True
    # consumer_level should be hr-only because CONFIDENTIAL
    assert parsed.get("consumer_level") == "hr-only"
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_hr_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, hr_meeting)
    assert_base_fields(parsed, "hr", "CONFIDENTIAL")
    assert "hr" in parsed
    hr = parsed["hr"]
    assert hr.get("subtype") is not None
    assert isinstance(hr.get("decisions"), list)
    assert isinstance(hr.get("action_items"), list)
    # consumer_level must be hr-only for hr meetings
    assert parsed.get("consumer_level") == "hr-only"
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_allhands_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, allhands)
    assert_base_fields(parsed, "company-allhands", "INTERNAL")
    assert "allhands" in parsed
    ah = parsed["allhands"]
    assert isinstance(ah.get("announcements"), list)
    assert ah.get("concerns_raised") is True
    # consumer_level should be director for allhands
    assert parsed.get("consumer_level") == "director"
    assert result.confidence_score > 0.5


@pytest.mark.live
def test_vendor_extraction(tmp_path):
    result, parsed = seed_and_extract(tmp_path, vendor_meeting)
    assert_base_fields(parsed, "vendor", "INTERNAL")
    assert "vendor" in parsed
    vd = parsed["vendor"]
    assert isinstance(vd.get("commitments"), list)
    assert vd.get("cost_implication") is True
    assert result.confidence_score > 0.5


# ── Cross-provider comparison test ───────────────────────────────

@pytest.mark.live
def test_provider_comparison_standup(tmp_path):
    """
    Run standup extraction with both providers and compare structure.
    Both should produce valid YAML with the same top-level keys.
    """
    r2 = R2Client(base_path=str(tmp_path))
    meta = standup.METADATA
    r2_path = f"/projects/{meta['project_id']}/{meta['date']}_{meta['meeting_id']}"
    r2.seed_meeting(r2_path, meta, standup.ATTENDEES, standup.TRANSCRIPT)

    from iris.config import settings
    if not settings.openai_api_key:
        pytest.skip("OPENAI_API_KEY not set")

    result_anthropic = run_extraction(r2_path, meta["meeting_id"], provider_override="anthropic", r2_client=r2)
    result_openai = run_extraction(r2_path, meta["meeting_id"], provider_override="openai", r2_client=r2)

    parsed_a = yaml.safe_load(result_anthropic.insights_yaml)
    parsed_o = yaml.safe_load(result_openai.insights_yaml)

    # Both should have the same top-level structural keys
    assert "standup" in parsed_a, "Anthropic output missing standup section"
    assert "standup" in parsed_o, "OpenAI output missing standup section"

    print(f"\n[Anthropic] confidence={result_anthropic.confidence_score:.2f}")
    print(f"[OpenAI]    confidence={result_openai.confidence_score:.2f}")


# ── Rerun test ────────────────────────────────────────────────────

@pytest.mark.live
def test_rerun_with_pm_notes(tmp_path):
    """Rerun should incorporate PM notes into the extraction."""
    r2 = R2Client(base_path=str(tmp_path))
    meta = client_call.METADATA
    r2_path = f"/projects/{meta['project_id']}/{meta['date']}_{meta['meeting_id']}"
    r2.seed_meeting(r2_path, meta, client_call.ATTENDEES, client_call.TRANSCRIPT)

    pm_notes = (
        "The blocker was actually resolved. Client confirmed credentials will arrive "
        "Thursday not Friday. Sentiment should be mixed not negative."
    )

    result = run_extraction(
        r2_path=r2_path,
        meeting_id=meta["meeting_id"],
        pm_notes=pm_notes,
        r2_client=r2,
    )
    parsed = yaml.safe_load(result.insights_yaml)
    assert "client" in parsed
    # With PM notes, sentiment should shift
    assert parsed["client"].get("sentiment") in ("mixed", "positive", "neutral")


# ── Non-live unit tests ───────────────────────────────────────────

def test_yaml_fence_stripping():
    """Extractor should strip markdown fences from LLM output."""
    from iris.core.extractor import _parse_and_validate_yaml

    raw = "```yaml\nmeeting_id: test-123\nextraction_confidence: 0.85\n```"
    parsed, clean = _parse_and_validate_yaml(raw, "test-123")
    assert parsed["meeting_id"] == "test-123"
    assert "```" not in clean


def test_confidence_extraction():
    """Confidence clamped to [0, 1]."""
    from iris.core.extractor import _extract_confidence

    assert _extract_confidence({"extraction_confidence": 0.95}) == 0.95
    assert _extract_confidence({"extraction_confidence": 1.5}) == 1.0
    assert _extract_confidence({"extraction_confidence": -0.1}) == 0.0
    assert _extract_confidence({}) == 0.5


def test_r2_client_seed_and_read(tmp_path):
    """R2 client correctly writes and reads meeting files."""
    from iris.storage.r2_client import R2Client

    r2 = R2Client(base_path=str(tmp_path))
    r2_path = "/projects/PROJ-TEST/2025-05-06_test-001"
    r2.seed_meeting(
        r2_path,
        {"meeting_id": "test-001", "project_id": "PROJ-TEST"},
        [{"type": "internal", "intranet_id": "p-test"}],
        "Hello world transcript",
    )

    assert r2.exists(r2_path, "metadata.json")
    assert r2.exists(r2_path, "attendees.json")
    assert r2.exists(r2_path, "transcript.txt")

    meta = r2.read_json(r2_path, "metadata.json")
    assert meta["meeting_id"] == "test-001"

    transcript = r2.read_text(r2_path, "transcript.txt")
    assert transcript == "Hello world transcript"


def test_trigger_rejects_incomplete_transcript(client, r2_client, tmp_r2_base):
    """Trigger endpoint must reject processing-status transcripts."""
    import json
    from datetime import datetime

    response = client.post(
        "/iris/trigger",
        json={
            "meeting_id": "test-partial",
            "project_id": "PROJ-TEST",
            "r2_path": "/projects/PROJ-TEST/2025-05-06_test-partial",
            "transcript_status": "processing",
            "triggered_at": datetime.utcnow().isoformat(),
        },
    )
    assert response.status_code == 400
    assert "completed" in response.json()["detail"]
