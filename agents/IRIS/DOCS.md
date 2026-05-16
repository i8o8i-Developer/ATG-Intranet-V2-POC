# IRIS — Technical Documentation

**Full name:** Insight & Record Intelligence System  
**Role in pipeline:** Agent 1 — extracts structured insights from completed meeting artifacts  
**Port:** 8000  
**Language:** Python 3.11+ / FastAPI

---

## What IRIS does

IRIS is triggered after a meeting is fully saved. It reads three files from R2 (or local mock):
- `metadata.json` — meeting type, project, attendees counts
- `attendees.json` — participant list with intranet IDs
- `transcript.txt` — raw transcript

It calls an LLM (Anthropic Claude Haiku or OpenAI GPT-4o-mini), extracts a meeting-type-specific structured YAML, writes `insights.yaml` back to R2, then fires a `iris.extraction.complete` event to NERVE.

---

## API Endpoints

### `POST /iris/trigger`

Triggered when a meeting record is fully saved. Only processes meetings with `transcript_status: completed`.

**Request body:**
```json
{
  "meeting_id": "abc-defg-hij",
  "project_id": "PROJ-CRM-0014",
  "r2_path": "/projects/PROJ-CRM-0014/2025-05-06_abc-defg-hij",
  "transcript_status": "completed",
  "triggered_at": "2025-05-06T14:32:00Z"
}
```

**Query param (optional):** `?provider=openai` — overrides LLM for this single request.

**Response `200`:**
```json
{
  "event": "iris.extraction.complete",
  "meeting_id": "abc-defg-hij",
  "project_id": "PROJ-CRM-0014",
  "confidence_score": 0.91,
  "flagged": false,
  "insights_path": "/projects/PROJ-CRM-0014/2025-05-06_abc-defg-hij/insights.yaml",
  "timestamp": "2025-05-06T14:32:11Z",
  "provider": "anthropic"
}
```

**Error codes:**
| Code | Meaning |
|------|---------|
| 400 | `transcript_status` is not `completed` |
| 404 | R2 artifacts not found |
| 422 | LLM returned invalid YAML |
| 500 | Unexpected extraction failure |

---

### `POST /iris/rerun`

Re-runs extraction for a meeting with PM correction notes. Overwrites `insights.yaml`. Use when the PM disagrees with auto-extracted sentiment, tasks, etc.

**Request body:**
```json
{
  "meeting_id": "abc-defg-hij",
  "pm_notes": "Sentiment should be mixed not negative. Credentials arriving Thursday."
}
```

**Response:** Same shape as `/iris/trigger`.

---

### `GET /iris/health`

```json
{
  "status": "ok",
  "service": "iris",
  "llm": { "provider": "anthropic", "model": "claude-haiku-4-5" }
}
```

---

## NERVE Event Emitted

After every successful extraction, IRIS POSTs to `NERVE_WEBHOOK_URL`:

```json
{
  "event": "iris.extraction.complete",
  "meeting_id": "...",
  "project_id": "...",
  "confidence_score": 0.91,
  "flagged": false,
  "insights_path": "/projects/...",
  "timestamp": "...",
  "provider": "anthropic"
}
```

**`flagged: true`** when `confidence_score < 0.6` — NERVE should route flagged events to the PM review queue. CELL still processes them but annotates the task with a low-confidence warning.

---

## insights.yaml Schema

Every extraction produces a YAML with a **BASE** section (common to all types) plus a **type-specific** section.

### BASE fields (always present)

```yaml
meeting_id: abc-defg-hij
project_id: PROJ-CRM-0014
date: "2025-05-06"
meeting_type: standup           # one of 10 supported types
duration_minutes: 30
security_level: INTERNAL        # or CONFIDENTIAL (forces hr-only consumer)
organiser_id: p-ananya-001
attendee_count_internal: 5
attendee_count_external: 0
extraction_confidence: 0.91     # 0.0–1.0; < 0.6 = flagged
extraction_review: false
language_mix: en
follow_up_owner: p-ananya-001
follow_up_type: planned         # none | planned | forced
next_meeting_date: "2025-05-07"
previous_meeting_ref: null
tags: [sprint, blocker]
consumer_level: pm              # pm | dept-head | director | hr-only
```

### Type-specific sections

| Meeting type | YAML section key | consumer_level |
|---|---|---|
| `standup` | `standup` | `pm` |
| `sprint-planning` | `internal` | `pm` |
| `client-call` | `client` | `pm` |
| `milestone-review` | `milestone_review` | `dept-head` |
| `cross-dept` | `cross_dept` | `pm` |
| `design-review` | `design_review` | `pm` |
| `sales-bd` | `sales_bd` | `dept-head` |
| `hr` | `hr` | `hr-only` |
| `company-allhands` | `allhands` | `director` |
| `vendor` | `vendor` | `pm` |

