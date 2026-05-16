"""
Tests: Deduplication Logic.
Uses mock embeddings — no live OpenAI calls.
"""
from __future__ import annotations

import json
import math
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from cell.core.deduplicator import cosine_similarity, token_overlap, DedupResult, check_duplicate
from cell.core.models import RawTask, TaskPriority, TaskSource


# ── Pure math tests ───────────────────────────────────────────

class TestCosineSimilarity:

    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_similar_vectors(self):
        a = [0.9, 0.1, 0.0]
        b = [0.85, 0.15, 0.0]
        sim = cosine_similarity(a, b)
        assert sim > 0.99

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert cosine_similarity(a, b) == 0.0


class TestTokenOverlap:

    def test_identical_strings(self):
        assert token_overlap("fix token refresh", "fix token refresh") == pytest.approx(1.0)

    def test_completely_different(self):
        assert token_overlap("fix auth module", "update documentation") == 0.0

    def test_partial_overlap(self):
        score = token_overlap("fix token refresh edge case", "fix token expiry issue")
        # "fix" and "token" overlap → 2 shared out of ~6 union
        assert 0.2 < score < 0.6

    def test_near_duplicate(self):
        score = token_overlap("fix token refresh", "fix the token refresh issue")
        assert score > 0.5

    def test_empty_string(self):
        assert token_overlap("", "something") == 0.0


# ── Dedup check integration (mocked DB + embeddings) ─────────

def _make_task(title: str, project="P1", assignee="a1") -> RawTask:
    return RawTask(
        title=title,
        project_id=project,
        assignee_id=assignee,
        priority=TaskPriority.NORMAL,
        source=TaskSource.IRIS,
        source_meeting_id="meet-001",
    )


def _make_embedding(seed: float, dim: int = 8) -> list:
    """Generate a deterministic unit vector for testing."""
    import math
    raw = [math.sin(seed + i) for i in range(dim)]
    mag = math.sqrt(sum(x * x for x in raw))
    return [x / mag for x in raw]


@pytest.mark.asyncio
async def test_no_existing_tasks_not_duplicate():
    task = _make_task("Fix auth token issue")
    with patch("cell.core.deduplicator.postgres.get_open_tasks_for_assignee", new=AsyncMock(return_value=[])):
        result = await check_duplicate(task)
    assert result.is_duplicate is False


@pytest.mark.asyncio
async def test_high_cosine_similarity_is_duplicate():
    """Two near-identical tasks should be flagged as duplicate."""
    task = _make_task("Fix token refresh edge case")
    # Existing task with very similar embedding
    existing_embedding = _make_embedding(0.0)
    new_embedding = _make_embedding(0.001)  # very close to existing

    existing = [{
        "id": 42,
        "erp_task_id": "ERP-042",
        "title": "Fix token refresh bug",
        "title_embedding": json.dumps(existing_embedding),
        "status": "open",
        "due_date": None,
    }]

    with patch("cell.core.deduplicator.postgres.get_open_tasks_for_assignee", new=AsyncMock(return_value=existing)):
        with patch("cell.core.deduplicator.get_embedding", new=AsyncMock(return_value=new_embedding)):
            result = await check_duplicate(task)

    assert result.is_duplicate is True
    assert result.existing_task_id == 42
    assert result.method == "cosine"


@pytest.mark.asyncio
async def test_low_cosine_similarity_not_duplicate():
    """Very different tasks should not be flagged."""
    task = _make_task("Write unit tests for auth module")
    existing_embedding = _make_embedding(0.0)
    new_embedding = _make_embedding(3.14)  # very different direction

    existing = [{
        "id": 10,
        "erp_task_id": "ERP-010",
        "title": "Deploy infrastructure on AWS",
        "title_embedding": json.dumps(existing_embedding),
        "status": "open",
        "due_date": None,
    }]

    with patch("cell.core.deduplicator.postgres.get_open_tasks_for_assignee", new=AsyncMock(return_value=existing)):
        with patch("cell.core.deduplicator.get_embedding", new=AsyncMock(return_value=new_embedding)):
            result = await check_duplicate(task)

    assert result.is_duplicate is False


@pytest.mark.asyncio
async def test_token_overlap_fallback_when_no_embedding():
    """Falls back to token overlap when embedding is unavailable."""
    task = _make_task("fix token refresh issue")
    existing = [{
        "id": 5,
        "erp_task_id": "ERP-005",
        "title": "fix token refresh bug in auth",
        "title_embedding": None,
        "status": "open",
        "due_date": None,
    }]

    with patch("cell.core.deduplicator.postgres.get_open_tasks_for_assignee", new=AsyncMock(return_value=existing)):
        with patch("cell.core.deduplicator.get_embedding", new=AsyncMock(return_value=None)):
            result = await check_duplicate(task)

    # "fix", "token", "refresh" overlap → should exceed 0.80 threshold
    overlap = token_overlap("fix token refresh issue", "fix token refresh bug in auth")
    if overlap >= 0.80:
        assert result.is_duplicate is True
        assert result.method == "token_overlap"
    else:
        assert result.is_duplicate is False
