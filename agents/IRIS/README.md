# IRIS — Insight & Record Intelligence System

Extraction intelligence agent (Agent 1). Reads completed meeting artifacts from R2 storage, extracts structured insights via LLM, writes `insights.yaml`, and emits an event to NERVE.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Required env vars

```
LLM_PROVIDER=anthropic           # or "openai"
ANTHROPIC_API_KEY=sk-ant-...     # if using Anthropic
OPENAI_API_KEY=sk-...            # if using OpenAI
```

---

## Running the service

**Terminal 1 — IRIS:**
```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Mock intranet API:**
```bash
python -m iris.mocks.intranet_server
```

**Terminal 3 — Mock NERVE receiver:**
```bash
python -m iris.mocks.nerve_server
```

---

## Triggering a test extraction

### Option A — seed + trigger script

```bash
# Single meeting type
python scripts/seed_and_trigger.py --type client-call --provider anthropic
python scripts/seed_and_trigger.py --type standup --provider openai

# All meeting types
python scripts/seed_and_trigger.py --type all --provider anthropic
```

### Option B — direct API call

```bash
curl -X POST http://localhost:8000/iris/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "abc-defg-hij",
    "project_id": "PROJ-CRM-0014",
    "r2_path": "/projects/PROJ-CRM-0014/2025-05-06_abc-defg-hij",
    "transcript_status": "completed",
    "triggered_at": "2025-05-06T14:32:00Z"
  }'
```

Add `?provider=openai` to override the LLM for a single request:
```
POST /iris/trigger?provider=openai
```

### PM correction rerun

```bash
curl -X POST http://localhost:8000/iris/rerun \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_id": "abc-defg-hij",
    "pm_notes": "Sentiment should be mixed not negative. Credentials arriving Thursday."
  }'
```

---

## Running tests

```bash
# Unit tests only (no API keys needed)
pytest -m "not live"

# All tests including real LLM calls
ANTHROPIC_API_KEY=sk-ant-... pytest -m live -v

# Single meeting type test
pytest tests/test_extractor.py::test_client_call_extraction -m live -v

# A/B comparison test (requires both keys)
ANTHROPIC_API_KEY=... OPENAI_API_KEY=... pytest tests/test_extractor.py::test_provider_comparison_standup -m live -v
```

---

## LLM provider switching

| Method | Effect |
|--------|--------|
| `.env` — `LLM_PROVIDER=anthropic` | Default for all requests |
| `.env` — `LLM_PROVIDER=openai` | Default for all requests |
| `?provider=anthropic` query param | Override for one request |
| `?provider=openai` query param | Override for one request |

**Models used:**
- Anthropic: `claude-haiku-4-5`
- OpenAI: `gpt-4o-mini`

Both are configurable via `ANTHROPIC_MODEL` / `OPENAI_MODEL` env vars.

---

## Project structure

```
IRIS/
├── main.py                    # FastAPI entrypoint
├── requirements.txt
├── .env.example
├── iris/
│   ├── config.py              # Settings (pydantic-settings)
│   ├── api/routes.py          # POST /iris/trigger, /iris/rerun, /iris/health
│   ├── core/
│   │   ├── models.py          # Pydantic models
│   │   ├── extractor.py       # Extraction pipeline
│   │   └── emitter.py         # NERVE event emitter
│   ├── llm/client.py          # Dual LLM client (Anthropic + OpenAI)
│   ├── prompts/
│   │   ├── system.py          # Shared system prompt
│   │   └── templates.py       # Per-meeting-type extraction templates
│   ├── storage/r2_client.py   # R2 abstraction (local filesystem mock)
│   └── mocks/
│       ├── intranet_server.py # Mock employee API (port 8001)
│       ├── intranet_client.py # Client with in-memory caching
│       └── nerve_server.py    # Mock NERVE receiver (port 8002)
├── tests/
│   ├── conftest.py
│   ├── test_extractor.py      # Full test suite (unit + live LLM)
│   └── fixtures/meetings/     # One fixture per meeting type
└── scripts/
    └── seed_and_trigger.py    # Quick end-to-end test script
```

---

## Supported meeting types

| Type | Section key | consumer_level |
|------|-------------|---------------|
| `standup` | `standup` | pm |
| `sprint-planning` | `internal` | pm |
| `client-call` | `client` | pm |
| `milestone-review` | `milestone_review` | dept-head |
| `cross-dept` | `cross_dept` | pm |
| `design-review` | `design_review` | pm |
| `sales-bd` | `sales_bd` | dept-head |
| `hr` | `hr` | hr-only |
| `company-allhands` | `allhands` | director |
| `vendor` | `vendor` | pm |

Note: `security_level=CONFIDENTIAL` overrides all → `hr-only`.

---

## Output

Each meeting produces `/projects/{project-id}/{date}_{meeting-id}/insights.yaml` in mock R2 (`./mock_r2/`).

After writing, IRIS POSTs to NERVE (`http://localhost:8002/events`):

```json
{
  "event": "iris.extraction.complete",
  "meeting_id": "...",
  "project_id": "...",
  "confidence_score": 0.91,
  "flagged": false,
  "insights_path": "/projects/.../insights.yaml",
  "timestamp": "...",
  "provider": "anthropic"
}
```

`flagged: true` when `confidence_score < 0.6` — NERVE routes these to the PM todo queue.
