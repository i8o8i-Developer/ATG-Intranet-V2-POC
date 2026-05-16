"""
CELL Deduplication Engine.

Strategy: pgvector cosine similarity on text-embedding-3-small embeddings.
Threshold: 0.92 (tuned for short task title strings ~5-15 words).

Rationale vs LLM binary classifier:
- text-embedding-3-small: ~$0.00002/1K tokens — orders of magnitude cheaper
- Latency: single embedding call vs full LLM chat round-trip
- For short task titles, cosine similarity on dense embeddings is more reliable
  than sparse token overlap and cheaper than a classifier call per pair.
- Fallback: exact token overlap > 80% for zero-embedding cases.

Decision: cosine threshold 0.92
  - Below 0.92: likely different tasks
  - 0.92–0.97: high probability same task (e.g. "Fix token refresh" vs "Resolve token refresh issue")
  - Above 0.97: near-identical
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from cell.config import settings
from cell.core.models import RawTask
from cell.db import postgres

logger = logging.getLogger(__name__)

_openai: Optional[AsyncOpenAI] = None


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


# ──────────────────────────────────────────────────────────────
# Embedding helper
# ──────────────────────────────────────────────────────────────

async def get_embedding(text: str) -> Optional[List[float]]:
    """Return embedding vector for text. Returns None on failure."""
    try:
        client = _get_openai()
        resp = await client.embeddings.create(
            model=settings.openai_embedding_model,
            input=text.strip(),
        )
        return resp.data[0].embedding
    except Exception as exc:
        logger.warning("Embedding failed for '%s': %s", text[:60], exc)
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def token_overlap(a: str, b: str) -> float:
    """Compute Jaccard token overlap between two strings."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


# ──────────────────────────────────────────────────────────────
# Dedup check
# ──────────────────────────────────────────────────────────────

class DedupResult:
    def __init__(
        self,
        is_duplicate: bool,
        existing_task_id: Optional[int] = None,
        existing_erp_id: Optional[str] = None,
        similarity: float = 0.0,
        method: str = "none",
    ):
        self.is_duplicate = is_duplicate
        self.existing_task_id = existing_task_id
        self.existing_erp_id = existing_erp_id
        self.similarity = similarity
        self.method = method

    def __repr__(self) -> str:
        return (
            f"DedupResult(dup={self.is_duplicate}, id={self.existing_task_id}, "
            f"sim={self.similarity:.3f}, method={self.method})"
        )


async def check_duplicate(task: RawTask) -> DedupResult:
    """
    Check if `task` is a duplicate of any open/in-progress task
    for the same project + assignee.

    Returns DedupResult.
    """
    existing = await postgres.get_open_tasks_for_assignee(
        task.project_id, task.assignee_id
    )
    if not existing:
        return DedupResult(is_duplicate=False)

    # Get embedding for new task title
    new_embedding = await get_embedding(task.title)

    best_sim = 0.0
    best_task: Optional[Dict[str, Any]] = None

    for existing_task in existing:
        sim = 0.0
        method = "token_overlap"

        # Try embedding similarity first
        if new_embedding and existing_task.get("title_embedding"):
            try:
                existing_vec = json.loads(existing_task["title_embedding"])
                sim = cosine_similarity(new_embedding, existing_vec)
                method = "cosine"
            except (json.JSONDecodeError, TypeError):
                sim = 0.0

        # Fallback: token overlap
        if sim == 0.0:
            sim = token_overlap(task.title, existing_task["title"])
            method = "token_overlap"
            # Adjust threshold for token overlap
            threshold = settings.dedup_token_overlap_threshold
        else:
            threshold = settings.dedup_cosine_threshold

        if sim >= threshold and sim > best_sim:
            best_sim = sim
            best_task = {**existing_task, "_method": method, "_threshold": threshold}

    if best_task:
        logger.info(
            "Duplicate detected: '%s' matches task_id=%s (sim=%.3f, method=%s)",
            task.title, best_task["id"], best_sim, best_task["_method"],
        )
        return DedupResult(
            is_duplicate=True,
            existing_task_id=best_task["id"],
            existing_erp_id=best_task.get("erp_task_id"),
            similarity=best_sim,
            method=best_task["_method"],
        )

    return DedupResult(is_duplicate=False)


async def get_embedding_for_storage(text: str) -> Optional[str]:
    """Get embedding and return as JSON string for pgvector storage."""
    vec = await get_embedding(text)
    return json.dumps(vec) if vec else None