> **Rule:** `security_level: CONFIDENTIAL` overrides all → `hr-only`.

---

## LLM Configuration

| Env var | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | Default provider |
| `ANTHROPIC_API_KEY` | — | Required if using Anthropic |
| `OPENAI_API_KEY` | — | Required if using OpenAI |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Override Anthropic model |
| `OPENAI_MODEL` | `gpt-4o-mini` | Override OpenAI model |

Per-request override: `POST /iris/trigger?provider=openai`

---

## Production Readiness Assessment

### What is ready
- Full FastAPI service with structured error handling
- Pydantic v2 request/response validation on all endpoints
- YAML repair logic handles common LLM output failures (unquoted colons)
- Confidence scoring + flagging pipeline
- Per-meeting-type prompt templates covering all 10 types
- Dual LLM provider support (Anthropic + OpenAI) with per-request override
- Unit tests + live LLM tests with `pytest -m "not live"` separation
- PM rerun endpoint for corrections
- Mock R2, mock intranet, and mock NERVE server for local dev

### Gaps before production deploy

| # | Issue | Severity | Fix needed |
|---|---|---|---|
| 1 | **R2 is mocked (local filesystem)** | Critical | Replace `iris/storage/r2_client.py` with real Cloudflare R2 / boto3 implementation using `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` env vars |
| 2 | **NERVE emit is fire-and-forget with no retry** | High | `emitter.py:57` logs the error but does not retry. In production, add a retry queue (DB or Redis) for failed NERVE pings |
| 3 | **No authentication on endpoints** | High | `/iris/trigger` and `/iris/rerun` have no auth. Add an `X-API-Key` header check or mTLS before exposing to network |
| 4 | **Extraction is synchronous** | Medium | `/iris/trigger` blocks the HTTP thread while calling the LLM (can take 5–15s). Wrap in `BackgroundTasks` and return `202 Accepted` immediately |
| 5 | **Intranet API is mocked** | Medium | `iris/mocks/intranet_client.py` is used for employee lookups. Wire to real intranet API before go-live |
| 6 | **No rate limiting** | Medium | Multiple triggers in quick succession could exhaust LLM API quota |
| 7 | **Pinned package versions are slightly old** | Low | `anthropic==0.34.2` and `openai==1.45.0` — verify against latest before deploy |

---

## Environment Variables (production)

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...            # keep as fallback even if not default

# Production R2 (replace mock)
R2_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=erp-agents

# Real intranet API
INTRANET_API_BASE_URL=https://intranet.internal/api

# NERVE (= CELL's /cell/ingest-nerve endpoint)
NERVE_WEBHOOK_URL=https://cell.internal/cell/ingest-nerve

IRIS_HOST=0.0.0.0
IRIS_PORT=8000
LOG_LEVEL=INFO
```

---

## BE Integration — What the backend needs to call

IRIS has a single integration surface for the backend:

### Trigger IRIS after meeting record is saved

```
POST https://iris.internal/iris/trigger
Content-Type: application/json
X-API-Key: <your-api-key>

{
  "meeting_id": "<uuid>",
  "project_id": "<project-id>",
  "r2_path": "/projects/<project-id>/<YYYY-MM-DD>_<meeting-id>",
  "transcript_status": "completed",
  "triggered_at": "<ISO8601 timestamp>"
}
```

**When to call:** After the meeting processing pipeline sets `transcript_status = "completed"` in the DB.

**What to do with the response:**
- Store `insights_path` from the response so you can retrieve the YAML later if needed.
- If `flagged: true` — surface a review prompt in the PM dashboard.
- If `confidence_score < 0.6` and `flagged: true` — you may skip auto-routing and queue for manual review.

### Trigger a PM correction rerun

```
POST https://iris.internal/iris/rerun
Content-Type: application/json

{
  "meeting_id": "<uuid>",
  "pm_notes": "Free text PM correction instructions"
}
```

This re-extracts using the same artifacts + PM notes, overwrites `insights.yaml`, and re-fires the NERVE event.

### Files IRIS expects pre-uploaded to R2

Before calling `/iris/trigger`, the meeting processing pipeline must have uploaded to `r2_path/`:
- `metadata.json` — see `MeetingMetadata` model
- `attendees.json` — list of `Attendee` objects
- `transcript.txt` — raw transcript text
